#!/bin/bash

# Set Django settings module
export DJANGO_SETTINGS_MODULE=futurelab.settings
export PYTHONPATH=/app

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "Database is ready!"

# Create static directories if they don't exist
echo "Creating static directories..."
mkdir -p /app/static
mkdir -p /app/staticfiles

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Start the application
echo "Starting Django application..."
exec gunicorn --bind 0.0.0.0:8000 futurelab.wsgi:application 