# Validation Suite (Phase 7 Starter)

## Purpose
Provide a single place to define mandatory gates and scenario checks before phase advancement.

## Mandatory Gates
1. Deterministic replay gate.
2. GDP identity residual gate.
3. Sector residual gate.
4. Social-state conservation gate.
5. Full test-suite gate.

## Gate Thresholds
- `gdp_identity_residual_ratio_max`: 0.001
- `sector_residual_abs_max`: 0.000001
- `social_population_residual_abs_max`: 0.000001

## Stress Scenarios Required
1. sanctions
2. energy_shock
3. sudden_stop
4. drought
5. banking_panic
6. disinformation_wave
7. identity_polarization

## Minimum Runner Output
- Timestamp.
- Python and package versions.
- Gate-by-gate pass/fail with measured values.
- Final verdict: pass or fail.
