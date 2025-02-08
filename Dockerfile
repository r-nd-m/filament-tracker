FROM python:3.13-slim

WORKDIR /app

# Copy all application files
COPY . .

# Install dependencies
# Make sure entrypoint.sh is executable
RUN apt-get update && apt-get install --no-install-recommends \
    ca-certificates && \
    pip install --no-cache-dir -r requirements.txt && \
    chmod +x app/entrypoint.sh && \
    groupadd app && \
    useradd -ms /bin/bash app -g nogroup && \
    chown -R app:nogroup /app

USER app

# Set the container entrypoint
ENTRYPOINT ["app/entrypoint.sh"]
