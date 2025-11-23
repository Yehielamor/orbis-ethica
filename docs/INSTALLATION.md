# Installation Guide

## Prerequisites

### Required
- **Python 3.11+**: [Download](https://www.python.org/downloads/)
- **Node.js 18+**: [Download](https://nodejs.org/)
- **Git**: [Download](https://git-scm.com/)

### Optional (for full features)
- **Docker**: [Download](https://www.docker.com/)
- **PostgreSQL 15+**: [Download](https://www.postgresql.org/)
- **Redis**: [Download](https://redis.io/)
- **IPFS**: [Download](https://ipfs.io/)

---

## Quick Start (Automated)

### macOS / Linux

```bash
# Clone repository
git clone https://github.com/orbis-ethica/orbis-ethica.git
cd orbis-ethica

# Run setup script
./scripts/setup.sh
```

### Windows

```cmd
REM Clone repository
git clone https://github.com/orbis-ethica/orbis-ethica.git
cd orbis-ethica

REM Run setup script
scripts\setup.bat
```

---

## Manual Installation

### 1. Backend Setup (Python)

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Frontend Setup (React + TypeScript)

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

### 3. Blockchain Setup (Hardhat + Solidity)

```bash
cd blockchain

# Install dependencies
npm install

# Compile contracts
npx hardhat compile
```

---

## Configuration

### Backend Configuration (`backend/.env`)

```bash
# Required
OPENAI_API_KEY=sk-...          # Get from https://platform.openai.com/
ANTHROPIC_API_KEY=sk-ant-...   # Get from https://console.anthropic.com/

# Optional (for full features)
DATABASE_URL=postgresql://localhost:5432/orbis_ethica
REDIS_URL=redis://localhost:6379
IPFS_API_URL=http://localhost:5001
WEB3_PROVIDER_URL=http://localhost:8545
```

### Frontend Configuration (`frontend/.env.local`)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## Verify Installation

### Test Backend

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run tests
pytest tests/

# Start CLI
python -m cli.main --help
```

### Test Frontend

```bash
cd frontend

# Start development server
npm run dev

# Open http://localhost:3000
```

### Test Blockchain

```bash
cd blockchain

# Run local node
npx hardhat node

# Deploy contracts (in another terminal)
npx hardhat run scripts/deploy.js --network localhost
```

---

## Docker Setup (Alternative)

```bash
# Build and run all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.11+

# If multiple Python versions installed
python3.11 -m venv venv
```

### Permission Errors (macOS/Linux)

```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Module Not Found Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Backend (default: 8000)
lsof -ti:8000 | xargs kill -9

# Frontend (default: 3000)
lsof -ti:3000 | xargs kill -9
```

---

## Development Tools

### Code Formatting

```bash
cd backend

# Format code
black .
isort .

# Lint code
flake8 .
mypy .
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 10 GB

### Recommended (for Phase II+)
- **CPU**: 4+ cores
- **RAM**: 16 GB
- **Storage**: 50 GB SSD
- **Network**: Stable internet connection
