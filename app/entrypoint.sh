#!/bin/sh
set -e

echo "Running database migrations..."
flask db upgrade || flask db migrate -m "Auto migration" && flask db upgrade

echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:5000 "app:app"
