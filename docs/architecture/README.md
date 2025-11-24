# Architecture Overview

Orbis Ethica is designed as a modular, decentralized system for ethical reasoning.

## High-Level Components

### 1. The Core (Backend)
Located in `backend/core/`.
- **Deliberation Engine**: The heart of the system. Orchestrates the debate between entities.
- **ULFR Framework**: `extended_ulfr.py` implements the mathematical scoring models (Utility, Life, Fairness, Rights).
- **LLM Provider**: Abstract interface for connecting to different LLM backends (Gemini, OpenAI, Mock).

### 2. Cognitive Entities
Located in `backend/entities/`.
- **Seeker**: Maximizes Utility (U).
- **Guardian**: Protects Rights (R).
- **Healer**: Prioritizes Life/Care (L).
- **Arbiter**: Weighs Fairness (F) and issues verdicts.
- **Mediator**: Resolves deadlocks and synthesizes compromises.
- **Creator**: (Planned) Generates novel solutions.

### 3. Memory Graph
Located in `backend/core/memory/`.
- A Directed Acyclic Graph (DAG) that stores the history of all deliberations.
- Nodes represent: Knowledge, Proposals, Rounds, Votes, Verdicts.
- Provides immutable audit trails.

### 4. Security & Governance
Located in `backend/security/` and `backend/governance/`.
- **Reputation Manager**: Handles staking and slashing of entity reputation.
- **Assembly Manager**: Manages sortition and Sybil resistance for the human oversight layer.

## Data Flow

1. **Input**: A Proposal is submitted (via CLI or API).
2. **Deliberation**:
   - Round 1: Entities evaluate the proposal independently.
   - Scoring: ULFR scores are aggregated.
   - Consensus Check: If score > threshold, Approve. If not, Refine.
3. **Refinement (if needed)**:
   - The Mediator analyzes feedback and generates a refined proposal.
   - Loop continues until Consensus or Max Rounds.
4. **Output**: A final Decision (Approved/Rejected) with a full audit trail.

## Tech Stack

- **Language**: Python 3.11+
- **LLM**: Google Gemini (via `google-generativeai`)
- **CLI**: `click` and `rich`
- **Testing**: `pytest`
