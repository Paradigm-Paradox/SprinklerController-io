#!/usr/bin/with-contenv bashio

bashio::log.info "Starting GardenControl-io Engine..."

# Ensure persistence directory exists
mkdir -p /data

# Export python path
export PYTHONPATH="/app:${PYTHONPATH}"

# Launch FastAPI / Uvicorn server on ingress port 8099
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8099
