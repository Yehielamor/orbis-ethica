# Orbis Ethica

**A Moral Operating System for AGI**

Version: 0.1.4-beta  
License: CC BY-SA 4.0  
Status: Phase IX (Identity & Security)

---

## Overview

Orbis Ethica is a decentralized moral infrastructure designed to operate as the ethical substrate for AGI systems. The framework integrates:

- **Clean Knowledge Layer**: Verified, cryptographically signed knowledge base.
- **Ethical Core**: ULFR framework (Utility, Life, Fairness, Rights).
- **Cognitive Entities**: 6 specialized agents for ethical deliberation.
- **Distributed Memory Graph**: Permanent record of moral reasoning.
- **P2P Network**: Decentralized node communication with Gossip Protocol.
- **Proof of Authority**: Cryptographic identity and block signing.
- **Burn Protocol**: Transparent corruption detection and remediation.
- **Decentralized Governance**: Global Assembly, DAO, and OEPs.

---

## Project Status

### Phase I-IV: Core Foundations (Completed)
- [x] Ethical Core & Decision Function
- [x] Cognitive Entities (Seeker, Healer, Guardian, etc.)
- [x] Distributed Memory Graph (DAG)
- [x] Immutable Ledger & Burn Protocol
- [x] DAO Governance & ConfigManager

### Phase VI: Dashboard Upgrade (Completed)
- [x] Glassmorphism UI
- [x] Real-time Deliberation Feed (SSE)
- [x] Governance & Ledger Views

### Phase VI.5: Clear Layer (Completed)
- [x] **Knowledge Gateway**: Ingestion & Verification API.
- [x] **Source Whitelisting**: Trusted registry for data providers.
- [x] **Purity Scoring**: Automated content validation.

### Phase VIII: P2P Decentralization (Completed)
- [x] **Node Manager**: Peer discovery and management.
- [x] **Gossip Protocol**: Broadcasting transactions and blocks.
- [x] **Consensus**: Longest Chain Rule implementation.

### Phase IX: Identity & Security (Completed)
- [x] **Node Identity**: Ed25519 Keypair generation.
- [x] **Proof of Authority**: Cryptographic block signing.
- [x] **Tamper Evidence**: Signature verification for all blocks.

---

## Architecture

```
orbis-ethica/
├── backend/           # Python core engine
│   ├── core/          # ULFR framework, Ledger, LLM providers
│   ├── entities/      # 6 cognitive entities
│   ├── memory/        # Distributed graph (DAG)
│   ├── security/      # Identity, Crypto, Burn Protocol
│   ├── p2p/           # Node Manager, Gossip Protocol
│   ├── knowledge/     # Knowledge Gateway (Clear Layer)
│   ├── governance/    # DAO, Assembly, OEPs
│   ├── api/           # REST/GraphQL/WebSocket API
│   └── main.py        # Entry point
├── frontend/          # React + TypeScript UI
├── scripts/           # Verification and utility scripts
├── tests/             # Unit, integration, e2e tests
└── docs/              # Documentation
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)
- **API Key (Optional)**: Google Gemini or Groq (System defaults to Mock LLM if no key provided)

### Installation

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed instructions.

```bash
# Clone repository
git clone https://github.com/orbis-ethica/orbis-ethica.git
cd orbis-ethica

# Backend setup
pip install -r requirements.txt

# Blockchain setup (Optional)
cd blockchain && npm install
```

### Run Phase I Simulation

To run the full end-to-end simulation with live agents:

```bash
# Optional: Set API Key for generative responses
export GEMINI_API_KEY="your_key_here" 

# Option 1: Run with Docker (Recommended for Production)
docker-compose up --build
# Backend: http://localhost:6429
# Frontend: http://localhost:3000

# Option 2: Run Locally (Development)
# Terminal 1: Start Backend
python -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 6429

# Terminal 2: Start Frontend
cd frontend/public && python3 -m http.server 4930
# Open http://localhost:4930 in your browser

# Option 3: Run CLI Simulation
python simulation.py
```

---

## Core Concepts

### ULFR Framework

Every decision is evaluated across four dimensions:

- **U (Utility)**: Aggregate welfare, efficiency, lives saved.
- **L (Life/Care)**: Harm reduction, protection of vulnerable.
- **F (Fairness)**: Equity, justice, distribution.
- **R (Rights)**: Autonomy, dignity, due process.

### Cognitive Entities

1. **Seeker**: Knowledge & utility maximization.
2. **Healer**: Harm reduction & care.
3. **Guardian**: Justice & rights.
4. **Mediator**: Balance & trade-offs.
5. **Creator**: Innovation & synthesis.
6. **Arbiter**: Final judgment & coherence.

### Security & Memory

- **Cryptographic Provenance**: All content signed with Ed25519.
- **Burn Protocol**: Public quarantine of corrupted data/agents.
- **Memory Graph**: A Directed Acyclic Graph (DAG) creating an immutable audit trail of every decision.

---

## Real-Time Deliberation Dashboard

Experience the ethical reasoning process live with our new real-time dashboard.

![Real-Time Dashboard](docs/images/dashboard_realtime.png)

**Features:**
- **Live Feed**: Watch the deliberation unfold step-by-step via Server-Sent Events (SSE).
- **Entity Visualization**: See each cognitive entity (Seeker, Healer, Guardian, etc.) cast their vote and explain their reasoning in real-time.
- **Mediator Timeline**: Track how the Mediator entity refines proposals across rounds to resolve ethical deadlocks.
- **Transparent Scoring**: View detailed ULFR (Utility, Life, Fairness, Rights) scores for every decision.



---

## Testing & Verification

We provide a suite of scripts to verify the integrity of the system components.

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Verification Scripts
python scripts/verification/verify_identity.py       # Test Key Generation & Signing
python scripts/verification/verify_block_signing.py  # Test Proof of Authority
python scripts/verification/verify_startup.py        # Test System Initialization
python scripts/verification/verify_p2p.py            # Test Network Layer
```

---

## Documentation

- [Architecture Overview](docs/architecture/README.md)
- [API Reference](docs/api/README.md)
- [Governance & OEPs](docs/guides/governance.md)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository.
2. Create feature branch (`git checkout -b feature/amazing-feature`).
3. Commit changes (`git commit -m 'Add amazing feature'`).
4. Push to branch (`git push origin feature/amazing-feature`).
5. Open Pull Request.

---

## License

This project is licensed under the **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.

See [LICENSE](LICENSE) for details.

---

## Contact

- **Email**: Amor5511@gmail.com
- **GitHub**: https://github.com/yehielamor/orbis-ethica
