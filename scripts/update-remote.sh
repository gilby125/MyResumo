#!/bin/bash

# Script to update the remote server with the latest code

# Set variables
REMOTE_SERVER="192.168.7.10"
REMOTE_USER="root"  # Change this to the appropriate user
REMOTE_PASSWORD="Lokifish123"  # Password for the remote server
CONTAINER_NAME="myresumo"  # Change this to the appropriate container name

# Display information
echo "Updating remote server at $REMOTE_SERVER"
echo "Container name: $CONTAINER_NAME"

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "sshpass is not installed. Please install it first:"
    echo "sudo dnf install sshpass"
    exit 1
fi

# Function to execute commands on the remote server
execute_remote_command() {
    local command="$1"
    echo "Executing: $command"
    sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_SERVER "$command"
}

# Connect to the remote server and execute commands
echo "Connecting to remote server..."

# Find the actual Docker container directory
echo "Finding Docker container directory..."
DOCKER_DIR=$(execute_remote_command "find / -name docker-compose.yml -type f 2>/dev/null | grep -v '/\.' | head -1 | xargs dirname")
if [ -z "$DOCKER_DIR" ]; then
    echo "Error: Could not find docker-compose.yml on the remote server."
    echo "Please check if Docker Compose is installed and the project is set up correctly."
    exit 1
fi
echo "Found Docker container directory: $DOCKER_DIR"

# Pull the latest code from GitHub
echo "Pulling latest code from GitHub..."
execute_remote_command "cd $DOCKER_DIR && git pull"

# Rebuild the Docker container
echo "Rebuilding Docker container..."
execute_remote_command "cd $DOCKER_DIR && docker-compose build --no-cache"

# Restart the container
echo "Restarting Docker container..."
execute_remote_command "cd $DOCKER_DIR && docker-compose down"
execute_remote_command "cd $DOCKER_DIR && docker-compose up -d"

# Check the status of the container
echo "Container status:"
execute_remote_command "docker ps | grep -i resume"

echo "Remote server update complete!"
