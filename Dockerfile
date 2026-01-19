# Use a lightweight Python image
FROM python:3.10-slim

# Install dependencies, cron, and dos2unix (for fixing Windows line endings)
RUN apt-get update && apt-get install -y cron dos2unix && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and updater
COPY script.py /app/script.py
COPY maxmind_updater.py /app/maxmind_updater.py

# Create MaxMind directory
RUN mkdir -p /app/maxmind
ENV MAXMIND_DIR=/app/maxmind

RUN mkdir -p /app/config
ENV CONFIG_DIR=/app/config

# Add the entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN dos2unix /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

# Default command to start the entrypoint
CMD ["/bin/bash", "/usr/local/bin/entrypoint.sh"]