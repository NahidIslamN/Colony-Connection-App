#!/bin/sh

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
# Using uvicorn with gunicorn workers since the app uses ASGI
exec gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
