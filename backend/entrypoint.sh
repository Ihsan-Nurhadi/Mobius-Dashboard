#!/bin/sh
set -e

# Ensure database directory exists
TARGET_DB_DIR="${DB_DIR:-/app/data}"
mkdir -p "$TARGET_DB_DIR"

echo "Applying database migrations..."
python manage.py migrate --noinput

# If specific command passed to container (e.g. run_simulator)
if [ $# -gt 0 ]; then
    echo "Executing custom container command: $@"
    exec "$@"
fi

# Default command: Web backend with Gunicorn
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Checking / seeding demo data..."
python manage.py seed_demo

echo "Starting Gunicorn server on 0.0.0.0:8000..."
exec gunicorn config.wsgi:application \
    --name mobius_backend \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
