#!/usr/bin/env bash
set -e

echo "[INFO] Starting FanControl-io Add-on..."

# Start FastAPI application with Uvicorn
exec uvicorn main:app --host 0.0.0.0 --port 8095 --app-dir /app
