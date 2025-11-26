# Orbis Ethica ⚖️
> *A Moral Operating System for Artificial General Intelligence*

**Current Status:** Phase XVIII Complete (Genesis Launch 🚀)
**Version:** 0.5.0 (Pre-Alpha)

Orbis Ethica is a decentralized framework designed to align AGI with human values through a "Moral Blockchain." It treats ethical reasoning not as a constraint, but as a cognitive dimension, using a consensus-based ledger to record, deliberate, and audit every AI decision.

## 🚀 Latest Updates (Genesis Edition)
- **Genesis Block (#0):** Successfully mined with the message *"Teaching silicon to care."*
- **Moral Ledger:** Fully migrated to **SQLite** with Merkle Tree integrity.
- **P2P Sync:** Implemented **Longest Chain Rule** for decentralized consensus.
- **Tokenomics:** **Ethica (ETHC)** token live (10M Supply) for reputation staking.
- **Whitepaper V5.0:** Updated architecture and economic model ([Read PDF](docs/whitepaper_v5.pdf)).
- **Distributed Memory Graph**: Permanent record of moral reasoning.
- **P2P Network**: Decentralized node communication with Gossip Protocol.
- **Proof of Authority**: Cryptographic identity and block signing.
- **Burn Protocol**: Transparent corruption detection and remediation.
- **Decentralized Governance**: Global Assembly, DAO, and OEPs.

---

## 🗺️ Roadmap

| Phase | Objective | Status |
|-------|-----------|--------|
| I-II | Core Engine & Entities | ✅ Complete |
| III | Memory Graph & RAG | ✅ Complete |
| IV-V | DAO Governance | ✅ Complete |
| VIII | P2P Networking (Libp2p) | ✅ Complete |
| XII | Economic Security (Burn) | ✅ Complete |
| XVII | Persistence (SQLite) | ✅ Complete |
| XVIII | Consensus & Sync | ✅ Complete 🚀 |
| XIX | Frontend Visualization | 🚧 Next |
| XX | Docker Deployment | 📅 Upcoming |

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

### Phase XI: True P2P (In Progress)
- [x] **Serverless Architecture**: Transition to Libp2p/WebRTC.
- [x] **Libp2p Service**: Background service for decentralized communication.
- [ ] **Discovery**: Kademlia DHT for peer finding.

### Phase XII: Economic Security (Completed)
- [x] **Vesting Contract**: 5-year lock for founder funds (Anti-Rugpull).
- [x] **Ethical Pool**: Dedicated allocation for diversity grants.
- [x] **Integrity Checks**: Protocol-level enforcement of economic rules.

### Phase XIII: The Bridge (Completed)
- [x] **Deliberation-Ledger Link**: Automatic rewards for approved proposals.
- [x] **Value Generation**: "Ethical Consensus" -> "Economic Value" pipeline.
- [x] **Wallet UI**: Real-time balance and staking interface.

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

### 🔐 Security (New in Phase XV)
Orbis Ethica now supports **Encryption at Rest** for node identities.
- **Key Encryption**: All private keys (`.sk`) are encrypted using AES-256-GCM.
- **Startup**: You MUST set the `KEY_PASSWORD` environment variable to start the server.

```bash
# Start with encrypted keys
KEY_PASSWORD=your_secure_password python -m uvicorn backend.api.app:app --reload
```

### 🧪 Simulation
Run the full system simulation to verify the end-to-end flow:

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

### 🌍 Deployment & P2P Architecture

**"Why localhost:3000?"**
When you run Orbis Ethica on your computer (via Docker or Python), your machine becomes a **Node** in the network. `localhost:3000` is simply the address of the dashboard running *on your own machine*.

**"Does it connect to a central server?"**
**No.** Orbis Ethica is a pure P2P network. There is no central server at Google or Amazon.
*   **Your Computer = The Server.** When you run the software, you are hosting a piece of the network.
*   **Connectivity:** For your node to participate (validate blocks, vote), your computer must be on and connected to the internet.
*   **Going Offline:** If you turn off your computer, your node stops. The network continues without you. When you return, your node will sync the missing blocks from peers.

**For Permanent Hosting:**
To run a 24/7 node (recommended for Validators), deploy the Docker container to a VPS (Virtual Private Server) like DigitalOcean, AWS, or even a Raspberry Pi at home.
```bash
# Example: Running on a public server
export NODE_HOST="203.0.113.1" # Your Public IP
docker-compose up -d
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
