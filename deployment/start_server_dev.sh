#!/usr/bin/env bash
# Easy Local Chat - Development Server Startup Script (with auto-reload)

set -e  # Exit on error

# Move to project root
cd "$(dirname "$0")/.."

echo "=========================================="
echo "Easy Local Chat - Development Mode"
echo "=========================================="
echo ""

# Check/setup virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "Error: Cannot find virtual environment activation script"
    exit 1
fi

# Install/update dependencies
pip install -q -r requirements.txt

echo "Starting development server (auto-reload enabled)..."
echo ""
echo "📝 Access URLs will be displayed after startup."
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Start development server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

