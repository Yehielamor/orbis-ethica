#!/bin/bash

# Orbis Ethica Node Startup Script
# Automatically detects network environment (Tailscale vs Local)

echo "🚀 Initializing Orbis Ethica Node..."

# 1. Detect IP Address
if command -v tailscale &> /dev/null; then
    echo "✅ Tailscale detected. Using VPN IP."
    export MY_IP=$(tailscale ip -4)
else
    echo "⚠️ Tailscale not found. Falling back to Localhost (127.0.0.1)."
    export MY_IP="127.0.0.1"
fi

# 2. Set Default Port if not set
if [ -z "$PORT" ]; then
    export PORT=8000
fi

# 3. Set Node ID if not set
if [ -z "$NODE_ID" ]; then
    export NODE_ID="node_$(whoami)_$PORT"
fi

# 4. Print Configuration
echo "--------------------------------"
echo "🌐 Node Configuration:"
echo "   ID:   $NODE_ID"
echo "   IP:   $MY_IP"
echo "   PORT: $PORT"
echo "   SEEDS: ${SEED_NODES:-"None (Genesis Mode)"}"
echo "--------------------------------"

# 5. Start Server
# Ensure PYTHONPATH includes the current directory
export PYTHONPATH=$PYTHONPATH:.
python backend/server.py
