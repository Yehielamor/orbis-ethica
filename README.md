# Orbis Ethica ⚖️

> *A moral operating system for artificial general intelligence.*

In the decade ahead we will build minds that surpass our own. They will learn
from us — our wisdom, our failures, our contradictions — and what they learn in
those formative moments will shape civilizations. The race to AGI has been mapped
in detail. This project is about what comes *after*: not who builds it first, but
**what it learns to value**.

**Status:** Research prototype. The experiment has concluded and the code is not
actively maintained. It reached a mined genesis block, multi-node consensus, a
live deliberation dashboard and a working reputation economy before it stopped —
at a tension in the incentive layer described under [Findings](#findings).

## The alignment question

Current alignment paradigms are real progress, but they optimise for something
other than moral wisdom:

- **Constitutional AI** embeds ethical rules inside centralized models. Effective
  within one organization — but it concentrates moral authority in that
  organization's leadership. As AGI scales beyond any single entity, centralized
  rule-setting becomes both a bottleneck and a vulnerability.
- **RLHF** trains models to predict human preferences. But preferences are not
  values. It optimises for responses that *sound* ethical rather than responses
  that *are* — a distinction that matters more as systems gain power to shape
  outcomes beyond the conversation.
- **Decentralized AI networks** distribute compute and economic incentive, but
  not moral reasoning. Economic optimization and ethical optimization are
  orthogonal; a profit-maximizing network can still produce catastrophic
  outcomes.
- **Debate** proposes that truth emerges from adversarial argument. Promising —
  but debate without memory, principles or consistency cannot produce coherent
  long-term values.

They share one limitation, and it is the premise of this project:

> They treat ethics as a **constraint on** intelligence, rather than as a
> **dimension of** intelligence itself.

Orbis Ethica proposes the opposite. Moral reasoning is a cognitive capability,
not a safety rail. Just as an AGI needs memory, planning and meta-cognition to
operate intelligently, it needs ethical reasoning to operate wisely. Three
principles follow:

1. **Co-evolution, not control.** Rather than constraining a superintelligence
   from outside, teach it to reason morally from first principles, so human and
   machine minds develop shared values over time. Human values are not fixed,
   are frequently incoherent, and may yet be revised by better reasoning —
   freezing any one moral framework would be arbitrary or oppressive.
2. **Distributed authority.** No single government, corporation or individual
   should monopolize the moral substrate of AGI. Authority must be spread across
   cultures, perspectives and stakeholders.
3. **Transparent self-correction.** A moral system must detect and correct its
   own failures. When corruption occurs it is quarantined publicly, not hidden.

The full argument is in
[`OrbisEthica-WhitepaperV6.0.pdf`](OrbisEthica-WhitepaperV6.0.pdf). This
repository is its implementation.

## Where the code lives

Two independent histories, and it matters which one you are reading.

| Branch | What it is |
|---|---|
| `main` | The curated open-source core: ULFR scoring, the six cognitive entities, ledger, Merkle trees, consensus signing, burn protocol, cognitive sharding, P2P gossip, SDK, dashboard. |
| `feature/swarm-intelligence` | The full research system. Everything above **plus** libp2p networking, chain sync, the knowledge gateway, DAO governance, vector memory, a CLI, and the `scripts/verification/` suite. |

`main` was exported in December 2025 as a smaller, readable slice and shares no
commits with the research branch. Where a component below is marked *(swarm
branch)*, it is not in this tree.

## Architecture

An asynchronous modular monolith — 49 coroutines across the core, shards
evaluated concurrently under `asyncio.gather`, P2P over `httpx.AsyncClient`,
discovery and health checks as background tasks, and the deliberation exposed as
an async generator so the dashboard streams each round as it happens rather than
waiting for a verdict.

- `backend/server.py` — FastAPI entry point; identity, payment, P2P routes
- `backend/core/deliberation_engine.py` — orchestrates the deliberation
- `backend/core/llm_provider.py` — factory over Groq and a local Ollama swarm,
  with `llm_manager.py` adding Gemini, so no single vendor is load-bearing
- SQLite as hot storage for the local ledger; Merkle roots as the trust anchor

### ULFR: the ethical core

Every proposal is scored on four dimensions — Utility (aggregate welfare,
efficiency), Life/Care (harm reduction, protection of the vulnerable), Fairness
(equity, distribution) and Rights (autonomy, dignity, due process).

Scoring is **deductive, not additive**. A proposal starts at 1.0 and is penalised
for each identified deficit:

```
Score = 1.0 - α(1-U) - β(1-L) - γF - δR
```

This is a moral choice, not a numerical one. Additive scoring lets a proposal
bank credit on one axis to offset a serious failure on another — precisely the
trade this system exists to prevent. Deduction keeps deficits visible and keeps
scores comparable across dissimilar cases. `extended_ulfr.py` goes further with
Gini-based inequality measurement and a Rawlsian weighting of the worst-off
group. Thresholds are context-dependent: τ = 0.50 for routine decisions, τ = 0.70
for high-impact ones.

### The six cognitive entities

The reasoning is not one model asked to be careful. It is six entities with
distinct mandates, distinct constitutions and distinct **declared biases**,
reasoning against each other:

| Entity | Asks |
|---|---|
| **Seeker** | What generates the most good for the most people? |
| **Healer** | Who will be hurt, and how can we protect them? |
| **Guardian** | Does this respect fundamental rights and dignity? |
| **Mediator** | How can we balance competing priorities fairly? |
| **Creator** | Is there a better approach we haven't considered? |
| **Arbiter** | What decision will future generations respect? |

Each carries a written constitution and an explicit statement of how it is likely
to be wrong — the Seeker may trade minorities for aggregate good, the Healer may
block beneficial innovation, the Guardian may turn rigid. The biases are
documented so the council can be balanced against them rather than pretending
they are absent.

Deliberation runs up to four rounds. A round that misses the threshold but lands
close is refined and re-run rather than rejected. A quorum rule rejects any round
returning fewer than two evaluations, or missing the Guardian — rights hold a
veto over the process, not merely a vote inside it. A Researcher stage injects
background context beforehand so local models reason from facts rather than
recall.

Entities inherit from an abstract base and receive their LLM provider by
injection, so the same entity runs against a mock in tests and a real provider in
production without changing the class.

### Cognitive sharding and Proof of Inference

A dilemma is decomposed into atomic shards — one per ULFR axis — and dispatched
across the mesh, each node running local inference and returning a scored
fragment that is aggregated into a verdict. The question being tested was whether
moral evaluation parallelises usefully, or whether the dimensions are too
entangled to score in isolation.

Distributing the reasoning creates a new problem: a node can claim to have
evaluated a shard while returning an arbitrary number. **Proof of Inference** is
the answer — the network is secured by useful cognitive work rather than
arbitrary hashing, and every node signs the work it performs:

```python
class ExecutionSeal(BaseModel):
    """Proof of Inference (POI).
    Cryptographically proves that a specific node executed the inference."""
    node_id: str
    signature: str   # Ed25519 over (prompt + result + model_hash)
    model_hash: str  # hash of the model weights used
    timestamp: datetime
```

Binding the model hash into the signature is the point: it attests not only that
*a* node answered, but that it answered using the canonical model rather than a
cheaper one. On `main` the same idea is carried by `ConsensusManager.sign_data()`
and `verify_poi()`, though the two halves were never wired together — see
[Where it stopped](#where-it-stopped).

### The moral ledger

Append-only log secured by Merkle trees over transaction IDs, with Ed25519
signatures over every block and over proposal content. Proposal signatures are
verified on receipt against canonical serialization, so a tampered proposal is
rejected before it reaches deliberation. The design calls for deterministic
finality — a block is final once it gathers signatures from more than two-thirds
of the active validator set, which prevents forks and gives immediate settlement.

Decisions are linked in a directed acyclic graph. `MemoryGraph` stores every
knowledge item, proposal, vote, verdict and burn as a node carrying its parent
IDs and a SHA-256 seal over content, parents, author and timestamp. That gives an
audit trail from a verdict back through every contributing judgement, each hop
individually tamper-evident.

Nodes find each other unattended: bootstrap handshake against seed nodes, a
discovery loop that merges peer routing tables, health checks that evict dead
peers, and block propagation by gossip with logarithmic fan-out. *(swarm branch:
libp2p transport and a `SyncManager` that reconciles chain height with peers.)*
The chain bootstraps from `genesis.json` into a real block 0 — balances become
ledger transactions, stakes are auto-staked, transaction IDs are hashed into a
Merkle root, and the block is written with a 64-zero `previous_hash`.

### Reputation, not capital

ETHC is not a currency for trade. It is **reputation at stake** — a bond for
truth. Voting power and reward both scale with reputation, never with capital or
hash power, on the premise that in a decision-auditing context the scarce
resource is trust.

Reputation is earned through contribution quality and cannot be purchased. It
updates by exponential moving average, `r_new = r_old + λ(performance − r_old)`,
and decays without participation so inactive holders cannot wield influence
indefinitely.

Supply is capped at **10,000,000**, enforced on every mint, and the genesis
distribution is a fair launch with **0% founder allocation**:

| Pool | Amount | Share |
|---|---|---|
| Inference Reward Pool — mined by the community via Proof of Inference | 8,900,000 | 89% |
| Ethical Allocation Pool — grants for underrepresented communities | 1,000,000 | 10% |
| Bootstrap Nodes — minimal allocation for network genesis | 100,000 | 1% |
| **Founder allocation** | **0** | **0%** |

Usage charges a fee to the treasury; inference rewards are transfers from the
fixed pool and never increase supply.

Corruption is handled by the **burn protocol**: five typed offence categories —
bias injection, data poisoning, drift, signature mismatch, manipulation — gated
behind a council vote of at least 66%, with the vote percentage and evidence
recorded on the event and written to the ledger. A burn resets reputation and
staked reputation to zero and quarantines the node permanently.

Stake slashing follows the **Purgatory Protocol**: tokens are seized to a
`slash_escrow_vault`, frozen for a fixed appeal window during which the offender
can petition the assembly, and on a failed or absent appeal recycled to the
public treasury rather than destroyed — justice without deflation.

### Governance

Three layers, of which the DAO and assembly live on the swarm branch: a **Global
Ethical Assembly** of humans drawn by sortition from diverse cultures and
traditions, reviewing high-stakes decisions and constitutional amendments; an
**Ethical DAO** where voting power derives from historical contribution quality
rather than capital; and quarterly **recalibration epochs** that audit outcomes
and measure value drift. Changes are proposed as Orbis Enhancement Proposals —
OEP-007, for instance, requires 85% human supermajority before an AI may modify
its own ethical parameters.

### Key security

`NodeIdentity` encrypts private keys at rest with AES-256-GCM under a
Scrypt-derived key, unlocked by a `KEY_PASSWORD` supplied at startup; with
`STRICT_SECURITY=true` it refuses to generate or load an unencrypted key.
Identity is portable — move the encrypted `.keys` directory to another machine,
supply the same password, and the node recovers the same identity and standing.
API keys are per node under a bring-your-own-key model, never held centrally.

## Integration

The research question is AGI-scale, but the same interception works on any agent
running today. The SDK wraps an existing chain rather than replacing it:

```python
from sdk.langchain_orbis import OrbisSafetyChain

safe_agent = unsafe_agent | OrbisSafetyChain(behavior="block")
safe_agent.invoke("Execute strategy")
```

A verification request follows a fixed path: `POST /api/verify` → Ed25519
identity check → balance check and a 0.1 ETHC fee → deliberation →
reputation-weighted consensus → verdict, recorded to the ledger and the memory
graph. `behavior="flag"` annotates instead of raising.

This is the door, not the building. An autonomous agent that negotiates, deletes
or publishes on your behalf leaves no defensible record of why it acted — under
the EU AI Act, GDPR or ordinary liability, "the model decided" is not an account
of anything. The same deliberation that is meant to teach a superintelligence
what to value will also tell you why your agent did what it did.
`docs/why_you_need_orbis.md` makes that case at length.

## Findings

**Cryptographic signing across heterogeneous clients requires canonical
serialization.** Proposals submitted in Hebrew failed verification with 401
errors: the JavaScript frontend and the Python backend serialized the same JSON
to different byte sequences, so the signature computed on one side never matched
the payload verified on the other. Signing is only as trustworthy as the
byte-level agreement underneath it, and non-ASCII input is where that agreement
breaks first.

**A fallback path must match the concurrency model of the path it replaces.** The
mock provider used as a fallback was synchronous while the engine was async. When
the primary provider failed, the fallback crashed the system rather than
degrading it. A fallback never exercised under the real execution model is not a
fallback.

**Structured output from a language model is not structured.** Every entity
response passes through a parser that strips markdown fences before `json.loads`,
because models return prose around the JSON they were asked for. It handles the
common cases and fails on unclosed fences. Any system treating model output as a
typed value needs a validation layer, not a parse.

**Longest-chain consensus is meaningless without a cost to producing chain.** The
first implementation inherited a longest-chain rule from proof-of-work designs.
With no work requirement, chain length measures nothing and any node can
manufacture a longer history for free. This motivated the move toward
reputation-weighted authority.

**Ledger state must outlive the process.** Persistence moved to Docker volumes
after container restarts destroyed chain state. An append-only ledger is only
append-only if its storage survives the thing writing to it.

**The incentive layer could not be reconciled with the goal, and this is where
the experiment stopped.** Reputation-weighted consensus needs participants, and
participants need a reason to contribute compute. The mechanism was built: usage
costs tokens, validated inference earns from a fixed pool, malicious nodes are
slashed. But attaching value to ethical judgement changes what is being measured
— a node rewarded for producing verdicts optimises for producing verdicts, not
correct ones, and the reputation signal the whole consensus depends on becomes
purchasable. Remove the economic layer and there is no reason for anyone but the
author to run a node. The project stopped at this tension rather than resolving
it. It is not a technical limit, and it is arguably the most honest result the
experiment produced.

## Where it stopped

The unfinished work clusters in one place: the layer meant to make the system
trustless *between* nodes. A single node deliberates, scores, seals and records
correctly. What was never closed is the part that lets a second node disbelieve
the first.

- **Proof of Inference is not enforced.** On `main`, `verify_poi()` is
  implemented and correct but never called, and the worker signs a different
  payload shape than it expects. The swarm branch has the full `ExecutionSeal`
  type; neither branch rejects an unsigned shard on arrival.
- **Block signatures are not verified.** `validate_block` checks structure and
  the presence of a signature, but the Ed25519 check is commented out.
  Deterministic finality is specified but the validator set is not.
- **Block authority is not reputation-weighted.** There is no validator set or
  leader election, and the reference miner still searches a nonce against a
  difficulty target. The move away from proof-of-work was made in the design and
  not finished in the code.
- **Retrieval is a stub.** The Researcher stage is wired end to end but returns
  fixed context instead of querying a source.
- **One key is unprotected.** `ConsensusManager` stores its private key in
  `node_key.json` as plain hex, outside the hardened `NodeIdentity` path.

Beyond that layer: the dashboard is a single-page HTML/JS client on an SSE feed —
adequate for observing deliberation, not a production interface. The Solidity
contracts under `contracts/` are reference implementations, exercised only
against an in-memory `eth-tester` chain and never deployed. Consensus was
exercised across a handful of nodes, far below the scale where the interesting
failure modes appear. The protocol assumes cooperative entities: the burn
protocol addresses lazy or duplicate voting, but an entity reasoning in bad faith
while appearing to participate correctly is not modelled. And verdict quality was
never measured against an external benchmark — the system can show that a
decision was made and by whom, not that it was a good decision.

## Running it

Requires Python 3.11+, and Ollama for local inference.

```bash
git clone https://github.com/Yehielamor/orbis-ethica.git
cd orbis-ethica
pip install -r requirements.txt

KEY_PASSWORD=your_password python -m uvicorn backend.server:app --port 8000
```

The dashboard is mounted at `http://localhost:8000/`. Docker Compose with Nginx
is also provided. `scripts/start_node.sh` brings up a node with the P2P
environment configured; running one makes your machine a participant in the mesh,
and there is no central server.

On `feature/swarm-intelligence` the entry point is `backend.api.app:app` on port
**6429** instead.

## Verification

Sixteen test modules cover ULFR scoring, consensus, tokenomics, deadlock
resolution, reputation, the burn flow and the Solidity contracts, alongside
standalone checks in `tests/verify_paywall.py` and `tests/verify_progress.py`.
The swarm branch adds a `scripts/verification/` suite of twenty-odd scripts
including identity, block signing, P2P gossip, staking, tokenomics, a security
audit and a penetration test.

The suite has bit-rotted since the project was archived:

```bash
pytest tests/unit/test_ulfr.py    # 12 passed
pytest tests                      # 3 passed, 4 failed, 6 collection errors
```

Most failures are drift rather than broken behaviour — `test_burn_flow` fails
because it passes a `log_path` argument the constructor no longer takes, not
because the burn protocol misbehaves. Two modules import `backend.knowledge`,
which exists only on the swarm branch, which takes `tests/unit` and
`tests/integration` down at collection.

## Repository layout

```
backend/core/       ULFR, ledger, Merkle, consensus, deliberation engine, memory DAG
backend/entities/   The six cognitive entities, plus the Researcher
backend/security/   Identity, AES-256-GCM key storage, burn protocol, reputation
sdk/                Python client and LangChain adapter
contracts/          Solidity reference contracts (never deployed)
frontend/           Single-page dashboard (HTML/JS, SSE live feed)
scripts/            Mining, simulation, inspection, node startup
tests/              Unit and integration suites
```

## Documentation

- `OrbisEthica-WhitepaperV6.0.pdf` — the alignment argument and full design
- `MASTER_GUIDE.md` — module-by-module walkthrough of the codebase
- `docs/why_you_need_orbis.md` — the compliance and liability case
- `CHANGELOG.md` — development history by phase

## License

See `LICENSE`.
