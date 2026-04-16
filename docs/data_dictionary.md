# Data Dictionary (v1 - Phase 2 Economic Core)

## Purpose
Define canonical names, units, and data types for the accounting core.

## Conventions
- Prefix `flow_` for monthly flows.
- Prefix `stock_` for state stocks.
- Prefix `idx_` for normalized indices.
- Currency unit: local currency (LCU).

## National Accounts Fields
- `flow_consumption`: household consumption flow (LCU per month).
- `flow_investment`: gross capital formation flow (LCU per month).
- `flow_government_spending`: government final consumption and investment (LCU per month).
- `flow_exports`: export value (LCU per month).
- `flow_imports`: import value (LCU per month).
- `flow_wages`: labor compensation (LCU per month).
- `flow_profits`: operating surplus and mixed income (LCU per month).
- `flow_taxes_production`: domestic production taxes (LCU per month).
- `flow_taxes_imports`: import taxes and duties (LCU per month).
- `flow_subsidies`: government subsidy payments (LCU per month).

## Derived Core Metrics
- `flow_gdp_expenditure`: GDP from expenditure identity (LCU per month).
- `flow_gdp_income`: GDP from income identity (LCU per month).
- `ratio_gdp_identity_residual`: absolute accounting residual ratio (unitless).

## Sector Balance Fields
- `flow_net_lending_households`: net lending/borrowing of households (LCU per month).
- `flow_net_lending_firms`: net lending/borrowing of firms (LCU per month).
- `flow_net_lending_government`: net lending/borrowing of government (LCU per month).
- `flow_net_lending_financial_sector`: net lending/borrowing of financial sector (LCU per month).
- `flow_net_lending_rest_of_world`: net lending/borrowing of rest of world (LCU per month).
- `flow_sector_residual`: aggregate residual across sectors; target near zero (LCU per month).

## Fiscal and External Fields (Phase 5)
- `flow_primary_balance`: fiscal primary balance (LCU per month).
- `flow_interest_payment`: sovereign interest outflow (LCU per month).
- `flow_fiscal_deficit`: total fiscal deficit (LCU per month).
- `stock_public_debt`: sovereign debt stock (LCU).
- `ratio_debt_to_gdp`: debt burden relative to nominal GDP (unitless).
- `flow_current_account`: current account balance (LCU per month).
- `flow_balance_of_payments`: BoP aggregate flow (LCU per month).
- `stock_reserves`: foreign reserve stock (LCU or import-month equivalent).
- `idx_fx_pressure`: depreciation pressure proxy (unitless index).

## Social-State Fields (Phase 6)
- `stock_population_cohort`: cohort population stock (persons).
- `flow_births`: births in period (persons per month).
- `flow_deaths`: deaths in period (persons per month).
- `flow_migration_net`: net migration (persons per month).
- `idx_legitimacy`: legitimacy index in [0,100].
- `idx_trust`: trust index in [0,100].
- `idx_unrest`: unrest risk index in [0,100].
- `ratio_mobility_up_prob`: upward mobility probability in [0,1].

## Gate Thresholds (Phase 2)
- GDP identity residual ratio tolerance: `<= 0.001`.
- Sector residual absolute tolerance: default `<= 1e-6`, scenario-adjustable.
