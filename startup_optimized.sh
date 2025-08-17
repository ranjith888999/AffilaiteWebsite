#!/bin/bash
set -e

# Set default port if not provided
PORT=${PORT:-8000}

echo "=== Starting Affiliate Website Application (Optimized) ==="
echo "Port: $PORT"
echo "Host: 0.0.0.0"

# Initialize database in background to avoid blocking server startup
echo "Starting database initialization in background..."
{
    echo "Waiting for PostgreSQL to be ready..."
    python /app/scripts/check_db.py
    echo "Running database initialization..."
    python /app/init_render_database.py || echo "Warning: Database initialization failed, but continuing..."
    echo "Database initialization completed."
} &

# Start the main application immediately
echo "Starting Uvicorn server on port $PORT..."
echo "Application will be available at http://0.0.0.0:$PORT"

# Set environment variables to reduce TensorFlow loading time
export TF_CPP_MIN_LOG_LEVEL=3
export CUDA_VISIBLE_DEVICES=""
export TF_FORCE_GPU_ALLOW_GROWTH=true

# Use exec to replace the shell process with uvicorn
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 120 --timeout-graceful-shutdown 30
