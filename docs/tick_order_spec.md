# Tick Order Specification (Phase 1/2 Draft)

## Tick Metadata
- Resolution: monthly.
- Determinism: required.
- State commit: end-of-tick only.

## Stage Contract
Each stage must define:
- Stage name.
- Inputs read from prior state.
- Outputs written to patch.
- Invariants validated after stage.

## Stage Read and Write Contracts
1. `apply_policies`
- Reads: policy settings, prior commitments.
- Writes: active policy vector for tick.

2. `update_expectations`
- Reads: prior inflation, growth, risk indicators.
- Writes: expectation state for prices, wages, and risk premia.

3. `compute_real_economy`
- Reads: production capacity, input inventories, technical coefficients.
- Writes: realized output, updated inventories, unmet demand.

4. `update_prices_labor`
- Reads: output gaps, costs, expectation state, labor slack.
- Writes: goods prices, inflation decomposition, wages, unemployment.

5. `update_public_external`
- Reads: tax base, spending rules, debt stock, trade flows, reserves.
- Writes: fiscal balance, debt delta, current account and reserve updates.

6. `update_social_political`
- Reads: needs gap, unemployment, inflation, inequality, trust state.
- Writes: trust, legitimacy, polarization, unrest probability.

7. `run_consistency_checks`
- Reads: full provisional next-state snapshot.
- Writes: gate diagnostics and pass/fail flags.

8. `commit_state`
- Reads: validated provisional next-state.
- Writes: canonical committed state and snapshot hash.

## Phase 2 Gate Targets
- GDP identity residual ratio must be <= 0.001 per tick.
- Sector aggregate residual must be <= configured absolute tolerance.

## Determinism Rules
- No direct use of global random APIs.
- All stochastic calls use deterministic stream from `DeterministicRNG`.
- Stage execution order must remain fixed.
