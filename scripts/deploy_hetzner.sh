#!/bin/bash

# Remote Deployment to Hetzner Node
SERVER_IP="46.62.199.4"
USER="root"
REMOTE_DIR="/root/orbis-ethica"

echo "🚀 Connecting to Hetzner Node ($SERVER_IP)..."

ssh -t $USER@$SERVER_IP << EOF
    echo "👋 Connected to Remote Server."
    
    # 1. Ensure Directory Exists (Clone if missing)
    if [ ! -d "$REMOTE_DIR" ]; then
        echo "📂 Repo not found. Cloning for the first time..."
        # Using HTTPS for public/easier access without SSH keys setup on server for now
        git clone https://github.com/yehielamor/orbis-ethica.git $REMOTE_DIR
    fi
    
    cd $REMOTE_DIR
    
    echo "⬇️ Forcing latest code (Nuclear Option)..."
    git fetch origin
    git reset --hard origin/main
    
    echo "🔍 Verifying update matches origin..."
    git log -1 --oneline
    
    # Check explicitly for the handshake function
    if grep -q "handshake" backend/server.py; then
        echo "✅ CODE IS CORRECT: 'handshake' found."
    else
        echo "❌ CRITICAL FAILURE: Git update failed."
        exit 1
    fi
    
    # 2. Setup Virtual Environment
    if [ ! -d "venv" ]; then
        echo "🐍 Creating Python Virtual Environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo "� Killing EVERYTHING on port 8000..."
    # Try friendly kill
    pkill -f "server.py" || true
    # Try aggressive port kill (fuser might not be installed, so we use python fallback again but simpler)
    fuser -k 8000/tcp || true
    killall python3 || true
    sleep 3

    
    export PORT=8000
    # Use the Public IP we know
    export MY_IP="$SERVER_IP"
    export NODE_ID="genesis_hetzner"
    
    # Using nohup to keep it running
    nohup python backend/server.py > server.log 2>&1 &
    
    echo "✅ Node Restarted in background!"
    echo "   Log file: $REMOTE_DIR/server.log"
    exit
EOF

echo "🔌 Disconnected."
