#!/bin/bash

# Check if CRON_SCHEDULE is set
if [ -z "$CRON_SCHEDULE" ]; then
    echo "CRON_SCHEDULE not set. Running the script once and exiting..."
    /usr/bin/python3 /app/script.py
    exit 0
fi

# If CRON_SCHEDULE is set, continue with cron setup
echo "Using schedule: $CRON_SCHEDULE"

# Set log directory and filename
LOG_DIR="/logs/geoip"
mkdir -p "$LOG_DIR"

# Function to generate unique log filename
generate_log_filename() {
    echo "${LOG_DIR}/geoip_$(date '+%Y-%m-%d_%H-%M-%S').log"
}

# Create a cron job
CRON_LOG_FILE=$(generate_log_filename)
echo "$CRON_SCHEDULE /usr/bin/python3 /app/script.py >> /logs/geoip/geoip_\$(date '+%Y-%m-%d_%H-%M-%S').log 2>&1" > /etc/cron.d/geoip-cron

# Apply the cron job
chmod 0644 /etc/cron.d/geoip-cron
crontab /etc/cron.d/geoip-cron

# Start the cron service in the background
service cron start

# Run the script immediately with unique log file
IMMEDIATE_LOG_FILE=$(generate_log_filename)
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running the script immediately..." >> /logs/geoip/geoip_container.log
/usr/bin/python3 /app/script.py >> "$IMMEDIATE_LOG_FILE" 2>&1

# Keep the container alive
tail -f /dev/null
