# Country Simulation (1990) - Economist and Sociologist Simulation-First Technical Specification

## 1) Modeling Philosophy and Scope

### 1.1 Purpose
- Build a deterministic macro-social simulator where economic accounting, institutional constraints, and social reproduction dynamics jointly determine outcomes.
- Treat gameplay as a policy interface over a validated model, not as a scripted narrative engine.

### 1.2 Scope
- Start date: January 1990 in a fictional world with realistic institutional analogs.
- Campaign horizon: 1990-2100.
- Resolution: monthly tick.
- Spatial unit: region/state.
- Modeling unit: aggregated sectors and cohorts (no individual-agent psychology in v0.1).
- Symmetry: player and AI use the same structural rules.

### 1.3 Non-Negotiable Design Principles
- Stock-flow consistency in all economic accounts.
- Social-state consistency in all cohort transitions.
- Explainability of every headline indicator via driver decomposition.
- Deterministic reproducibility under fixed seed.

## 2) Real-World Systems Represented (Economic and Social)

### 2.1 Economic Systems
- National accounts identities with expenditure-side and income-side GDP consistency.
- Sector balances: households, firms, government, financial sector, rest of world.
- Public finance, debt service, refinancing risk, and debt dynamics.
- Monetary transmission and inflation channels (cost-push, demand-pull, pass-through, expectations).
- Skill-segmented labor markets and wage formation.
- Input-output production with energy/logistics bottlenecks.
- Trade, exchange-rate regimes, external funding, and reserve adequacy.
- Technology diffusion and productivity growth.

### 2.2 Sociological Systems
- Class structure and stratification by income decile and labor-market position.
- Education, health, and intergenerational human-capital reproduction.
- Social mobility and opportunity access constraints.
- Household vulnerability and unmet-needs dynamics.
- Demographic transitions: births, deaths, internal migration, external migration, age structure.
- Cohort-level identity and ideology formation.
- Trust, legitimacy, and institutional compliance.
- Collective action, protest mobilization, and repression feedback loops.
- Media and information effects on expectations and polarization.
- Social cohesion/fragmentation interactions with state capacity.

## 3) Assumptions
- Monthly tick is the base dynamic interval for all state transitions.
- Prices and quantities are tracked in nominal and real terms.
- Cohorts are indexed by region, age band, education tier, income decile, and ideology cluster.
- Political behavior is outcome-responsive, not fully rational-optimizing.
- Supply constraints and logistics can bind before demand equilibrates.
- Commodity markets are region-segmented with a global benchmark reference price.
- Institutions alter parameter values (tax capacity, compliance, diffusion speed), not accounting identities.
- Random shocks are stochastic but seeded and deterministic for replay.

## 4) State Variables and Units

### 4.1 Notation
- $t$: month index.
- $r$: region.
- $s$: production sector.
- $g$: good.
- $h$: household cohort.
- $k$: skill segment.
- $d$: income decile.

### 4.2 Economic State Variables
- $Y_t$: real GDP (billions local currency, annualized-equivalent level).
- $Y^n_t$: nominal GDP (billions local currency, annualized-equivalent level).
- $P_{g,t}$: price of good $g$ (local currency per unit).
- $\pi_t$: inflation rate (% month over month).
- $e_t$: exchange rate (local currency per foreign numeraire).
- $i_t$: policy interest rate (% annualized).
- $Q_{s,t}$: sector output (units per month).
- $K_{s,t}$: effective capital stock (index).
- $L_{s,t}$: employed labor (workers).
- $Inv_{g,t}$: inventory stock (units).
- $B_t$: public debt stock (billions local currency).
- $Res_t$: reserves (months of imports equivalent).
- $CA_t$: current account (billions local currency per month).

### 4.3 Social and Institutional State Variables
- $Pop_{h,t}$: cohort population (persons).
- $u_{k,t}$: unemployment by skill segment (%).
- $w_{k,t}$: average wage by skill segment (local currency per worker per month).
- $Ineq_t$: inequality index (Gini-like 0-100 scale).
- $Mob_t$: social mobility index (0-100).
- $Trust_t$: interpersonal and institutional trust index (0-100).
- $Leg_t$: regime legitimacy index (0-100).
- $Cap_t$: state capacity index (0-100).
- $Pol_t$: polarization index (0-100).
- $Urest_t$: unrest risk index (0-100).
- $NeedGap_{h,t}$: unmet-needs ratio for cohort $h$ (0-1).

## 5) Core Equations and Behavioral Rules

### 5.0 Equation Format
- Each equation includes: variables and units, intuition, parameter ranges, failure modes.

### 5.1 Production with Input Constraints
$$
Q^{cap}_{s,t}=A_{s,t}K_{s,t}^{\alpha_s}L_{s,t}^{\beta_s}E_{s,t}^{\gamma_s}
$$
$$
Q_{s,t}=\min\left(Q^{cap}_{s,t},\min_g\frac{InputAvail_{g,s,t}}{a_{g,s,t}}\right)
$$
- Variables and units: $Q$ in units/month, $A$ TFP index, $a_{g,s,t}$ technical input coefficient.
- Intuition: output is bounded by both productive capacity and scarcest required input.
- Typical ranges: $\alpha_s$ 0.2-0.5, $\beta_s$ 0.3-0.7, $\gamma_s$ 0.05-0.3.
- Failure modes: weak input constraints remove supply-chain gameplay; overly strict coefficients create brittle collapse.

### 5.2 Price Update and Inflation Decomposition
$$
P_{g,t+1}=P_{g,t}\left(1+\lambda_c\Delta c_{g,t}+\lambda_d gap_{g,t}+\lambda_x\Delta e_t+\lambda_e\pi^e_t\right)
$$
$$
\pi_t=\sum_g\omega_g\frac{P_{g,t}-P_{g,t-1}}{P_{g,t-1}}
$$
- Variables and units: $P_{g,t}$ in local currency/unit, $gap_{g,t}$ excess-demand ratio.
- Intuition: inflation combines cost pressure, demand pressure, FX pass-through, and expectations.
- Typical ranges: $\lambda_c$ 0.2-0.6, $\lambda_d$ 0.1-0.5, $\lambda_x$ 0.05-0.4, $\lambda_e$ 0.1-0.4.
- Failure modes: excessive pass-through creates unstable inflation loops.

### 5.3 Household Consumption Demand
$$
C_{h,g,t}=\kappa_{h,g}\left(\frac{YDisp_{h,t}}{P_{g,t}}\right)\left(\frac{P_{g,t}}{P^{basket}_{h,t}}\right)^{-\eta_{h,g}}
$$
- Variables and units: $C_{h,g,t}$ units/month, $YDisp_{h,t}$ local currency/month.
- Intuition: real purchasing power sets baseline demand; relative prices induce substitution.
- Typical ranges: $\eta_{h,g}$ 0.1-1.2.
- Failure modes: high elasticities flatten scarcity and make welfare shocks too weak.

### 5.4 Wage and Unemployment Dynamics
$$
\Delta \ln(w_{k,t})=\phi_1\Delta \ln(prod_{k,t})-\phi_2(u_{k,t}-u^*_k)+\phi_3\pi^e_t
$$
$$
u_{k,t+1}=u_{k,t}+sep_{k,t}-match_{k,t}
$$
- Variables and units: $w_{k,t}$ local currency/worker/month, $u_{k,t}$ percent.
- Intuition: wage growth follows productivity and expectations, restrained by labor slack.
- Typical ranges: $\phi_1$ 0.3-0.8, $\phi_2$ 0.1-0.5, $\phi_3$ 0.2-0.7.
- Failure modes: weak slack term can cause wage-price spirals.

### 5.5 Government Budget Identity
$$
PB_t=T_t-G^{nonint}_t
$$
$$
Def_t=G^{nonint}_t+Int_t-T_t
$$
$$
Int_t=\frac{r^b_t B_{t-1}}{12}
$$
- Variables and units: all nominal local currency/month.
- Intuition: fiscal balance determines borrowing need before valuation effects.
- Typical ranges: primary balance between -8% and +6% of annual GDP.
- Failure modes: rigid spending plus weak compliance causes chronic debt acceleration.

### 5.6 Debt Evolution
$$
B_t=B_{t-1}+Def_t+ValFX_t
$$
$$
\frac{B_t}{Y^n_t}\approx\frac{B_{t-1}}{Y^n_{t-1}}(1+r^b_t-g^n_t)-pb_t
$$
- Variables and units: debt in nominal local currency, ratios in percent of GDP.
- Intuition: debt burden rises when interest-growth differential is positive and primary balance is weak.
- Typical ranges: vulnerability often rises quickly above 60-90% debt/GDP in weaker institutions.
- Failure modes: high FX share with depreciation can trigger nonlinear crisis.

### 5.7 External Balance and FX Pressure
$$
CA_t=X_t-M_t+NFI_t+Tr_t
$$
$$
BoP_t=CA_t+KA_t,\quad Res_t=Res_{t-1}+BoP_t
$$
$$
\Delta e_t=\psi_1\left(-\frac{BoP_t}{Y^n_t}\right)+\psi_2 infl\_diff_t+\psi_3 risk_t
$$
- Variables and units: flows in local currency/month, $e_t$ local currency per foreign numeraire.
- Intuition: external deficits and risk premia weaken currency unless financed.
- Typical ranges: $\psi_1$ 0.1-0.8, $\psi_2$ 0.05-0.3, $\psi_3$ 0.1-0.6.
- Failure modes: low reserves plus high pass-through creates self-reinforcing FX crisis.

### 5.8 Technology Diffusion and Productivity
$$
A_{s,t+1}=A_{s,t}+\rho_s RD_t+\chi_s Spill_t-\delta^A_s A_{s,t}
$$
$$
Adopt_{s,t+1}=Adopt_{s,t}+\kappa_s Readiness_t(Frontier_s-Adopt_{s,t})
$$
- Variables and units: $A$ productivity index, $Adopt$ share 0-1.
- Intuition: innovation raises frontier while adoption speed depends on readiness and institutions.
- Typical ranges: $\rho_s$ 0.001-0.02 monthly, $\kappa_s$ 0.01-0.08 monthly.
- Failure modes: very high adoption erases transition conflict and distributional tension.

### 5.9 Political Stability Risk Index
$$
Urest_t=clamp\left(0,100,\theta_0+\theta_1 NeedGap_t+\theta_2 \pi_t+\theta_3 u_t+\theta_4 Ineq_t-\theta_5 Leg_t-\theta_6 Cap_t+\theta_7 Repress_t\right)
$$
- Variables and units: normalized indices 0-100.
- Intuition: material stress and inequality raise instability, while legitimacy and capacity dampen it.
- Typical ranges: standardized coefficients 0.1-0.5.
- Failure modes: weak damping yields permanent unrest; strong damping makes politics inert.

### 5.10 Social Unrest and Mobilization Function
$$
Mobil_t=\mu_1 Griev_t+\mu_2 Network_t+\mu_3 EliteSplit_t-\mu_4 Fear_t
$$
$$
ProtestProb_t=\sigma(Mobil_t-\tau)
$$
- Variables and units: index inputs 0-100, probability in 0-1.
- Intuition: collective action requires grievance plus coordination capacity, moderated by repression fear.
- Typical ranges: $\mu_i$ 0.05-0.5, threshold $\tau$ 30-70.
- Failure modes: low threshold creates protest spam; high threshold suppresses all contention.

### 5.11 Legitimacy and Trust Update
$$
Leg_{t+1}=Leg_t+\ell_1 ServicePerf_t+\ell_2 RealIncome_t-\ell_3 Corr_t-\ell_4 RepressExcess_t+\ell_5 Fairness_t
$$
$$
Trust_{t+1}=Trust_t+\zeta_1 Leg_t+\zeta_2 InfoQuality_t-\zeta_3 Polar_t-\zeta_4 InequalityShock_t
$$
- Variables and units: all index changes on 0-100 scale.
- Intuition: legitimacy and trust respond to performance, fairness, information quality, and coercion.
- Typical ranges: coefficients 0.01-0.2 per month.
- Failure modes: overly persistent trust can make social shocks irrelevant.

### 5.12 Social Mobility Transition Function
$$
Pr(d\rightarrow d+1)_t=\sigma\left(\beta_0+\beta_1 EduAccess_t+\beta_2 Health_t+\beta_3 FormalJobs_t-\beta_4 Closure_t-\beta_5 Discrimination_t\right)
$$
$$
Pop_{d,t+1}=Pop_{d,t}+Inflow_{d,t}-Outflow_{d,t}
$$
- Variables and units: transition probability in 0-1; populations in persons.
- Intuition: upward mobility depends on access to capability-building institutions and labor opportunities.
- Typical ranges: $\beta_i$ 0.05-0.5 after normalization.
- Failure modes: excessively high mobility destroys class persistence; low mobility locks permanent stratification.

## 6) Tick-Order Execution Graph

1. Apply policy package, institutional changes, and exogenous shocks.
2. Update expectations, risk premia, and information climate.
3. Compute sector capacities and input requirements.
4. Allocate constrained intermediates, logistics, and energy.
5. Realize output, shortages, inventories, and firm accounts.
6. Clear internal and external markets; update trade and FX.
7. Update prices and inflation decomposition.
8. Update employment, wages, household disposable income, and consumption.
9. Update demographic transitions, unmet needs, and social reproduction states.
10. Execute fiscal and debt accounting, then banking and credit states.
11. Update technology, human capital, and productivity.
12. Update trust, legitimacy, polarization, mobilization, and unrest risk.
13. Trigger endogenous crisis and event modules.
14. Run consistency checks and write causality logs.
15. Commit clean state for $t+1$.

Execution constraints:
- Stage-isolated reads and writes.
- Deterministic random stream keyed by tick and event ID.
- Tick abort with diagnostics if accounting or social-state consistency fails.

## 7) Calibration Targets
- Inflation annualized normal band: 1%-12%.
- Unemployment: 3%-18% depending on cycle and structure.
- Real GDP growth annual: -8% to +10%.
- Debt burden warning band: context-specific, baseline alert near 70% debt/GDP for vulnerable states.
- Inequality index: 25-55 normal political tolerance range, >60 high instability risk.
- Trust index: 40-70 stable governance band, <30 legitimacy fragility.
- Unrest index: 0-30 stable, 31-60 contentious, 61-100 acute crisis.

## 8) Validation and Stress Testing

### 8.1 Accounting Identity Checks
- GDP expenditure-income discrepancy <0.1% GDP per tick.
- Sector financial balances sum to zero within tolerance.
- Debt and reserves reconcile with flow updates.

### 8.2 Social Stock-Transition Checks
- Cohort populations are non-negative.
- Birth-death-migration transitions preserve total population accounting.
- Identity-share vectors sum to 1.0 within tolerance.
- Mobility transition matrices are row-stochastic.

### 8.3 Stability Tests
- 240-month baseline run without numeric explosion or sign-flip oscillation.
- Parameter perturbation +/-10% preserves plausible directional responses.

### 8.4 Long-Run Soak Tests
- 1000+ ticks with periodic shocks.
- Pass criteria: no NaN/infinite states, bounded key ratios, complete trace logs.

### 8.5 Counterfactual Sensitivity Tests
- One-policy deltas under fixed seed for rates, taxes, transfers, tariffs, and media policy.
- Expected result: interpretable comparative statics.

### 8.6 Distributional Incidence Tests
- For each policy shock, compute gain/loss by decile, region, skill band, and ideology cluster.
- Fail if aggregate gains hide persistent severe losses in any protected cohort without policy visibility.

### 8.7 Required Stress Scenarios
- Sanctions shock.
- Energy shock.
- Sudden stop in capital flows.
- Drought shock.
- Banking panic.
- Disinformation wave.
- Identity polarization shock.

## 9) Game Layer Mapping (Player-Facing)

### 9.1 Decision Surfaces
- Fiscal policy, social transfers, subsidy targeting, and public investment mix.
- Monetary and macroprudential controls.
- Industrial policy and strategic stockpiles.
- External sector controls: tariffs, capital controls, treaty stance.
- Institutional reforms: anti-corruption, administrative capacity, media regulation, social integration policy.

### 9.2 Spreadsheet Sheets
- National Accounts.
- Production and Supply Chains.
- Prices and Inflation Drivers.
- Labor and Income Distribution.
- Public Finance and Debt.
- Trade, FX, and Reserves.
- Demography and Social Mobility.
- Trust, Legitimacy, Polarization, Unrest.
- Events and Causality Log.

### 9.3 Events and AI
- Events are mostly endogenous to model thresholds and trend breaks.
- AI uses same structural model with different objective weights.
- Difficulty scales via strategic quality and shock profile, not hidden bonuses.

## 10) MVP and Out-of-Scope

### 10.1 MVP
- 1 fully playable country with 10 regions.
- 20 goods, 12 industries, 8 interest groups.
- Cohort model with deciles, education tiers, and ideology clusters.
- Full monthly deterministic pipeline with driver decomposition.

### 10.2 Out-of-Scope
- Tactical warfare.
- Multiplayer.
- Full espionage operations.
- City-level microsimulation.

## 11) Locked Decisions
- Campaign horizon: 1990-2100.
- Market structure: region-segmented commodity markets with a global benchmark reference.
- UI transparency: expose decompositions and coefficients, not engine implementation internals.
- Exchange-rate regime at start: managed float; peg options unlock later.
- Launch scope: one highly polished playable country first.
