#!/bin/bash

LOG_DIR="/logs/geoip"
mkdir -p "$LOG_DIR"

LOG_FILE="${LOG_DIR}/geoip_$(date '+%Y-%m-%d_%H-%M-%S').log"

# Default CRON schedule: Every Saturday at 3 AM (0 3 * * 6)
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 3 * * 6"}

echo "Starting GeoIP Extractor..."
echo "CRON Schedule: $CRON_SCHEDULE"

# Without this file and the job sourcing it, cron runs the script without MAXMIND_LICENSE_KEY and the other container variables.
printenv | grep -v "no_proxy" >> /etc/environment

echo "$CRON_SCHEDULE . /etc/environment; /usr/local/bin/python /app/script.py >> $LOG_FILE 2>&1" > /etc/cron.d/geoip-cron
chmod 0644 /etc/cron.d/geoip-cron
crontab /etc/cron.d/geoip-cron

echo "$(date '+%Y-%m-%d %H:%M:%S') - Running initial extraction..."
python /app/script.py >> "$LOG_FILE" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - Inital run complete. Waiting for next schedule..."
cron && tail -f "$LOG_FILE"
