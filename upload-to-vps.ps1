# PowerShell Upload Script for Hostinger VPS
# This script helps upload your project files to the VPS from Windows

# VPS Configuration
$VPS_IP = "31.97.237.145"
$VPS_USER = "root"
$VPS_PATH = "/var/www/affiliate-website"

# Colors for output
function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Status "🚀 Starting file upload to Hostinger VPS..."

# Check if SSH/SCP is available
try {
    scp 2>&1 | Out-Null
    Write-Status "SCP is available ✓"
} catch {
    Write-Error "SCP command not found. Please install OpenSSH client or use WSL."
    Write-Host "To install OpenSSH on Windows 10/11:"
    Write-Host "1. Go to Settings > Apps > Optional Features"
    Write-Host "2. Add 'OpenSSH Client'"
    Write-Host "3. Or use: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0"
    exit 1
}

# Create directory on VPS
Write-Status "Creating directory on VPS..."
ssh "$VPS_USER@$VPS_IP" "mkdir -p $VPS_PATH"

# Files to exclude from upload
$excludePatterns = @(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".vscode",
    ".idea",
    "*.log",
    "logs",
    ".env",
    "venv",
    ".venv",
    "node_modules",
    ".DS_Store",
    "Thumbs.db"
)

# Upload main files
Write-Status "Uploading main project files..."

# Use robocopy for Windows or rsync if available
if (Get-Command rsync -ErrorAction SilentlyContinue) {
    # Create exclude file for rsync
    $excludeFile = ".upload_exclude"
    $excludePatterns | Out-File -FilePath $excludeFile -Encoding ascii
    
    rsync -avz --progress --exclude-from=$excludeFile . "$VPS_USER@${VPS_IP}:$VPS_PATH/"
    Remove-Item $excludeFile -Force
} else {
    # Use SCP for individual files
    Write-Status "Using SCP to upload files..."
    
    # Get all files excluding patterns
    $filesToUpload = Get-ChildItem -Recurse -File | Where-Object {
        $file = $_
        $shouldExclude = $false
        foreach ($pattern in $excludePatterns) {
            if ($file.FullName -like "*$pattern*") {
                $shouldExclude = $true
                break
            }
        }
        -not $shouldExclude
    }
    
    $totalFiles = $filesToUpload.Count
    $current = 0
    
    foreach ($file in $filesToUpload) {
        $current++
        $relativePath = $file.FullName.Substring((Get-Location).Path.Length + 1)
        $remotePath = "$VPS_PATH/$($relativePath -replace '\\', '/')"
        $remoteDir = Split-Path $remotePath -Parent
        
        # Create remote directory
        ssh "$VPS_USER@$VPS_IP" "mkdir -p '$remoteDir'"
        
        # Upload file
        Write-Progress -Activity "Uploading files" -Status "[$current/$totalFiles] $relativePath" -PercentComplete (($current / $totalFiles) * 100)
        scp "$($file.FullName)" "${VPS_USER}@${VPS_IP}:$remotePath"
    }
    
    Write-Progress -Activity "Uploading files" -Completed
}

if ($LASTEXITCODE -eq 0) {
    Write-Status "✅ Files uploaded successfully!"
} else {
    Write-Error "❌ File upload failed!"
    exit 1
}

# Upload environment template
Write-Status "Uploading environment template..."
scp "env.example" "${VPS_USER}@${VPS_IP}:$VPS_PATH/.env"

Write-Status "Setting proper permissions..."
ssh "$VPS_USER@$VPS_IP" @"
    cd $VPS_PATH
    chmod +x *.sh
    chmod 644 *.yml *.yaml *.json *.md *.txt
    chmod 755 app/ static/ templates/ scripts/ || true
    chown -R root:root .
"@

Write-Status "🎉 Upload completed!"
Write-Host ""
Write-Status "Next steps on your VPS:"
Write-Host "1. SSH to your VPS: ssh $VPS_USER@$VPS_IP"
Write-Host "2. Navigate to project: cd $VPS_PATH"
Write-Host "3. Configure environment: nano .env"
Write-Host "4. Run deployment: chmod +x deploy-hostinger-docker.sh && ./deploy-hostinger-docker.sh"
Write-Host ""
Write-Warning "Don't forget to configure your .env file with actual values!"
Write-Host ""
Write-Host "To connect to your VPS now, run:"
Write-Host "ssh $VPS_USER@$VPS_IP" -ForegroundColor Cyan
