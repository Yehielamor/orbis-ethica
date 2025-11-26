# Orbis Ethica: Economic Security Model (Phase XII)

## 1. Executive Summary
To move beyond "Security Theater" and create true deterrence, Orbis Ethica introduces a **Crypto-Economic Layer**. This layer binds the abstract concept of "Reputation" to tangible value (Tokens), creating a direct financial cost for malicious behavior.

**Core Principle:** *It must cost more to attack the network than the potential gain from the attack.*

## 2. The Asset: Ethica Token ($ETHC)
$ETHC is not just a currency; it is a **Bond of Trust**.
- **Type**: Utility Token (ERC-20 equivalent standard).
- **Supply**: Fixed / Inflationary (TBD based on governance).
- **Utility**:
    1.  **Staking**: Required to become a Validator or Knowledge Source.
    2.  **Governance**: Voting power in the DAO (Quadratic Voting).
    3.  **Access**: Payment for high-throughput API access (Anti-Spam).

## 3. Staking Mechanisms

### 3.1. Validator Staking (Consensus Layer)
To participate in block creation and voting (Proof of Authority/Stake hybrid):
- **Minimum Stake**: 32,000 $ETHC.
- **Lock-up Period**: 2 weeks withdrawal delay.
- **Role**: Validates transactions, executes ULFR calculations, proposes blocks.

### 3.2. Knowledge Staking (Clear Layer)
To submit data to the Knowledge Gateway (as a "Trusted Source"):
- **Minimum Stake**: 10,000 $ETHC per feed.
- **Liability**: The stake serves as collateral for the *truthfulness* of the data.
- **Dispute Period**: Data is "optimistically verified" but can be challenged for 24 hours.

## 4. The Burn Protocol 2.0 (Slashing)

The "Burn" is no longer just a flag in the database; it is a **Token Burn Event**.

### 4.1. Slashing Conditions (The 7 Deadly Sins)
1.  **Equivocation (Double Signing)**: Signing two different blocks at the same height.
    *   *Penalty*: 100% of Stake Burned. Immediate expulsion.
2.  **Invalid Block Proposal**: Proposing a block that violates protocol rules (e.g., invalid transactions).
    *   *Penalty*: 10% of Stake Burned.
3.  **Malicious Knowledge Injection**: Submitting data proven to be false (via Cross-Verification or Oracle).
    *   *Penalty*: 50% of Stake Burned.
4.  **Censorship**: Consistently ignoring valid transactions (detected by statistical analysis).
    *   *Penalty*: 5% of Stake Burned.
5.  **Downtime**: Failing to produce blocks when elected.
    *   *Penalty*: Minor leak (0.1% per occurrence).

### 4.2. The Burn Mechanism
When a slash occurs:
1.  The slashed tokens are sent to a `0x00...dead` address (permanently removed from supply).
2.  A `BurnReceipt` is generated and broadcasted to the network.
3.  The node's reputation score is instantly set to 0.

## 5. Incentive Structure (Rewards)

To encourage honest participation:
- **Block Rewards**: Newly minted $ETHC for proposing valid blocks.
- **Attestation Rewards**: Fees for verifying other blocks.
- **Knowledge Rewards**: Micro-payments for high-utility knowledge (measured by citation in cognitive deliberation).

## 6. Implementation Strategy

### Phase XII.1: The Ledger Upgrade
- Upgrade `LedgerBlock` to support `Balance` state.
- Implement `TokenTransaction` type (Transfer, Stake, Unstake, Slash).

### Phase XII.2: The Staking Contract
- Smart Contract (or Python equivalent logic) to manage deposits and locks.
- Logic to freeze funds during dispute periods.

### Phase XII.3: The Slashing Circuit
- Automated detection of Equivocation.
- Governance-triggered slashing for Knowledge disputes.

## 7. Risk Analysis
- **Rich-Get-Richer**: Mitigated by Quadratic Voting in governance.
- **Nothing-at-Stake**: Solved by the lock-up period and slashing penalties.
- **Oracle Problem**: Who decides if knowledge is false? (Solved by the "Arbiter" entity + DAO voting).
