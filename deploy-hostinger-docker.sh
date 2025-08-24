#!/bin/bash

# Hostinger Docker Deployment Script
# For Affiliate Website

set -e  # Exit on any error

echo "🚀 Starting Hostinger Docker Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_warning "Please copy env.example to .env and configure it first"
    exit 1
fi

print_status "Environment file found ✓"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    exit 1
fi

print_status "Docker and Docker Compose are available ✓"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p /var/log/affiliate-website
mkdir -p /var/lib/postgresql/data
mkdir -p ./ssl

# Set proper permissions
chown -R www-data:www-data /var/log/affiliate-website || chown -R 1000:1000 /var/log/affiliate-website
chmod -R 755 /var/log/affiliate-website

print_status "Directories created and permissions set ✓"

# Configure firewall
print_status "Configuring firewall..."
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable || print_warning "UFW might already be enabled"

print_status "Firewall configured ✓"

# Stop any running containers
print_status "Stopping any existing containers..."
docker-compose down || true

# Build and start containers
print_status "Building and starting containers..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check if containers are running
print_status "Checking container status..."
if docker ps | grep -q "affiliate_app"; then
    print_status "Application container is running ✓"
else
    print_error "Application container failed to start!"
    docker-compose logs web
    exit 1
fi

if docker ps | grep -q "affiliate_db"; then
    print_status "Database container is running ✓"
else
    print_error "Database container failed to start!"
    docker-compose logs db
    exit 1
fi

if docker ps | grep -q "affiliate_nginx"; then
    print_status "Nginx container is running ✓"
else
    print_error "Nginx container failed to start!"
    docker-compose logs nginx
    exit 1
fi

# Initialize database
print_status "Initializing database..."
sleep 10  # Wait a bit more for database to be ready

docker exec affiliate_app python -c "
from app.database import create_tables
try:
    create_tables()
    print('Database tables created successfully!')
except Exception as e:
    print(f'Database initialization error: {e}')
    print('This might be normal if tables already exist.')
" || print_warning "Database initialization had issues (might be normal if already initialized)"

# Test the application
print_status "Testing application..."
sleep 5

if curl -f -s http://localhost:80 > /dev/null; then
    print_status "Application is responding on port 80 ✓"
else
    print_warning "Application might not be responding yet. Check logs with: docker-compose logs -f"
fi

# Show container status
print_status "Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Show logs
print_status "Recent application logs:"
docker-compose logs --tail=20 web

echo ""
print_status "🎉 Deployment completed!"
echo ""
print_status "Your application should be accessible at:"
echo "  • http://31.97.237.145"
echo ""
print_status "Useful commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Restart app: docker-compose restart web"
echo "  • Stop all: docker-compose down"
echo "  • Update app: git pull && docker-compose down && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
echo ""
print_status "Next steps:"
echo "  1. Configure your domain name in .env if you have one"
echo "  2. Set up SSL certificates using Certbot"
echo "  3. Monitor logs regularly"
echo "  4. Set up automated backups"
echo ""

# Optional: Show system resources
print_status "Current system resources:"
echo "Memory usage:"
free -h
echo ""
echo "Disk usage:"
df -h /
echo ""
echo "Docker stats:"
docker stats --no-stream
