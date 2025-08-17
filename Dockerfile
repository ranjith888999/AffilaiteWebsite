# Optimized Dockerfile for faster builds
FROM tensorflow/tensorflow:2.17.0-gpu

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install core requirements first (faster dependencies)
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Install ML requirements separately
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

# Copy the rest of the application
COPY . .

# Make script files executable
RUN chmod +x startup.sh
RUN find ./scripts -name "*.py" -exec chmod +x {} \; || true

# Set up environment variables
ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/ || exit 1

# Command to run the application
CMD ["./startup.sh"]
