#!/bin/bash
# Build script for Vercel deployment

echo "Starting build process..."

# Install requirements using pip3
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Collect static files using python3
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# Create staticfiles_build directory
echo "Setting up static files..."
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/

echo "Build completed successfully!"