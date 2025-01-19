FROM python:3.13-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Make sure entrypoint.sh is executable
RUN chmod +x /app/entrypoint.sh

# Set the container entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
