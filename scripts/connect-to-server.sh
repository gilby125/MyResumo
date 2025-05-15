#!/bin/bash

# Script to connect to the remote server

# Set variables
REMOTE_SERVER="192.168.7.10"
REMOTE_USER="root"
REMOTE_PASSWORD="Lokifish123"

# Display information
echo "Connecting to remote server at $REMOTE_SERVER"
echo "User: $REMOTE_USER"

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "sshpass is not installed. Please install it first:"
    echo "sudo dnf install sshpass"
    exit 1
fi

# Connect to the remote server
echo "Connecting to remote server..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_SERVER

echo "Connection closed."
