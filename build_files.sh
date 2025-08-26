#!/bin/bash
# Build script for Vercel deployment

echo "Building Django application for Vercel..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations (if needed)
python manage.py migrate --noinput

echo "Build completed successfully!"