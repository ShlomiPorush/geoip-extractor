#!/bin/bash

# Set log directory
LOG_DIR="/logs/geoip"
mkdir -p "$LOG_DIR"

# Generate unique log filename
LOG_FILE="${LOG_DIR}/geoip_$(date '+%Y-%m-%d_%H-%M-%S').log"

# Default CRON schedule: Every Saturday at 3 AM (0 3 * * 6)
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 3 * * 6"}

echo "Starting GeoIP Extractor..."
echo "CRON Schedule: $CRON_SCHEDULE"

# Save environment variables for Cron
printenv | grep -v "no_proxy" >> /etc/environment

# Setup Cron Job
# We redirect stdout/stderr to the log file so we can tail it
# We explicitly source /etc/environment to ensure Cron sees the container variables
echo "$CRON_SCHEDULE . /etc/environment; /usr/local/bin/python /app/script.py >> $LOG_FILE 2>&1" > /etc/cron.d/geoip-cron
chmod 0644 /etc/cron.d/geoip-cron
crontab /etc/cron.d/geoip-cron

# Run the script immediately once on startup (optional, but good for verification)
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running initial extraction..."
python /app/script.py >> "$LOG_FILE" 2>&1

# Start Cron in foreground (or tail logs)
echo "$(date '+%Y-%m-%d %H:%M:%S') - Inital run complete. Waiting for next schedule..."
cron && tail -f "$LOG_FILE"
