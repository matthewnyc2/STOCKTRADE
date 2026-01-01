#!/bin/bash

# Script to check TypeScript syntax of test files

echo "Checking TypeScript syntax of integration tests..."

# List of test files
TEST_FILES=(
    "__tests__/integration/strategy-workflow.test.tsx"
    "__tests__/integration/backtest-workflow.test.tsx"
    "__tests__/integration/paper-trade-workflow.test.tsx"
    "__tests__/integration/websocket-resilience.test.tsx"
    "__tests__/integration/mode-switching.test.tsx"
    "__tests__/integration/error-handling.test.tsx"
    "__tests__/utils/test-utils.ts"
    "__tests__/utils/setup.ts"
)

# Check each file
ERRORS=0
for file in "${TEST_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "Checking: $file"
        # Use npx tsc to check syntax without emitting files
        npx tsc --noEmit --skipLibCheck "$file" 2>&1
        if [ $? -eq 0 ]; then
            echo "✅ Syntax OK: $file"
        else
            echo "❌ Syntax Error: $file"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "❌ File not found: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "🎉 All test files have valid TypeScript syntax!"
    exit 0
else
    echo "❌ Found $ERRORS files with syntax errors!"
    exit 1
fi