#!/bin/bash

# Run Local Tests Script
# This script runs the end-to-end tests against a local server but with the remote MongoDB

# Load environment variables from .env.local-test file
if [ -f .env.local-test ]; then
  echo "Loading environment variables from .env.local-test"
  export $(grep -v '^#' .env.local-test | xargs)
else
  echo "Warning: .env.local-test file not found, using default values"
  # Set default values
  export TEST_BASE_URL="http://localhost:8000"
  export MONGODB_HOST="192.168.7.10"
  export MONGODB_PORT="27017"
  export DB_NAME="myresumo"
fi

# Print the test environment
echo "Running tests against local server: $TEST_BASE_URL"
echo "Using remote MongoDB at: $MONGODB_HOST:$MONGODB_PORT"
echo "Using database: $DB_NAME"
echo "Using Playwright version: $(npx playwright --version)"

# Check if the local application is running
echo "Checking if the local application is running..."
if curl -s --head "$TEST_BASE_URL" | grep "200 OK" > /dev/null; then
  echo "Local application is running at $TEST_BASE_URL"
else
  echo "Error: Local application is not running at $TEST_BASE_URL"
  echo "Please start the local server before running the tests"
  echo "You can start the local server with: python -m app.main"
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