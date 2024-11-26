#!/bin/bash

# Set log directory
LOG_DIR="/logs/geoip"
mkdir -p "$LOG_DIR"

# Generate unique log filename
LOG_FILE="${LOG_DIR}/geoip_$(date '+%Y-%m-%d_%H-%M-%S').log"

# Run the script and log output
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting script... Logs will be saved to $LOG_FILE"
python /app/script.py >> "$LOG_FILE" 2>&1

# Log completion and exit
echo "$(date '+%Y-%m-%d %H:%M:%S') - Script completed. Exiting container."
exit 0
