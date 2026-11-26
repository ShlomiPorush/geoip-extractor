# Configuration

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MAXMIND_LICENSE_KEY` | none | MaxMind license key. Without it, the container does not download or update the databases. |
| `CRON_SCHEDULE` | `0 3 * * 6` | Cron expression for scheduled runs. The default is every Saturday at 03:00. |
| `MAXMIND_DIR` | `/app/maxmind` | Directory of `GeoLite2-Country.mmdb` and `GeoLite2-ASN.mmdb`. |
| `CONFIG_DIR` | `/app/config` | Directory of `config.yaml`. |
| `OUTPUT_DIR` | `output/` | Directory for the output files. Relative paths start at `/app`. |

## Database updates

When `MAXMIND_LICENSE_KEY` is set, each run starts by checking both databases. The container downloads a database that is missing or older than 7 days. If MaxMind refuses the download or the network fails, the existing file stays. If a database is missing after this step, the run stops with an error.

If you already keep the databases up to date, for example with `geoipupdate`, leave `MAXMIND_LICENSE_KEY` empty and mount the files into `MAXMIND_DIR`.

## Global ASN blacklist

`config.yaml` in `CONFIG_DIR` lists the providers to remove from the country files:

```yaml
global_asn_blacklist:
  - asn: 15169
    name: "Google LLC"
```

The blacklist does not apply to the provider files in `asn/`. See the [example config](../config/config.yaml).

## Logs

When the container starts, it creates `/logs/geoip/geoip_<date>_<time>.log`. The first run and every scheduled run write to this file until the container restarts. `docker logs` shows the same lines.
