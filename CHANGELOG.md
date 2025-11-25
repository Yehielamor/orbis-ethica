# Changelog

All notable changes to the **Orbis Ethica** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
