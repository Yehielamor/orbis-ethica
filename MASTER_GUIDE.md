# The Orbis Ethica Master Guide
*A deep-dive technical bible for the Creator. Use this to master your codebase from scratch.*

---

## 🏗️ Module 1: High-Level Architecture

We view the system from 30,000 feet.

### 1. The Component Map
The system is an **Asynchronous Modular Monolith**.
*   **Backend (API Layer)**: `backend/server.py`. The entry point implementing `FastAPI`. Handles Auth & Payments.
*   **Orchestrator (Logic)**: `backend/core/deliberation_engine.py`. The "Brain" that manages the conversation between agents.
*   **LLM Provider (Abstract Layer)**: `backend/core/llm_provider.py`. A Factory Pattern preventing vendor lock-in (Gemini/Groq/Ollama).
*   **Data Persistence**:
    *   **SQLite**: Hot storage (Local Ledger).
    *   **Blockchain**: Cold storage (Trust Anchor via Merkle Roots).

### 2. The Data Flow
1.  **User Request**: `POST /api/verify` ("Is it ethical to fire Bob?").
2.  **Payment**: `server.py` checks `ledger` for 0.1 ETHC balance. Burns it.
3.  **Engine Start**: `DeliberationEngine` spins up.
4.  **Agent Debate**: Engine calls `Guardian`, `Healer`, `Arbiter` via LLM.
5.  **Consensus**: Scores are weighted.
6.  **Response**: JSON verdict returned to user.

---

## 🏗️ Module 2: The Cognitive Entities (OOP & Logic)

We choose **Object Oriented Programming** (OOP) here because our Agents need to share behavior (`evaluate_proposal`) but implement internal logic differently (`System Prompt`).

### 1. The Contract: `backend/entities/base.py`

This file defines the strict rules every Agent must follow.

#### Key Class: `BaseEntity(ABC)`

```python
class BaseEntity(ABC):
    def __init__(self, entity: Entity, llm_provider: Optional[LLMProvider] = None, ...):
        self.entity = entity
        self.llm_provider = llm_provider or get_llm_provider()
```

*   **`ABC` (Abstract Base Class)**: We assume `from abc import ABC`. This prevents us from forcefully instantiating a "raw" entity. You *cannot* say `x = BaseEntity()`. You MUST inherit from it.
*   **Dependency Injection**: Notice `llm_provider`. We pass it in `__init__`.
    *   *Why?* Flexibility. In tests, we pass a `MockLLM`. In prod, we pass `Gemini`. This makes testing 100x easier because we don't hardcode API calls inside the class.
    *   *Best Practice?* Yes. Known as **Inversion of Control (IoC)**.

#### Critical Function: `_parse_json_response`

```python
def _parse_json_response(self, response: str) -> Dict[str, Any]:
    # Regex magic to strip markdown code blocks
    if "```json" in clean_response: ...
```

*   *Why Regex?* LLMs are chatty. Even if you ask for JSON, they might say: "Here is your JSON: ```json {...} ```".
*   `json.loads()` will crash on "Here is your JSON".
*   The Regex logic `r"```json(.*?)```"` extracts *only* the content inside the code fencing.
*   *Is this unstable?* Slightly. If the LLM doesn't close the backticks, it might fail. But it's robust enough for 99% of cases compared to raw parsing.

### 2. The Implementation: `backend/entities/guardian.py`

This is where the magic happens. The Guardian *extends* `BaseEntity`.

#### `get_system_prompt()` (The Soul)

```python
def get_system_prompt(self) -> str:
    return """You are the Guardian...
    YOUR PRIMARY QUESTION: "Does this respect fundamental rights and dignity?"
    ..."""
```
*   *Why return a string?* This string is injected into *every* call to the LLM as the "System Message". It sets the personality.
*   *Why `self._get_json_format_instructions()`?* We concat the JSON instructions at the end of *every* prompt to ensure the LLM never forgets the output format strictness.

#### `evaluate_proposal()` (The Brain)

```python
async def evaluate_proposal(self, proposal: Proposal) -> EntityEvaluation:
    prompt = f"Evaluate this proposal... {proposal.title}..."
    response = await self._call_llm(prompt)
    data = self._parse_json_response(response)
```
*   **Async/Await**: We use `async def` because `_call_llm` uses network (IO). If we didn't, the entire server would freeze while waiting for Gemini.
*   **The Flow**:
    1.  Build a huge f-string prompt with the Proposal data.
    2.  Send to LLM (await).
    3.  Receive String -> Parse to Dictionary (`_parse_json_response`).
    4.  Convert Dictionary to Pydantic Object (`EntityEvaluation`).
    5.  Return the Object.

### 3. The Data Structure: `backend/core/models/decision.py`

This file holds the *result* of the agents' work. We use **Pydantic** (`BaseModel`).

#### `EntityEvaluation` vs `Decision`

*   **`EntityEvaluation`**: The opinion of *one* agent.
    *   Contains: `ulfr_score`, `vote` (1/0/-1), `reasoning`.
    *   *Why `vote: int`?* Integers are easier to sum up for consensus than strings ("APPROVE").

*   **`Decision`**: The final verdict of the *whole system*.
    *   Contains: `List[EntityEvaluation]`.
    *   **Consensus Logic**: `calculate_weighted_vote()`.
    *   *Formula*: Sum of (Vote * Weight) / Total Weight.
    *   *Why?* Allows us to give the `Guardian` more power (weight 1.5) than a `Newbie Agent` (weight 0.5) if we want later.

#### `DecisionOutcome` (Enum)

```python
class DecisionOutcome(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REFINED = "refined" ...
```
*   *Why Enums?* Magic strings are dangerous. If you typo `"aprove"` (one p) in code, you break everything. With `DecisionOutcome.APPROVED`, the IDE protects you.

---

## ⚡ Module 3: Concurrency & Asyncio (The Engine)

This is the hardest part for most developers. Python is single-threaded, but our server handles 1000s of requests. How?

### 1. The Core Concept: Cooperative Multitasking

In a normal script, if you run `slow_function()`, the entire CPU stops and waits.
In our system (`FastAPI + asyncio`), we use `await` to yield control back to the **Event Loop**.

#### The Golden Rule
> **"While one request is waiting for the LLM, the CPU should be serving someone else."**

### 2. The Implementation: `backend/core/deliberation_engine.py`

Look at the `deliberate_generator` function. This is a masterpiece of async design.

```python
async def deliberate_generator(self, proposal: Proposal, ...):
    yield {"type": "init", ...}
    
    # 1. IO-Bound Operation (Network Call)
    # The 'await' keyword pauses this function here.
    # The Event Loop goes to do other work until the LLM replies.
    round_evaluations = await self.entity_evaluator.evaluate_panel(proposal)
    
    # 2. CPU-Bound Operation (Math)
    # No await here. This blocks the loop, but it's super fast (<1ms).
    weighted_score = self._calculate_weighted_score(evaluations)
```

#### Why a Generator (`async for`)?

We defined `deliberate_generator` instead of a simple `return`.
*   **Streaming**: We want the Frontend (UI) to see "Guardian is thinking..." *live*.
*   If we just returned the final `Decision`, the user would face a generic "Loading..." spinner for 20 seconds.
*   With `async for event in engine.deliberate_generator(...)`:
    1.  Server yields "Thinking...".
    2.  Server awaits LLM.
    3.  Server yields "Guardian voted 80%".
    4.  Client renders progress bar updates in real-time.

### 3. Critical: Handling Race Conditions

A **Race Condition** happens when two tasks try to modify the same resource (like the Ledger) at the same time.

#### The Problem
Imagine User A sends "Verify Action X" (Cost 0.1) twice rapidly.
1.  Request 1 reads Balance: 0.1
2.  Request 2 reads Balance: 0.1 (Before Req 1 saves!)
3.  Req 1 subtracts 0.1 -> writes 0.0
4.  Req 2 subtracts 0.1 -> writes 0.0
**Result**: User spent 0.1 tokens but got 0.2 tokens worth of service.

#### The Solution (Reference: `backend/server.py`)

In `verify_payment`, we strictly check balance *before* proceeding.
However, for true safety, we use **Database Transactions** (ACID).
SQLite locks the file during a write. So:
1.  Req 1 locks DB. Reads 0.1. Updates to 0.0. Unlocks.
2.  Req 2 locks DB. Reads 0.0. Fails.

*Note: In `asyncio`, we must also be careful with shared memory variables. We avoided global state variables for this reason.*

### 4. `asyncio.gather` (The Turbo Boost)

In `entity_evaluator.py`, we iterate over entities:

```python
# Sequential (Slow) - 3 seconds each = 9 seconds total
for entity in self.entities:
    await entity.evaluate_proposal(proposal) 

# Parallel (Fast) - 3 seconds total!
await asyncio.gather(
    guardian.evaluate_proposal(proposal),
    healer.evaluate_proposal(proposal),
    seeker.evaluate_proposal(proposal)
)
```
*We currently use `evaluate_panel` (Single Prompt) to save tokens, but if we switch back to individual agents, `gather` is the key to speed.*

---

## ⛓️ Module 4: The Hybrid Blockchain Model (State & Truth)

This is the "Secret Sauce" of Orbis Ethica. We solve the Crypto Trilemma (Security, Scalability, Decentralization) by cheating slightly: we use **Layer 2 logic with Layer 1 security**.

### 1. The Concept: Optimistic Execution

1.  **Fast Path (Python/SQLite)**: When you click "Verify", we write to `backend/core/ledger.py` instantly.
    *   Latency: 0.01s.
    *   Cost: 0.
2.  **Slow Path (Ethereum/Solidity)**: Every X blocks (or hours), we take a "Snapshot" (Merkle Root) of the local ledger and send it to the Blockchain.
    *   Latency: 15s.
    *   Cost: Gas.

### 2. The Local Ledger: `backend/core/ledger.py`

This file mimics a blockchain node but runs on SQLite.

#### `record_transaction()`
```python
def record_transaction(self, sender, recipient, amount, ...):
    with self._lock:  # Thread Safety!
         # 1. Check Hard Cap (10M Tokens)
         if total_supply + amount > MAX_SUPPLY: return False
         
         # 2. Check Balance
         if self.get_balance(sender) < amount: return False
         
         # 3. Write to DB (ACID)
         session.add(LedgerEntryModel(...))
         session.commit()
```
*   **The Lock**: `self._lock` prevents two threads from reading the balance at the exact same microsecond.
*   **Hard Cap**: We enforce tokenomics in *code*. If `MAX_SUPPLY` is reached, `mint` fails.

#### `create_block()` (The Mining Process)
We don't use Proof of Work (mining with GPUs). We use **Proof of Authority / Reputation**.
1.  Gather all "Pending" transactions (those in DB but no `block_hash`).
2.  Create a **Merkle Tree** (Hash of hashes) to fingerprint them.
3.  Sign the block with the Node's Private Key.
4.  Save `BlockModel` to DB.

### 3. The Smart Contracts (The Truth)

Located in `contracts/`.

*   `OrbisToken.sol` (ERC-20): The actual token on the blockchain.
    *   People hold `ETHC` in their Metamask.
*   `ComplianceNode.sol`: The bridge.
    *   We send the `Merkle Root` here.
    *   This proves that our SQLite DB hasn't been tampered with.

#### **Why do we need both?**
If we only had SQLite, I could manually edit the DB file and give myself 1,000,000 tokens.
But if I do that, the `Merkle Root` will change. The Blockchain contract will say: "Hey, that Root doesn't match what you sent me yesterday!"
**The Blockchain acts as a Checksum for the Database.**

---

## 🛡️ Module 5: Quality Assurance & Testing Strategy

How do we sleep at night? By having a test suite that proves the math is right.

### 1. The Strategy: Pytest & Fixtures

We use `pytest`. It's modern, minimal, and powerful.

#### Key Concept: Fixtures (`@pytest.fixture`)
In `tests/test_tokenomics.py`:
```python
@pytest.fixture
def ledger():
    db_manager = DatabaseManager("sqlite:///:memory:") 
    Base.metadata.create_all(db_manager.engine)
    return Ledger(db_manager)
```
*   **In-Memory DB**: Notice `"sqlite:///:memory:"`.
    *   This creates a brand new database in RAM for *every single test*.
    *   It's destroyed when the test finishes.
    *   *Why?* Tests should never affect the production DB (file on disk). RAM is fast and clean.

### 2. Unit vs Integration

*   **Unit Tests (`tests/unit/`)**: Test *one* thing in isolation.
    *   Example: `tests/unit/test_ulfr.py`.
    *   Calculates `(0.5 * 0.5) + ...` to verify the math formula. No Database, no LLM. Milliseconds.
    
*   **Integration Tests (`tests/*.py`)**: Test how modules talk to each other.
    *   Example: `tests/test_tokenomics.py`.
    *   Tests `Ledger` + `Database` + `Logic`. It simulates a real flow: "Mint -> Check Cap -> Burn -> Mint Again".

### 3. The Burn Protocol Logic

The most critical test in our economy is **Hard Cap Enforcement**.

```python
def test_hard_cap_enforcement(ledger):
    # 1. Fill the bucket to water_level = 9,999,999
    ledger.mint(..., 9_999_999) 
    
    # 2. Try to add 2 drops
    success = ledger.mint(..., 2) 
    assert success is False # MUST FAIL
    
    # 3. Scoop out 10 drops (Burn)
    ledger.burn(..., 10)
    
    # 4. Add 5 drops
    success = ledger.mint(..., 5)
    assert success is True # MUST SUCCEED (Because we made room!)
```
*   *Why is this critical?* If this fails, inflation destroys the token value. This test is the "Central Bank" guarantee.

---

## 🔐 Module 6: Security, Consensus & Reputation

You asked: *"How prevents a hacker from faking the SQLite data?"*
The answer lies in **Public Key Cryptography** and **Reputation Staking**.

### 1. The Quiz Answer: Node Identity (`consensus.py`)

If a hacker changes the SQLite balance to 1,000,000, they must calculate a new `Merkle Root`.
To submit this Root to the Blockchain, they need to **Sign** it.

```python
# backend/core/consensus.py
def sign_proposal(self, proposal: Proposal):
    # 1. Canonicalize (Sort keys alphabetically so hash is deterministic)
    content = json.dumps(data, sort_keys=True)
    
    # 2. Sign with Private Key (Ed25519)
    signed = self.signing_key.sign(content.encode())
```

*   **The Check**: The Smart Contract (`ComplianceNode.sol`) knows your **Public Key**.
*   If the hacker signs with *their* key -> Contract rejects it ("Who are you?").
*   If the hacker doesn't sign -> Contract rejects it.
*   **The Only Risk**: If the hacker steals your `node_key.json` from the server. (That's why `os.chmod 600` is critical).

### 2. Proof of Reputation (PoR)

We don't just rely on encryption. We rely on **Skin in the Game**.

#### `ReputationManager` (`backend/security/reputation_manager.py`)

Every Entity (Guardian, Healer) has a `reputation` score (0.0 to 1.0).
When they vote on a sensitive proposal, they **Stake** reputation.

```python
def stake_reputation(self, entity, amount):
    # Free Rep = Total - Staked
    if free_reputation < amount: return False
    entity.staked_reputation += amount # Lock it!
```

*   **If they lie/hallucinate**: We call `slash_stake()`, and they lose that reputation forever.
*   **If they hit 0.0**: They are ignored by the Consensus Engine.
*   *Why?* It fits the "Ethical" theme. Bad actors lose their voice, not just their money.

### 3. Conclusion for the Interview

If asked about security:
> "We use a **Defense in Depth** strategy.
> 1.  **Application Layer**: Pydantic Validation & Hard Caps.
> 2.  **Consensus Layer**: Ed25519 Signatures on every block/proposal.
> 3.  **Economic Layer**: Reputation Staking & Slashing (PoR).
> 4.  **Base Layer**: Ethereum Smart Contracts as the final immutable source of truth."
