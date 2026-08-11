# Orbis Ethica ⚖️

> *A moral operating system for autonomous machines.*

An attempt to build the thing that is missing when an AI agent acts on your
behalf: not a safety filter, but a **deliberation** — several independently
reasoning agents arguing a decision out, scoring it along four ethical axes, and
committing the argument itself to a tamper-evident ledger, so that months later
anyone can reconstruct what was decided, by whom, on what grounds, and prove the
record has not been touched since.

**Status:** Research prototype. The experiment has concluded and the code is not
actively maintained. It reached a mined genesis block, multi-node consensus, a
live deliberation dashboard and a working token economy before it stopped — at a
tension in the incentive layer described under [Findings](#findings).

## The problem

An autonomous agent that negotiates, deletes or publishes on your behalf leaves
no defensible record of why it acted. When the decision is later challenged, what
remains is an output and a log line, not evidence. Under the EU AI Act, GDPR or
ordinary liability, "the model decided" is not an account of anything.

Orbis Ethica asked whether the deliberation itself could be made the artifact.
The design borrows from distributed ledgers, but the ledger is not the
interesting part. The interesting parts are how you decompose a judgement into
something several machines can evaluate independently, and how a node proves it
actually did the reasoning it claims to have done.

Integration was meant to be non-invasive — wrapping an existing agent rather than
replacing it:

```python
from sdk.langchain_orbis import OrbisSafetyChain

safe_agent = unsafe_agent | OrbisSafetyChain(behavior="block")
safe_agent.invoke("Execute strategy")
```

## Where the code lives

This repository holds two independent histories, and it matters which one you are
reading.

| Branch | What it is |
|---|---|
| `main` | The curated open-source core: ULFR scoring, the six cognitive agents, ledger, Merkle trees, consensus signing, burn protocol, cognitive sharding, P2P gossip, SDK, dashboard. |
| `feature/swarm-intelligence` | The full research system. Everything above **plus** libp2p networking, chain sync, the knowledge gateway, DAO governance, vector memory, a CLI, and the `scripts/verification/` suite. |

`main` was exported in December 2025 as a smaller, readable slice of the project
and shares no commits with the research branch. Where a component below is marked
*(swarm branch)*, it is not in this tree — check out
`origin/feature/swarm-intelligence` to read it.

## Architecture

An asynchronous modular monolith — 49 coroutines across the core, shards
evaluated concurrently under `asyncio.gather`, P2P over `httpx.AsyncClient`,
discovery and health checks as background tasks, and the deliberation exposed as
an async generator so the dashboard streams each round as it happens rather than
waiting for a verdict.

- `backend/server.py` — FastAPI entry point; identity, payment, P2P routes
- `backend/core/deliberation_engine.py` — orchestrates the exchange between agents
- `backend/core/llm_provider.py` — factory over Groq and a local Ollama swarm,
  with `llm_manager.py` adding Gemini, so no single vendor is load-bearing
- SQLite as hot storage for the local ledger; Merkle roots as the trust anchor

A verification request follows a fixed path: `POST /api/verify` → Ed25519
identity check → balance check and a 0.1 ETHC fee → deliberation →
reputation-weighted consensus → verdict, recorded to the ledger and the memory
graph.

### The six cognitive agents

The reasoning is not one model asked to be careful. It is six agents with
distinct mandates, distinct system prompts and distinct declared biases, argued
against each other:

| Agent | Asks |
|---|---|
| **Seeker** | What generates the most good for the most people? |
| **Healer** | Who will be hurt, and how can we protect them? |
| **Guardian** | Does this respect fundamental rights and dignity? |
| **Mediator** | How can we balance competing priorities fairly? |
| **Creator** | Is there a better approach we haven't considered? |
| **Arbiter** | What decision will future generations respect? |

Each carries its own written constitution and an explicit statement of how it is
likely to be wrong — the Seeker may trade minorities for aggregate good, the
Healer may block beneficial innovation, the Guardian may turn rigid. The biases
are documented so the council can be balanced against them rather than pretending
they are absent.

All six are instantiated and vote. Deliberation runs up to four rounds; a round
that misses the threshold but lands close is refined and re-run rather than
rejected. A quorum rule rejects any round returning fewer than two evaluations,
or missing the Guardian — rights hold a veto over the process, not merely a vote
inside it. A separate Researcher stage injects background context before
deliberation begins, so local models reason from facts rather than from recall.

Agents inherit from an abstract base and receive their LLM provider by injection,
so the same agent runs against a mock in tests and a real provider in production
without changing the class.

### ULFR: scoring a judgement

Every proposal is scored on four axes — Utility (aggregate welfare, efficiency),
Life/Care (harm reduction, protection of the vulnerable), Fairness (equity,
distribution) and Rights (autonomy, dignity, due process).

Scoring is **deductive, not additive**. A proposal starts at 1.0 and is penalised
for each identified deficit:

```
Score = 1.0 - α(1-U) - β(1-L) - γF - δR
```

This was deliberate. Additive scoring lets a proposal bank credit on one axis to
offset a serious failure on another — exactly the trade a system like this exists
to prevent. Deduction keeps deficits visible and keeps scores comparable across
dissimilar cases. `extended_ulfr.py` takes it further with Gini-based inequality
measurement and a Rawlsian weighting of the worst-off group.

### Cognitive sharding and Proof of Inference

A dilemma is decomposed into atomic shards — one per ULFR axis — and dispatched
across the mesh, each node running local inference and returning a scored
fragment that is aggregated into a single verdict. The question being tested was
whether ethical evaluation parallelises usefully, or whether the dimensions are
too entangled to score in isolation.

Distributing the reasoning creates a new problem: a node can claim to have
evaluated a shard while returning an arbitrary number. **Proof of Inference** is
the answer — every node cryptographically signs the cognitive work it performs.
On the swarm branch this is an `ExecutionSeal` attached to each shard:

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
and `verify_poi()`, though the two halves were never wired to each other — see
[Where it stopped](#where-it-stopped).

### Consensus, reputation and the token economy

Nodes find each other and stay in touch unattended: bootstrap handshake against
seed nodes, a discovery loop that merges peer routing tables, health checks that
evict dead peers, and block propagation by gossip with logarithmic fan-out, so a
block reaches the mesh in roughly log(N) hops with no node holding a full view.
*(swarm branch: libp2p transport and a `SyncManager` that reconciles chain height
with peers.)*

The chain bootstraps from `genesis.json` into a real block 0 — balances become
ledger transactions, stakes are auto-staked, transaction IDs are hashed into a
Merkle root, and the block is written with a 64-zero `previous_hash` and every
transaction linked to it.

Reputation, not stake or hash power, is the weighting currency: agent evaluations
aggregate into the final score in proportion to reputation, and block rewards
scale by the producer's reputation on top of a halving schedule. The premise is
that in a decision-auditing context the scarce resource is trust, not compute.

ETHC is capped at **10,000,000**, enforced on every mint. Usage charges a fee to
the treasury; rewards for validated inference are transfers from a fixed
`INFERENCE_REWARD_POOL` and never increase supply. `genesis.json` allocates
8,900,000 (89%) to that reward pool, 1,000,000 (10%) to an ethical allocation
pool, and 100,000 (1%) to a founder address — note that this contradicts the
"0% founder allocation" claim carried in earlier releases. The allocation is
small, but it is real.

Penalties run through a dedicated **burn protocol**: five typed offence
categories — bias injection, data poisoning, drift, signature mismatch,
manipulation — gated behind a council vote of at least 66%, with the vote
percentage and the evidence recorded on the event and written to the ledger. A
burn resets reputation and staked reputation to zero and quarantines the node
permanently. Stake slashing is separate: tokens move to a `slash_escrow_vault`
for an appeal window and are recycled to the treasury on expiry rather than
destroyed.

### Ledger and provenance

Append-only log secured by Merkle trees over transaction IDs, with Ed25519
signatures over every block and over proposal content. Proposal signatures are
verified on receipt against canonical serialization, so a tampered proposal is
rejected before it reaches deliberation.

Decisions are linked in a directed acyclic graph. `MemoryGraph` stores every
knowledge item, proposal, vote, verdict and burn as a node carrying its parent
IDs and a SHA-256 seal over content, parents, author and timestamp. That gives an
audit trail from a verdict back through every contributing judgement, each hop
individually tamper-evident.

### Key security

`NodeIdentity` encrypts private keys at rest with AES-256-GCM under a
Scrypt-derived key, unlocked by a `KEY_PASSWORD` supplied at startup; with
`STRICT_SECURITY=true` it refuses to generate or load an unencrypted key.
Identity is portable — move the encrypted `.keys` directory to another machine,
supply the same password, and the node recovers the same identity and standing.
API keys are per node under a bring-your-own-key model, read from the
environment, never held centrally.

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

**Structured output from a language model is not structured.** Every agent
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
it. It is not a technical limit.

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
exercised across a handful of nodes, well below the scale where the interesting
failure modes appear. The protocol assumes cooperative agents: the burn protocol
addresses lazy or duplicate voting, but an agent reasoning in bad faith while
appearing to participate correctly is not modelled. And verdict quality was never
measured against an external benchmark — the system can show that a decision was
made and by whom, not that it was a good decision.

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
backend/entities/   The six cognitive agents, plus the Researcher
backend/security/   Identity, AES-256-GCM key storage, burn protocol, reputation
sdk/                Python client and LangChain adapter
contracts/          Solidity reference contracts (never deployed)
frontend/           Single-page dashboard (HTML/JS, SSE live feed)
scripts/            Mining, simulation, inspection, node startup
tests/              Unit and integration suites
```

## Documentation

- `MASTER_GUIDE.md` — module-by-module walkthrough of the codebase
- `OrbisEthica-WhitepaperV6.0.pdf` — the full design
- `docs/why_you_need_orbis.md` — the compliance and liability case
- `CHANGELOG.md` — development history by phase

## License

See `LICENSE`.
