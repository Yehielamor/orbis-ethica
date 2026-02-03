#!/bin/bash

# start_all.sh - Run Orbis Ethica (Server + Miner)
# This script handles the complexity of running both processes.

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Orbis Ethica Auto-Pilot...${NC}"

# 1. Kill old processes (Cleanup)
echo -e "${BLUE}🧹 Cleaning up old processes...${NC}"
pkill -f "backend/server.py" || true
pkill -f "scripts/genesis_miner.py" || true
sleep 1

# 2. Start Server
echo -e "${GREEN}🔌 Starting Server (API Layer)...${NC}"
nohup python -u backend/server.py > server.log 2>&1 &
SERVER_PID=$!
echo "   PID: $SERVER_PID"

echo "⏳ Waiting 5s for server to boot..."
sleep 5

# 3. Health Check
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Server is Online!${NC}"
else
    echo -e "${RED}❌ Server failed to start. Check server.log${NC}"
    tail -n 10 server.log
    kill $SERVER_PID
    exit 1
fi

# 4. Start Miner
echo -e "${GREEN}⛏️  Starting Genesis Miner (PoW Layer)...${NC}"
export NODE_URL="http://127.0.0.1:8000"
nohup python -u scripts/genesis_miner.py > miner.log 2>&1 &
MINER_PID=$!
echo "   PID: $MINER_PID"

echo -e "${BLUE}✨ System Fully Operational!${NC}"
echo "   - API:    http://127.0.0.1:8000"
echo "   - Docs:   http://127.0.0.1:8000/docs"
echo "   - Logs:   tail -f server.log miner.log"
echo ""
echo "Press [CTRL+C] to stop everything."

# 5. Trap Exit
trap "kill $SERVER_PID $MINER_PID; exit" INT
wait
