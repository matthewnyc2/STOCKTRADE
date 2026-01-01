#!/bin/bash

# Script to validate integration test structure and dependencies

echo "Validating integration test suite..."

# Check if test directory exists
if [ ! -d "__tests__/integration" ]; then
    echo "❌ Integration tests directory not found!"
    exit 1
fi

echo "✅ Integration tests directory exists"

# List of required test files
REQUIRED_TESTS=(
    "strategy-workflow.test.tsx"
    "backtest-workflow.test.tsx"
    "paper-trade-workflow.test.tsx"
    "websocket-resilience.test.tsx"
    "mode-switching.test.tsx"
    "error-handling.test.tsx"
)

# Check for required test files
for test_file in "${REQUIRED_TESTS[@]}"; do
    if [ -f "__tests__/integration/$test_file" ]; then
        echo "✅ Found: $test_file"
    else
        echo "❌ Missing: $test_file"
    fi
done

# Check for utility files
if [ -f "__tests__/utils/test-utils.ts" ]; then
    echo "✅ Found: test-utils.ts"
else
    echo "❌ Missing: test-utils.ts"
fi

if [ -f "__tests__/utils/setup.ts" ]; then
    echo "✅ Found: setup.ts"
else
    echo "❌ Missing: setup.ts"
fi

# Check for documentation
if [ -f "__tests__/integration/README.md" ]; then
    echo "✅ Found: README.md"
else
    echo "❌ Missing: README.md"
fi

# Count test files
TEST_COUNT=$(find __tests__/integration -name "*.test.tsx" | wc -l)
echo "Total test files: $TEST_COUNT"

# Check if all required tests are present
MISSING_TESTS=()
for test_file in "${REQUIRED_TESTS[@]}"; do
    if [ ! -f "__tests__/integration/$test_file" ]; then
        MISSING_TESTS+=("$test_file")
    fi
done

if [ ${#MISSING_TESTS[@]} -eq 0 ]; then
    echo "🎉 All required integration tests are present!"
    exit 0
else
    echo "❌ Missing tests: ${MISSING_TESTS[*]}"
    exit 1
fi