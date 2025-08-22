#!/bin/bash

# Quick Docker Deployment Script for Hostinger VPS
# Run this script on your VPS: bash deploy.sh

set -e  # Exit on any error

echo "🚀 Starting Docker deployment on Hostinger VPS..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get user inputs
echo "📝 Please provide the following information:"
read -p "Your domain name (e.g., mysite.com): " DOMAIN_NAME
read -p "Database password (create a secure one): " -s DB_PASSWORD
echo
read -p "Cuelinks API Key: " -s CUELINKS_API_KEY
echo
read -p "Secret key (press Enter to generate): " SECRET_KEY
echo

# Generate secret key if not provided
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -base64 32)
    print_status "Generated secret key: $SECRET_KEY"
fi

# Update system
print_status "Updating system..."
apt update && apt upgrade -y

# Install Git if not present
if ! command -v git &> /dev/null; then
    print_status "Installing Git..."
    apt install git -y
fi

# Clone or update repository
if [ -d "AffilaiteWebsite" ]; then
    print_status "Updating existing repository..."
    cd AffilaiteWebsite
    git pull origin feature/superbase_url
else
    print_status "Cloning repository..."
    git clone -b feature/superbase_url https://github.com/ranjith888999/AffilaiteWebsite.git
    cd AffilaiteWebsite
fi

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
DB_PASSWORD=$DB_PASSWORD
CUELINKS_API_KEY=$CUELINKS_API_KEY
SECRET_KEY=$SECRET_KEY
DOMAIN_NAME=$DOMAIN_NAME
EOF

# Create SSL directory (temporary self-signed certificate)
print_status "Creating SSL certificates..."
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN_NAME"

# Build and start containers
print_status "Building and starting containers..."
docker compose down --remove-orphans 2>/dev/null || true
docker compose up --build -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 30

# Check if containers are running
print_status "Checking container status..."
docker compose ps

# Initialize database
print_status "Initializing database..."
docker compose exec web python scripts/initialize_database.py

# Import data
print_warning "Importing offers data (this will use API calls)..."
docker compose exec web python scripts/precision_data_fetch.py

# Test the application
print_status "Testing application..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ Application is running successfully!"
else
    print_error "❌ Application health check failed"
fi

# Display access information
echo
echo "🎉 Deployment completed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "🌐 Your website is accessible at:"
echo "   📍 Local: http://localhost"
echo "   📍 Public: http://$DOMAIN_NAME (configure DNS)"
echo "   📍 IP: http://31.97.237.145"
echo
echo "🔐 HTTPS will work once you configure your domain DNS"
echo
echo "📊 Management commands:"
echo "   📋 View logs: docker compose logs -f"
echo "   🔄 Restart: docker compose restart"
echo "   🛑 Stop: docker compose down"
echo "   📈 Status: docker compose ps"
echo
echo "🚨 IMPORTANT: Configure your domain DNS to point to 31.97.237.145"
echo
print_status "Deployment successful! 🚀"
