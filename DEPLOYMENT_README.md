# 🚀 Hostinger VPS Docker Deployment Guide

## Quick Start

Your Hostinger VPS details:
- **Server**: srv971199.hstgr.cloud  
- **IP**: 31.97.237.145
- **OS**: Ubuntu 24.04 with Docker
- **Access**: `ssh root@31.97.237.145`

## 📋 Prerequisites Checklist

- [x] Hostinger VPS with Docker installed
- [ ] SSH access to VPS working
- [ ] Cuelinks API key
- [ ] Domain name (optional, can use IP initially)

## 🎯 Deployment Steps

### Step 1: Upload Project Files

**From Windows PowerShell:**
```powershell
# Run the upload script
.\upload-to-vps.ps1
```

**Or manually using SCP:**
```powershell
scp -r . root@31.97.237.145:/var/www/affiliate-website
```

### Step 2: Connect to VPS and Configure

```bash
# Connect to your VPS
ssh root@31.97.237.145

# Navigate to project directory
cd /var/www/affiliate-website

# Configure environment variables
nano .env
```

**Required environment variables:**
```env
# Database password (create a strong password)
DB_PASSWORD=your_secure_database_password_123

# Get this from your Cuelinks account
CUELINKS_API_KEY=your_cuelinks_api_key_here

# Generate a random 32-character string
SECRET_KEY=your_super_secret_key_32_chars_long

# Use your IP for now, replace with domain later
DOMAIN_NAME=31.97.237.145
```

### Step 3: Deploy with Docker

```bash
# Make deployment script executable
chmod +x deploy-hostinger-docker.sh

# Run the deployment
./deploy-hostinger-docker.sh
```

### Step 4: Verify Deployment

```bash
# Check if containers are running
docker ps

# Test the application
curl http://31.97.237.145

# View logs
docker-compose logs -f
```

## 🔧 Management Commands

### Application Management
```bash
# Restart the application
docker-compose restart web

# Update application (after code changes)
git pull
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# View logs
docker-compose logs -f web        # Application logs
docker-compose logs -f db         # Database logs
docker-compose logs -f nginx      # Web server logs
```

### Monitoring
```bash
# Run health check
./monitor.sh

# Continuous monitoring
./monitor.sh watch

# Performance test
./monitor.sh perf

# Check SSL status
./monitor.sh ssl
```

### Backup
```bash
# Create backup
./backup.sh

# View backups
ls -la /var/backups/affiliate-website/
```

## 🌐 Domain Configuration

### If you have a domain name:

1. **Point your domain to the VPS:**
   - Create an A record: `yourdomain.com` → `31.97.237.145`
   - Create an A record: `www.yourdomain.com` → `31.97.237.145`

2. **Update configuration:**
   ```bash
   # Edit environment file
   nano .env
   
   # Change DOMAIN_NAME to your domain
   DOMAIN_NAME=yourdomain.com
   
   # Update nginx configuration
   nano nginx-simple.conf
   # Change server_name to: yourdomain.com www.yourdomain.com
   
   # Restart containers
   docker-compose restart
   ```

3. **Set up SSL certificate:**
   ```bash
   # Install Certbot
   apt install certbot python3-certbot-nginx -y
   
   # Stop nginx container temporarily
   docker stop affiliate_nginx
   
   # Get SSL certificate
   certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
   
   # Copy certificates
   cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
   cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
   
   # Update nginx for HTTPS and restart
   docker-compose restart
   ```

## 🔒 Security Checklist

- [ ] Change default database password
- [ ] Use strong SECRET_KEY
- [ ] Enable firewall (done by deployment script)
- [ ] Set up SSL certificates
- [ ] Regular security updates
- [ ] Monitor access logs

## 📊 Performance Optimization

### Database Optimization
The production configuration includes optimized PostgreSQL settings:
- Connection pooling
- Memory optimization
- Query performance tuning

### Application Optimization
- Gunicorn with multiple workers
- Static file caching
- Gzip compression

### Monitoring
```bash
# System resources
htop
df -h
free -h

# Docker resources
docker stats

# Application performance
./monitor.sh perf
```

## 🆘 Troubleshooting

### Container Issues
```bash
# Check container status
docker ps -a

# View container logs
docker logs affiliate_app
docker logs affiliate_db
docker logs affiliate_nginx

# Restart problematic container
docker-compose restart <service_name>
```

### Application Not Responding
```bash
# Check if port 80 is occupied
lsof -i :80

# Check nginx configuration
docker exec affiliate_nginx nginx -t

# Check application logs
docker-compose logs -f web
```

### Database Issues
```bash
# Check database connectivity
docker exec affiliate_db pg_isready -U affiliate_user

# Access database directly
docker exec -it affiliate_db psql -U affiliate_user -d affiliate_website

# Reset database (CAUTION: This will delete all data!)
docker-compose down
docker volume rm affiliate-website_postgres_data
docker-compose up -d
```

### Memory Issues
```bash
# Check memory usage
free -h

# Clean Docker resources
docker system prune -a

# Restart containers
docker-compose restart
```

## 📱 Accessing Your Application

Once deployed, your application will be available at:
- **HTTP**: http://31.97.237.145
- **With domain**: http://yourdomain.com (after domain setup)
- **HTTPS**: https://yourdomain.com (after SSL setup)

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks
1. **Weekly**: Check logs and performance
2. **Monthly**: Update system packages and Docker images
3. **Quarterly**: Review security settings and backups

### Updating Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### System Updates
```bash
# Update system packages
apt update && apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Run the monitoring script: `./monitor.sh`
3. Check the troubleshooting section above
4. Review Docker and system resources

## 🎉 Success!

Your FastAPI affiliate website should now be running on Hostinger VPS with:
- ✅ Containerized deployment with Docker
- ✅ PostgreSQL database
- ✅ Nginx reverse proxy
- ✅ Production-ready configuration
- ✅ Monitoring and backup scripts
- ✅ Security optimizations

**Your website is now live at: http://31.97.237.145** 🌟
