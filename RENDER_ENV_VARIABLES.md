# Environment Variables for Render Deployment

## Required Environment Variables

Copy these environment variables to your Render web service:

### 1. CUELINKS_API_KEY
```
CUELINKS_API_KEY=your_actual_cuelinks_api_key_here
```

### 2. SECRET_KEY
Generate a secure secret key using:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Then set:
```
SECRET_KEY=your_generated_secret_key_here
```

### 3. PORT (Auto-configured by Render)
```
PORT=8000
```

## Database Variables (Auto-configured by Render)

These are automatically set by Render when you use the blueprint:

- `DATABASE_URL` - Full PostgreSQL connection string
- `DATABASE_HOST` - Database host
- `DATABASE_PORT` - Database port (usually 5432)
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Database user
- `DATABASE_PASSWORD` - Database password

## Setting Environment Variables in Render

1. Go to your Render dashboard
2. Click on your web service
3. Go to "Environment" tab
4. Click "Add Environment Variable"
5. Add the required variables above

## Note

- Never commit actual API keys or secrets to your repository
- Use Render's environment variable system for sensitive data
- The database variables are automatically configured when using the blueprint
