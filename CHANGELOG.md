# Changelog

All notable changes to the **Orbis Ethica** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5-beta] - 2025-12-01 (Phase X: Production Hardening)

### Added
- **Privacy Masking:** Implemented SHA-256 masking for Node IDs in the P2P network status to protect user privacy.
- **Real AI Integration:** Activated Gemini Pro on the production server by securely configuring the API key.
- **Local Node Sync:** Updated local environment configuration to sync seamlessly with the "Iron Keys" production chain.
- **Network UI:** Added "Viewer Count" placeholder (Backend support pending) and ensured encrypted display of active nodes.

### Changed
- **Genesis Allocation:** Corrected the Genesis Block to allocate exactly **100,000 ETHC** (Founder Allocation) to the user's wallet, aligning with the Whitepaper.
- **Database Persistence:** Switched to Docker Volumes (`/app/data`) for database storage to ensure "Iron Keys" persistence across restarts.
- **Mining Prompts:** Enhanced Swarm Miner system prompts to be "Rigorous, Analytical, and Tireless", simulating fine-tuning behavior.
- **LLM Provider:** Updated `MockLLM` to be asynchronous to prevent system crashes during fallback.
- **Authentication:** Updated signature verification to support Unicode (Hebrew) characters in proposals.

### Fixed
- **Localhost Connection:** Fixed `ERR_EMPTY_RESPONSE` by updating the frontend to point to the correct local backend port (8000).
- **P2P Connection:** Fixed local node connection issues by updating the Seed Node IP to the new production server (`77.42.30.95`).
- **401 Unauthorized:** Resolved authentication errors for Hebrew proposals by aligning JSON serialization between Frontend (JS) and Backend (Python).

### Security
- **Server Hardening:** Tightened permissions on the production `.env` file (chmod 600).
- **API Key Protection:** Confirmed API keys are isolated per node (BYOK model).

## [0.1.4-beta] - 2025-11-25 (Phase IX)

### Added
- **Node Identity**: Implemented `NodeIdentity` class using Ed25519 cryptography for secure key management.
- **Proof of Authority (PoA)**: Added block signing logic to `LocalBlockchain`.
- **Secure P2P Messaging**: Integrated digital signatures into the `NodeManager` gossip protocol.
- **Verification Scripts**: Added `verify_identity.py` and `verify_block_signing.py` to `scripts/verification/`.
- **Whitepaper V4.1**: Restored full V2.1 content and updated with technical implementation details.

### Changed
- **Project Structure**: Reorganized verification scripts into `scripts/verification/` and tests into `tests/`.
- **Documentation**: Updated `README.md` and `whitepaper_v4_1.tex` with academic styling.
- **Initialization**: Refactored `app.py` startup sequence to ensure Identity is initialized before Ledger and P2P components.

## [0.1.3-alpha] - 2025-11-24 (Phase VIII)

### Added
- **P2P Network Layer**: Implemented `NodeManager` for peer discovery and management.
- **Gossip Protocol**: Added `broadcast` method to propagate transactions and blocks across the network.
- **Consensus Mechanism**: Implemented "Longest Chain Rule" in `LocalBlockchain` (`replace_chain`).
- **Network API**: Added WebSocket endpoint `/ws/p2p` for inter-node communication.

### Changed
- **Deliberation Engine**: Updated to broadcast blocks immediately upon mining.

## [0.1.2-alpha] - 2025-11-23 (Phase VI.5 & VII)

### Added
- **Knowledge Gateway**: Created the "Clear Layer" for ingesting and verifying external data sources.
- **Source Whitelisting**: Implemented a registry of trusted domains.
- **Docker Support**: Added `Dockerfile` and `docker-compose.yml` for containerized deployment.
- **Adversarial Simulation**: Added `scenarios/adversarial.py` to test system resilience against Sybil attacks and data poisoning.

## [0.1.1-alpha] - 2025-11-22 (Phase VI)

### Added
- **Real-Time Dashboard**: Implemented Server-Sent Events (SSE) for live deliberation updates.
- **Glassmorphism UI**: completely redesigned the frontend with a modern, premium aesthetic.
- **Navigation**: Added dedicated tabs for Deliberation, Governance, Ledger, Memory, and Knowledge.

## [0.1.0-alpha] - 2025-11-20 (Phase I-IV)

### Added
- **Core Engine**: Implemented the ULFR (Utility, Life, Fairness, Rights) ethical framework.
- **Cognitive Entities**: Launched 6 specialized agents (Seeker, Healer, Guardian, Mediator, Creator, Arbiter).
- **LLM Integration**: Added support for Google Gemini, Groq, and Mock providers.
- **Distributed Memory Graph**: Implemented a DAG-based audit trail for all decisions.
- **Immutable Ledger**: Created `LocalBlockchain` for securing the memory graph.
- **Burn Protocol**: Implemented the basic logic for quarantining corrupted nodes.
- **DAO Governance**: Added `ConfigManager` for dynamic system parameter updates via voting.
- **CLI Simulation**: Created `simulation.py` for terminal-based demos.

### Initial Release
- Project inception and initial architecture setup.
