#!/bin/bash

# Run E2E Tests Script
# This script runs the end-to-end tests for the MyResumo application

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
echo "Running tests against: $TEST_BASE_URL"
echo "Using MongoDB at: $MONGODB_HOST:$MONGODB_PORT"
echo "Using database: $DB_NAME"
echo "Using Playwright version: $(npx playwright --version)"

# Check if the application is running
echo "Checking if the application is running..."
if curl -s --head "$TEST_BASE_URL" | grep "200 OK" > /dev/null; then
  echo "Application is running at $TEST_BASE_URL"
else
  echo "Error: Application is not running at $TEST_BASE_URL"
  echo "Please make sure the application is running before running the tests"
  exit 1
fi

# Run the tests
echo "Running end-to-end tests..."
npx playwright test "$@"

# Check the exit code
if [ $? -eq 0 ]; then
  echo "All tests passed!"
else
  echo "Some tests failed. Check the test report for details."
fi

# Open the test report
echo "Opening test report..."
npx playwright show-report

echo "Done!"
