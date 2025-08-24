#!/bin/bash

# File Upload Script for Hostinger VPS
# This script helps upload your project files to the VPS

# VPS Configuration
VPS_IP="31.97.237.145"
VPS_USER="root"
VPS_PATH="/var/www/affiliate-website"

# Colors
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

# Check if scp is available
if ! command -v scp &> /dev/null; then
    print_error "scp command not found. Please install OpenSSH client."
    exit 1
fi

print_status "🚀 Starting file upload to Hostinger VPS..."

# Create directory on VPS
print_status "Creating directory on VPS..."
ssh $VPS_USER@$VPS_IP "mkdir -p $VPS_PATH"

# Upload project files (excluding unnecessary files)
print_status "Uploading project files..."

# Create temporary exclude file
cat > .upload_exclude << 'EOF'
.git/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
.venv/
.env
venv/
ENV/
env.bak/
venv.bak/
.idea/
.vscode/
*.log
logs/
node_modules/
.DS_Store
Thumbs.db
*.tmp
*.temp
.upload_exclude
EOF

# Upload files
rsync -avz --progress --exclude-from=.upload_exclude . $VPS_USER@$VPS_IP:$VPS_PATH/

if [ $? -eq 0 ]; then
    print_status "✅ Files uploaded successfully!"
else
    print_error "❌ File upload failed!"
    rm -f .upload_exclude
    exit 1
fi

# Clean up
rm -f .upload_exclude

# Upload environment template
print_status "Uploading environment template..."
scp env.example $VPS_USER@$VPS_IP:$VPS_PATH/.env

print_status "Setting proper permissions..."
ssh $VPS_USER@$VPS_IP "
    cd $VPS_PATH
    chmod +x *.sh
    chmod 644 *.yml *.yaml *.json *.md *.txt
    chmod 755 app/ static/ templates/ scripts/
    chown -R root:root .
"

print_status "🎉 Upload completed!"
echo ""
print_status "Next steps on your VPS:"
echo "1. SSH to your VPS: ssh $VPS_USER@$VPS_IP"
echo "2. Navigate to project: cd $VPS_PATH"
echo "3. Configure environment: nano .env"
echo "4. Run deployment: chmod +x deploy-hostinger-docker.sh && ./deploy-hostinger-docker.sh"
echo ""
print_warning "Don't forget to configure your .env file with actual values!"
