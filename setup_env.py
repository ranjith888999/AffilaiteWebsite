#!/usr/bin/env python3
"""
Environment setup script for the Affiliate Website.
This script helps configure the required environment variables.
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file with the current configuration."""
    
    env_path = Path('.env')
    
    # Check if .env already exists
    if env_path.exists():
        response = input("📝 .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled.")
            return False
    
    print("🔧 Setting up environment variables for your affiliate website...")
    print("🌐 Using the domain: https://couponsapp-affiliate.p9ghy4.easypanel.host")
    
    # Get required values
    google_client_id = input("🔑 Enter your Google Client ID: ").strip()
    google_client_secret = input("🔒 Enter your Google Client Secret: ").strip()
    secret_key = input("🛡️  Enter a secret key (or press Enter for auto-generated): ").strip()
    
    if not secret_key:
        import secrets
        secret_key = secrets.token_urlsafe(32)
        print(f"🎲 Generated secret key: {secret_key}")
    
    cuelinks_api_key = input("💼 Enter your Cuelinks API Key (optional): ").strip()
    db_password = input("🗄️  Enter database password (optional): ").strip()
    
    # Create .env content
    env_content = f"""# Environment variables for Affiliate Website
# Generated on {os.popen('date').read().strip()}

# Base URL for the application
BASE_URL=https://couponsapp-affiliate.p9ghy4.easypanel.host

# Google OAuth Configuration
GOOGLE_CLIENT_ID={google_client_id}
GOOGLE_CLIENT_SECRET={google_client_secret}
GOOGLE_REDIRECT_URI=https://couponsapp-affiliate.p9ghy4.easypanel.host/auth/callback

# Security
SECRET_KEY={secret_key}

# Domain (without http/https)
DOMAIN_NAME=couponsapp-affiliate.p9ghy4.easypanel.host

# Cuelinks API (optional)
{"CUELINKS_API_KEY=" + cuelinks_api_key if cuelinks_api_key else "# CUELINKS_API_KEY=your_api_key_here"}

# Database Configuration (optional)
{"DB_PASSWORD=" + db_password if db_password else "# DB_PASSWORD=your_database_password"}

# Debug mode (set to True for development)
DEBUG=False
"""
    
    # Write .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created successfully!")
        print("📍 Location:", env_path.absolute())
        print("\n🔍 Configuration Summary:")
        print(f"   Base URL: https://couponsapp-affiliate.p9ghy4.easypanel.host")
        print(f"   Google Client ID: {google_client_id[:20]}...")
        print(f"   Secret Key: {secret_key[:10]}...")
        print(f"   Cuelinks API: {'✅ Configured' if cuelinks_api_key else '⚪ Not set'}")
        print(f"   Database: {'✅ Configured' if db_password else '⚪ Not set'}")
        
        print("\n📝 Next Steps:")
        print("1. Restart your application to load the new environment variables")
        print("2. Make sure these URLs are configured in your Google Console:")
        print("   - Authorized JavaScript origins: https://couponsapp-affiliate.p9ghy4.easypanel.host")
        print("   - Authorized redirect URIs: https://couponsapp-affiliate.p9ghy4.easypanel.host/auth/callback")
        print("3. Test the authentication by visiting your website")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def check_current_config():
    """Check and display current configuration."""
    from app.config import Config, print_env_status
    
    print("🔍 Current Configuration:")
    print_env_status()
    Config.print_auth_config()

def main():
    """Main setup script."""
    print("🌟 Affiliate Website Environment Setup")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        check_current_config()
        return
    
    print("This script will help you configure environment variables.")
    print("Make sure you have your Google OAuth credentials ready.\n")
    
    if create_env_file():
        print("\n🎉 Setup complete! Your affiliate website is ready to go.")
    else:
        print("\n😞 Setup was not completed.")

if __name__ == "__main__":
    main()