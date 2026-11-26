#!/bin/bash

LOG_DIR="/logs/geoip"
mkdir -p "$LOG_DIR"

LOG_FILE="${LOG_DIR}/geoip_$(date '+%Y-%m-%d_%H-%M-%S').log"
touch "$LOG_FILE"

# Default CRON schedule: Every Saturday at 3 AM (0 3 * * 6)
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 3 * * 6"}
# Set to false to skip the extraction at container start and wait for the schedule.
RUN_ON_START=${RUN_ON_START:-true}

echo "Starting GeoIP Extractor..."
echo "CRON Schedule: $CRON_SCHEDULE"

# cron jobs get the container variables, such as MAXMIND_LICENSE_KEY, only through /etc/environment.
printenv | grep -v "no_proxy" >> /etc/environment

echo "$CRON_SCHEDULE . /etc/environment; /usr/local/bin/python /app/script.py >> $LOG_FILE 2>&1" > /etc/cron.d/geoip-cron
chmod 0644 /etc/cron.d/geoip-cron
crontab /etc/cron.d/geoip-cron

if [ "${RUN_ON_START,,}" = "false" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - RUN_ON_START is false. Skipping the initial extraction. Waiting for next schedule..."
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running initial extraction..."
    python /app/script.py >> "$LOG_FILE" 2>&1
    initial_exit_code=$?
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Initial run ended with exit code $initial_exit_code. Waiting for next schedule..."
fi

cron && tail -f "$LOG_FILE"
