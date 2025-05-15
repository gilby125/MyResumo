#!/bin/bash

# Script to update the version.txt file to force Docker to rebuild

# Get the current timestamp
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Get the current git commit hash
COMMIT_HASH=$(git rev-parse --short HEAD)

# Update the version.txt file
echo "${TIMESTAMP}-${COMMIT_HASH}" > version.txt

echo "Updated version.txt to ${TIMESTAMP}-${COMMIT_HASH}"
