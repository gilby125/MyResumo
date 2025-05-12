
#!/bin/sh

# Add extensive debugging
echo "DEBUG: Raw PORT value before processing: '$PORT'"

# Set default port if PORT is not set or empty
if [ -z "$PORT" ]; then
    PORT=8080
    echo "DEBUG: PORT was empty, set to default: $PORT"
else
    echo "DEBUG: PORT was set to: $PORT"
fi

# Ensure PORT is an integer
if ! [ "$PORT" -eq "$PORT" ] 2>/dev/null; then
    echo "WARNING: PORT value '$PORT' is not a valid integer, using default 8080"
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

echo "Attempting to locate app.main (via python -c 'import app.main'):"
python -c 'import app.main' 2>/dev/null || echo "app.main module not found"

echo "===== Now starting Uvicorn using 'python -m uvicorn' ====="
echo "Command: python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"

# Use exec with the full command as separate arguments to avoid shell interpretation issues
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
