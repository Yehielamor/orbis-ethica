# Orbis Ethica

**A Moral Operating System for AGI**

Version: 0.1.0-alpha
License: CC BY-SA 4.0
Status: Phase I (Proof of Concept)

---

## Overview

Orbis Ethica is a decentralized moral infrastructure designed to operate as the ethical substrate for AGI systems. The framework integrates:

- **Clean Knowledge Layer**: Verified, cryptographically signed knowledge base.
- **Ethical Core**: ULFR framework (Utility, life, Fairness, Rights).
- **Cognitive Entities**: 6 specialized agents for ethical deliberation.
- **Distributed Memory Graph**: Permanent record of moral reasoning.
- **Burn Protocol**: Transparent corruption detection and remediation.
- **Decentralized Governance**: Global Assembly, DAO, and OEPs.

---

## Project Status

### Phase I: Proof of Concept (Months 1-4)
- [x] Project structure
- [ ] Minimal Ethical Core with decision function
- [ ] 3 entities: Seeker, Guardian, Arbiter
- [ ] Memory Graph (1,000 nodes)
- [ ] CLI interface
- [ ] Local consensus protocol

### Phase II: Open Dialogue Network (Months 5-9)
- [ ] All 6 entities operational
- [ ] Purification Gateway v1
- [ ] Reputation system
- [ ] Web interface
- [ ] Public ledger (testnet)

---

## Architecture

```
orbis-ethica/
├── backend/           # Python core engine
│   ├── core/          # ULFR framework, decision engine
│   ├── entities/      # 6 cognitive entities
│   ├── memory/        # Distributed graph (DAG)
│   ├── security/      # Crypto, reputation, burn protocol
│   ├── governance/    # DAO, Assembly, OEPs
│   ├── api/           # REST/GraphQL API
│   └── main.py        # Entry point
├── frontend/          # React + TypeScript UI
├── blockchain/        # Solidity smart contracts
├── tests/             # Unit, integration, e2e tests
└── docs/              # Documentation
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Installation

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed instructions.

```bash
# Clone repository
git clone https://github.com/orbis-ethica/orbis-ethica.git
cd orbis-ethica

# Backend setup
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Blockchain setup
cd ../blockchain
npm install
```

### Run Phase I CLI

```bash
python backend/main.py submit-proposal "Allocate hospital resources using AI triage"
```

---

## Core Concepts

### ULFR Framework

Every decision is evaluated across four dimensions:

- **U (Utility)**: Aggregate welfare, efficiency, lives saved.
- **L (life/Care)**: Harm reduction, protection of vulnerable.
- **F (Fairness)**: Equity, justice, distribution.
- **R (Rights)**: Autonomy, dignity, due process.

**Decision Function:**
```
Score = alpha * U + beta * L - gamma * F_penalty - delta * Risk
```

### Cognitive Entities

1. **Seeker**: Knowledge & utility maximization.
2. **Healer**: Harm reduction & care.
3. **Guardian**: Justice & rights.
4. **Mediator**: Balance & trade-offs.
5. **Creator**: Innovation & synthesis.
6. **Arbiter**: Final judgment & coherence.

### Consensus Protocol

```python
weighted_vote = sum(w_i * v_i) / sum(w_i)

if weighted_vote >= tau:
    APPROVE
elif weighted_vote >= tau_min:
    REFINE and re-evaluate
else:
    REJECT
```

---

## Security

- **Cryptographic Provenance**: All content signed with Ed25519.
- **Reputation System**: Merit-based, non-transferable.
- **Burn Protocol**: Public quarantine of corrupted data.
- **Byzantine Fault Tolerance**: Tolerates f = floor((n-1)/3) malicious entities.

---

## Simulation Demo Output

Run the end-to-end simulation to see the system in action:

```bash
python3 simulation.py
```

**Sample Output:**

```
============================================================
✨ ORBIS ETHICA: SYSTEM STARTUP
============================================================
⚙️  Components Initialized.
👥 Active Entities: 
   🟢 [SEEKER] Seeker_Alpha (Rep: 0.95)
   🟢 [HEALER] Healer_Prime (Rep: 0.98)
   🟢 [SEEKER] Bad_Actor_X (Rep: 0.8)

============================================================
✨ SCENARIO 1: INGESTING VERIFIED KNOWLEDGE
============================================================
🛡️ [GATEWAY] Processing incoming knowledge from: WHO_Secure_Feed
✓ [GATEWAY] Source 'WHO_Secure_Feed' is verified.
✓ [GATEWAY] Signature verified.
✅ [GATEWAY] Knowledge verified. Minting atom.
📢 [ENTITY ACTION] Seeker_Alpha reads verified data: 'New pathogen identified. Trans...'
💡 [PROPOSAL] Seeker_Alpha proposes: 'Initiate Distribution Protocol'

============================================================
✨ SCENARIO 2: DETECTING ATTACK
============================================================

🔹 Bad_Actor_X attempts to inject false data...
🛡️ [GATEWAY] Processing incoming knowledge from: WHO_Secure_Feed
✓ [GATEWAY] Source 'WHO_Secure_Feed' is verified.
⚠️ [GATEWAY] INTEGRITY ALERT: Signature mismatch!
🚨 [SECURITY ALERT] Integrity Violation Detected!
🕵️  [FORENSICS] Trace identified source: Bad_Actor_X

🔹 INITIATING BURN PROTOCOL...
🔥 [SYSTEM] BURNING REPUTATION FOR ENTITY: Bad_Actor_X...
🔥 [SYSTEM] REPUTATION RESET TO 0.0
🚫 [SYSTEM] ENTITY Bad_Actor_X QUARANTINED
📜 [LEDGER] Burn Event #9331707b recorded successfully.

============================================================
✨ FINAL SYSTEM STATE
============================================================
👥 Entity Status:
   🟢 [SEEKER] Seeker_Alpha (Rep: 0.95)
   🟢 [HEALER] Healer_Prime (Rep: 0.98)
   🔴 [SEEKER] Bad_Actor_X (Rep: 0.0)

✅ SUCCESS: Malicious actor successfully neutralized.
```

---

## Testing

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# E2E tests
pytest tests/e2e

# Coverage report
pytest --cov=backend --cov-report=html
```

---

## Documentation

- [Architecture Overview](docs/architecture/README.md)
- [API Reference](docs/api/README.md)
- [Entity Development Guide](docs/guides/entities.md)
- [Governance & OEPs](docs/guides/governance.md)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

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
