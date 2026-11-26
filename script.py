import geoip2.database
import maxminddb
import ipaddress
import os
import logging
import yaml
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import maxmind_updater

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Paths and configurations
# Use a directory for maxmind files to keep them organized
MAXMIND_DIR = os.getenv("MAXMIND_DIR", "maxmind")
MMDB_COUNTRY_FILE = os.path.join(MAXMIND_DIR, "GeoLite2-Country.mmdb")
MMDB_ASN_FILE = os.path.join(MAXMIND_DIR, "GeoLite2-ASN.mmdb")
CONFIG_DIR = os.getenv("CONFIG_DIR", "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output/")
PROVIDER_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "asn")

# Load configuration
config = {}
if os.path.exists(CONFIG_FILE):
    logging.info(f"Loading configuration from {CONFIG_FILE}...")
    try:
        with open(CONFIG_FILE, "r") as config_file:
            config = yaml.safe_load(config_file) or {}
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
else:
    logging.info(f"Configuration file {CONFIG_FILE} not found. Using defaults.")

# Load global ASN blacklist
GLOBAL_ASN_BLACKLIST = config.get("global_asn_blacklist", [])
if not GLOBAL_ASN_BLACKLIST:
    logging.info("Global ASN blacklist is empty. No filtering will be applied.")

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

def log_progress(step, done, total):
    percent = done * 100 // total
    previous_percent = (done - 1) * 100 // total
    if done == total or percent // 10 != previous_percent // 10:
        logging.info(f"{step}: {percent}% ({done}/{total})")

# Main processing function
def main():
    started_at = datetime.now()
    # Attempt to update databases first
    license_key = os.getenv("MAXMIND_LICENSE_KEY")
    if license_key:
        logging.info("Checking for MaxMind database updates...")
        maxmind_updater.update_databases(license_key, MAXMIND_DIR)
    else:
        logging.warning("MAXMIND_LICENSE_KEY not found. Skipping update check.")

    current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
    combined_subnets = defaultdict(list)
    combined_asn_set = defaultdict(nested_defaultdict)

    block_count = 256
    logging.info(f"Step 1/3 Scanning IP blocks: started ({block_count} blocks)")
    with ProcessPoolExecutor(max_workers=4) as executor:  # Adjust max_workers to control CPU usage
        for done, (subnets, asn_set) in enumerate(executor.map(process_block, range(block_count)), start=1):
            for country_code, subnet_list in subnets.items():
                combined_subnets[country_code].extend(subnet_list)
            for country_code, asn_map in asn_set.items():
                for asn_number, names in asn_map.items():
                    combined_asn_set[country_code][asn_number].update(names)
            log_progress("Step 1/3 Scanning IP blocks", done, block_count)

    country_count = len(combined_subnets)
    logging.info(f"Step 2/3 Writing country files: started ({country_count} countries)")
    for done, (country_code, subnets) in enumerate(combined_subnets.items(), start=1):
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

        log_progress("Step 2/3 Writing country files", done, country_count)

    export_providers(current_date)

    elapsed = str(datetime.now() - started_at).split(".")[0]
    logging.info(f"Task completed successfully in {elapsed}.")

def export_providers(generated_on):
    provider_networks = defaultdict(list)
    provider_names = {}

    with maxminddb.open_database(MMDB_ASN_FILE) as asn_reader:
        for network, record in asn_reader:
            if network.version != 4 or not record:
                continue
            asn_number = record.get("autonomous_system_number")
            if asn_number is None:
                continue
            provider_networks[asn_number].append(network)
            provider_names[asn_number] = record.get("autonomous_system_organization") or "Unknown"

    provider_count = len(provider_networks)
    logging.info(f"Step 3/3 Writing provider files: started ({provider_count} providers)")
    os.makedirs(PROVIDER_OUTPUT_DIR, exist_ok=True)
    for done, (asn_number, networks) in enumerate(provider_networks.items(), start=1):
        collapsed_networks = ipaddress.collapse_addresses(networks)
        provider_file = os.path.join(PROVIDER_OUTPUT_DIR, f"AS{asn_number}.txt")
        with open(provider_file, "w", encoding="utf-8") as file:
            file.write(f"# ASN: {asn_number}\n")
            file.write(f"# Provider: {provider_names[asn_number]}\n")
            file.write(f"# Generated on: {generated_on}\n")
            file.write("# Subnets:\n")
            file.write("\n".join(map(str, collapsed_networks)) + "\n")
        log_progress("Step 3/3 Writing provider files", done, provider_count)

if __name__ == "__main__":
    main()
