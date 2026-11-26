import io
import os
import logging
import shutil
import tarfile
from datetime import datetime, timedelta

import requests

DOWNLOAD_URL_TEMPLATE = "https://download.maxmind.com/app/geoip_download?edition_id={edition_id}&license_key={license_key}&suffix=tar.gz"
EDITION_IDS = ("GeoLite2-Country", "GeoLite2-ASN")

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
        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            reason = "MAXMIND_LICENSE_KEY is invalid (401)" if response.status_code == 401 else f"status {response.status_code}"
            logging.error(f"Failed to download {edition_id}: {reason}.")
            return

        with tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz") as tar:
            mmdb_member = next((member for member in tar.getmembers() if member.name.endswith(".mmdb")), None)
            if mmdb_member is None:
                logging.error(f"Could not find .mmdb file in {edition_id} archive.")
                return

            mmdb_file = tar.extractfile(mmdb_member)
            target_path = os.path.join(output_dir, f"{edition_id}.mmdb")
            partial_path = f"{target_path}.partial"
            with open(partial_path, "wb") as out:
                shutil.copyfileobj(mmdb_file, out)
            os.replace(partial_path, target_path)
        logging.info(f"Successfully updated {target_path}")

    except Exception as e:
        logging.error(f"Error downloading/extracting {edition_id}: {type(e).__name__}")

def update_databases(license_key, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    outdated_editions = [edition_id for edition_id in EDITION_IDS if should_update(os.path.join(output_dir, f"{edition_id}.mmdb"))]
    for edition_id in outdated_editions:
        download_database(edition_id, license_key, output_dir)
