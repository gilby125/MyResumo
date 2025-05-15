# Portainer Rebuild Configuration

This document explains the configuration to force Portainer to rebuild the application container after changes are pushed to GitHub.

## Overview

By default, Docker and Portainer use caching mechanisms to speed up builds. While this is efficient for development, it can sometimes cause issues when you want to ensure that all changes are properly incorporated into a new build.

The following mechanisms have been implemented to force a complete rebuild:

## 1. Version File

A `version.txt` file is used to invalidate Docker's build cache. This file is:
- Updated with a timestamp and commit hash before each build
- Copied early in the Dockerfile to invalidate the cache for subsequent steps

## 2. No-Cache Build Options

Several mechanisms force Docker to build without using cache:
- The `update-portainer.sh` script uses the `--no-cache` flag when building
- A `docker-compose.override.yml` file sets `no_cache: true` for local development
- The GitHub workflow has been modified to use `no-cache: true`

## 3. Container Replacement

Instead of just restarting the container, the update script:
1. Stops the current container
2. Removes it completely
3. Rebuilds the image from scratch
4. Creates a new container

## Usage

### Manual Deployment

To manually trigger a rebuild:

```bash
./scripts/update-portainer.sh
```

### Automatic Deployment

The GitHub workflow will automatically:
1. Update the version file
2. Build without cache
3. Push to the GitHub Container Registry

## Troubleshooting

If changes are still not appearing after a push:

1. SSH into the server
2. Navigate to the repository directory
3. Run `git pull` to ensure the latest code is present
4. Run `docker-compose build --no-cache` to force a rebuild
5. Run `docker-compose down && docker-compose up -d` to restart the containers
