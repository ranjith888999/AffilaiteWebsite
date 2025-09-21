#!/bin/bash
set -e

# Start the Gunicorn server in the background
echo "Starting Gunicorn server..."
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
