import os
import requests
import logging
import tarfile
import shutil
from datetime import datetime, timedelta

MAXMIND_VALIDATION_URL = "https://secret-scanning.maxmind.com/secrets/validate-license-key"
DOWNLOAD_URL_TEMPLATE = "https://download.maxmind.com/app/geoip_download?edition_id={edition_id}&license_key={license_key}&suffix=tar.gz"

EDITION_IDS = {
    "Country": "GeoLite2-Country",
    "ASN": "GeoLite2-ASN"
}

def validate_license_key(license_key):
    logging.info("Validating MaxMind License Key...")
    try:
        response = requests.post(
            MAXMIND_VALIDATION_URL,
            data={"license_key": license_key},
            timeout=10
        )
        
        if response.status_code == 204:
            logging.info("License Key is valid.")
            return True
        elif response.status_code == 401:
            logging.error("License Key invalid or unauthorized (401).")
            return False
        else:
            logging.error(f"License Key validation failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.RequestException as e:
        logging.error(f"Network error during license key validation: {e}")
        return False

def should_update(file_path):
    if not os.path.exists(file_path):
        logging.info(f"File {file_path} does not exist. Update required.")
        return True
    
    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
    age = datetime.now() - file_time
    
    if age > timedelta(days=7):
        logging.info(f"File {file_path} is {age.days} days old. Update required.")
        return True
    
    logging.info(f"File {file_path} is fresh ({age.days} days old). No update needed.")
    return False

def download_database(edition_id, license_key, output_dir):
    url = DOWNLOAD_URL_TEMPLATE.format(edition_id=edition_id, license_key=license_key)
    logging.info(f"Downloading {edition_id} from MaxMind...")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        
        if response.status_code != 200:
            logging.error(f"Failed to download {edition_id}. Status: {response.status_code}")
            return False
        
        tar_path = os.path.join(output_dir, f"{edition_id}.tar.gz")
        
        with open(tar_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logging.info(f"Extracting {edition_id}...")
        with tarfile.open(tar_path, "r:gz") as tar:
            
            mmdb_member = None
            for member in tar.getmembers():
                if member.name.endswith(".mmdb"):
                    mmdb_member = member
                    break
            
            if mmdb_member:
                mmdb_file = tar.extractfile(mmdb_member)
                target_path = os.path.join(output_dir, f"{edition_id}.mmdb")
                with open(target_path, 'wb') as out:
                    shutil.copyfileobj(mmdb_file, out)
                logging.info(f"Successfully updated {target_path}")
            else:
                logging.error(f"Could not find .mmdb file in {edition_id} archive.")

        os.remove(tar_path)
        return True
        
    except Exception as e:
        logging.error(f"Error downloading/extracting {edition_id}: {e}")
        return False

def update_databases(license_key, output_dir):
    if not license_key:
        logging.warning("No MAXMIND_LICENSE_KEY provided. Skipping updates.")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    country_path = os.path.join(output_dir, f"{EDITION_IDS['Country']}.mmdb")
    asn_path = os.path.join(output_dir, f"{EDITION_IDS['ASN']}.mmdb")
    
    needs_update_country = should_update(country_path)
    needs_update_asn = should_update(asn_path)
    
    if needs_update_country or needs_update_asn:
        if not validate_license_key(license_key):
            logging.error("Aborting updates due to invalid license key.")
            return

        if needs_update_country:
            download_database(EDITION_IDS['Country'], license_key, output_dir)
            
        if needs_update_asn:
            download_database(EDITION_IDS['ASN'], license_key, output_dir)
    else:
        logging.info("All databases are up to date.")
