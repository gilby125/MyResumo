# Updating the Remote Server

This document explains how to update the remote server with the latest code changes.

## Problem

When you make changes to the code locally, commit them to GitHub, and push them to the remote repository, the changes are not automatically reflected on the remote server. This is because the Docker container on the remote server is built with the code at build time, not at runtime.

## Solution

To update the remote server with the latest code changes, you need to:

1. Connect to the remote server
2. Pull the latest code from GitHub
3. Rebuild the Docker container
4. Restart the container

## Manual Update Process

1. SSH into the remote server:
   ```bash
   ssh root@192.168.7.10
   ```

2. Navigate to the project directory:
   ```bash
   cd /opt/myresumo  # Adjust this path as needed
   ```

3. Pull the latest code from GitHub:
   ```bash
   git pull
   ```

4. Rebuild the Docker container:
   ```bash
   docker-compose build --no-cache
   ```

5. Restart the container:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

6. Check the status of the container:
   ```bash
   docker ps | grep myresumo
   ```

## Automated Update Script

We've created a script to automate this process. The script is located at `scripts/update-remote.sh`. To use it:

1. Edit the script to set the correct values for:
   - `REMOTE_SERVER`: The IP address of the remote server
   - `REMOTE_USER`: The username to use for SSH
   - `REMOTE_DIR`: The directory where the project is located on the remote server
   - `CONTAINER_NAME`: The name of the Docker container

2. Run the script:
   ```bash
   ./scripts/update-remote.sh
   ```

## Troubleshooting

If you're still not seeing your changes after updating the remote server, check the following:

1. Make sure your changes are committed and pushed to GitHub:
   ```bash
   git status
   git log -1
   ```

2. Make sure the remote server is pulling from the correct branch:
   ```bash
   git branch -v
   ```

3. Check the Docker container logs for any errors:
   ```bash
   docker logs myresumo
   ```

4. Check if the container is using the correct volume mounts:
   ```bash
   docker inspect myresumo
   ```

## Best Practices

1. Always test your changes locally before pushing them to GitHub
2. Use a staging environment to test changes before deploying to production
3. Consider setting up a CI/CD pipeline to automate the deployment process
4. Use Docker volumes for development to avoid having to rebuild the container for every change
