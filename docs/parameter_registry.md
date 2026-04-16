# Parameter Registry (v1)

## Purpose
Central registry for tunable model coefficients with defaults and ranges.

## Pricing Block
- `lambda_cost`
- Meaning: pass-through from unit-cost changes to prices.
- Default: 0.35
- Range: 0.20 to 0.60

- `lambda_demand`
- Meaning: pass-through from excess demand to prices.
- Default: 0.20
- Range: 0.10 to 0.50

- `lambda_fx`
- Meaning: exchange-rate pass-through to prices.
- Default: 0.15
- Range: 0.05 to 0.40

- `lambda_expectations`
- Meaning: inflation expectation contribution.
- Default: 0.20
- Range: 0.10 to 0.40

## Wage Block
- `phi_productivity`
- Meaning: wage response to productivity growth.
- Default: 0.60
- Range: 0.30 to 0.80

- `phi_slack`
- Meaning: wage response to unemployment slack.
- Default: 0.35
- Range: 0.10 to 0.50

- `phi_expectations`
- Meaning: wage response to expected inflation.
- Default: 0.45
- Range: 0.20 to 0.70

## Household Demand Block
- `eta_household_good`
- Meaning: relative-price elasticity in household demand.
- Default: 0.60
- Range: 0.10 to 1.20

## Gate Thresholds
- `gdp_identity_residual_ratio_max`: 0.001
- `sector_residual_abs_max`: 0.000001

## Fiscal, External, and Monetary Block
- `tax_ratio`
- Meaning: baseline government revenue share of monthly nominal GDP.
- Default: 0.20
- Range: 0.15 to 0.30

- `spend_ratio`
- Meaning: baseline non-interest spending share of monthly nominal GDP.
- Default: 0.205
- Range: 0.15 to 0.30

- `automatic_stabilizer_strength`
- Meaning: extra spending response to unemployment slack.
- Default: 0.018
- Range: 0.005 to 0.040

- `foreign_debt_share`
- Meaning: share of debt stock exposed to FX valuation effects.
- Default: 0.25
- Range: 0.00 to 0.60

- `risk_premium`
- Meaning: baseline sovereign risk premium before reserve and debt stress adjustments.
- Default: 0.02
- Range: 0.00 to 0.15

- `psi1`
- Meaning: FX pressure sensitivity to BoP-to-GDP gap.
- Default: 0.50
- Range: 0.10 to 0.80

- `psi2`
- Meaning: FX pressure sensitivity to inflation differential.
- Default: 0.20
- Range: 0.05 to 0.30

- `psi3`
- Meaning: FX pressure sensitivity to risk premium.
- Default: 0.40
- Range: 0.10 to 0.60

- `investment_rate_sensitivity`
- Meaning: investment impulse response to real policy rate.
- Default: 0.50
- Range: 0.10 to 1.00

## Social and Political Block
- `m1`, `m2`, `m3`, `m4`
- Meaning: mobilization weights on grievance, network, elite split, fear.
- Default: 0.40, 0.30, 0.20, 0.30
- Range: 0.05 to 0.50

- `theta1` to `theta7`
- Meaning: unrest risk sensitivities to needs, inflation, unemployment, inequality, legitimacy, capacity, repression.
- Default baseline: 20.0, 40.0, 30.0, 0.2, 0.3, 0.2, 0.1
- Range: calibrated by normalized state scale.

- `l1` to `l5`
- Meaning: legitimacy update coefficients.
- Default baseline: 0.2, 0.2, 0.1, 0.1, 0.2
- Range: 0.01 to 0.30

- `z1` to `z4`
- Meaning: trust update coefficients.
- Default baseline: 0.01, 0.20, 0.05, 0.05
- Range: 0.01 to 0.30
