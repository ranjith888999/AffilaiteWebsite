# Render Docker Deployment Guide

This document provides step-by-step instructions for deploying your Affiliate Website to Render using Docker.

## Prerequisites

- GitHub account with your repository
- Render account
- Docker Desktop (for local testing)

## Deployment Steps

### 1. Test Docker Locally (Optional but Recommended)

```bash
# Build the Docker image
docker build -t affiliate-website .

# Run the container locally
docker run -p 8000:8000 --env-file .env affiliate-website
```

Visit http://localhost:8000 to verify it works correctly.

### 2. Push Changes to GitHub

```bash
# Add all files to git
git add .

# Commit the changes
git commit -m "Add Docker configuration for Render deployment"

# Push to GitHub
git push origin main
```

### 3. Deploy to Render

1. **Log in to Render Dashboard**:
   - Go to https://dashboard.render.com/

2. **Create a New Blueprint**:
   - Click on "New" in the top navigation
   - Select "Blueprint"
   - Connect your GitHub repository

3. **Configure Your Blueprint**:
   - Render will automatically detect your `render.yaml` file
   - Review the proposed services (web service and database)
   - Make any necessary adjustments to the settings

4. **Set Environment Variables**:
   - Add your `CUELINKS_API_KEY` and `SECRET_KEY` values
   - Note: Database credentials will be automatically generated

5. **Deploy**:
   - Click "Apply" to start the deployment process
   - Wait for Render to build and deploy your application

### 4. Monitor Deployment

1. **Check Build Logs**:
   - Review the build logs for any errors
   - Make sure the Docker build completes successfully

2. **Verify Database Setup**:
   - Check that the PostgreSQL database with pgvector extension is properly created
   - Verify connectivity between your app and database

3. **Test Your Live Application**:
   - Visit your Render URL when deployment is complete
   - Test key functionality like search, chat, and affiliate links

### 5. Post-Deployment Tasks

1. **Initialize Database**:
   - If needed, run database initialization scripts through the Render shell
   - You can open a shell from the Render dashboard

2. **Set Up Custom Domain (Optional)**:
   - Configure a custom domain in the Render dashboard
   - Update DNS settings with your domain provider

### Troubleshooting

If you encounter issues with your deployment:

1. **Check Docker Logs**:
   - Review build logs in the Render dashboard
   - Look for any error messages during the build or startup

2. **Verify Environment Variables**:
   - Make sure all required environment variables are set
   - Check database connection strings

3. **Database Issues**:
   - Ensure the pgvector extension is properly installed
   - Check database migrations if data is not appearing

4. **Contact Render Support**:
   - If you continue to have issues, Render support can help troubleshoot

## Maintenance

To update your deployment:

1. Make changes to your code locally
2. Test with Docker locally if needed
3. Push changes to GitHub
4. Render will automatically rebuild and deploy

## Important Files

Your deployment configuration relies on these key files:

- `render.yaml` - Defines the services for Render
- `Dockerfile` - Instructions for building your Docker container
- `.dockerignore` - Files to exclude from the Docker build
- `requirements.txt` - Python dependencies

Remember to keep these files updated when making significant changes to your application.
