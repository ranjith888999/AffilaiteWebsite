# Easypanel Deployment Configuration

## Issue Analysis
Your application is running successfully inside the Docker container on port 8000, but it's not reachable from outside. This is typically due to:

1. **Port Configuration Mismatch**
2. **Environment Detection Issues**
3. **Missing Health Check Endpoint**
4. **Dockerfile Command Issues**

## Fixes Applied

### 1. Updated Dockerfile
- Changed CMD to use `uvicorn` directly instead of `gunicorn`
- Added health check endpoint
- Set proper environment variables
- Added curl for health checks

### 2. Added Health Check Endpoint
- New `/health` endpoint in main.py
- Tests database connectivity
- Returns JSON status for monitoring

### 3. Enhanced Environment Detection
- Added Docker container detection (`/.dockerenv`)
- Better production environment detection
- Proper port handling

### 4. Startup Scripts
- `start.sh` - Enhanced startup with debugging
- `Dockerfile.debug` - Debug version with verbose logging

## Easypanel Configuration

### Environment Variables to Set in Easypanel:
```
ENVIRONMENT=production
DEBUG=False
PORT=8000
DATABASE_HOST=31.97.237.145
DATABASE_PORT=5432
DATABASE_NAME=coupons
DATABASE_USER=ranjith
DATABASE_PASSWORD=ranjith123
CUELINKS_API_KEY=MUmQPF2MLjDzMOHi0PSCdOwI082JAfj6vRLLT1QcY00
SECRET_KEY=supersecret-affiliate-oauth-key-2025-production-ready
```

### Port Configuration:
- **Container Port**: 8000
- **Published Port**: 8000 (or whatever Easypanel assigns)

### Health Check:
- **Path**: `/health`
- **Interval**: 30s
- **Timeout**: 30s

## Deployment Steps

1. **Use the updated Dockerfile**:
   ```dockerfile
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Set Environment Variables** in Easypanel dashboard

3. **Configure Port Mapping**: 
   - Map container port 8000 to external port

4. **Test Health Endpoint**:
   ```
   curl https://your-domain.com/health
   ```

## Troubleshooting

### If Still Not Working:

1. **Check Easypanel Logs**:
   - Look for uvicorn startup messages
   - Check for any port binding errors

2. **Test Health Endpoint Internally**:
   ```bash
   # In container terminal
   curl http://localhost:8000/health
   ```

3. **Verify Port Configuration**:
   - Ensure Easypanel maps external port to container port 8000
   - Check firewall settings

4. **Use Debug Dockerfile**:
   - Rename `Dockerfile.debug` to `Dockerfile` for verbose logging

### Expected Success Logs:
```
✅ Running in Docker container
🐍 Python version: Python 3.11.x
🚀 Starting uvicorn server...
INFO: Uvicorn running on http://0.0.0.0:8000
INFO: Application startup complete.
```

## Next Steps

1. Rebuild your Docker container in Easypanel
2. Check the new health endpoint: `https://your-domain.com/health`
3. Monitor logs for the startup messages
4. If issues persist, use the debug Dockerfile for more detailed logging

The main fix is ensuring uvicorn runs directly and the health check endpoint is available for Easypanel to verify the service is running correctly.
