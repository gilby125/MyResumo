# Updating the Application on Portainer

This document explains how to update the application running on Portainer on the remote server.

## Prerequisites

1. SSH access to the remote server
2. Access to the Portainer web interface
3. Knowledge of the application container name

## Method 1: Using the Portainer Web Interface

1. Connect to the Portainer web interface at http://192.168.7.10:9000
2. Log in with your credentials
3. Navigate to the Containers section
4. Find the application container (usually named "myresumo" or similar)
5. Click on the container to view its details
6. Click on the "Recreate" button to recreate the container with the latest image
7. If needed, click on the "Restart" button to restart the container

## Method 2: Using SSH

1. Connect to the remote server using SSH:
   ```bash
   ssh root@192.168.7.10
   ```
   Password: `Lokifish123`

2. Find the application container:
   ```bash
   docker ps | grep -i myresumo
   ```

3. Get the container ID:
   ```bash
   CONTAINER_ID=$(docker ps | grep -i myresumo | awk '{print $1}')
   ```

4. Find the GitHub repository directory:
   ```bash
   find / -name .git -type d 2>/dev/null | grep -v '/\.' | grep -i myresumo
   ```

5. Navigate to the GitHub repository directory:
   ```bash
   cd /path/to/repository
   ```

6. Pull the latest code from GitHub:
   ```bash
   git pull
   ```

7. Restart the container:
   ```bash
   docker restart $CONTAINER_ID
   ```

8. Check the status of the container:
   ```bash
   docker ps | grep $CONTAINER_ID
   ```

## Method 3: Using the Connect Script

We've created a script to connect to the remote server. To use it:

1. Run the script:
   ```bash
   ./scripts/connect-to-server.sh
   ```

2. Once connected, follow the steps in Method 2 from step 2 onwards.

## Troubleshooting

If you're still not seeing your changes after updating the application, try the following:

1. Check if the container is using volume mounts:
   ```bash
   docker inspect $CONTAINER_ID | grep -A 10 "Mounts"
   ```

2. If the container is using volume mounts, check if the mounted directories contain the latest code:
   ```bash
   ls -la /path/to/mounted/directory
   ```

3. If the mounted directories don't contain the latest code, you may need to manually copy the files:
   ```bash
   cp -r /path/to/repository/* /path/to/mounted/directory/
   ```

4. Restart the container again:
   ```bash
   docker restart $CONTAINER_ID
   ```

## Best Practices

1. Always test your changes locally before pushing them to GitHub
2. Use a staging environment to test changes before deploying to production
3. Consider setting up a CI/CD pipeline to automate the deployment process
4. Use Docker volumes for development to avoid having to rebuild the container for every change
