# Hostinger Deployment Guide

## Required Information for Deployment

### 1. Server Details
- **Hostinger Plan**: VPS or Cloud hosting (required for Python apps)
- **Server IP**: Your VPS IP address
- **SSH Access**: Username and password/SSH key
- **Domain**: Your domain name (e.g., mysite.com)

### 2. Database Configuration
- **Database Name**: affiliate_website
- **Database User**: affiliate_user  
- **Database Password**: [CREATE A SECURE PASSWORD]

### 3. API Keys
- **Cuelinks API Key**: [YOUR EXISTING API KEY]
- **Secret Key**: [GENERATE A SECURE SECRET KEY]

### 4. SSL Certificate
- **Email**: For Let's Encrypt SSL certificate

## Deployment Steps

1. **Connect to your Hostinger VPS via SSH**
2. **Run the deployment commands**
3. **Configure your domain DNS**
4. **Test the application**

## Essential Files Created:
- `requirements-hostinger.txt` - Production dependencies
- `precision_data_fetch.py` - Data import script
- `initialize_database.py` - Database setup script

## Quick Deployment Commands:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip postgresql nginx git -y

# Clone repository
git clone https://github.com/ranjith888999/AffilaiteWebsite.git
cd AffilaiteWebsite

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-hostinger.txt

# Setup database
sudo -u postgres createdb affiliate_website
sudo -u postgres createuser affiliate_user

# Configure environment
cp .env.example .env  # Edit with your details

# Initialize database
python scripts/initialize_database.py

# Start application
gunicorn main:app --bind 0.0.0.0:8000
```
