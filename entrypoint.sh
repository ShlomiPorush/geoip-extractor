#!/bin/bash

# Check if CRON_SCHEDULE is set
if [ -z "$CRON_SCHEDULE" ]; then
    echo "CRON_SCHEDULE not set. Exiting..."
    exit 0
fi

# Using the provided schedule
echo "Using schedule: $CRON_SCHEDULE"

# Set log directory
LOG_DIR="/logs/geoip"
mkdir -p "$LOG_DIR"

# Function to generate unique log filename
generate_log_filename() {
    echo "${LOG_DIR}/geoip_$(date '+%Y-%m-%d_%H-%M-%S').log"
}

# Create a cron job
CRON_LOG_FILE=$(generate_log_filename)
echo "$CRON_SCHEDULE echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Starting scheduled run... Logs will be saved to $CRON_LOG_FILE\" >> /logs/geoip/geoip_container.log; /usr/local/bin/python /app/script.py >> $CRON_LOG_FILE 2>&1" > /etc/cron.d/geoip-cron

# Apply the cron job
chmod 0644 /etc/cron.d/geoip-cron
crontab /etc/cron.d/geoip-cron

# Start the cron service
echo "Starting cron service..."
service cron start

# Keep the container alive
tail -f /dev/null
