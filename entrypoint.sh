#!/bin/sh
set -e

echo "Running database migrations..."
python -c "from db import run_schema_migrations; run_schema_migrations()"

echo "Starting application..."
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT:-8000}
