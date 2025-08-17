# Docker Deployment Troubleshooting Guide

## Common Docker Issues and Solutions

### 1. Docker Desktop is not running

**Symptoms:**
- Docker commands return no output
- `docker-compose up` fails silently

**Solution:**
1. Make sure Docker Desktop is installed and running
2. Open Docker Desktop application
3. Wait for the Docker engine to start (look for the green status indicator)
4. Try your Docker commands again

### 2. Environment Variable Issues

**Symptoms:**
- Error about unexpected characters in .env file
- Variable substitution not working

**Solution:**
1. Use the provided `local.env` file for local development
2. Ensure there are no quotes around your environment variable values
3. Avoid special characters in your environment variables
4. Make sure your files don't have any BOM (Byte Order Mark) or unusual encodings

### 3. Port Conflicts

**Symptoms:**
- Error message about port 5432 or 8000 already in use

**Solution:**
1. Stop any running PostgreSQL instances on your machine
2. Stop any running web servers on port 8000
3. Alternatively, modify the `docker-compose.yml` to use different ports

### 4. Docker Build Failures

**Symptoms:**
- Build process fails with error messages

**Solution:**
1. Check the Docker build logs for specific error messages
2. Ensure you have enough disk space
3. Make sure your Dockerfile is properly formatted
4. Try rebuilding with `docker-compose build --no-cache`

## Step-by-Step Docker Deployment Process

### Local Deployment

1. Start Docker Desktop and wait for it to be running (green icon in taskbar)

2. Navigate to your project directory:
   ```powershell
   cd "c:\Users\Ranjit\Desktop\Python\Affiliate Website"
   ```

3. Build and start your containers:
   ```powershell
   docker-compose up --build
   ```

4. Access your application at http://localhost:8000

### Render Deployment

1. Push your code to GitHub:
   ```powershell
   git add .
   git commit -m "Add Docker configuration"
   git push
   ```

2. Log in to your Render account

3. Create a new Blueprint pointing to your GitHub repository

4. Render will automatically use your render.yaml file to set up the services

5. Set the required environment variables in the Render dashboard

6. Deploy the service

## Useful Docker Commands

- View running containers:
  ```
  docker ps
  ```

- Stop all containers:
  ```
  docker-compose down
  ```

- Rebuild containers:
  ```
  docker-compose build --no-cache
  ```

- View container logs:
  ```
  docker-compose logs
  ```

- Connect to a running container:
  ```
  docker exec -it affiliate-website_web_1 bash
  ```
