#!/bin/bash

# Get the current version from version.txt
CURRENT_VERSION=$(cat version.txt | head -n 1 | grep -o "^[0-9]*\.[0-9]*\.[0-9]*")

# If no version was found, use a default
if [ -z "$CURRENT_VERSION" ]; then
    CURRENT_VERSION="2.0.0"
fi

# Get the current timestamp
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Update the version.txt file with the timestamp
echo "${CURRENT_VERSION}-${TIMESTAMP}" > version.txt

echo "Updated version.txt to ${CURRENT_VERSION}-${TIMESTAMP}"
