#!/bin/bash

# Run E2E Tests Script
# This script runs the end-to-end tests for the MyResumo application

# Set the base URL for the tests
export BASE_URL="http://192.168.7.10:32811"

# Print the test environment
echo "Running tests against: $BASE_URL"
echo "Using Playwright version: $(npx playwright --version)"

# Check if the application is running
echo "Checking if the application is running..."
if curl -s --head "$BASE_URL" | grep "200 OK" > /dev/null; then
  echo "Application is running at $BASE_URL"
else
  echo "Error: Application is not running at $BASE_URL"
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