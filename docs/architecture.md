# Architecture

## Principles
- Deterministic by default.
- Stage-isolated tick processing.
- Stock-flow and social-state checks as first-class concerns.
- Explainability-ready state transitions.

## Modules
- `src/core/rng.py`: deterministic random stream.
- `src/core/state_store.py`: canonical state storage and snapshot hashing.
- `src/core/tick_engine.py`: monthly stage pipeline with immutable prior state reads.

## Tick Lifecycle
1. Load prior state.
2. Build tick context.
3. Execute ordered stages.
4. Merge stage outputs into next state.
5. Compute and persist snapshot hash.

## Contract
- Stages must be pure with respect to inputs.
- Stages receive prior-state view and context.
- Stage output is a dictionary patch only.
