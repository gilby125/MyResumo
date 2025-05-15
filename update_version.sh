#!/bin/bash

# Get the current version from version.txt
CURRENT_VERSION=$(cat version.txt | head -n 1)

# Get the current timestamp
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Update the version.txt file with the timestamp
echo "${CURRENT_VERSION}-${TIMESTAMP}" > version.txt

echo "Updated version.txt to ${CURRENT_VERSION}-${TIMESTAMP}"
