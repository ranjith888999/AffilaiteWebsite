# Docker Deployment Guide for Affiliate Website

This document provides instructions for deploying the Affiliate Website using Docker, both locally and on Render.

## Local Development with Docker

### Prerequisites
- Docker and Docker Compose installed
- Cuelinks API key

### Running Locally

1. Create a `.env` file in the root directory with your environment variables:
```
CUELINKS_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
```

2. Build and start the Docker containers:
```bash
docker-compose up --build
```

3. Access the application at http://localhost:8000

## Deploying to Render

### Prerequisites
- GitHub repository with your code
- Render account
- Docker installed (for local testing)

### Deployment Steps

1. Push your code to GitHub, including the Dockerfile, docker-compose.yml, and render.yaml files.

2. Log in to your Render account and navigate to the Dashboard.

3. Click "New" and select "Blueprint".

4. Connect your GitHub repository.

5. Render will automatically detect the render.yaml file and create the necessary services.

6. Set up the required environment variables in the Render dashboard:
   - CUELINKS_API_KEY
   - SECRET_KEY

7. Deploy the service.

### Troubleshooting

If you encounter issues with the deployment:

1. Check the build logs in the Render dashboard.
2. Ensure the pgvector extension is properly installed in the database.
3. Verify that all environment variables are correctly set.
4. Check if the container is able to connect to the database.

## Maintenance

To update your deployment:

1. Push changes to your GitHub repository.
2. Render will automatically rebuild and redeploy your application.

For database migrations:

1. Connect to the Render database using the provided connection details.
2. Run your migration scripts or use Alembic to manage schema changes.
