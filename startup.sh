#!/bin/bash
set -e

# Set default port if not provided
PORT=${PORT:-8000}

echo "=== Starting Affiliate Website Application ==="
echo "Port: $PORT"
echo "Host: 0.0.0.0"

# Wait for the database to be ready
echo "Waiting for PostgreSQL to be ready..."
python /app/scripts/check_db.py

# Run the database initialization script
echo "Running database initialization..."
python /app/init_render_database.py || {
    echo "Warning: Database initialization failed, but continuing..."
}

# Start the main application
echo "Starting Uvicorn server on port $PORT..."
echo "Application will be available at http://0.0.0.0:$PORT"

# Use exec to replace the shell process with uvicorn
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
