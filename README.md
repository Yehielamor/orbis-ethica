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
- `backend/core/llm_provider.py` — factory-pattern abstraction over Gemini, Groq
  and Ollama, so no single vendor is load-bearing
- SQLite as hot storage for the local ledger; Merkle roots as the trust anchor

A verification request follows a fixed path: `POST /api/verify` → balance check
and burn of 0.1 ETHC → deliberation → weighted consensus → signed verdict.

### ULFR: scoring a judgement

Every proposal is evaluated across four dimensions — Utility (aggregate welfare,
efficiency), Life/Care (harm reduction, protection of the vulnerable), Fairness
(equity, distribution) and Rights (autonomy, dignity, due process).

Scoring is deductive rather than additive: a proposal begins at 1.0 and is
penalised for each identified deficit. This was deliberate. Additive scoring lets
a proposal accumulate credit on one axis to offset a serious failure on another;
deduction keeps deficits visible and scores normalised across dissimilar cases.

### Cognitive entities

Six roles are defined, each with a distinct mandate and system prompt: **Seeker**
(knowledge and utility), **Healer** (harm reduction and care), **Guardian**
(justice and rights), **Mediator** (balance and trade-offs), **Creator**
(synthesis and alternatives) and **Arbiter** (final judgement and coherence).
The standard verification flow runs Guardian, Healer and Arbiter; the remaining
roles participate in extended deliberation, with the Mediator refining proposals
across rounds to resolve deadlock rather than forcing a vote.

Entities inherit from an abstract base class and receive their LLM provider by
injection, so the same entity runs against a mock in tests and a real provider in
production without changing the class.

### Cognitive sharding

Complex dilemmas are decomposed into atomic shards along the ULFR axes and
distributed across P2P nodes, each running local inference (Ollama / TinyLlama).
Results are aggregated into a single verdict. The motivation was to test whether
ethical evaluation parallelises usefully, or whether the dimensions are too
entangled to score in isolation.

### Proof of Inference

Nodes must cryptographically sign the cognitive work they perform, producing an
`ExecutionSeal`. Without it, a node can claim to have evaluated a shard while
returning an arbitrary score. Proof of Inference is what makes distributed
reasoning verifiable rather than merely distributed.

### Consensus, reputation and penalties

Proof-of-Authority across a P2P mesh, with block signing weighted by node
reputation rather than stake or hash power — on the assumption that in a
decision-auditing context the scarce resource is trust, not compute.

Reputation (ETHC) is capped at 10,000,000 with no founder pre-mine. Usage burns
tokens; rewards for validated inference are transfers from a fixed
`INFERENCE_REWARD_POOL` and therefore do not increase supply.

Penalties are handled by a separate burn protocol with typed offence categories
and a recorded council vote threshold. A node found to have acted maliciously has
its staked reputation slashed, up to a full reset to zero. Token burn and
reputation burn are distinct mechanisms and are recorded separately.

### Ledger and provenance

Append-only log secured by Merkle trees, with Ed25519 signatures over every block
and over all content. Decisions are linked in a directed acyclic graph, giving an
audit trail from a verdict back through every contributing judgement. Given the
chain and the public keys, any node can confirm the history independently of
whoever wrote it.

### Key security and privacy

Node private keys are encrypted at rest with AES-256-GCM and unlocked by a
`KEY_PASSWORD` supplied at startup. Identity is portable: moving the encrypted
`.keys` directory to another machine and supplying the same password restores the
same identity and standing. Node IDs are SHA-256 masked in the public network
status. API keys are held per node under a bring-your-own-key model, never
centrally.

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
manufacture a longer history for free. This motivated the move to
reputation-weighted Proof-of-Authority.

**Ledger state must outlive the process.** Database persistence moved to Docker
volumes after container restarts destroyed chain state. An append-only ledger is
only append-only if its storage survives the thing writing to it.

**The incentive layer could not be reconciled with the goal, and this is where
the experiment stopped.** Reputation-weighted consensus needs participants, and
participants need a reason to contribute compute. The mechanism was built: usage
burns tokens, validated inference earns from a fixed pool, malicious nodes are
slashed. But attaching value to ethical judgement changes what is being measured
— a node rewarded for producing verdicts optimises for producing verdicts, not
correct ones, and the reputation signal the entire consensus depends on becomes
purchasable. Removing the economic layer leaves no reason for anyone but the
author to run a node. The project stopped at this tension rather than resolving
it. It is not a technical limit.

## Limitations

The front end is a single-page HTML/JavaScript dashboard with a live SSE feed —
adequate for observing deliberation, not a production interface. The Solidity
contracts under `contracts/` are reference implementations and were never
deployed. Consensus was exercised across a small number of nodes, well below the
scale at which the interesting failure modes appear. The deliberation protocol
assumes cooperative entities: the burn protocol addresses lazy or duplicate
voting, but an agent that reasons in bad faith while appearing to participate
correctly is not modelled. Verdict quality itself was never measured against an
external benchmark — the system can prove that a decision was made and by whom,
not that it was a good decision.

## Running it

Requires Python 3.11+ and Ollama for local inference.

bash
git clone https://github.com/Yehielamor/orbis-ethica.git
cd orbis-ethica
./scripts/setup_swarm.sh

KEY_PASSWORD=your_password python -m uvicorn backend.api.app:app --port 6429


The dashboard is served at `http://localhost:6429/`. Docker Compose with Nginx is
also provided. Running a node makes your machine a participant in the mesh; there
is no central server, and a node that goes offline resynchronises from peers on
return.

## Verification

bash
pytest tests/unit
pytest tests/integration

python scripts/verification/verify_identity.py       # key generation and signing
python scripts/verification/verify_block_signing.py  # Proof of Authority
python scripts/verification/verify_startup.py        # initialisation ordering
python scripts/verification/verify_p2p.py            # network layer


## Repository layout


backend/      Core engine, ledger, consensus, deliberation, security, P2P router
tests/        Unit and integration suites
scripts/      Setup, mining, simulation, verification and deployment tooling
sdk/          Python client, including the LangChain adapter
contracts/    Solidity contracts (reference only, never deployed)
frontend/     Single-page dashboard (HTML/JS, SSE live feed)
docs/         Architecture notes and design rationale


## Documentation

- `MASTER_GUIDE.md` — module-by-module walkthrough of the codebase
- `docs/why_you_need_orbis.md` — the compliance and liability case for the design
- `CHANGELOG.md` — development history by phase

## License

See `LICENSE`.
