#!/bin/bash

# Run MongoDB Integration Tests Script
# This script runs the MongoDB integration tests for the MyResumo application

# Load environment variables from .env.test file
if [ -f .env.test ]; then
  echo "Loading environment variables from .env.test"
  export $(grep -v '^#' .env.test | xargs)
else
  echo "Warning: .env.test file not found, using default values"
  # Set default values
  export MONGODB_HOST="192.168.7.10"
  export MONGODB_PORT="27017"
  export DB_NAME="myresumo"
fi

# Allow overriding the MongoDB host from command line
if [ ! -z "$1" ]; then
  export MONGODB_HOST="$1"
fi

# Allow overriding the MongoDB port from command line
if [ ! -z "$2" ]; then
  export MONGODB_PORT="$2"
fi

# Print the test environment
echo "Testing MongoDB connection to: $MONGODB_HOST:$MONGODB_PORT"
echo "Using database: $DB_NAME"
echo "Using Playwright version: $(npx playwright --version)"

# Run the MongoDB integration tests
echo "Running MongoDB integration tests..."
LOG_FILE="mongodb-test-output.log"

if [ "$HEADED" = "true" ]; then
  echo "Running tests in headed mode (browser visible)"
  npx playwright test e2e/mongodb-integration.spec.ts --project=chromium --headed --reporter=list > "$LOG_FILE" 2>&1
else
  echo "Running tests in headless mode"
  npx playwright test e2e/mongodb-integration.spec.ts --project=chromium --reporter=list > "$LOG_FILE" 2>&1
fi

# Display the log file
echo "Test output saved to $LOG_FILE"
echo "=== Test Output ==="
cat "$LOG_FILE"
echo "=== End Test Output ==="

# Check the exit code
if [ $? -eq 0 ]; then
  echo "All MongoDB tests passed!"
else
  echo "Some MongoDB tests failed. Check the test report for details."
fi

# Generate the test report but don't open it
echo "Test report generated at ./playwright-report"
echo "To view the report, run: npx playwright show-report"

echo "Done!"