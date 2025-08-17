# Render Docker Deployment Guide

This guide will help you deploy your affiliate website to Render using Docker.

## Prerequisites

1. **GitHub Repository**: Your code is already pushed to the `feature/docker_enhancements` branch
2. **Render Account**: Sign up at [render.com](https://render.com) if you haven't already
3. **Cuelinks API Key**: Have your Cuelinks API key ready

## Step-by-Step Deployment Process

### Step 1: Connect GitHub to Render

1. Go to [render.com](https://render.com) and sign in
2. Click "New +" button in the top-right corner
3. Select "Blueprint" from the dropdown menu

### Step 2: Create a New Blueprint

1. **Connect GitHub Repository**:
   - Click "Connect" next to GitHub
   - Select your repository: `ranjith888999/AffilaiteWebsite`
   - Choose the branch: `feature/docker_enhancements`

2. **Blueprint Configuration**:
   - Render will automatically detect the `render.yaml` file
   - Review the services that will be created:
     - Web Service: `affiliate-website`
     - Database: `affiliate-db` (PostgreSQL 15 with vector extension)

### Step 3: Configure Environment Variables

Before deployment, you'll need to set up these environment variables:

1. **CUELINKS_API_KEY**: Your Cuelinks API key
2. **SECRET_KEY**: A secure random string for JWT tokens

To generate a SECRET_KEY, you can use:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 4: Deploy

1. Click "Create Blueprint" 
2. Render will start building your application
3. The build process includes:
   - Installing system dependencies
   - Installing Python packages (core and ML libraries)
   - Setting up the application environment
   - Creating the PostgreSQL database with vector extensions

### Step 5: Monitor Deployment

1. **Database Creation**: Usually takes 2-3 minutes
2. **Web Service Build**: May take 15-20 minutes due to ML libraries
3. **Health Check**: Render will verify your app is responding at `/`

## Expected Build Time

- **Database**: 2-3 minutes
- **Web Service**: 15-20 minutes (first build)
- **Total**: ~20-25 minutes

## Post-Deployment

### Verify Deployment

1. Once deployed, visit your Render URL
2. Check that the homepage loads correctly
3. Test the chat functionality
4. Verify database connectivity

### Environment Variables Setup

In the Render dashboard:
1. Go to your web service
2. Click on "Environment" tab
3. Add/verify these variables:
   - `CUELINKS_API_KEY`: Your API key
   - `SECRET_KEY`: Your generated secret key
   - `PORT`: Should be automatically set to 8000

### Logs and Monitoring

- **View Logs**: In Render dashboard → Your service → Logs
- **Health Status**: Monitor the health check status
- **Database**: Check database connection in logs

## Troubleshooting

### Common Issues

1. **Build Timeout**: 
   - ML libraries take time to install
   - This is normal for the first build
   - Subsequent builds will be faster due to Docker layer caching

2. **Database Connection Issues**:
   - Check if DATABASE_URL is properly set
   - Verify PostgreSQL service is running
   - Check database logs for connection errors

3. **Import Errors**:
   - All ML dependencies are included in requirements-ml.txt
   - tf-keras is included for Keras compatibility

### Checking Logs

```bash
# In Render dashboard, check these log patterns:
- "Database connection successful" ✅
- "vector extension is enabled" ✅
- "Database tables created successfully" ✅
- "Starting Uvicorn server..." ✅
```

## Key Files for Deployment

- `Dockerfile`: Optimized multi-stage build with TensorFlow base
- `startup.sh`: Handles database initialization and app startup
- `render.yaml`: Render service configuration
- `requirements-core.txt`: Core dependencies
- `requirements-ml.txt`: ML/AI dependencies
- `init_render_database.py`: Database initialization script

## Performance Optimizations

1. **Docker Layer Caching**: Requirements split into core/ML for better caching
2. **TensorFlow Base Image**: Avoids compiling ML libraries from source
3. **Lazy Loading**: ML services loaded only when needed
4. **Database Race Condition Prevention**: Startup script waits for database

## Scaling Considerations

- **Free Tier**: Sufficient for development and light production use
- **Upgrade Options**: Consider paid plans for higher traffic
- **Database**: PostgreSQL with vector extensions for semantic search

## Support

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Docker Best Practices**: Included in this setup
- **Monitoring**: Use Render's built-in monitoring tools

---

Your application is now ready for deployment! The Docker setup ensures consistent behavior between local development and production environments.
