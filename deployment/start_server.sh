#!/usr/bin/env bash
# Easy Local Chat - Production Server Startup Script

set -e  # Exit on error

# Move to project root
cd "$(dirname "$0")/.."

echo "=========================================="
echo "Easy Local Chat - Starting Server"
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

# Get local IP address
get_local_ip() {
    # Try common network interfaces
    for interface in en0 en1 eth0 wlan0; do
        LOCAL_IP=$(ifconfig "$interface" 2>/dev/null | grep "inet " | awk '{print $2}' | grep -v "127.0.0.1")
        [ -n "$LOCAL_IP" ] && echo "$LOCAL_IP" && return
    done
    # Fallback: use ip command (Linux)
    LOCAL_IP=$(ip addr show 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | head -1 | awk '{print $2}' | cut -d/ -f1)
    [ -n "$LOCAL_IP" ] && echo "$LOCAL_IP"
}

LOCAL_IP=$(get_local_ip)

echo "Server starting..."
echo ""
echo "Access URLs:"
echo "  Local:   http://localhost:8000"
[ -n "$LOCAL_IP" ] && echo "  Network: http://$LOCAL_IP:8000"
echo ""
echo "Admin:   /admin"
echo "Login:   /login"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Start server
uvicorn src.main:app --host 0.0.0.0 --port 8000

