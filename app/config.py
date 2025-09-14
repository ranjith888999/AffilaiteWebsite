"""
Configuration management for the Affiliate Website application.
Handles environment variables and provides configuration utilities.
"""
import os
from typing import Optional

class Config:
    """Configuration class to manage environment variables and settings."""
    
    @staticmethod
    def get_base_url() -> str:
        """Get the base URL for the application."""
        base_url = os.getenv('BASE_URL')
        if base_url:
            return base_url.rstrip('/')
        
        # Fallback to localhost for development
        return 'http://localhost:8000'
    
    @staticmethod
    def get_google_redirect_uri() -> str:
        """Get the Google OAuth redirect URI."""
        # Priority 1: Explicit GOOGLE_REDIRECT_URI
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        if redirect_uri:
            return redirect_uri
        
        # Priority 2: Construct from BASE_URL
        base_url = Config.get_base_url()
        return f"{base_url}/auth/callback"
    
    @staticmethod
    def get_google_client_id() -> Optional[str]:
        """Get Google OAuth client ID."""
        return os.getenv('GOOGLE_CLIENT_ID')
    
    @staticmethod
    def get_google_client_secret() -> Optional[str]:
        """Get Google OAuth client secret."""
        return os.getenv('GOOGLE_CLIENT_SECRET')
    
    @staticmethod
    def is_google_auth_configured() -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(
            Config.get_google_client_id() and 
            Config.get_google_client_secret()
        )
    
    @staticmethod
    def get_auth_config_summary() -> dict:
        """Get a summary of authentication configuration for debugging."""
        return {
            'base_url': Config.get_base_url(),
            'google_redirect_uri': Config.get_google_redirect_uri(),
            'google_client_id_configured': bool(Config.get_google_client_id()),
            'google_client_secret_configured': bool(Config.get_google_client_secret()),
            'google_auth_ready': Config.is_google_auth_configured()
        }
    
    @staticmethod
    def print_auth_config():
        """Print authentication configuration for debugging."""
        config = Config.get_auth_config_summary()
        print("\n🔐 Authentication Configuration:")
        print(f"   Base URL: {config['base_url']}")
        print(f"   Google Redirect URI: {config['google_redirect_uri']}")
        print(f"   Google Client ID: {'✅ Configured' if config['google_client_id_configured'] else '❌ Missing'}")
        print(f"   Google Client Secret: {'✅ Configured' if config['google_client_secret_configured'] else '❌ Missing'}")
        print(f"   Google Auth Status: {'✅ Ready' if config['google_auth_ready'] else '❌ Not configured'}")
        print()

# Environment variables validation
REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'GOOGLE_CLIENT_ID',
    'GOOGLE_CLIENT_SECRET'
]

OPTIONAL_ENV_VARS = [
    'BASE_URL',
    'GOOGLE_REDIRECT_URI',
    'CUELINKS_API_KEY',
    'DB_PASSWORD'
]

def validate_environment():
    """Validate that required environment variables are set."""
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please check your .env file or environment configuration.")
        return False
    
    return True

def print_env_status():
    """Print the status of all environment variables."""
    print("\n📋 Environment Variables Status:")
    print("   Required Variables:")
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var)
        status = "✅ Set" if value else "❌ Missing"
        # Don't show actual values for security
        print(f"     {var}: {status}")
    
    print("   Optional Variables:")
    for var in OPTIONAL_ENV_VARS:
        value = os.getenv(var)
        status = "✅ Set" if value else "⚪ Not set"
        # Show some values that are safe to display
        if var in ['BASE_URL', 'GOOGLE_REDIRECT_URI'] and value:
            print(f"     {var}: {status} ({value})")
        else:
            print(f"     {var}: {status}")
    print()