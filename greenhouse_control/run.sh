#!/usr/bin/with-contenv bashio

bashio::log.info "Starting GreenhouseControl-io Engine..."

export PYTHONPATH="/app:${PYTHONPATH}"

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8099
