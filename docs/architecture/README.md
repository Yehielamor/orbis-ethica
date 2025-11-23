# Architecture Overview

## System Architecture

Orbis Ethica is built as a modular, scalable system with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI / Web UI                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Deliberation Engine                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Consensus Protocol                           │  │
│  │  • Weighted voting                                   │  │
│  │  • Threshold checking                                │  │
│  │  • Quorum validation                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Cognitive Entities Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Seeker  │  │ Guardian │  │ Arbiter  │  (Phase I)      │
│  └──────────┘  └──────────┘  └──────────┘                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Healer  │  │ Mediator │  │ Creator  │  (Phase II)     │
│  └──────────┘  └──────────┘  └──────────┘                 │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Core Models                               │
│  • ULFR Framework                                           │
│  • Proposal / Decision                                      │
│  • Entity Configuration                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Memory    │  │  Reputation │  │   Crypto    │        │
│  │    Graph    │  │   System    │  │ Provenance  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    IPFS     │  │  Blockchain │  │  Database   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Core Models (`backend/core/models/`)

Foundation data structures:

- **`ulfr.py`** - ULFR Framework
  - `ULFRScore`: Four-dimensional ethical evaluation
  - `ULFRWeights`: Configurable weights (alpha, beta, gamma, delta)
  - Decision function: `Score = alpha*U + beta*L - gamma*F - delta*R`

- **`proposal.py`** - Proposal lifecycle
  - Categories: routine, high_impact, constitutional, emergency
  - Domains: healthcare, finance, technology, etc.
  - Status tracking through deliberation

- **`entity.py`** - Entity configuration
  - 6 entity types with distinct perspectives
  - Reputation tracking
  - Constitutional principles

- **`decision.py`** - Decision outcomes
  - Entity evaluations
  - Consensus calculation
  - Explainability reports

### 2. Cognitive Entities (`backend/entities/`)

Specialized agents for ethical deliberation:

#### Phase I (3 Entities)
- **Seeker** - Utility maximization, evidence-based reasoning
- **Guardian** - Rights protection, procedural justice
- **Arbiter** - Final judgment, civilizational wisdom

#### Phase II (6 Entities)
- **Healer** - Harm reduction, care for vulnerable
- **Mediator** - Balance, fair trade-offs
- **Creator** - Innovation, novel solutions

Each entity:
- Has a constitutional prompt defining its perspective
- Evaluates proposals along ULFR dimensions
- Provides vote, confidence, reasoning, concerns, recommendations
- Signs evaluations cryptographically

### 3. Consensus Protocol (`backend/core/protocols/`)

Implements the ethical consensus algorithm:

```python
# Weighted vote calculation
weighted_vote = sum(w_i * v_i) / sum(w_i)

# Decision logic
if weighted_vote >= tau:
    APPROVE
elif weighted_vote >= tau_min:
    REFINE  # Close to threshold
else:
    REJECT
```

**Thresholds:**
- Routine: 0.50
- High-impact: 0.70
- Constitutional: 0.85
- Emergency: 0.60

**Quorum:** 60% participation required

### 4. Deliberation Engine (`backend/core/protocols/`)

Orchestrates multi-round deliberation:

1. **Round 1**: Independent entity evaluation
2. **Consensus Check**: Calculate weighted vote
3. **Outcome**:
   - Approved: Done
   - Refined: Next round with improvements
   - Rejected: Done
4. **Max Rounds**: 4 (configurable)

### 5. CLI Interface (`backend/cli/`)

Command-line interface for Phase I:

```bash
# Submit proposal
python -m cli.main submit "Title" -d "Description"

# Run demo
python -m cli.main demo

# Test system
python -m cli.main test

# System info
python -m cli.main info
```

---

## Data Flow

### Proposal Submission -> Decision

```
1. User submits proposal
   |
2. Deliberation Engine initializes
   |
3. Entities evaluate independently
   |
   |--> Seeker: Utility analysis
   |--> Guardian: Rights check
   |--> Arbiter: Wisdom synthesis
   |
4. Consensus Protocol calculates vote
   |
5. Decision outcome determined
   |
6. If REFINED: Apply feedback, goto step 3
   |
7. Final decision recorded
   |
8. (Future) Store in Memory Graph
   |
9. (Future) Publish to blockchain
```

---

## Technology Stack

### Backend
- **Python 3.11+** - Core language
- **Pydantic** - Data validation
- **OpenAI API** - GPT-4 for entities
- **Anthropic API** - Claude for entities
- **Click** - CLI framework
- **Rich** - Terminal UI

### Future (Phase II+)
- **FastAPI** - REST API
- **React + TypeScript** - Web UI
- **PostgreSQL** - Database
- **Redis** - Caching
- **IPFS** - Distributed storage
- **Ethereum/Hardhat** - Blockchain
- **NetworkX** - Graph algorithms

---

## Security Model

### Current (Phase I)
- API key management via `.env`
- Input validation with Pydantic
- Entity signature tracking

### Future (Phase II+)
- Cryptographic signing (Ed25519)
- Content hashing (SHA-256/BLAKE3)
- IPFS content addressing
- Merkle trees for evaluations
- Reputation system with decay
- Burn Protocol for corruption

---

## Scalability Considerations

### Phase I (Current)
- **Entities**: 3
- **Throughput**: ~1 proposal/minute (LLM limited)
- **Storage**: In-memory
- **Users**: Single CLI user

### Phase II (Target)
- **Entities**: 6
- **Throughput**: ~10 proposals/minute
- **Storage**: PostgreSQL + IPFS
- **Users**: Multi-user web interface

### Phase III+ (Future)
- **Entities**: Scalable entity pools
- **Throughput**: 100+ proposals/minute
- **Storage**: Distributed graph database
- **Users**: 10,000+ participants

---

## Extension Points

The architecture is designed for extensibility:

1. **New Entities**: Implement `BaseEntity` interface
2. **Custom Weights**: Adjust ULFR parameters via OEPs
3. **New Domains**: Add to `ProposalDomain` enum
4. **Alternative LLMs**: Swap OpenAI/Anthropic for local models
5. **Storage Backends**: Replace in-memory with database
6. **Consensus Algorithms**: Modify `ConsensusProtocol`

---

## Testing Strategy

### Unit Tests
- Core models (ULFR, Proposal, Entity)
- Consensus calculations
- Weight normalization

### Integration Tests
- Entity evaluation pipeline
- Deliberation rounds
- CLI commands

### E2E Tests
- Full proposal -> decision flow
- Multi-round refinement
- Error handling

---

## Deployment

### Development
```bash
python -m cli.main demo
```

### Production (Future)
```bash
# API server
uvicorn backend.api.main:app

# Frontend
npm run build && npm start

# Blockchain node
npx hardhat node
```

---

## Performance Metrics

### Phase I Benchmarks
- Entity evaluation: ~10-30s per entity
- Consensus calculation: <1ms
- Full deliberation: ~1-2 minutes (3 entities, 1 round)

### Bottlenecks
- LLM API latency (main bottleneck)
- Sequential entity evaluation

### Optimizations (Future)
- Parallel entity evaluation
- Response caching
- Local model deployment
- Batch processing

---

## Next Steps

See [ROADMAP.md](../ROADMAP.md) for development timeline.

**Phase I** (Current):
- Core models
- 3 entities
- Consensus protocol
- CLI interface

**Phase II** (Next):
- 6 entities
- Web interface
- Reputation system
- IPFS integration

**Phase III**:
- Blockchain deployment
- Global Assembly
- Burn Protocol
- Meta-cognition layer
