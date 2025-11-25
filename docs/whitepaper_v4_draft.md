# Orbis Ethica Whitepaper V4.1 (Draft)

**A Moral Operating System for AGI**

**Status**: Phase VI Implementation Complete  
**Date**: November 2025

---

## 1. Introduction
Orbis Ethica is a decentralized moral infrastructure designed to operate as the ethical substrate for AGI systems. It ensures that AI decisions are not black boxes but are the result of a transparent, multi-agent deliberation process rooted in human values.

## 2. Core Philosophy: The ULFR Framework
Every decision is evaluated across four dimensions:
- **Utility (U)**: Maximizing well-being and efficiency.
- **Life/Care (L)**: Prioritizing harm reduction and protection of the vulnerable.
- **Fairness (F)**: Ensuring equity and justice (Penalty factor).
- **Rights (R)**: Protecting fundamental liberties (Risk factor).

## 3. Cognitive Architecture (The "Council")
The system is composed of specialized agents:
1.  **Seeker**: Facts & Utility.
2.  **Healer**: Care & Harm Reduction.
3.  **Guardian**: Fairness & Rights.
4.  **Mediator**: Synthesis & Consensus.
5.  **Creator**: Innovation.
6.  **Arbiter**: Final Verdict.

## 4. System Architecture V4.1

### 4.1 Persistence Layer (SQL)
Unlike previous versions that relied on ephemeral memory, V4.1 introduces a robust persistence layer using **SQLAlchemy**.
- **Entities**: Reputation scores and stats are persisted to a relational database.
- **Memory Graph**: The DAG is stored in `memory_nodes` table, ensuring audit trails survive system restarts.
- **Ledger Anchoring**: Each memory node is cryptographically linked to the `LocalBlockchain` (and in future, Ethereum/Solana).

### 4.2 Associative Memory (RAG)
To enable "Common Law" reasoning, entities are now equipped with **Vector Memory**.
- **Embedding**: Decisions and proposals are converted to vector embeddings using `sentence-transformers`.
- **Recall**: Before voting, entities query the `VectorStore` for semantically similar past decisions.
- **Consistency**: This ensures that the system does not contradict itself over time without justification.
- **Evidence Citation**: Entities now explicitly cite recalled memories ("precedents") in their reasoning, visible in the UI.

### 4.3 Automated Governance (DAO)
- **Constitutional Proposals**: The community can propose changes to system parameters (e.g., ULFR weights).
- **Auto-Execution**: Approved constitutional changes are automatically deployed via the `ConfigManager`.
- **Configuration API**: The `/api/governance/config` endpoint exposes the live system constitution.

### 4.4 Dashboard & Visualization (Phase VI)
A comprehensive React-based dashboard provides real-time visibility into the system's cognition:
- **Live Deliberation Feed**: Streams the step-by-step reasoning of the Council, including "thinking" states and mediator interventions.
- **Entity Cards**: Displays individual votes, ULFR scores, confidence levels, and *Memories Recalled*.
- **Ledger Explorer**: Allows auditing of the immutable blockchain ledger.
- **Memory Search**: Semantic search interface for the system's knowledge base.

## 5. Security & Trust
- **Burn Protocol**: Automated reputation slashing for malicious actors.
- **Immutable Ledger**: All major events are hashed and chained.
- **Cryptographic Signatures**: Every entity vote is signed (simulated in V4.1).

## 6. Recent Implementations (V4.1)

### 6.1 The Clear Layer (Knowledge Gateway)
To prevent "Garbage In, Garbage Out," V4.1 introduces the **Knowledge Gateway**:
- **Ingestion API**: A dedicated endpoint (`/api/knowledge/ingest`) for submitting raw data.
- **Verification Pipeline**:
    1.  **Cryptographic Check**: Verifies the signature of the data provider.
    2.  **Source Whitelisting**: Checks if the source ID is in the trusted registry (e.g., "WHO_Secure_Feed").
    3.  **Purity Scoring**: Assigns a confidence score to the data before it enters the Memory Graph.
- **UI Integration**: A dedicated "Knowledge" tab allows users to submit and verify data in real-time.

### 6.2 Advanced Simulation & Deployment
- **Dockerization**: Full containerization of Backend (FastAPI) and Frontend (Nginx) for reproducible deployments.
- **Adversarial Testing**: Automated scenarios (`scenarios/adversarial.py`) that simulate "Sybil Attacks" and "Data Poisoning" to verify the Burn Protocol's response.
- **Stress Testing**: High-load simulations (`scenarios/stress_test.py`) to ensure system stability under rapid deliberation rounds.
- **Rate Limiting**: API protection using `slowapi` to prevent abuse.

## 7. Future Roadmap: Phase VIII (P2P)
The next major evolution is the transition to a fully peer-to-peer architecture:
- **Node Discovery**: Implementing a distributed hash table (DHT) or similar mechanism for peer finding.
- **Gossip Protocol**: Efficient broadcasting of blocks and votes across the network.
- **Consensus Upgrade**: Moving from local consensus to a distributed consensus mechanism (e.g., Proof of Stake or Proof of Authority).

---

*This draft supersedes V4.0 for architectural implementation details.*
