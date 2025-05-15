#!/bin/bash

# Script to update the application running on Portainer on the remote server

# Set variables
REMOTE_SERVER="192.168.7.10"
REMOTE_USER="root"
REMOTE_PASSWORD="Lokifish123"
APP_NAME="myresumo"  # The name of the application container in Portainer

# Display information
echo "Updating application on Portainer at $REMOTE_SERVER"
echo "Application name: $APP_NAME"

# Function to execute commands on the remote server
execute_remote_command() {
    local command="$1"
    echo "Executing: $command"
    sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_SERVER "$command"
}

# Connect to the remote server and execute commands
echo "Connecting to remote server..."

# Check if Portainer is running
echo "Checking if Portainer is running..."
PORTAINER_RUNNING=$(execute_remote_command "docker ps | grep -i portainer | wc -l")
if [ "$PORTAINER_RUNNING" -eq "0" ]; then
    echo "Error: Portainer is not running on the remote server."
    echo "Please start Portainer and try again."
    exit 1
fi
echo "Portainer is running."

# Find the application container
echo "Finding the application container..."
APP_CONTAINER=$(execute_remote_command "docker ps | grep -i $APP_NAME | awk '{print \$1}'")
if [ -z "$APP_CONTAINER" ]; then
    echo "Error: Could not find the application container."
    echo "Please check if the application is running and try again."
    exit 1
fi
echo "Found application container: $APP_CONTAINER"

# Get the container details
echo "Getting container details..."
CONTAINER_DETAILS=$(execute_remote_command "docker inspect $APP_CONTAINER")
echo "Container details retrieved."

# Find the volume mounts
echo "Finding volume mounts..."
VOLUME_MOUNTS=$(execute_remote_command "docker inspect $APP_CONTAINER | grep -A 10 'Mounts' | grep 'Source' | awk -F '\"' '{print \$4}'")
echo "Volume mounts: $VOLUME_MOUNTS"

# Find the GitHub repository directory
echo "Finding GitHub repository directory..."
GITHUB_DIR=$(execute_remote_command "find / -name .git -type d 2>/dev/null | grep -v '/\.' | grep -i myresumo | head -1 | xargs dirname")
if [ -z "$GITHUB_DIR" ]; then
    echo "Error: Could not find the GitHub repository directory."
    echo "Please check if the repository is cloned on the remote server and try again."
    exit 1
fi
echo "Found GitHub repository directory: $GITHUB_DIR"

# Pull the latest code from GitHub
echo "Pulling latest code from GitHub..."
execute_remote_command "cd $GITHUB_DIR && git pull"

# Update the version file to force cache invalidation
echo "Updating version file..."
execute_remote_command "cd $GITHUB_DIR && bash scripts/update-version.sh"

# Rebuild the container with no cache
echo "Rebuilding the container with no cache..."
execute_remote_command "cd $GITHUB_DIR && docker build --no-cache -t myresumo:latest ."

# Stop the current container
echo "Stopping the current container..."
execute_remote_command "docker stop $APP_CONTAINER"

# Remove the current container
echo "Removing the current container..."
execute_remote_command "docker rm $APP_CONTAINER"

# Start a new container with the same configuration
echo "Starting a new container..."
execute_remote_command "cd $GITHUB_DIR && docker-compose up -d"

# Check the status of the container
echo "Container status:"
execute_remote_command "docker ps | grep $APP_CONTAINER"

echo "Application update complete!"
echo "Please wait a few moments for the application to restart and then check if your changes are visible."
