# Google Authentication Configuration Guide

This guide explains how to configure Google OAuth authentication for your affiliate website with the new domain: `https://couponsapp-semantic2.p9ghy4.easypanel.host`

## Quick Setup

### 1. Using the Setup Script (Recommended)

Run the automated setup script:

```bash
python setup_env.py
```

This will guide you through setting up all required environment variables.

### 2. Manual Configuration

Create a `.env` file in the project root with the following content:

```env
# Base URL for the application
BASE_URL=https://couponsapp-semantic2.p9ghy4.easypanel.host

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://couponsapp-semantic2.p9ghy4.easypanel.host/auth/callback

# Security
SECRET_KEY=your_super_secret_key_here

# Domain (without http/https)
DOMAIN_NAME=couponsapp-semantic2.p9ghy4.easypanel.host

# Optional: Cuelinks API
CUELINKS_API_KEY=your_cuelinks_api_key_here

# Optional: Database
DB_PASSWORD=your_database_password
```

## Google Console Configuration

### 1. Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one)
3. Navigate to **APIs & Services > Credentials**
4. Find your OAuth 2.0 Client ID
5. Update the configuration:

**Authorized JavaScript origins:**
```
https://couponsapp-semantic2.p9ghy4.easypanel.host
```

**Authorized redirect URIs:**
```
https://couponsapp-semantic2.p9ghy4.easypanel.host/auth/callback
```

### 2. Environment Variable Priority

The authentication system uses the following priority for determining the redirect URI:

1. **`GOOGLE_REDIRECT_URI`** (explicit setting) - highest priority
2. **`BASE_URL`** (constructs `{BASE_URL}/auth/callback`) - medium priority
3. **Request host** (fallback for development) - lowest priority

## Verification

### 1. Check Configuration

Run this command to verify your configuration:

```bash
python setup_env.py --check
```

### 2. Test Authentication

1. Start your application
2. Visit: `http://localhost:8000/auth/config` (development) or `https://couponsapp-semantic2.p9ghy4.easypanel.host/auth/config` (production)
3. Check that all configuration values are correct

### 3. Test Login Flow

1. Visit your website
2. Click "Sign in with Google"
3. Complete the OAuth flow
4. Verify you're redirected back to your website

## Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch" Error**
   - Check that the redirect URI in Google Console exactly matches your environment variable
   - Ensure no trailing slashes or typos

2. **"invalid_client" Error**
   - Verify your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
   - Check for extra spaces or characters

3. **Environment Variables Not Loading**
   - Ensure your `.env` file is in the project root
   - Restart your application after making changes
   - Check file permissions

### Debug Mode

Enable debug mode to see detailed authentication logs:

```env
DEBUG=true
```

### Configuration Endpoint

Visit `/auth/config` to see the current authentication configuration:

```json
{
  "status": "success",
  "config": {
    "base_url": "https://couponsapp-semantic2.p9ghy4.easypanel.host",
    "google_redirect_uri": "https://couponsapp-semantic2.p9ghy4.easypanel.host/auth/callback",
    "google_client_id_configured": true,
    "google_client_secret_configured": true,
    "google_auth_ready": true
  }
}
```

## Security Best Practices

1. **Keep credentials secure**
   - Never commit `.env` files to version control
   - Use environment variables in production
   - Rotate secrets regularly

2. **Use HTTPS in production**
   - Google OAuth requires HTTPS for production domains
   - Ensure your certificates are valid

3. **Validate domains**
   - Only add trusted domains to Google Console
   - Use specific redirect URIs, not wildcards

## Support

If you encounter issues:

1. Check the application logs
2. Verify Google Console configuration
3. Test with the `/auth/config` endpoint
4. Use debug mode for detailed logs