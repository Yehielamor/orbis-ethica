#!/bin/bash

# Remote Deployment to Hetzner Node
SERVER_IP="46.62.199.4"
USER="root"
REMOTE_DIR="/root/orbis-ethica"

echo "🚀 Connecting to Hetzner Node ($SERVER_IP)..."

ssh -t $USER@$SERVER_IP << EOF
    echo "👋 Connected to Remote Server."
    
    # 0. Install utilities if missing
    apt-get update && apt-get install -y lsof net-tools curl
    
    # 1. Ensure Directory Exists (Clone if missing)
    if [ ! -d "$REMOTE_DIR" ]; then
        echo "📂 Repo not found. Cloning for the first time..."
        git clone https://github.com/yehielamor/orbis-ethica.git $REMOTE_DIR
    fi
    
    cd $REMOTE_DIR
    
    echo "⬇️ Forcing latest code..."
    git fetch origin
    git reset --hard origin/main
    
    # Check explicitly for the handshake function
    if grep -q "handshake" backend/server.py; then
        echo "✅ CODE IS CORRECT: 'handshake' found on disk."
    else
        echo "❌ CRITICAL FAILURE: Git update failed. Aborting."
        exit 1
    fi
    
    # 2. Setup Virtual Environment
    if [ ! -d "venv" ]; then
        echo "🐍 Creating Python Virtual Environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo "🐳 Checking for blocking Docker containers..."
    # Legacy container name check
    if docker ps -a --format '{{.Names}}' | grep -q "^orbis-ethica-backend$"; then
        echo "🛑 Stopping and removing legacy Docker container 'orbis-ethica-backend'..."
        docker stop orbis-ethica-backend || true
        docker rm orbis-ethica-backend || true
    fi
    
    # General Port 8000 check (Find ID of any container mapping to port 8000)
    DOCKER_PID=\$(docker ps --format '{{.ID}}' --filter expose=8000)
    
    if [ ! -z "\$DOCKER_PID" ]; then
        echo "🛑 Stopping unknown container binding port 8000: \$DOCKER_PID"
        docker stop \$DOCKER_PID || true
        docker rm \$DOCKER_PID || true
    fi

    echo "🔫 Hunting down process on port 8000..."
    
    # Find PID using lsof
    PID=\$(lsof -t -i:8000)
    
    if [ ! -z "\$PID" ]; then
        echo "💥 Killing PID \$PID (using port 8000)..."
        kill -9 \$PID
    else
        echo "Testing if port is taken by other means..."
        fuser -k 8000/tcp || true
    fi
    
    # Wait for port to clear
    echo "⏳ Waiting for port 8000 to clear..."
    for i in {1..10}; do
        if ! lsof -i:8000 > /dev/null; then
            echo "✅ Port 8000 is free."
            break
        fi
        echo "."
        sleep 1
    done
    
    # Final check
    if lsof -i:8000 > /dev/null; then
        echo "❌ Port 8000 is STILL in use. Cannot deploy."
        exit 1
    fi

    export PORT=8000
    export MY_IP="$SERVER_IP"
    export NODE_ID="genesis_hetzner"
    
    echo "🚀 Starting Server..."
    nohup python -u backend/server.py > server.log 2>&1 &
    
    echo "⏳ Waiting for server to boot..."
    sleep 5
    
    # Verify proper boot
    ROOT_RESP=\$(curl -s http://127.0.0.1:8000/health)
    echo "🔍 Health Check Response: \$ROOT_RESP"
    
    # Check if 'p2p_peers' is in response (marker of new version)
    if [[ "\$ROOT_RESP" == *"p2p_peers"* ]]; then
        echo "✅ SUCCESS: New version is live!"
        
        echo "⛏️  Starting Genesis Miner (Background)..."
        # Kill old miners
        pkill -f "genesis_miner.py" || true
        
        export NODE_URL="http://127.0.0.1:8000"
        nohup python -u scripts/genesis_miner.py > miner.log 2>&1 &
        echo "✅ Miner started! Check 'miner.log' for activity."
        
    else
        echo "⚠️ WARNING: Server responding, but might be old version or error."
        tail -n 20 server.log
    fi
    
    echo "   Server Log: $REMOTE_DIR/server.log"
    echo "   Miner Log:  $REMOTE_DIR/miner.log"
    exit
EOF

echo "🔌 Disconnected."
