#!/bin/sh

# Set default port if PORT is not set or empty
if [ -z "$PORT" ]; then
    PORT=8080
fi

echo "===== Starting MyResumo Application (Runtime Diagnostics) ====="
echo "Current Working Directory: $(pwd)"
echo "PYTHONPATH: $PYTHONPATH"
echo "Using PORT: $PORT"
echo "sys.path (via python -c 'import sys; print(sys.path)'):"
python -c 'import sys; print(sys.path)'

echo "Listing /code directory:"
ls -la /code

echo "Listing /code/app directory:"
ls -la /code/app

echo "Attempting to locate app.main (via python -m find_module app.main):"
python -m find_module app.main || echo "find_module: app.main not found"

echo "===== Now starting Uvicorn using 'python -m uvicorn' ====="
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT