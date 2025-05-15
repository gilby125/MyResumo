#!/bin/bash

# Run All Tests Script
# This script runs all the tests for the MyResumo application

# Load environment variables from .env.test file
if [ -f .env.test ]; then
  echo "Loading environment variables from .env.test"
  export $(grep -v '^#' .env.test | xargs)
else
  echo "Warning: .env.test file not found, using default values"
  # Set default values
  export TEST_BASE_URL="http://localhost:8000"
  export MONGODB_HOST="192.168.7.10"
  export MONGODB_PORT="27017"
  export DB_NAME="myresumo"
fi

# Allow overriding the base URL from command line
if [ ! -z "$1" ]; then
  export TEST_BASE_URL="$1"
fi

# Print the test environment
echo "Testing against: $TEST_BASE_URL"
echo "MongoDB connection: $MONGODB_HOST:$MONGODB_PORT"
echo "Database: $DB_NAME"

# Run the tests
echo "Running all tests..."

# Run the MongoDB integration tests
echo "Running MongoDB integration tests..."
npx playwright test e2e/mongodb-integration.spec.ts --project=chromium

# Run the UI tests
echo "Running UI tests..."
npx playwright test e2e/dashboard.spec.ts e2e/create-resume.spec.ts e2e/home.spec.ts --project=chromium

# Run the MCP tests
echo "Running MCP tests..."
npx playwright test e2e/mcp-test.spec.ts e2e/advanced-mcp.spec.ts --project=chromium

# Generate the test report but don't open it
echo "Test report generated at ./playwright-report"
echo "To view the report, run: npx playwright show-report"
