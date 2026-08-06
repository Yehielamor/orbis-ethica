# Orbis Ethica

A research prototype exploring whether autonomous agent decisions can be
intercepted, adjudicated and recorded in a way that is independently auditable
and tamper-evident — without a trusted central authority.

**Status:** Research prototype. The experiment has concluded. The code is not
actively maintained and is not currently deployed.

## The problem

An autonomous agent that negotiates, deletes or publishes on your behalf leaves
no defensible record of why it acted. When the decision is later challenged, what
remains is an output and a log line, not evidence. Under the EU AI Act, GDPR or
ordinary liability, "the model decided" is not an account of anything.

Orbis Ethica asked whether the deliberation itself could be made the artifact:
intercept an action before it executes, have several independently-scored
entities evaluate it, and commit the result to a ledger such that any party can
later verify what was decided, by whom, on what grounds, and that the record has
not been altered since.

The design borrows from distributed ledgers, but the ledger is not the
interesting part. The interesting parts are how you decompose a judgement into
something several machines can evaluate independently, and how a node proves it
actually did the reasoning it claims to have done.

Integration was intended to be non-invasive — wrapping an existing chain rather
than replacing it:

```python
from sdk.langchain_orbis import OrbisSafetyChain

safe_agent = unsafe_agent | OrbisSafetyChain(behavior="block")
safe_agent.invoke("Execute strategy")
```

## Architecture

An asynchronous modular monolith.

- `backend/server.py` — FastAPI entry point; authentication and payment
- `backend/core/deliberation_engine.py` — orchestrates the exchange between entities
- `backend/core/llm_provider.py` — factory-pattern abstraction over Groq and a
  local Ollama swarm, with a mock provider for tests;
  `backend/core/llm_manager.py` adds Gemini and falls back between providers, so
  no single vendor is load-bearing
- SQLite as hot storage for the local ledger; Merkle roots as the trust anchor

Roughly 9,300 lines of tracked Python across 40 backend modules and 16 test
modules, plus a 1,100-line single-file dashboard and 167 lines of Solidity.

Asynchronous throughout: 49 coroutines across the core, shards evaluated
concurrently under `asyncio.gather`, P2P over `httpx.AsyncClient`, discovery and
health checks as background tasks, and the deliberation itself exposed as an
async generator so the dashboard streams each round as it happens rather than
waiting for a verdict.

A verification request follows a fixed path: `POST /api/verify` → Ed25519
identity check → balance check and a 0.1 ETHC fee to the treasury → deliberation
→ reputation-weighted consensus → verdict. The signature covers
`timestamp:wallet_id`, proving wallet ownership and rejecting replays outside a
60-second window.

### ULFR: scoring a judgement

Every proposal is evaluated across four dimensions — Utility (aggregate welfare,
efficiency), Life/Care (harm reduction, protection of the vulnerable), Fairness
(equity, distribution) and Rights (autonomy, dignity, due process).

Scoring is deductive rather than additive: a proposal begins at 1.0 and is
penalised for each identified deficit —
`Score = 1.0 - α(1-U) - β(1-L) - γF - δR`, clamped at 0. Note the asymmetry in
how the axes enter: Utility and Life/Care are scored as attainment and penalised
for what is missing, while Fairness and Rights are scored directly as penalties.
This was deliberate. Additive scoring lets
a proposal accumulate credit on one axis to offset a serious failure on another;
deduction keeps deficits visible and scores normalised across dissimilar cases.

### Cognitive entities

Six roles are defined, each with a distinct mandate and system prompt: **Seeker**
(knowledge and utility), **Healer** (harm reduction and care), **Guardian**
(justice and rights), **Mediator** (balance and trade-offs), **Creator**
(synthesis and alternatives) and **Arbiter** (final judgement and coherence).
All six are instantiated in the running server and all six vote. In the local
fallback path the Arbiter is held back from routine voting, so that it weighs in
on coherence rather than adding another ordinary ballot.

Deliberation runs up to four rounds. A round that misses the approval threshold
but lands close to it is marked for refinement and re-run rather than rejected
outright, and a quorum check rejects any round that returns fewer than two
evaluations or that is missing the Guardian — rights get a veto on the process,
not just a vote inside it.

Entities inherit from an abstract base class and receive their LLM provider by
injection, so the same entity runs against a mock in tests and a real provider in
production without changing the class.

Before deliberation begins, a separate Researcher module
(`backend/entities/researcher.py`) injects background context so local models
have facts to reason from. It is deliberately not one of the six: it holds no
place in the `EntityType` enum, does not inherit the entity base class and casts
no vote. Its retrieval is a stub — it returns a fixed block of legal, economic
and ethical context where a search backend was meant to go — so the RAG stage is
wired end to end but not yet retrieving anything.

### Cognitive sharding

Every proposal is decomposed into exactly four shards, one per ULFR axis, and
gossiped to peers over `POST /api/p2p/shard/process`. A worker maps the axis to
the matching entity — U to Seeker, L to Healer, F to Mediator, R to Guardian —
runs local inference and returns the evaluation; results are aggregated into a
single verdict. Local inference is an Ollama swarm reached over Tailscale,
hard-coded to `deepseek-r1:8b`, with a Groq (`llama3-70b-8192`) cloud fallback.
Each shard has a five-second deadline, after which the leader evaluates that axis
locally instead, so a mesh with no reachable peers degrades to single-node
deliberation rather than failing.

The motivation was to test whether ethical evaluation parallelises usefully, or
whether the dimensions are too entangled to score in isolation.

### Proof of Inference

Nodes sign the cognitive work they perform. Without it, a node can claim to have
evaluated a shard while returning an arbitrary score — Proof of Inference is what
would make distributed reasoning verifiable rather than merely distributed.

Both halves live in `ConsensusManager` (`backend/core/consensus.py`):
`sign_data()` produces an Ed25519 signature over canonical JSON, and
`verify_poi()` checks a proof over `shard_id`, `result_hash`, `miner_id`, `model`
and `timestamp`. There is no separate seal type — the signature travels on the
shard result itself.

This is the piece that was specified but not closed. `verify_poi()` is never
called on the receiving side, the worker signs the raw evaluation rather than the
payload shape `verify_poi()` expects, and with no consensus manager attached the
worker falls back to a placeholder string. The verification half exists and is
correct; nothing calls it yet. See [Where it stopped](#where-it-stopped).

### Consensus, reputation and penalties

Nodes find each other and stay in touch on their own: a bootstrap handshake
against seed nodes, a discovery loop that merges peer routing tables, periodic
health checks that evict dead peers, and block propagation by gossip with
logarithmic fan-out, so a block reaches the mesh in roughly log(N) hops without
any node holding a full view of it.

The chain bootstraps from `genesis.json` into a real block 0: initial balances
become ledger transactions, initial stakes are auto-staked into the staking
contract, the transaction IDs are hashed into a Merkle root, and the block is
written with a 64-zero `previous_hash` and every transaction linked to it.
`finalize_block` then marks a block final once it has collected a set of
signatures.

Reputation is the weighting currency in two places: entity evaluations are
aggregated into the final score in proportion to reputation, and block rewards
are scaled by the producer's reputation on top of a halving schedule (1.0 ETHC
initial, halving every 100,000 blocks). The premise — that in a decision-auditing
context the scarce resource is trust, not compute — is carried by the scoring and
reward layers. It does not yet extend to block authority itself; see
[Where it stopped](#where-it-stopped).

ETHC is capped at 10,000,000, enforced on every mint. Usage charges a fee to the
treasury; rewards for validated inference are transfers from a fixed
`INFERENCE_REWARD_POOL` and so do not increase supply. `genesis.json` allocates
8,900,000 (89%) to that reward pool, 1,000,000 (10%) to an
`ETHICAL_ALLOCATION_POOL`, and 100,000 (1%) to a single named address — a founder
pre-mine, small but real.

Penalties run through a dedicated burn protocol: five typed offence categories —
bias injection, data poisoning, drift, signature mismatch, manipulation — gated
behind a council vote of at least 66%, with the vote percentage and the evidence
recorded on the event and written to the ledger. A burn resets both reputation
and staked reputation to zero and quarantines the node permanently. Stake
slashing is a separate ledger operation: tokens move to a `slash_escrow_vault`
for an appeal window, and on expiry are recycled to the treasury rather than
destroyed. Reputation burn is implemented and irreversible; permanent token burn
is accounted for in the supply calculation but never triggered — nothing writes
to the `system_burn` sink, and the declared 50/30/20 recycle-burn split is not
applied by the escrow path, which returns 100% to the treasury.

### Ledger and provenance

Append-only log secured by Merkle trees over transaction IDs, with Ed25519
signatures over every block and over proposal content. Proposal signatures are
verified on receipt against canonical serialization, so a tampered proposal is
rejected before it reaches deliberation.

Decisions are linked in a directed acyclic graph. `MemoryGraph`
(`backend/core/memory.py`) stores every knowledge item, proposal, vote, verdict
and burn as a node carrying its parent IDs and a SHA-256 seal over content,
parents, author and timestamp, persisted through SQLAlchemy. That gives an audit
trail from a verdict back through every contributing judgement, with each hop
individually tamper-evident.

Block signatures are generated but not yet verified on receipt; see
[Where it stopped](#where-it-stopped).

### Key security and privacy

`NodeIdentity` encrypts private keys at rest with AES-256-GCM under a Scrypt-derived
key, unlocked by a `KEY_PASSWORD` supplied at startup; with `STRICT_SECURITY=true`
it refuses to generate or load an unencrypted key. Identity is portable: moving
the encrypted `.keys` directory to another machine and supplying the same password
restores the same identity and standing.

API keys are held per node under a bring-your-own-key model, read from the
environment, never centrally.

One key escaped this: `ConsensusManager` keeps its own keypair in `node_key.json`
as plain hex. See [Where it stopped](#where-it-stopped).

## Findings

**Cryptographic signing across heterogeneous clients requires canonical
serialization.** Proposals submitted in Hebrew failed verification with 401
errors: the JavaScript frontend and the Python backend serialized the same JSON
to different byte sequences, so the signature computed on one side never matched
the payload verified on the other. Signing is only as trustworthy as the
byte-level agreement underneath it, and non-ASCII input is where that agreement
breaks first.

**A fallback path must match the concurrency model of the path it replaces.**
The mock provider used as a fallback was synchronous while the engine was async.
When the primary provider failed, the fallback crashed the system rather than
degrading it. A fallback never exercised under the real execution model is not a
fallback.

**Structured output from a language model is not structured.** Every entity
response passes through a parser that strips markdown fences before `json.loads`,
because models return prose around the JSON they were asked for. The approach
handles the common cases and fails on unclosed fences. Any system treating model
output as a typed value needs a validation layer, not a parse.

**Longest-chain consensus is meaningless without a cost to producing chain.**
The first implementation inherited a longest-chain rule from proof-of-work
designs. With no work requirement, chain length measures nothing and any node can
manufacture a longer history for free. This motivated a move to
reputation-weighted Proof-of-Authority — a move the design made and the code did
not finish: the reference miner still hunts a nonce against a difficulty target,
and reputation ended up weighting rewards rather than authority.

**Ledger state must outlive the process.** Database persistence moved to Docker
volumes after container restarts destroyed chain state. An append-only ledger is
only append-only if its storage survives the thing writing to it.

**The incentive layer could not be reconciled with the goal, and this is where
the experiment stopped.** Reputation-weighted consensus needs participants, and
participants need a reason to contribute compute. The mechanism was built: usage
costs tokens, validated inference earns from a fixed pool, malicious nodes are
slashed. But attaching value to ethical judgement changes what is being measured
— a node rewarded for producing verdicts optimises for producing verdicts, not
correct ones, and the reputation signal the entire consensus depends on becomes
purchasable. Removing the economic layer leaves no reason for anyone but the
author to run a node. The project stopped at this tension rather than resolving
it. It is not a technical limit.

## Where it stopped

The unfinished work clusters in one place, and it is the same place the Findings
above end: the layer that was supposed to make the system trustless *between*
nodes. A single node deliberates, scores, seals and records correctly. What was
never closed is the part that would let a second node disbelieve the first.

- **Proof of Inference is not enforced.** `verify_poi()` is implemented and
  correct but never called; the worker signs a different payload shape than it
  expects, and falls back to a placeholder signature when no consensus manager is
  attached. A shard result is currently trusted on arrival.
- **Block signatures are not verified.** `validate_block` checks structure and
  the presence of a signature, but the Ed25519 check is commented out, and blocks
  from validators named `miner_*` are admitted with a placeholder.
- **Block authority is not reputation-weighted.** There is no validator set or
  leader election; any peer passing `validate_block` can extend the chain, and
  the reference miner still searches a nonce against a difficulty target. The
  move away from proof-of-work was made in the design and not in the code.
- **No catch-up sync.** Peers discover each other and gossip new blocks, but a
  node that was offline does not recover what it missed.
- **One key is unprotected.** `ConsensusManager` stores its private key in
  `node_key.json` as plain hex, chmod 600. The hardened path (`NodeIdentity`,
  AES-256-GCM) covers node identity but not this one.
- **Retrieval is a stub.** The Researcher stage is wired but returns fixed
  context instead of querying anything.

Beyond that layer: the front end is a single-page dashboard consuming
`text/event-stream` from `GET /api/verify/stream` — adequate for observing
deliberation, not a production interface. The Solidity contracts under
`contracts/` are reference implementations, exercised only against an in-memory
`eth-tester` chain and never deployed; there are no deployment scripts and no
recorded addresses. Consensus was exercised across a small number of nodes, well
below the scale at which the interesting failure modes appear. The deliberation
protocol assumes cooperative entities: the burn protocol addresses lazy or
duplicate voting, but an agent that reasons in bad faith while appearing to
participate correctly is not modelled. And verdict quality was never measured
against an external benchmark — the system can show that a decision was made and
by whom, not that it was a good decision.

## Running it

Requires Python 3.11+ and Ollama for local inference.

```bash
git clone https://github.com/Yehielamor/orbis-ethica.git
cd orbis-ethica
pip install -r requirements.txt

KEY_PASSWORD=your_password python -m uvicorn backend.server:app --port 8000
```

The server binds `PORT`, defaulting to 8000, and mounts the dashboard at
`http://localhost:8000/`. Docker Compose with Nginx is also provided; it serves
the dashboard separately on port 80 and publishes 6429 and the 6430-6440 P2P
range, though nothing currently listens on 6429.

`scripts/start_node.sh` brings up a node with the P2P environment configured.
Running one makes your machine a participant in the mesh; there is no central
server. A node that goes offline will rejoin and receive new blocks, but will not
recover the ones it missed.

## Verification

Sixteen test modules covering ULFR scoring, consensus, tokenomics, deadlock
resolution, reputation, the burn flow and the Solidity contracts, plus standalone
checks in `tests/verify_paywall.py`, `tests/verify_progress.py` and
`tests/gold_verification.py`.

The suite has bit-rotted since the project was archived, and the commands below
are recorded as they behave today rather than as intended:

```bash
pytest tests/unit/test_ulfr.py    # 12 passed
pytest tests                      # 3 passed, 4 failed, 6 collection errors
```

Most of the failures are drift rather than broken behaviour — `test_burn_flow`
fails because it passes a `log_path` argument the constructor no longer takes,
not because the burn protocol misbehaves. Two modules import `backend.knowledge`,
which no longer exists in this tree, which takes `tests/unit` and
`tests/integration` down at collection. Running everything at once also collides
on the two files named `test_ulfr.py`, since the test directories have no
`__init__.py`.


## Repository layout

```
backend/      Core engine, ledger, consensus, deliberation, security, P2P router
tests/        Unit and integration suites
scripts/      Mining, simulation, inspection and node startup tooling
sdk/          Python client (sdk/orbis.py) and LangChain adapter (sdk/langchain_orbis.py)
contracts/    Solidity contracts (reference only, never deployed)
frontend/     Single-page dashboard (HTML/JS, SSE live feed)
docs/         Architecture notes and design rationale
```


## Documentation

- `MASTER_GUIDE.md` — module-by-module walkthrough of the codebase
- `docs/why_you_need_orbis.md` — the compliance and liability case for the design
- `CHANGELOG.md` — development history by phase

## License

See `LICENSE`.
