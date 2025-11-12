#!/usr/bin/env bash
# Easy Local Chat - Server Status Check Script

# Move to project root
cd "$(dirname "$0")/.."

echo "=========================================="
echo "Easy Local Chat - Server Status"
echo "=========================================="
echo ""

# Check process
echo "Process:"
PROCESSES=$(ps aux | grep "uvicorn src.main:app" | grep -v grep)
if [ -n "$PROCESSES" ]; then
    echo "✓ Server is running"
    echo "$PROCESSES"
else
    echo "✗ Server is not running"
fi

echo ""
echo "Port 8000:"
if command -v lsof >/dev/null 2>&1; then
    PORT_STATUS=$(lsof -i :8000 2>/dev/null)
    if [ -n "$PORT_STATUS" ]; then
        echo "$PORT_STATUS"
    else
        echo "Not in use"
    fi
else
    echo "lsof not available"
fi

# Get local IP
get_local_ip() {
    for interface in en0 en1 eth0 wlan0; do
        LOCAL_IP=$(ifconfig "$interface" 2>/dev/null | grep "inet " | awk '{print $2}' | grep -v "127.0.0.1")
        [ -n "$LOCAL_IP" ] && echo "$LOCAL_IP" && return
    done
    LOCAL_IP=$(ip addr show 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | head -1 | awk '{print $2}' | cut -d/ -f1)
    [ -n "$LOCAL_IP" ] && echo "$LOCAL_IP"
}

LOCAL_IP=$(get_local_ip)

echo ""
echo "Access URLs:"
echo "  http://localhost:8000"
[ -n "$LOCAL_IP" ] && echo "  http://$LOCAL_IP:8000"

echo ""
echo "=========================================="

