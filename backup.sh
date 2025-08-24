#!/bin/bash

# Backup Script for Affiliate Website
# Creates backups of database and application files

set -e

# Configuration
BACKUP_DIR="/var/backups/affiliate-website"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

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

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_status "Starting backup process..."

# Backup database
print_status "Backing up database..."
docker exec affiliate_db pg_dump -U affiliate_user affiliate_website > "$BACKUP_DIR/database_$DATE.sql"

if [ $? -eq 0 ]; then
    print_status "Database backup completed: database_$DATE.sql"
    gzip "$BACKUP_DIR/database_$DATE.sql"
    print_status "Database backup compressed"
else
    print_error "Database backup failed!"
    exit 1
fi

# Backup application files (excluding sensitive data)
print_status "Backing up application files..."
tar -czf "$BACKUP_DIR/app_files_$DATE.tar.gz" \
    --exclude='.env' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='logs' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    . 2>/dev/null || true

print_status "Application files backup completed: app_files_$DATE.tar.gz"

# Backup environment configuration (without sensitive values)
print_status "Backing up configuration..."
if [ -f ".env" ]; then
    # Create a sanitized version of .env
    sed 's/=.*/=***REDACTED***/g' .env > "$BACKUP_DIR/env_template_$DATE.txt"
    print_status "Environment template backup completed"
fi

# Clean old backups
print_status "Cleaning old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.txt" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Show backup summary
print_status "Backup summary:"
ls -lh "$BACKUP_DIR"/*$DATE* 2>/dev/null || print_warning "No backup files found for this session"

# Show disk usage
print_status "Backup directory size:"
du -sh "$BACKUP_DIR"

print_status "Backup process completed successfully!"

# Optional: Send backup notification (uncomment to use)
# echo "Backup completed on $(hostname) at $(date)" | mail -s "Affiliate Website Backup" admin@yourdomain.com
