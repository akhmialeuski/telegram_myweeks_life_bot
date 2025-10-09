#!/bin/bash

# Script for automatic code formatting fixes
# Runs black and isort to fix formatting issues

set -e

echo "🔧 Fixing code style..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    echo "❌ This script must be run from the project root!"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "Virtual environment not activated. Attempting to activate..."
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "❌ Virtual environment not found in .venv/"
        exit 1
    fi
fi

# 1. Fix code formatting with black
echo "📝 Fixing code formatting (black)..."
black .
print_status "Code formatting fixed"

# 2. Fix import sorting with isort
echo "📦 Fixing import sorting (isort)..."
isort .
print_status "Import sorting fixed"

echo ""
print_status "Code style fixed! You can now commit your changes."