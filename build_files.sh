#!/bin/bash
# Build script for Vercel deployment

# Install requirements using pip3
pip3 install -r requirements-vercel.txt

# Collect static files using python3
python3 manage.py collectstatic --noinput

# Create staticfiles_build directory
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/