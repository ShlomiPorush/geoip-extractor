# Use a lightweight Python image
FROM python:3.10-slim

# Install dependencies and cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY script.py /app/script.py

# Add the entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Default command to start the entrypoint
CMD ["/bin/bash", "/usr/local/bin/entrypoint.sh"]