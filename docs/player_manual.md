# Country Simulation Player Manual

Version: v1
Last verified: 2026-04-25
Audience: Players (beginner to advanced)

## Table of Contents
1. What This Game Is
2. Your Core Objective
3. First 12 Ticks Quickstart
4. The Monthly Tick Loop
5. Economy and Supply Chain Basics
6. Labor, Income, and Class Dynamics
7. Buildings, Construction, and Regions
8. Commodities, Logistics, and Shortages
9. Diplomacy, Trade, FX, and External Stress
10. Laws, Interest Groups, and Traditions
11. Crises, Victory, and Failure
12. UI Guide: How to Read Every Sheet
13. Symptom -> Action Playbook
14. Glossary

## 1) What This Game Is
Country Simulation is a monthly, systems-heavy governance game.

You manage a state under economic, social, and geopolitical pressure. Your main challenge is not maximizing one number. It is balancing:
- growth and prices
- debt and reserves
- class support and social unrest
- internal capacity and external shocks

The game is designed around delayed effects. Good policy can take several ticks to show up. Bad policy can look fine for a while before the downside hits.

## 2) Your Core Objective
You win by surviving long enough while keeping political and macro stability inside safe ranges.

Primary strategic goals:
- Keep legitimacy stable or rising.
- Keep unrest under control.
- Keep debt dynamics and reserves sustainable.
- Prevent supply stress from becoming social crisis.

Common failure path:
1. persistent shortages or inflation
2. class support erosion
3. legitimacy decline + unrest rise
4. higher risk premium + reserve drain
5. crisis intensity and state failure risk spike

## 3) First 12 Ticks Quickstart
Use this as your opening script.

Tick 1-3:
- Open Executive Overview, Production and Supply Chains, Trade/FX/Reserves.
- Record baseline: unrest, legitimacy, debt, reserves, unmet demand, goods_shortage_pressure.
- Avoid large simultaneous policy swings.

Tick 4-6:
- If shortages are high: raise infrastructure_spend_share and keep food stabilization active.
- If inflation is high with weak output: avoid hard demand cuts first; target bottlenecks.
- If reserves are deteriorating: moderate import pressure and improve diplomacy posture.

Tick 7-9:
- Check class sheets and shortages-by-class impact.
- If workers/informal support falls quickly: reduce scarcity burden and protect service performance.
- Start one construction pipeline that improves long-run capacity (infrastructure or human capital).

Tick 10-12:
- Re-check debt trend and risk premium.
- If debt service pressure is rising fast: tune tax/spend mix gradually.
- Confirm regional stability: address high-unrest pockets before they become national drag.

## 4) The Monthly Tick Loop
The simulation runs in ordered stages every month. Read this as cause-and-effect, not isolated systems.

High-level flow:
1. Policy status and world diplomacy update.
2. Construction and expectations update.
3. Real economy computes output, inventories, shortages.
4. Logistics/market pressure updates and shortages propagate.
5. Prices, wages, unemployment update.
6. Fiscal, debt, reserves, FX, external stress update.
7. Laws, technology, military/security update.
8. Class dynamics and social legitimacy/unrest update.
9. Crisis and victory/failure checks update.

Player implication:
- You rarely fix problems in one tick.
- Most levers move intermediate variables first, then headline metrics later.

## 5) Economy and Supply Chain Basics
The economy has five macro sectors with linked pressures:
- agriculture
- energy
- manufacturing
- construction
- services

Core dynamics to watch:
- production vs demand
- inventory buffer
- unmet demand
- sector prices and shortage split

Interpretation:
- High unmet demand + low inventory means current supply is structurally too weak.
- Rising sector prices with stagnant output means constraint, not healthy demand growth.

What usually helps:
- Improve bottlenecks (infrastructure/logistics) before pure demand suppression.
- Use construction and industrial bias where capacity is constrained.
- Protect critical commodities first (food, fuel, power, medicine).

## 6) Labor, Income, and Class Dynamics
Employment and class support are central political channels.

Key mechanisms:
- unemployment and wage movement affect disposable pressure
- class income shares shift with policy, stress, and ownership structure
- each class has support and unrest values
- class conflict pressure feeds trust/legitimacy and instability

Classes tracked:
- workers
- professionals
- capitalists
- informal sector

Important pattern:
- Scarcity and inflation can reduce support before headline unrest fully spikes.
- Informal expansion can absorb labor but weakens tax/fiscal capacity.

## 7) Buildings, Construction, and Regions
Buildings are physical production units with condition, utilization, labor, and ownership.

What matters:
- condition degrades over time
- low maintenance and poor enabling inputs lower output quality
- building ownership distribution affects class income channels
- construction projects convert budget into future capacity with delay

Regional model:
- state and subregion outcomes differ
- regional inequality and service gaps feed national political risk

Practical rule:
- If one region repeatedly appears as high unrest + low service + high unemployment, treat it as a strategic stability front, not a local issue.

## 8) Commodities, Logistics, and Shortages
This is the deepest operational layer.

You have named commodities with:
- perishability
- strategic priority
- importability/exportability
- substitution relationships

Logistics adds:
- corridor capacity
- friction/spoilage effects
- congestion and chokepoints
- regional shortfall patterns even when national totals look acceptable

Social demand layer translates commodity access into:
- household, institutional, productive pressure
- class-specific scarcity burden
- adaptation channels (rationing and informal response)

Practical rule:
- Solve strategic commodity access and chokepoints first.
- National averages can hide local failures that become political crises.

## 9) Diplomacy, Trade, FX, and External Stress
External balance can quietly dominate your run.

Core channels:
- exports/imports -> current account -> reserves
- reserves and debt ratio -> risk premium -> borrowing cost
- FX pressure amplifies import-driven inflation
- diplomacy posture influences relation/trade access/sanction pressure

Warning signs:
- reserves trending down for many ticks
- rising risk premium despite stable policy rate
- persistent current account deficits plus high import dependency

Stabilization sequence:
1. slow reserve drain
2. avoid cost-push inflation loop
3. preserve trade access while reducing chokepoint sensitivity

## 10) Laws, Interest Groups, and Traditions
Formal policy intent is not the same as realized outcome.

Governance layer includes:
- law state (labor/property/media/welfare)
- interest-group power competition
- policy bandwidth constraints
- ideology/tradition influence shifts
- delayed consequence queue

Player implication:
- You cannot execute everything at once.
- Coherent policy bundles outperform frequent contradictory moves.

## 11) Crises, Victory, and Failure
Crisis intensity combines multiple stressors:
- supply pressure
- internal security load
- external stress
- inequality and regional strain

Failure is usually cumulative, not sudden randomness.

Recovery principle:
- stabilize essentials first (food/fuel/power/medicine, reserves, legitimacy floor)
- then rebuild medium-term capacity and social confidence

## 12) UI Guide: How to Read Every Sheet
Use sheets as a diagnosis stack.

Executive Overview:
- first stop each tick
- check risk direction, not just level

Production and Supply Chains:
- detect hard supply constraints and inventory depletion

Sector Prices and Shortages:
- find which block is driving inflation or output loss

Commodity Flows and Storage:
- verify strategic commodity coverage and storage-days risk

Logistics Chokepoints:
- identify corridor congestion and friction hotspots

Shortages and Class Impact:
- find who is absorbing scarcity pain before trust/unrest fully reacts

Trade/FX/Reserves:
- track reserve coverage and external stress trajectory

Class and Inequality Dynamics:
- check coalition stability and class conflict pressure

Trust/Legitimacy/Unrest:
- confirm whether social state is stabilizing or deteriorating

Events, Crises, and Victory:
- verify if you are in containment, recovery, or breakdown path

## 13) Symptom -> Action Playbook
Use this section during live play.

Symptom: Inflation rising while production is flat
- Check: sector shortages, logistics bottleneck, commodity deficits
- Try: targeted bottleneck relief, strategic commodity stabilization, avoid blunt demand cuts first

Symptom: Reserves falling and risk premium rising
- Check: current account, import dependence, sanctions/trade access
- Try: reduce import pressure, improve trade access, protect FX-sensitive supply chain nodes

Symptom: Trust falls faster than output
- Check: class scarcity burdens, needs gap, service performance
- Try: reduce household/informal scarcity burden, strengthen visible service delivery

Symptom: High national averages but sudden regional unrest spikes
- Check: State Explorer + regional sheets + building distribution
- Try: re-balance regional support/infrastructure and reduce local unemployment pressure

Symptom: Debt grows despite stable spending ratio
- Check: debt rate, risk premium, interest payment share, nominal growth
- Try: restore confidence channels (reserves, legitimacy, conflict pressure), then retune fiscal mix

## 14) Glossary
needs_gap:
- Composite social shortfall indicator feeding unrest pressure.

risk_premium:
- Extra borrowing cost from perceived macro/external risk.

goods_shortage_pressure:
- Composite supply stress index from unmet demand and constraints.

logistics_bottleneck_index:
- Friction/capacity stress in movement of goods.

class_conflict_pressure:
- Aggregate intensity of cross-class political-economic tension.

scarcity_burden_*:
- Class-specific exposure to commodity shortfall effects.

rationing_intensity:
- Strength of formal scarcity management response.

informal_market_response:
- Degree of extra-formal adaptation under shortages.

vitality (policy context):
- Persistence/strength of active policy effects over time.

---

## Appendix A: Recommended Learning Path
Session 1:
- Learn sheet reading and tick cadence.

Session 2:
- Practice shortage and logistics stabilization.

Session 3:
- Practice external-balance crisis recovery.

Session 4:
- Practice class coalition management under inflation and unemployment stress.

## Appendix B: Manual Scope Notes
This manual describes currently implemented systems in the codebase and UI.
Future expansions should append, not overwrite, this baseline.
