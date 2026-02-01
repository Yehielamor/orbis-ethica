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
    
    echo "⬇️ Pulling latest code..."
    git pull origin main
    
    # 2. Setup Virtual Environment (Fixes 'externally-managed-environment' error)
    if [ ! -d "venv" ]; then
        echo "� Creating Python Virtual Environment..."
        python3 -m venv venv
    fi
    
    # Activate Venv
    source venv/bin/activate
    
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    echo "🔄 Restarting Orbis Node..."
    pkill -f "backend/server.py" || true
    
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
