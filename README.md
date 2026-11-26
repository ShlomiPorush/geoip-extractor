# GeoIP Extractor

This project extracts IP ranges and ASN (Autonomous System Numbers) data for all countries from MaxMind's GeoLite2 database. It organizes the data into per-country files with optional filtering based on a global ASN blacklist.

It includes **automatic updates** for MaxMind databases and **Cron scheduling** for periodic execution.

## Features

- **Automated MaxMind Updates**: Checks if database files are older than 7 days and downloads fresh copies using your MaxMind License Key.
- **Scheduled Extraction**: Runs automatically based on a configurable Cron schedule (default: weekly).
- **Efficient Processing**: Minimizes IP ranges using CIDR collapsing and uses multi-processing for speed.
- **Organization**: Outputs per-country IP ranges and ASN details, plus per-provider (ASN) IP ranges.
- **Filtering**: Supports a global ASN blacklist via `config.yaml` see example [config.yaml](config/config.yaml).

---

## Prerequisites

- Docker & Docker Compose.
- A MaxMind License Key.

* [ ] Sign up for a free MaxMind account at [https://www.maxmind.com/](https://www.maxmind.com/)
* [ ] Create a **License Key**

---

## Installation & Usage

1. **Create `docker-compose.yml`:**
   Create a file named `docker-compose.yml` with the following content:
   ```yaml
   services:
     geoip-extractor:
       image: shlomip/geoip-extractor:latest
       container_name: geoip-extractor
       env_file:
         - .env
       volumes:
         - /etc/localtime:/etc/localtime:ro
         - ./maxmind:/app/maxmind
         - ./output:/app/output
         - ./config:/app/config
         - ./logs:/logs/geoip
       tty: true
   ```

2. **Configure Environment:**
   Create a `.env` file in the same directory:
   ```ini
   MAXMIND_LICENSE_KEY=your_actual_license_key
   
   # Optional: Change schedule (Default: Every Saturday at 3 AM)
   CRON_SCHEDULE=0 3 * * 6
   ```

3. **(Optional) Global Blacklist:**
   Create a `config/config.yaml` file to block specific ASNs (e.g., Facebook, Google) from the output.
   ([View example config](config/config.yaml))

4. **Run with Docker:**
   ```bash
   docker compose up -d
   ```

   The container will:
   - Validate your License Key.
   - Download the latest MaxMind databases (if missing or old).
   - Run the initial extraction immediately.
   - Continue running in the background as per the Cron schedule.

5. **Check Logs:**
   ```bash
   docker logs -f geoip-extractor
   ```

---

## Output Files

The extracted files are saved in the `output/` directory:

- `<country_code>.txt`: IP ranges (CIDR format).
- `<country_code>_ASN.txt`: ASN details.
- `asn/AS<number>.txt`: all IP ranges of one provider (ASN), in CIDR format. The global ASN blacklist does not apply to these files.

Example `US.txt`:
```
# Country: US
# Generated on: 19/01/2026 14:00
# ...
8.8.8.0/24
```

---

## Credits

* **Location Data**: This product includes GeoLite2 data created by MaxMind, available from [https://www.maxmind.com](https://www.maxmind.com).