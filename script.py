import geoip2.database
import ipaddress
import os
import logging
import yaml
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Paths and configurations
MMDB_COUNTRY_FILE = "GeoLite2-Country.mmdb"
MMDB_ASN_FILE = "GeoLite2-ASN.mmdb"
CONFIG_FILE = "config.yaml"
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output_ips/")

# Load configuration
with open(CONFIG_FILE, "r") as config_file:
    config = yaml.safe_load(config_file)

# Load global ASN blacklist
GLOBAL_ASN_BLACKLIST = config.get("global_asn_blacklist", [])
if not GLOBAL_ASN_BLACKLIST:
    logging.warning("Global ASN blacklist is empty. No filtering will be applied.")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Function to format ASN details for comments
def format_asn_list(asn_list):
    return [f"#   {asn['asn']} - {asn.get('name', 'Unknown')}" for asn in asn_list]

# Define a nested defaultdict structure for ASN sets
def nested_defaultdict():
    return defaultdict(set)

# Function to process a single /8 block
def process_block(block_index):
    logging.info(f"Processing block {block_index}.0.0.0/8...")
    subnets = defaultdict(list)
    asn_set = defaultdict(nested_defaultdict)

    try:
        ip_block = ipaddress.IPv4Network(f"{block_index}.0.0.0/8")
        with geoip2.database.Reader(MMDB_COUNTRY_FILE) as country_reader, geoip2.database.Reader(MMDB_ASN_FILE) as asn_reader:
            for subnet in ip_block.subnets(new_prefix=24):
                try:
                    # Get country information
                    country_response = country_reader.country(subnet.network_address.exploded)
                    country_code = country_response.country.iso_code

                    # Skip if country code is missing
                    if not country_code:
                        continue

                    # Get ASN information
                    asn_response = asn_reader.asn(subnet.network_address.exploded)
                    asn_number = asn_response.autonomous_system_number
                    asn_name = asn_response.autonomous_system_organization

                    # Skip IPs with blacklisted ASN
                    if any(asn_number == asn["asn"] for asn in GLOBAL_ASN_BLACKLIST):
                        continue

                    # Add subnet to the country's list
                    subnets[country_code].append(str(subnet))

                    # Add ASN details to the country's ASN list
                    asn_set[country_code][asn_number].add(asn_name)

                except geoip2.errors.AddressNotFoundError:
                    continue

    except Exception as e:
        logging.error(f"Error processing block {block_index}: {e}")
    return subnets, asn_set

# Main processing function
def main():
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
    combined_subnets = defaultdict(list)
    combined_asn_set = defaultdict(nested_defaultdict)

    # Process all /8 blocks in parallel
    logging.info("Starting parallel processing...")
    with ProcessPoolExecutor(max_workers=4) as executor:  # Adjust max_workers to control CPU usage
        results = executor.map(process_block, range(256))

    # Combine results from all blocks
    for subnets, asn_set in results:
        for country_code, subnet_list in subnets.items():
            combined_subnets[country_code].extend(subnet_list)
        for country_code, asn_map in asn_set.items():
            for asn_number, names in asn_map.items():
                combined_asn_set[country_code][asn_number].update(names)

    # Write results to files
    for country_code, subnets in combined_subnets.items():
        logging.info(f"Saving data for country: {country_code}")

        # Collapse subnets to minimize the number of lines
        collapsed_subnets = list(ipaddress.collapse_addresses([ipaddress.IPv4Network(subnet) for subnet in subnets]))

        # Write subnets to file
        subnet_file = os.path.join(OUTPUT_DIR, f"{country_code}.txt")
        with open(subnet_file, "w") as file:
            file.write(f"# Country: {country_code}\n")
            file.write(f"# Generated on: {current_date}\n")
            file.write("# Global ASN Blacklist:\n")
            file.write("\n".join(format_asn_list(GLOBAL_ASN_BLACKLIST)) + "\n")
            file.write("# Subnets:\n")
            file.write("\n".join(map(str, collapsed_subnets)))

        # Write ASN details to file
        asn_file = os.path.join(OUTPUT_DIR, f"{country_code}_ASN.txt")
        with open(asn_file, "w") as file:
            file.write(f"# Country: {country_code}\n")
            file.write(f"# Generated on: {current_date}\n")
            file.write("# ASN Details:\n")
            for asn_number, names in combined_asn_set[country_code].items():
                for name in names:
                    file.write(f"{asn_number} - {name}\n")

    logging.info("Task completed successfully.")

if __name__ == "__main__":
    main()
