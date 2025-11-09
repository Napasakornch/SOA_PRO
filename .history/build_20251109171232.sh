#!/usr/bin/env bash

echo "=== Starting Pet Store Build Process ==="

echo "1. Installing dependencies..."
pip install -r requirements.txt

echo "2. Running database migrations..."
python manage.py migrate

echo "3. Collecting static files..."
python manage.py collectstatic --noinput

echo "4. Creating necessary directories..."
mkdir -p templates/auth templates/pets templates/orders templates/errors
mkdir -p media/pets static

echo "=== Build completed successfully! ==="