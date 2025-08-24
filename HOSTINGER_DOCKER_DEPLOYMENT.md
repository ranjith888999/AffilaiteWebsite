# Hostinger Docker Deployment Guide

## Server Details
- VPS: srv971199.hstgr.cloud
- IP: 31.97.237.145
- OS: Ubuntu 24.04 with Docker
- Access: SSH root@31.97.237.145

## Step 1: Initial Server Setup

First, connect to your VPS and update the system:

```bash
# Connect to VPS
ssh root@31.97.237.145

# Update system packages
apt update && apt upgrade -y

# Install essential packages
apt install -y git curl wget htop nano ufw

# Verify Docker installation
docker --version
docker-compose --version

# If Docker Compose is not installed:
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

## Step 2: Configure Firewall

```bash
# Configure UFW firewall
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status
```

## Step 3: Clone Your Repository

```bash
# Navigate to web directory
cd /var/www

# Clone your repository (replace with your actual repo URL)
git clone https://github.com/ranjith888999/AffilaiteWebsite.git affiliate-website
cd affiliate-website

# Or if you're uploading files manually, create the directory:
# mkdir -p /var/www/affiliate-website
# Then upload your files using SCP or SFTP
```

## Step 4: Environment Configuration

```bash
# Create environment file
cp env.example .env
nano .env
```

Configure your `.env` file with these values:
```env
# Database Configuration
DB_PASSWORD=your_secure_database_password_here_123

# Cuelinks API
CUELINKS_API_KEY=your_cuelinks_api_key_here

# Security (generate a random 32-character string)
SECRET_KEY=your_super_secret_key_32_chars_long

# Domain (use your IP for now, later replace with domain)
DOMAIN_NAME=31.97.237.145
```

## Step 5: Update Docker Configuration for Production

Create a production docker-compose override:

```bash
nano docker-compose.prod.yml
```

Add this content:
```yaml
version: '3.8'

services:
  web:
    environment:
      - ALLOWED_HOSTS=31.97.237.145,yourdomain.com,www.yourdomain.com
      - DEBUG=False
    restart: unless-stopped
    
  db:
    restart: unless-stopped
    volumes:
      - /var/lib/postgresql/data:/var/lib/postgresql/data
      
  nginx:
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl  # For future SSL certificates
```

## Step 6: Create Application Directories

```bash
# Create necessary directories
mkdir -p /var/log/affiliate-website
mkdir -p /var/lib/postgresql/data
mkdir -p /var/www/affiliate-website/ssl

# Set proper permissions
chown -R www-data:www-data /var/log/affiliate-website
chmod -R 755 /var/log/affiliate-website
```

## Step 7: Deploy the Application

```bash
# Build and start the containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Check if containers are running
docker ps

# Check logs
docker-compose logs -f

# If you need to restart
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Step 8: Initialize Database

```bash
# Access the web container to run database initialization
docker exec -it affiliate_app bash

# Inside the container, run database setup
python -c "
from app.database import create_tables
create_tables()
print('Database tables created successfully!')
"

# Exit the container
exit
```

## Step 9: Test the Deployment

```bash
# Test if the application is responding
curl http://31.97.237.145

# Check individual container logs
docker logs affiliate_app
docker logs affiliate_db
docker logs affiliate_nginx

# Monitor system resources
htop
```

## Step 10: Domain Configuration (Optional)

If you have a domain name:

1. Point your domain's A record to: `31.97.237.145`
2. Update the `.env` file:
   ```env
   DOMAIN_NAME=yourdomain.com
   ```
3. Update nginx configuration:
   ```bash
   nano nginx-simple.conf
   # Change server_name to: yourdomain.com www.yourdomain.com
   ```
4. Restart containers:
   ```bash
   docker-compose restart
   ```

## Step 11: SSL Certificate (Recommended)

Install Certbot for free SSL:

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Stop nginx container temporarily
docker stop affiliate_nginx

# Get SSL certificate (replace with your domain)
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to your project
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/

# Update nginx configuration for HTTPS
# Then restart containers
docker-compose restart
```

## Maintenance Commands

```bash
# View all containers
docker ps -a

# View logs for specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f nginx

# Restart specific service
docker-compose restart web

# Update application (after code changes)
git pull
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Backup database
docker exec affiliate_db pg_dump -U affiliate_user affiliate_website > backup_$(date +%Y%m%d_%H%M%S).sql

# Monitor system resources
docker stats

# Clean up unused containers/images
docker system prune -a
```

## Troubleshooting

### Common Issues:

1. **Port already in use:**
   ```bash
   sudo lsof -i :80
   sudo kill -9 <PID>
   ```

2. **Database connection issues:**
   ```bash
   docker logs affiliate_db
   docker exec -it affiliate_db psql -U affiliate_user -d affiliate_website
   ```

3. **Permission issues:**
   ```bash
   sudo chown -R $USER:$USER /var/www/affiliate-website
   ```

4. **Memory issues:**
   ```bash
   free -h
   docker stats
   ```

## Security Recommendations

1. Change default passwords
2. Enable firewall (UFW)
3. Regular system updates
4. Use SSL certificates
5. Monitor logs regularly
6. Set up automated backups

## Performance Optimization

1. **Enable Gzip compression** (already configured in nginx)
2. **Static file caching** (already configured)
3. **Database connection pooling** (configured in FastAPI)
4. **Monitor resource usage:**
   ```bash
   docker stats
   htop
   ```

## Monitoring

```bash
# Check application status
curl -I http://31.97.237.145

# Monitor logs in real-time
docker-compose logs -f --tail=100

# Check disk usage
df -h

# Check memory usage
free -h
```

Your application should now be accessible at `http://31.97.237.145`

Remember to:
- Replace placeholder values in `.env` with your actual API keys
- Configure your domain name if you have one
- Set up SSL certificates for production use
- Monitor the application logs regularly
