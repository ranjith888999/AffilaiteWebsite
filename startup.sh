#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for PostgreSQL to be ready..."
python /app/scripts/check_db.py

# Run the database initialization script
echo "Running database initialization..."
python /app/init_render_database.py

# Start the main application
echo "Starting Uvicorn server on port $PORT..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
