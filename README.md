# GeoIP Extractor

This project extracts IP ranges and ASN (Autonomous System Numbers) data for all countries from MaxMind's GeoLite2 database. It organizes the data into per-country files with optional filtering based on a global ASN blacklist.

---

## Features

- Extracts IP ranges per country from MaxMind's `GeoLite2-Country.mmdb`.
- Extracts ASN data per country from MaxMind's `GeoLite2-ASN.mmdb`.
- Supports filtering by a global ASN blacklist (`config.yaml`).
- Minimizes IP ranges using CIDR collapsing to reduce file size.
- Utilizes multi-processing for better performance.
- Outputs results into organized files:
  - `<country_code>.txt`: Contains the country's IP ranges.
  - `<country_code>_ASN.txt`: Contains the country's ASN details.

---

## Prerequisites

- Python 3.10 or later
- MaxMind GeoLite2 database files:
  - `GeoLite2-Country.mmdb`
  - `GeoLite2-ASN.mmdb`
- Docker (optional, for containerized execution)

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/geoip-extractor.git
   cd geoip-extractor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Place the MaxMind database files in the project directory:
   - `GeoLite2-Country.mmdb`
   - `GeoLite2-ASN.mmdb`

4. Create or edit the `config.yaml` file:
   ```yaml
   global_asn_blacklist:
     - asn: 32934
       name: "Facebook"
     - asn: 15169
       name: "Google LLC"
   ```

---

## Usage

### Local Execution

Run the script:
```bash
python script.py
```

### Using Docker

1. Build the Docker image:
   ```bash
   docker build -t geoip-extractor .
   ```

2. Run the container:
   ```bash
   docker run -v $(pwd):/app -e OUTPUT_DIR=/app/output_ips geoip-extractor
   ```

---

## Output Files

The script generates two files per country:

1. `<country_code>.txt`:
   - Contains the country's IP ranges.
   - Example:
     ```
     # Country: US
     # Generated on: 19/11/2024 14:00
     # Global ASN Blacklist:
     #   32934 - Facebook
     #   15169 - Google LLC
     # Subnets:
     8.8.8.0/24
     8.8.4.0/22
     ```

2. `<country_code>_ASN.txt`:
   - Contains ASN details for the country.
   - Example:
     ```
     # Country: US
     # Generated on: 19/11/2024 14:00
     # ASN Details:
     15169 - Google LLC
     13335 - Cloudflare
     ```

---

## Configuration

The script uses a YAML configuration file (`config.yaml`) for the global ASN blacklist:

```yaml
global_asn_blacklist:
  - asn: 32934
    name: "Facebook"
  - asn: 15169
    name: "Google LLC"
  - asn: 8075
    name: "Microsoft"
```

---

## Performance Optimization

- **Multi-processing**:
  The script uses `ProcessPoolExecutor` to parallelize processing of `/8 blocks`. You can adjust the number of workers with:
  ```python
  with ProcessPoolExecutor(max_workers=4)
  ```

- **Resource Limits in Docker**:
  To avoid overloading the server, use Docker resource limits:
  ```bash
  docker run --cpus="2.0" --memory="4g" geoip-extractor
  ```

---

## Troubleshooting

- **Missing YAML dependency**:
  Ensure `PyYAML` is installed by running:
  ```bash
  pip install PyYAML
  ```

- **Pickle errors in multiprocessing**:
  Ensure there are no `lambda` functions or non-pickleable objects in the code.

- **MaxMind database not found**:
  Ensure `GeoLite2-Country.mmdb` and `GeoLite2-ASN.mmdb` are in the project directory.

---

## License

This project is licensed under the MIT License. See `LICENSE` for more details.

---

## Acknowledgments

- **MaxMind** for providing the GeoLite2 database.
