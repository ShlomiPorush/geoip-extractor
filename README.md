# GeoIP Extractor

IPv4 ranges for every country and every provider, built from MaxMind GeoLite2.

GeoIP Extractor reads the GeoLite2 Country and ASN databases and writes plain-text CIDR lists: one file per country, one file of ASN details per country, and one file per provider (ASN). Use the lists in firewalls, allowlists, and blocklists. It runs in Docker, keeps the databases up to date with your MaxMind license key, and repeats the extraction on a cron schedule.

## Features

- Per-country IP ranges and ASN details.
- Per-provider (ASN) IP ranges.
- A global ASN blacklist that removes providers, such as Google or Amazon, from the country lists.
- Automatic MaxMind database downloads when a database is missing or older than 7 days.
- Scheduled runs, weekly by default, with progress percentages in the log.

## Installation

You need Docker with Docker Compose and a free [MaxMind license key](https://www.maxmind.com/).

1. Create `docker-compose.yml`:

	```yaml
	services:
	  geoip-extractor:
	    image: ghcr.io/shlomiporush/geoip-extractor:latest
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

2. Create `.env` next to it:

	```ini
	MAXMIND_LICENSE_KEY=
	```

	Set the value to your license key.

3. Start the container:

	```bash
	docker compose up -d
	```

The container downloads the databases, runs the first extraction, and then waits for the next scheduled run. The files appear in `output/`.

To update, run `docker compose pull && docker compose up -d`. To uninstall, run `docker compose down`.

## Common questions

**The log says "MaxMind database files are missing".**
The error names the missing files. Set a valid `MAXMIND_LICENSE_KEY` so the container downloads them, or mount your own `GeoLite2-Country.mmdb` and `GeoLite2-ASN.mmdb` into `MAXMIND_DIR`, which is `/app/maxmind` by default.

**Why does a provider appear in `output/asn` but not in the country files?**
The country files leave out the providers on the global ASN blacklist. They also sample one address per /24 block, so a small range can be missing from them. The provider files use the exact ranges from the ASN database.

**How do I follow a run?**
Run `tail -f` on the newest file in `logs/`. Each of the three steps logs its progress every 10%, and the last line gives the total run time. `docker logs -f geoip-extractor` also shows scheduled runs, but it shows the first run only after it finishes.

## Documentation

- [Configuration](docs/configuration.md): environment variables, paths, the schedule, and the blacklist.
- [Output files](docs/output.md): the files that a run writes and their format.

<details>
<summary>Stack</summary>

- Python 3.10 with `geoip2`, `maxminddb`, `PyYAML`, and `requests`.
- Docker, with cron for scheduled runs.
- GitHub Actions publishes the image to GitHub Container Registry.

</details>

## Credits

This product includes GeoLite2 data created by MaxMind, available from [https://www.maxmind.com](https://www.maxmind.com).
