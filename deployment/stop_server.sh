#!/usr/bin/env bash
# Easy Local Chat - Stop Server Script

# Move to project root
cd "$(dirname "$0")/.."

echo "Stopping server..."

# Stop uvicorn process
if pkill -f "uvicorn src.main:app" 2>/dev/null; then
    echo "✓ Server stopped"
else
    echo "✗ No running server found"
    exit 1
fi

