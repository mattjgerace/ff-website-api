#!/bin/sh

# Exit if anything fails
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
gunicorn ffwebsite.wsgi:application