#!/bin/bash

# Script to run tests with Python 3.11
# Usage: ./run_tests_py311.sh [pytest_options]

set -e

echo "🐍 Running tests with Python 3.11..."
echo "📁 Test environment: test_env_py311"
echo ""

# Check if virtual environment exists
if [ ! -d "test_env_py311" ]; then
    echo "❌ Python 3.11 test environment not found!"
    echo "Please run: python3.11 -m venv test_env_py311"
    echo "Then run: test_env_py311/bin/pip install -r requirements-test.txt"
    exit 1
fi

# Run tests with provided options or default
if [ $# -eq 0 ]; then
    echo "🚀 Running all tests..."
    test_env_py311/bin/python -m pytest tests/ -v --tb=short
else
    echo "🚀 Running tests with options: $@"
    test_env_py311/bin/python -m pytest tests/ "$@"
fi

echo ""
echo "✅ Tests completed!" 