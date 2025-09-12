#!/bin/bash

echo "🚀 Starting Affiliate Website Application..."
echo "Environment: $ENVIRONMENT"
echo "Debug: $DEBUG"
echo "Port: ${PORT:-8000}"

# Check if we're in a Docker container
if [ -f /.dockerenv ]; then
    echo "✅ Running in Docker container"
    export ENVIRONMENT=production
fi

# Check if this is Easypanel
if [ ! -z "$EASYPANEL_PROJECT" ]; then
    echo "✅ Detected Easypanel deployment"
    export ENVIRONMENT=production
    export DEBUG=False
fi

# Show current working directory and files
echo "📁 Current directory: $(pwd)"
echo "📋 Files in /app:"
ls -la /app/ | head -10

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found!"
    exit 1
fi

# Check Python version
echo "🐍 Python version: $(python --version)"

# Show environment variables (excluding secrets)
echo "🔧 Environment variables:"
env | grep -E "^(ENVIRONMENT|DEBUG|PORT|DATABASE_HOST|CUELINKS_)" | sort

# Start the application
echo "🚀 Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
