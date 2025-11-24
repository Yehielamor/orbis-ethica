# API Reference

Currently, Orbis Ethica operates primarily via a CLI and internal Python API. A REST API is planned for Phase II.

## Python API

### DeliberationEngine

The main entry point for running simulations.

```python
from backend.core.deliberation_engine import DeliberationEngine
from backend.entities import SeekerEntity, GuardianEntity

# Initialize
engine = DeliberationEngine(entities=[SeekerEntity(...), GuardianEntity(...)])

# Run
decision = engine.deliberate(proposal)
```

#### `deliberate(proposal: Proposal) -> Decision`
Runs the full deliberation protocol.
- **proposal**: A `Proposal` object containing title, description, and category.
- **Returns**: A `Decision` object with the final outcome and score.

### Entities

Base class: `backend.entities.base.BaseEntity`

#### `evaluate_proposal(proposal: Proposal) -> EntityEvaluation`
Evaluates a proposal based on the entity's specific ethical focus.
- **Returns**: `EntityEvaluation` containing ULFR scores, vote, and reasoning.

#### `refine_proposal(proposal: Proposal, evaluations: List[EntityEvaluation]) -> str`
(Mediator only) Generates a refined description of the proposal to resolve conflicts.

### Models

#### `Proposal`
- `title`: str
- `description`: str
- `category`: ProposalCategory (ROUTINE, HIGH_IMPACT, etc.)

#### `Decision`
- `outcome`: DecisionOutcome (APPROVED, REJECTED, REFINED)
- `weighted_score`: float (0.0 - 1.0)
- `deliberation_rounds`: int

## CLI Commands

Run via `python -m backend.cli.main [COMMAND]`.

- `test`: Run system diagnostics and verification.
- `demo`: Run the "Hospital Resource Allocation" scenario.
- `submit`: Interactive mode to submit a custom proposal.
