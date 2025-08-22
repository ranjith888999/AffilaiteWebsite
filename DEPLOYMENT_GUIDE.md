# Hostinger Docker VPS Deployment Guide

## Your Server Details ✅
- **Server**: srv971199.hstgr.cloud  
- **IP**: 31.97.237.145
- **SSH**: `ssh root@31.97.237.145`
- **Password**: 868635123@rR
- **OS**: Ubuntu 24.04 with Docker pre-installed

## 🚀 SUPER EASY 1-COMMAND DEPLOYMENT

### Step 1: Connect to Your VPS
```bash
ssh root@31.97.237.145
# Enter password: 868635123@rR
```

### Step 2: Run ONE Command
```bash
curl -sSL https://raw.githubusercontent.com/ranjith888999/AffilaiteWebsite/feature/superbase_url/deploy.sh | bash
```

**That's it! The script will:**
- ✅ Clone your repository
- ✅ Set up Docker containers
- ✅ Configure database (PostgreSQL)
- ✅ Set up Nginx reverse proxy
- ✅ Initialize your data
- ✅ Import all 1,184 offers
- ✅ Start your website

### Step 3: Configure Your Domain (Optional)
Point your domain DNS to: `31.97.237.145`

## 📋 What You'll Need to Provide During Deployment:
1. **Domain name** (e.g., yoursite.com)
2. **Database password** (create a secure one)
3. **Cuelinks API key** (your existing key)
4. **Secret key** (script can generate one)

## 🌐 Access Your Website:
- **By IP**: http://31.97.237.145
- **By Domain**: http://yourdomain.com (after DNS setup)
- **HTTPS**: Available after domain DNS is configured

## 🔧 Management Commands:
```bash
# View all containers
docker compose ps

# View logs
docker compose logs -f

# Restart application
docker compose restart

# Stop everything
docker compose down

# Update and restart
git pull && docker compose up --build -d
```

## 📦 What Gets Deployed:
- **FastAPI Application** (your affiliate website)
- **PostgreSQL Database** (with all your offers)
- **Nginx Reverse Proxy** (with SSL support)
- **All 1,184 offers imported**
- **Semantic search enabled**
- **Chat system ready**

## 🎯 Total Deployment Time: ~5 minutes!
