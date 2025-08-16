#!/bin/bash
# Test runner with proper environment configuration

# Load test environment variables
if [ -f .env.test ]; then
    echo "📄 Loading test environment from .env.test"
    export $(cat .env.test | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env.test file not found"
fi

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)/src"
echo "🐍 PYTHONPATH set to: $PYTHONPATH"

# Function to show timing
time_it() {
    local start=$(date +%s)
    "$@"
    local result=$?
    local end=$(date +%s)
    echo "⏱️  Execution time: $((end - start)) seconds"
    return $result
}

# Default to running all tests with coverage
if [ $# -eq 0 ]; then
    echo "🧪 Running all tests with coverage..."
    time_it pytest --cov=src --cov-report=html --cov-report=term-missing
else
    echo "🧪 Running tests with arguments: $@"
    time_it pytest "$@"
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi