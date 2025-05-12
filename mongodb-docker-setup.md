# MongoDB Docker Setup

## Changes Made

We've modified the Docker configuration to expose MongoDB to external connections:

1. Updated `docker-compose.yml` to:
   - Expose port 27017 to the host machine
   - Configure MongoDB to accept connections from any IP address with `--bind_ip_all`

## How to Apply Changes

To apply these changes, run the following commands:

```bash
# Stop the current containers
docker-compose down

# Start the containers with the new configuration
docker-compose up -d
```

## Verifying the Connection

After restarting the containers, you should be able to:

1. Connect to MongoDB from outside the container using:
   ```
   mongodb://192.168.7.10:27017
   ```

2. Access the Swagger documentation for the prompts API at:
   ```
   http://192.168.7.10:32779/docs
   ```

## Troubleshooting

If you still can't connect to MongoDB after making these changes:

1. Check if MongoDB is running:
   ```bash
   docker-compose ps
   ```

2. Check MongoDB logs:
   ```bash
   docker-compose logs mongodb
   ```

3. Verify network connectivity:
   ```bash
   telnet 192.168.7.10 27017
   ```

4. Check for firewall rules that might be blocking port 27017.
