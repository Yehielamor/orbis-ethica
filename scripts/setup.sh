#!/bin/bash

# Orbis Ethica - Setup Script
# This script sets up the development environment

set -e

echo "🌍 Orbis Ethica - Setup Script"
echo "================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3.11 &> /dev/null; then
    echo -e "${YELLOW}Python 3.11 not found. Please install Python 3.11+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3.11+ found${NC}"

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Create .env file
if [ ! -f ".env" ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created (please update with your keys)${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Setup frontend
cd ../frontend
if [ -f "package.json" ]; then
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

# Setup blockchain
cd ../blockchain
if [ -f "package.json" ]; then
    echo -e "${BLUE}Installing blockchain dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Blockchain dependencies installed${NC}"
fi

cd ..

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your API keys"
echo "2. Activate virtual environment: cd backend && source venv/bin/activate"
echo "3. Run tests: pytest tests/"
echo "4. Start CLI: python -m cli.main --help"
echo ""
