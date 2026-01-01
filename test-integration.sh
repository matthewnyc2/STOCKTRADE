#!/bin/bash

# Run integration tests for the frontend
echo "Running integration tests..."

# Navigate to frontend directory
cd frontend

# Run integration tests
npx jest __tests__/integration/ --verbose --testTimeout=30000

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Integration tests passed!"
    exit 0
else
    echo "❌ Integration tests failed!"
    exit 1
fi