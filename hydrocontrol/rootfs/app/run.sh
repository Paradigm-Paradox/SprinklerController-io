#!/usr/bin/env sh
set -e

echo "Starting HydroControl-io service..."
exec python3 /app/main.py
