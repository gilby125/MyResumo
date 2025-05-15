#!/bin/bash

# Update version.txt with timestamp
./update_version.sh

# Set cache bust environment variable
export CACHE_BUST=$(date +%s)
echo "Setting CACHE_BUST to $CACHE_BUST"

# Build with no cache
echo "Building Docker image with no cache..."
docker-compose build --no-cache web

echo "Build complete. You can now push the changes to GitHub or deploy directly to Portainer."
