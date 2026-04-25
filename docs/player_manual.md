# Country Simulation Player Manual

Version: v2
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
10. The Policy System: Bandwidth, Vitality, and the Graveyard
11. Ideological Traditions
12. Laws, Interest Groups, and Unintended Consequences
13. Crises, Victory, and Failure
14. UI Guide: How to Read Every Sheet
15. Symptom -> Action Playbook
16. Glossary

---

## 1) What This Game Is

Country Simulation is a monthly, systems-heavy governance game. You manage a state under simultaneous economic, social, and geopolitical pressure. Your challenge is not maximizing a single number. It is maintaining a dynamic balance across four interconnected domains:

- **Growth and prices**: Output must stay ahead of demand or you will face shortages and inflation. Inflation that outstrips wages shrinks real incomes and undermines class support.
- **Debt and reserves**: The state borrows to fill fiscal gaps. Rising debt raises the risk premium, which raises borrowing costs, which widens the deficit. Falling reserves signal external vulnerability and push the risk premium higher independently of the debt level.
- **Class support and social unrest**: Four social classes each respond to material conditions (wages, scarcity, service quality) and political signals (repression, corruption, information quality). Losing a class coalition erodes legitimacy. Losing legitimacy reduces your bandwidth to govern.
- **Internal capacity and external shocks**: Your production base, logistics network, and building stock determine how resilient you are to commodity shortfalls, trade disruptions, or global price shocks.

The game runs on delayed effects. A policy enacted today may not show up in headline indicators for 6–24 ticks. The unintended consequences of major reforms are hidden until they manifest. Bad policy can look fine for a long time. Good crisis management often looks like nothing is happening.

---

## 2) Your Core Objective

You win by surviving long enough while keeping political and macro stability inside safe ranges.

**Primary strategic goals:**
- Keep legitimacy stable or rising.
- Keep unrest below the threshold where protests become cascading events.
- Keep the debt-to-GDP ratio from trending upward without a credible stabilization plan.
- Keep reserve coverage above 3 months of import value.
- Prevent supply stress from becoming a social crisis.

**The common failure path:**
1. Persistent shortages or inflation erode class support.
2. Legitimacy declines; trust falls faster than output recovers.
3. Unrest rises; crisis intensity index climbs.
4. Rising risk premium and reserve drain tighten fiscal space.
5. Spending cuts or tax increases deepen scarcity, closing the loop.

**Winning is not about growth**. A run that holds legitimacy at 55, unrest at 25, and reserves at 4 months import cover for 48 ticks is a successful run even if GDP growth is flat. A run with 6% growth but rising unrest and declining reserves is on a failure path.

---

## 3) First 12 Ticks Quickstart

Use this as your opening script. Internalize the diagnosis steps before you touch any levers.

**Tick 1–3: Baseline diagnosis**
- Open Executive Overview. Record: unrest level, legitimacy level, reserve cover, risk premium, debt-to-GDP direction.
- Open Production and Supply Chains. Record: which sectors have unmet demand > 0, which have inventory < 10% of production.
- Open Trade/FX/Reserves. Record: current account sign, reserve cover (reserves / monthly imports). If cover < 3, treat as red flag.
- Open Commodities. Note which strategic commodities (food, fuel, power, medicine) have coverage ratio < 0.8.
- Do not make large policy moves yet. Changing two or more major levers simultaneously makes it impossible to read the causal chain.

**Tick 4–6: First targeted responses**
- If goods_shortage_pressure > 0.30: your logistics or production is structurally weak. Raise infrastructure_spend_share first. Do not cut demand — that suppresses output, not just prices.
- If inflation is high but output is flat: this is supply-side constraint, not demand overheating. Target sector bottlenecks. Raising the policy rate in this environment will increase borrowing costs without fixing the output gap.
- If reserves have been falling for 3+ ticks: moderate import_shock_factor (reduce it toward 0.9) and examine whether your trade access is being compressed by diplomacy posture.

**Tick 7–9: Social and class monitoring**
- Open Shortages and Class Impact. Check scarcity_burden_workers and scarcity_burden_informal. These lead headline unrest by 2–4 ticks. If they are above 0.45, begin scarcity relief measures immediately.
- Check service_perf on the Class and Inequality sheet. If it has dropped two or more points from your tick-1 baseline, institutional delivery is degrading; hospitals and universities need maintenance spending.
- Begin one construction project targeting capacity bottlenecks (road_rail_hub if logistics is congested; farm or factory if sector output is the binding constraint).

**Tick 10–12: Fiscal and stability review**
- Recalculate debt trajectory: is the deficit stable, growing, or shrinking? If debt_service_pressure > 0.04 (4% of GDP), you are in danger of a debt spiral.
- Check risk_premium direction. If it is rising with stable spending, it is being driven by reserve depletion or external stress — fix the balance-of-payments before cutting spending.
- Scan regional sheets for any subregion with unrest > 60. Regional crises that go unaddressed for 6+ ticks become national drag on legitimacy.

---

## 4) The Monthly Tick Loop

The simulation runs in fixed stage order every month. Outputs from each stage feed into the next. Understanding this chain tells you why your lever moves take time to show up.

**Stage 1: apply_policies**
Active policies are evaluated. Each policy has a formal value (what the decree says) and a realized value (what actually happens on the ground). The gap between them is determined by bureaucratic reach, legitimacy, elite capture, and policy vitality. Policies that have been underfunded lose vitality and drift toward the beneficiary class of their family (see Section 10).

**Stage 2: update_expectations**
Inflation expectations are updated. They blend toward a 0.8%/month target but are pushed upward by cost pressures, FX depreciation, and high unemployment. Expectations feed back into wages and prices next tick. A sustained expectations drift above 2% monthly is a warning sign.

**Stage 3: compute_real_economy**
Building output is computed using: `output = capacity × utilization × condition × quality_modifier`. Sector totals are aggregated. Inventory is updated: `inventory_next = inventory_prev + production - demand`. Unmet demand is recorded where `production + inventory_prev < demand`.

**Stage 4: update_logistics_and_market**
The logistics network runs inter-region redistribution. Surplus regions ship to deficit regions along transport corridors. Each corridor has a capacity limit, a friction rate, and a congestion ratio. Goods in transit suffer spoilage based on `friction × perishability × 5.0` (capped at 40% loss). Congestion triggers when utilization exceeds 75% of corridor capacity. Social demand signals (scarcity burdens, access indices) are computed from regional commodity coverage.

**Stage 5: update_prices_labor**
Prices are updated by four weighted channels: cost push (weight 0.28), demand gap (0.16), FX pressure (0.08), and expectations (0.10). Wages are updated by a modified Phillips curve: productivity growth lifts wages, unemployment slack compresses them, and expected inflation anchors them. Unemployment is updated by separations minus matches, with a floor at 75% of the natural rate.

**Stage 6: update_public_external**
Fiscal position: revenue = GDP × tax_ratio adjusted for slack; spending includes automatic stabilizers that expand when unemployment rises. Interest payments are computed monthly: `debt × annual_rate / 12`. Debt changes by the total fiscal deficit plus FX valuation effects on foreign-currency debt.

External sector: current account = exports - imports + net factor income + transfers. Balance of payments adds the capital account. Reserves update by the BOP flow. Risk premium rises when reserve coverage falls below 3 months of imports or when debt-to-GDP exceeds 75%.

**Stage 7: update_governance_laws**
Policy vitalities update. Credibility updates based on policy collapses and failed law proposals. Tradition influence shifts based on crisis signals. The consequence queue is checked — matured unintended consequences from past policy enactments are applied.

**Stage 8: update_class_dynamics and update_social_political**
Class support and income shares are updated. Legitimacy changes based on service performance, real income, corruption, repression, and fairness. Trust changes based on legitimacy, information quality, polarization, and inequality shocks. Unrest risk is computed from: needs_gap, inflation, unemployment, inequality, legitimacy (dampening), state capacity (dampening), and repression.

**Stage 9: crisis and victory/failure checks**
Crisis intensity index is computed. Victory conditions are checked. State failure risk is assessed.

**Player implication:**
- A policy enacted in Stage 1 affects production in Stage 3, prices in Stage 5, fiscal position in Stage 6, and trust/legitimacy in Stage 8 — all within the same tick. But the full cascade (e.g., reduced scarcity burden → improved class support → stabilized legitimacy) takes 3–6 ticks to stabilize.
- Unintended consequences from signature laws are hidden for 6–24 ticks (reduced by information quality). You will not see them coming unless you have invested in a statistical bureau or equivalent governance infrastructure.

---

## 5) Economy and Supply Chain Basics

### Five Macro Sectors

The economy has five sectors. Each has production, capacity, utilization, and demand.

| Sector | Key outputs | Key inputs | Notes |
|---|---|---|---|
| Agriculture | staple_food, fertilizer | water, land, fuel | High perishability; price floors can stabilize but add fiscal cost |
| Energy | fuel, power, coal | crude_oil, iron, infrastructure | Power has zero storability (used or lost each tick) |
| Manufacturing | steel, cement, consumer_goods, machine_parts | iron_ore, coal, fuel, power | Machine parts are required by all sectors to maintain output |
| Construction | build_capacity | steel, cement, stone_aggregate | Converts budget into future capacity with delay |
| Services | health_index, research_points, trade_access | medicine, power, skilled labor | Service degradation is a leading indicator of legitimacy decline |

### Production Formula

For each building: `output = capacity × utilization × condition × quality_modifier`

Where:
- **capacity**: base capacity × level_scale^(level-1)
- **utilization**: adjusts toward sector demand signal each tick; bounded 0.3–0.95
- **condition**: starts at 0.25–0.98 based on infrastructure; degrades each tick; restored by maintenance spending
- **quality_modifier**: scales with human_capital and falls below the building's skill_threshold

A building at condition 0.5 and quality 0.7 operates at 35% of its theoretical maximum output even at full utilization.

### Interpreting Supply Signals

- **unmet_demand > 0**: production + inventories are failing to cover demand this tick. If sustained, inventories are being depleted.
- **inventory < 20% of monthly production**: you are one shock away from a visible shortage. Inventories below 10% mean a supply crisis is already underway.
- **Rising sector prices with flat output**: classic supply constraint. Adding demand stimulus here will only accelerate price increases. Target the input or logistics bottleneck instead.
- **Falling sector prices with rising unmet demand**: paradoxical — usually means informal substitution is replacing formal production, or classification effects in aggregation. Check commodity-level coverage ratios directly.

### What Usually Helps

1. Improve infrastructure and road/rail hubs before cutting demand. Transport connectivity feeds directly into building viability scores and logistics corridor capacity.
2. Use construction spend and industrial bias to expand capacity where the bottleneck is structural (not just a temporary shock).
3. Protect food, fuel, power, and medicine coverage above all others. Their strategic priority is 4–5, meaning shortages directly trigger political crisis channels.
4. Sector interdependencies matter: a fuel shortage will cut manufacturing output (fuel is a production input), which will reduce consumer goods availability, which will raise household scarcity pressure. Follow the input chain.

---

## 6) Labor, Income, and Class Dynamics

### The Labor Market

Wages are determined by a modified Phillips curve:
```
wage_growth = 0.6 × productivity_growth - 0.35 × (unemployment - natural_unemployment) + 0.18 × expected_inflation
```

- Wages are capped at 1% growth per tick to prevent unrealistic acceleration.
- Wages cannot fall more than 2–5% per tick (floor adjusts with labor market panic signals).
- Natural unemployment is approximately 6%. Above that, slack compresses wages. Below it, wages accelerate.

### Four Classes

| Class | Income source | Primary scarcity exposure | Policy sensitivity |
|---|---|---|---|
| Workers | Wage income from employed buildings | Household pressure (food, fuel, power, medicine) | Minimum wage, labor law, public spending, employment levels |
| Professionals | Institutional salaries; building_owner_output_state share | Institutional pressure (healthcare, power, fuel) | Public sector quality, corruption, info quality |
| Capitalists | Building profits; building_owner_output_capitalist share | Productive pressure (machine_parts, materials, transport) | Tax rate, property rights, trade access, interest rates |
| Informal | Informal market earnings; informal_market_response channels | Highest household exposure; lowest medicine access | Rationing, informal suppression, welfare programs |

**Class support** for each class updates based on:
- Real wage growth (workers, professionals)
- Scarcity burden specific to that class
- Service performance (all classes, but especially professionals)
- Repression level (suppresses workers and informal most)
- Tax changes (capitalists are sensitive to tax_ratio increases)
- Corruption (erodes professional trust significantly)

**Class conflict pressure** rises when income share gaps widen or when one class perceives another gaining at its expense. High class_conflict_pressure feeds directly into unrest and legitimacy decline.

### Informal Economy Dynamics

The informal sector expands under two conditions:
1. Formal employment is insufficient (high unemployment pushes workers into informal channels).
2. Formal commodity availability is low (households substitute informal_goods for consumer_goods).

Informal expansion is captured by informal_market_response (0–1). This reduces measured scarcity burden in the short term but has fiscal costs: informal workers do not contribute to tax revenue, and the indirect tax base shrinks. Policies like trade_liberalization can inadvertently boost informal_income_share by creating import competition that displaces formal workers.

### Income Share Channels

Building ownership matters beyond production. When a building produces output, its owner class captures a portion of the income:
- **capitalist-owned buildings** increase capitalist income share.
- **state-owned buildings** route income through the public budget.
- **cooperative-owned buildings** route income to worker_income_share.
- **informal-owned buildings** (market_bazaar, some farms) route to informal_income_share.

Nationalization, land redistribution, or cooperative enterprise programs change ownership distribution and thus change which class benefits from growth. These are structural class dynamic moves, not just production tweaks.

---

## 7) Buildings, Construction, and Regions

### Building Types

| Building | Sector | Key outputs | Skill threshold | Notes |
|---|---|---|---|---|
| farm | agriculture | food_tonnage | 0.30 | Requires fertility ≥ 0.25 and water ≥ 0.20 |
| irrigation_district | agriculture | yield_multiplier | 0.35 | Boosts adjacent farm output; requires water ≥ 0.35 |
| coal_power_plant | energy | mw_capacity | 0.45 | Requires coal ≥ 0.30 and grid ≥ 0.25 |
| oil_gas_well | energy | energy_units | 0.50 | Requires oil or gas endowment ≥ 0.40 |
| factory | manufacturing | goods_units | 0.45 | Core consumer goods and intermediate producer |
| steel_mill | manufacturing | intermediate_goods | 0.50 | Requires iron ≥ 0.35 and coal ≥ 0.25 |
| construction_yard | construction | build_capacity | 0.38 | Needed to execute construction projects |
| hospital | services | health_index | 0.60 | State-owned only; drives medicine access and service_perf |
| university | services | research_points | 0.65 | Drives human capital accumulation over time |
| market_bazaar | services | trade_access | 0.20 | Informal and cooperative ownership; low skill barrier |
| road_rail_hub | construction | transport friction modifier | 0.35 | Reduces logistics friction in adjacent corridors |
| military_barracks | services | security capacity | 0.35 | Required for repression capacity and crisis containment |

### Condition Degradation and Maintenance

Every building loses condition each tick without maintenance. The degradation rate is fixed per archetype (0.004–0.011 condition points per tick). Maintenance spending partially offsets this. The recovery formula is:
```
condition_delta = upkeep_recovery × capacity_modifier × legitimacy_modifier  (if funded)
condition_delta = -degradation_rate / (capacity_modifier × legitimacy_modifier)  (if unfunded)
```

At zero maintenance, a building that starts at condition 0.90 will reach condition 0.50 within roughly 40–100 ticks depending on archetype. Below condition 0.40, output falls dramatically.

**Practical rule:** Budget for maintenance before budget for new construction. A network of well-maintained buildings at condition 0.75 outperforms an expanded network of neglected buildings at condition 0.45.

### Regional Archetypes

Each subregion is seeded with buildings appropriate to its archetype:

| Archetype | Strong sectors | Notes |
|---|---|---|
| agro_periphery | agriculture (2×), construction (0.6×) | Food production base; low industry |
| resource_core | energy (2.5×), manufacturing (0.8×) | Oil/gas or coal-heavy; prone to Dutch disease |
| industrial_belt | manufacturing (2.5×), energy (1.2×) | Highest unmet machine_parts and power demand |
| service_metro | services (2.5×), construction (0.8×) | Political center; high professional class share |
| fragile_frontier | agriculture (1.2×), all others weak | Low infrastructure; prone to food crises; high security cost |

### Construction Pipeline

New buildings require:
1. Sufficient construction_yard capacity in the region.
2. Construction budget allocation.
3. A delay period (build_cost ranges from 0.006 to 0.024 × national budget share per level per tick).

A road_rail_hub (build_cost 0.018) in a mid-size region will take several ticks to complete and will then reduce logistics friction in adjacent corridors. Plan construction for problems you anticipate in 10–20 ticks, not problems you already have today.

### Regional Inequality

Regional inequality (regional_inequality_index) rises when:
- Some regions have high service_perf and others do not.
- Building concentration and building ownership is lopsided.
- Transport corridors between high- and low-service regions are congested.

Sustained regional inequality feeds both national class_conflict_pressure and legitimacy decline. A region that is visibly lagging despite national-level stability metrics is a political liability.

---

## 8) Commodities, Logistics, and Shortages

### Full Commodity Catalog

| Commodity | Category | Strategic priority | Perishability | Importability | Key substitutes |
|---|---|---|---|---|---|
| staple_food | food | 5 | 4%/tick | 0.70 | imported_food |
| imported_food | food | 4 | 3%/tick | 1.00 | staple_food |
| fertilizer | food | 3 | 1%/tick | 0.80 | — |
| fuel | energy | 5 | 0.5%/tick | 0.85 | charcoal |
| power | energy | 5 | 100%/tick | 0.20 | diesel_power |
| diesel_power | energy | 3 | 100%/tick | 0.30 | power |
| coal | energy | 3 | 0.2%/tick | 0.65 | charcoal |
| charcoal | energy | 1 | 0.8%/tick | 0.30 | coal, fuel |
| crude_oil | material | 4 | 0.1%/tick | 0.75 | — |
| iron_ore | material | 3 | 0.1%/tick | 0.70 | — |
| stone_aggregate | material | 2 | 0%/tick | 0.35 | — |
| steel | industrial | 4 | 0.2%/tick | 0.75 | — |
| cement | industrial | 4 | 1%/tick | 0.55 | — |
| machine_parts | industrial | 4 | 0.3%/tick | 0.80 | — |
| consumer_goods | social | 3 | 1.2%/tick | 0.85 | informal_goods |
| informal_goods | social | 1 | 1.5%/tick | 0.00 | consumer_goods |
| medicine | social | 5 | 2%/tick | 0.90 | — |

**Strategic commodities** (priority ≥ 4): staple_food, imported_food, fuel, power, crude_oil, steel, cement, machine_parts, medicine. Shortages in these trigger direct political consequence channels.

**Importability** indicates how easily a shortage can be covered via imports. Power (0.20) is effectively non-importable — you must produce it domestically. Informal_goods (0.00) cannot be imported at all. Medicine (0.90) is the easiest strategic commodity to source internationally, but it is expensive and depends on foreign exchange availability.

**Perishability** is a per-tick stock loss rate. Power and diesel_power are fully perishable (1.0) — any stock not consumed is lost. Staple food loses 4% per tick. Do not over-import perishables — excess stock decays and does not cushion future shortfalls.

### How Commodity Coverage Works

The social demand system computes a coverage ratio per commodity: `stock / demand`. A ratio of 1.0 means demand is exactly met. Below 0.8, scarcity pressure starts rising. Below 0.5, scarcity burden signals become acute.

Composite access indices:
- `food_access = 0.75 × staple_food_coverage + 0.25 × imported_food_coverage`
- `power_access = 0.85 × power_coverage + 0.15 × diesel_power_coverage`
- `consumer_access = 0.75 × consumer_goods_coverage + 0.25 × informal_goods_coverage`

### Three Demand Blocs

| Bloc | Primary commodities | Who bears the burden |
|---|---|---|
| Household | food (30%), fuel (18%), power (17%), medicine (17%), consumer goods (10%), transport (8%) | Workers and informal carry most; rationing and informal response can partially offset |
| Institutional | medicine (30%), power (25%), fuel (20%), transport (15%), service_perf (10%) | Professionals bear most; affects health and education delivery |
| Productive | machine_parts (30%), materials (24%), power (18%), fuel (16%), transport (12%) | Capitalists bear most; affects manufacturing output directly |

### Adaptation Channels

When household pressure rises, two adaptation mechanisms activate:

**Rationing intensity** = `household_pressure × (0.35 + state_capacity × 0.50)`
- State-organized rationing reduces measured household pressure by ~20%.
- Requires state capacity. Low-capacity states cannot ration effectively.
- Has legitimacy costs — populations often resent rationing, but it is better than unchecked scarcity.

**Informal market response** = `household_pressure × (0.45 + unemployment × 0.90) × (1 - state_capacity × 0.45)`
- Black markets and informal distribution expand under scarcity.
- More pronounced when unemployment is high (more people seeking informal income).
- Reduces measured pressure by ~18% but erodes formal trade tax base and feeds informal class income share.

Adapted household pressure after both channels feeds scarcity burdens:
- `scarcity_burden_workers = adapted_household × 0.65 + institutional × 0.20`
- `scarcity_burden_informal = adapted_household × 0.72 + unemployment × 0.18 + (1 - medicine_access) × 0.10`

### Logistics Network

The logistics network connects regions via transport corridors. Each corridor has:
- **capacity**: maximum throughput per tick
- **friction**: 0–1 transit cost/spoilage multiplier
- **congestion_ratio**: 0 below 75% utilization; reaches 1.0 at 100% utilization

Spoilage in transit: `loss_rate = friction × perishability × 5.0` (capped at 40%)

A corridor with friction 0.30 carrying staple_food (perishability 0.04) loses `0.30 × 0.04 × 5.0 = 6%` of each shipment. The same corridor carrying medicine (perishability 0.02) loses 3%.

**Chokepoints** form when demand between adjacent regions exceeds corridor capacity. When congestion_ratio > 0.70, the corridor is flagged as a chokepoint and its effective throughput is constrained. The fix: road_rail_hub construction reduces friction; increasing infrastructure_spend_share improves corridor capacity over time.

**National averages hide local failures.** A region with high food_access nationally can have a deficit subregion if the connecting corridor is congested or if the surplus region is too far away. Always check the Logistics Chokepoints sheet when regional unrest spikes without a national shortage signal.

---

## 9) Diplomacy, Trade, FX, and External Stress

### External Balance Mechanics

Current account = exports - imports + net_factor_income + transfers

Balance of payments = current_account + capital_account

Reserves = reserves_prev + balance_of_payments

If BOP is positive, reserves grow. If negative, reserves drain.

**Reserve coverage** = reserves / monthly_imports. The critical threshold is 3 months. Below 3, risk premium starts rising. Below 1, you are in a balance-of-payments crisis.

### Risk Premium Dynamics

Risk premium rises when:
- Reserve coverage falls below 3 months of imports: `+0.02 per unit below 3`
- Debt-to-GDP exceeds 75%: `+0.03 per unit above 0.75`

Risk premium feeds back into the effective debt rate:
```
debt_rate_next = 0.75 × current_rate + 0.25 × (policy_rate + risk_premium)
```

A risk premium that rises from 0.02 to 0.06 adds roughly 1 percentage point to the effective borrowing rate, which increases annual interest payments by 1% of debt stock. On a high-debt state, that is a significant fiscal shock.

### FX Pressure

FX depreciation pressure is driven by three channels:
- Negative BOP (capital outflows and current account deficits push FX down)
- Inflation differential above the baseline
- Risk premium (capital flight)

`fx_pressure = 0.5 × (-bop_to_gdp) + 0.2 × inflation_differential + 0.4 × risk_premium`

FX depreciation (positive fx_delta) affects imports:
- Higher import costs feed cost_delta, which feeds into sector prices.
- Foreign-currency debt faces a valuation effect: `debt_increase = debt × foreign_share × fx_delta × 0.08`

A 5% monthly depreciation on a state with 25% foreign-currency debt and 500 in debt stock adds 5 in debt valuation losses per tick.

### External Stress Composite

`external_stress = (-CA/annual_GDP) × 0.35 + fx_delta × 2.0 + 0.20 if reserve_cover < 3.0`

External stress above 0.25 is a warning state. Above 0.50, it begins feeding into crisis intensity.

### Trade Shocks

Export shocks and import shocks multiply structural trade flows. An import_shock of 0.80 means imports are running at 80% of their structural level (useful if you are actively restraining import dependency). An export_shock above 1.0 means your exports are above structural (a positive terms-of-trade moment).

Trade liberalization (from the liberal_institutionalism tradition) raises both export_shock (+0.15) and import_shock (+0.20). Net effect on current account depends on which adjusts more quickly. Historically, imports respond faster than exports — expect a short-term current account deterioration before exports catch up.

---

## 10) The Policy System: Bandwidth, Vitality, and the Graveyard

### Political Bandwidth

Every policy action costs bandwidth. Your bandwidth regenerates each tick:
```
bandwidth_regen = 20 + floor(legitimacy × 0.25 + coalition_cohesion × 15)
```
Maximum regeneration is 60 units per tick. At low legitimacy (20) and poor coalition cohesion (0.3), you regenerate roughly 24 units per tick. At high legitimacy (80) and strong cohesion (0.9), you regenerate 47 units.

**Bandwidth costs for common actions** (at institutional_quality = 0.5):

| Action | Base cost | Notes |
|---|---|---|
| adjust_tax_rate | 5 | Routine |
| adjust_spend_ratio | 5 | Routine |
| adjust_policy_rate | 6 | Monetary |
| adjust_infrastructure | 12 | Investment |
| adjust_industrial_bias | 10 | Investment |
| adjust_tariffs | 10 | Trade |
| adjust_repression | 6 | Security |
| adjust_corruption | 15 | Governance |
| enact_program | 20 | Persistent commitment |
| repeal_program | 12 | — |
| propose_law | 35 | Legislative |
| constitutional_change | 80 | Rare |
| nationalize_sector | 30 | Structural |

High institutional quality reduces costs by up to 50%. Low institutional quality raises them by up to 50%. A meritocratic bureaucracy or technocratic tradition significantly expands your effective bandwidth.

### Policy Vitality

Every active policy has a vitality value (0–100). Vitality starts at 50 when a policy is created. It recovers at 4.0 points/tick when upkeep is funded, and decays at 2.5 points/tick when unfunded. Both rates are moderated by institutional quality and legitimacy.

**Realized policy value** is computed from:
```
capacity_factor = bureaucratic_reach × 0.5 + legitimacy_norm × 0.3 + vitality/100 × 0.2
realized = formal_value × max(0, capacity_factor - elite_capture × 0.4)
```

A policy with formal_value 0.80 enacted in a low-capacity state (bureaucratic_reach 0.3, legitimacy 0.4, vitality 50) has a realized value of roughly:
- `capacity_factor = 0.3×0.5 + 0.4×0.3 + 0.5×0.2 = 0.15 + 0.12 + 0.10 = 0.37`
- `realized = 0.80 × max(0, 0.37 - elite_capture×0.4)`

If elite_capture is 0.3: `realized = 0.80 × (0.37 - 0.12) = 0.80 × 0.25 = 0.20`. The policy does 25% of its intended effect.

This is the shadow gap: formal law says one thing, ground reality is another. The gap closes as you invest in bureaucratic reach, reduce corruption (which proxies elite capture), and keep policies funded.

### Policy Drift

When vitality falls below 40, underfunded policies drift toward a beneficiary class:

| Policy family | Drift beneficiary |
|---|---|
| fiscal | capitalist (tax enforcement weakness) |
| labor | capitalist (labor law erosion) |
| land | capitalist (landlords recapture land reform) |
| services | state (bureaucracy captures program budgets) |
| trade | informal (smugglers exploit gaps) |
| monetary | capitalist (finance sector benefits) |
| governance | state (incumbents entrench) |

Drift means a labor protection law that you cannot afford to maintain will effectively shift toward capital interests over time. Budget for upkeep on policies you care about, or they work against you.

### The Policy Graveyard

When a policy collapses (vitality reaches 0) or is explicitly repealed, it enters the graveyard. Graveyard entries:
- Generate **grievance** = `20 + policy_age × 0.5` (capped at 100). A well-established labor standard repealed after 40 ticks generates 40 grievance points.
- Last for `max(12, min(60, age / 2))` ticks.
- Decay at 1.5 grievance points per tick.
- All active graveyard grievance feeds into unrest and legitimacy pressure.

Repealing a popular policy creates a scar that lasts 1–5 years. Do not repeal programs unless you have a clear transition plan and can absorb the political cost.

### Credibility Multiplier

Credibility (0.2–1.0) scales how fast new policies take effect. It decays by 0.04 per collapsed or failed law and recovers by 0.005 per tick naturally. At credibility 0.5, a policy that would take 6 ticks to reach full effect instead takes 12. Credibility loss is a compounding problem: more failures → lower credibility → new policies take longer to show results → more failures look like failures.

Protect credibility by not proposing laws you cannot pass, not enacting programs you cannot fund, and not making policy reversals that look opportunistic.

---

## 11) Ideological Traditions

Six traditions compete for political influence. The dominant tradition grants bandwidth discounts for its policy families and shapes which unintended consequences are most likely.

### Tradition Overview

**Developmental Nationalism**
- Core idea: State builds industry through directed investment and protection.
- Signature policies: five_year_plan, strategic_soe, export_discipline, import_substitution
- Policy family discounts (25%): industrial, trade, governance
- Class base: state, worker
- Boosts under: external stress, goods shortage pressure
- Drags under: high debt ratio
- Side effects: mild growth bonus (+0.4%), mild inequality reduction, slight repression tendency

**Liberal Institutionalism**
- Core idea: Rules not rulers — independent institutions, property rights, open markets.
- Signature policies: central_bank_independence, property_rights_reform, anti_trust, trade_liberalization
- Policy family discounts (20%): fiscal, monetary, trade
- Class base: capitalist, professional
- Boosts under: high debt, rising risk premium
- Drags under: high unrest
- Side effects: growth bonus (+0.2%), mild inequality increase, reduces repression tendency

**Social Democracy**
- Core idea: Decommodify labor — universal services, collective bargaining, progressive taxes.
- Signature policies: universal_healthcare, collective_bargaining, progressive_tax, public_housing
- Policy family discounts (25%): labor, services, fiscal
- Class base: worker, professional
- Boosts under: high poverty, high unemployment
- Drags under: high inflation
- Side effects: best inequality reduction (-2.5%), small growth cost, reduces repression tendency

**Agrarian Populism**
- Core idea: Land to the tiller — redistribution, rural credit, price floors.
- Signature policies: land_redistribution, rural_credit_program, food_price_floor, cooperative_farming
- Policy family discounts (20%): land, agriculture, services
- Class base: worker, informal
- Boosts under: food shortages, high poverty
- Drags under: external stress
- Side effects: strong inequality reduction (-2%), very small growth, mild repression tendency

**Technocratic Modernism**
- Core idea: Expertise governs — meritocracy, evidence-based policy, efficiency.
- Signature policies: meritocratic_bureaucracy, evidence_policy_office, statistical_bureau, technocrat_cabinet
- Policy family discounts (30%): governance, research, fiscal
- Class base: professional, state
- Boosts under: high corruption
- Drags under: high unrest (experts do not respond well to political pressure)
- Side effects: best growth bonus (+0.3%), slight inequality increase, neutral on repression

**Communal Solidarity**
- Core idea: Local self-organization — cooperatives, mutual aid, decentralized governance.
- Signature policies: cooperative_enterprises, mutual_aid_network, decentralized_governance, community_land_trust
- Policy family discounts (15%): land, services, labor (weakest discounts)
- Class base: informal, worker, cooperative
- Boosts under: regional inequality, unrest
- Drags under: external stress
- Side effects: best inequality reduction (-3%), small negative growth impact, strong anti-repression tendency

### How Tradition Influence Shifts

Tradition influence (0–100) shifts each tick based on crisis signals matching each tradition's appeal. For example, if food_shortage_pressure spikes, Agrarian Populism gains influence at `food_shortage × 0.06 × 10`. The governing tradition gains a small incumbency bonus (+0.5/tick) but also faces governing fatigue (-0.2/tick). All traditions mean-revert toward 30.

The dominant tradition is simply whoever has the highest current influence score. Switching dominant tradition requires either a crisis that consistently boosts the challenger, or explicit policy actions that reinforce it.

### Choosing Your Tradition

Traditions are not equally powerful in all situations:

- **Early-game** with high debt and external pressure: Liberal Institutionalism reduces risk premium and attracts capital. But it has inequality costs that will hurt you later.
- **Food crisis** or high poverty: Agrarian Populism or Social Democracy. Food price floors directly address agricultural sector coverage ratios.
- **Governance and corruption problem**: Technocratic Modernism. Statistical bureau and meritocratic bureaucracy shrink the shadow gap and extend your effective bandwidth.
- **Industrial bottleneck** and strategic capacity shortage: Developmental Nationalism. Five-year plans and industrial bias give you the framework to direct construction spending to where it matters.
- **Regional fragmentation and informal unrest**: Communal Solidarity. Decentralized governance and cooperative frameworks reach informal and worker classes that other traditions ignore.

---

## 12) Laws, Interest Groups, and Unintended Consequences

### Enacting Signature Policies

Signature policies belong to a tradition and require a specific bandwidth action. The most important ones:

| Policy | Tradition | Bandwidth action | Intended effects | Unintended (after delay) |
|---|---|---|---|---|
| five_year_plan | dev_nationalism | propose_law (35) | growth +0.5%, industrial bias +0.2, unrest -3 | corruption +0.04, debt +5% (after 12 ticks) |
| import_substitution | dev_nationalism | adjust_tariffs (10) | imports -25% | shortages +0.06, inflation +0.01 (after 18 ticks) |
| central_bank_independence | liberal_inst | constitutional_change (80) | inflation -0.5%, risk_premium -0.01 | unemployment +0.01 (after 6 ticks) |
| trade_liberalization | liberal_inst | adjust_tariffs (10) | exports +15%, imports +20% | unemployment +0.02, informal income +0.01 (after 24 ticks) |
| universal_healthcare | social_dem | enact_program (20) | poverty -3%, trust +5, unrest -4 | debt +2%, tax pressure +2% (after 6 ticks) |
| collective_bargaining | social_dem | propose_law (35) | worker income +3%, unemployment -0.5% | informal income +0.01 (after 12 ticks) |
| land_redistribution | agrarian | propose_law (35) | poverty -4%, land concentration -8% | production -5%, unrest +5 (after 18 ticks) |
| food_price_floor | agrarian | adjust_industrial_bias (10) | food stabilization +0.2, poverty -2% | debt +1.5% (after 6 ticks) |
| statistical_bureau | technocratic | enact_program (20) | info_quality +8%, corruption -3% | none |
| meritocratic_bureaucracy | technocratic | propose_law (35) | corruption -6%, info_quality +5% | professional support +5 (after 12 ticks) |
| cooperative_enterprises | communal | enact_program (20) | worker income +2%, informal income -1% | production -2% (after 18 ticks) |
| decentralized_governance | communal | propose_law (35) | regional equity +0.2, regional inequality -4% | corruption +2% (after 12 ticks) |

### The Consequence Queue

When you enact a signature policy, its unintended consequences are placed in a hidden queue. They manifest after `delay × (1 - info_quality × 0.4)` ticks. High information quality (0.8) shortens the delay by 32%. The magnitude of unintended effects is also reduced by `1 - info_quality × 0.25`.

A statistical_bureau enacted early reduces both how long you have to wait before unintended consequences surface and how severe they are. This is the most defensively efficient governance investment in the game.

### Ministry Budgets

Seven ministries divide the total spending budget:

| Ministry | Default share | Funded policy families |
|---|---|---|
| finance | 8% | fiscal, monetary, trade |
| social | 28% | labor, services |
| agriculture | 10% | land |
| industry | 12% | industrial |
| defense | 16% | military |
| interior | 8% | governance |
| education | 18% | research |

Policy upkeep is drawn from the relevant ministry budget. If a ministry budget falls below the sum of its upkeep obligations, all its policies begin losing vitality. Watch the Ministry Budgets panel for budget coverage ratios before cutting spend_ratio.

---

## 13) Crises, Victory, and Failure

### Crisis Intensity

Crisis intensity is a composite index combining:
- goods_shortage_pressure (supply system stress)
- internal security load (unrest × repression interaction)
- external_stress (BOP and FX channel)
- regional_inequality_index and regional_service_gap_index
- class_conflict_pressure

**Thresholds:**
- Below 30: stable or manageable
- 30–55: warning; one additional shock could cascade
- 55–75: active crisis; all stabilization resources required
- Above 75: state failure risk is present

### Unrest Risk Formula

The simulation computes unrest risk each tick from:
```
unrest = base + θ1×needs_gap + θ2×inflation + θ3×unemployment + θ4×inequality
         - θ5×legitimacy - θ6×state_capacity + θ7×repression
```

- needs_gap, inflation, unemployment, and inequality all increase unrest.
- legitimacy and state capacity dampen unrest.
- repression increases unrest (repression excess beyond a threshold is counterproductive).

### Legitimacy Formula

```
legitimacy_delta = l1×service_performance + l2×real_income - l3×corruption - l4×repression_excess + l5×fairness
```

- service_performance: aggregates hospital, school, and infrastructure delivery quality.
- real_income: wage growth minus inflation.
- corruption: erodes legitimacy directly.
- repression_excess: using repression above the level justified by actual unrest backfires.
- fairness: Gini-related measure; inequality reduction improves perceived fairness.

### Trust Formula

```
trust_delta = z1×legitimacy + z2×info_quality - z3×polarization - z4×inequality_shock
```

Trust is downstream of legitimacy but also shaped by the quality of information in the public sphere. Polarization (which rises with class conflict) erodes trust even when legitimacy is stable.

### Failure Paths

**Path 1 – Supply spiral:** Shortage → scarcity burden → unrest → legitimacy fall → lower bandwidth → cannot fix shortage → deeper shortage.
- Break by: emergency import coverage of strategic commodities, logistics investment, rationing.

**Path 2 – Debt-reserve spiral:** Deficit → debt rise → risk premium → higher borrowing cost → larger deficit → reserve drain → FX depreciation → import inflation → cost-push prices → legitimacy fall.
- Break by: primary balance adjustment (more gradual than spending cuts alone), diplomatic reserve support, trade access improvement.

**Path 3 – Class coalition collapse:** Inflation + unemployment → worker and informal class support falls → class conflict pressure rises → legitimacy erodes → unrest mobilizes → crisis intensity spikes.
- Break by: direct income support, scarcity burden relief, service quality protection.

### Recovery Sequence

1. Stabilize the essentials: food, fuel, power, medicine coverage above 0.7 in all regions.
2. Stabilize the external account: stop reserve bleeding before addressing inflation.
3. Floor the legitimacy: even minor visible service delivery improvements buy time.
4. Then rebuild: construction pipelines, human capital, medium-term capacity.
5. Finally optimize: once stable, shift to longer-horizon efficiency and growth.

The biggest recovery mistake is starting fiscal consolidation before stabilizing the supply chain. Cutting spending under shortage conditions deepens scarcity.

---

## 14) UI Guide: How to Read Every Sheet

Use sheets as a diagnosis stack, in order, every tick.

**Executive Overview**
- Primary signals: unrest direction (not level), legitimacy direction, risk_premium trend, reserve cover.
- Check direction, not level. A legitimacy of 50 falling for 3 ticks is more dangerous than a legitimacy of 40 that has been stable for 10 ticks.

**Production and Supply Chains**
- Find sectors with unmet_demand > 0.
- Find sectors with inventory below 10% of production (impending shortage).
- Check building_total_workers relative to prior tick — a sudden drop signals a maintenance crisis in a key building type.

**Sector Prices and Shortages**
- Find which sector is driving inflation (sector_price_growth highest).
- Distinguish supply constraint (high prices + low output) from demand pressure (high prices + high output, low inventory).
- If energy prices are rising, check whether fuel or power access has fallen — all sectors use energy inputs.

**Commodity Flows and Storage**
- Check strategic commodity coverage ratios. Below 0.80 is a warning; below 0.50 is a crisis.
- Check storage-days for perishables (staple_food, medicine). If storage-days is below 15, one missed import shipment creates a shortage.
- Power and diesel_power storage is always 0 — they are consumed immediately. Track production vs demand directly.

**Logistics Chokepoints**
- Sort by congestion_ratio. Any corridor above 0.70 is constraining redistribution.
- Check friction levels — corridors with high friction are losing significant commodity share in transit, especially for perishables.
- If the same corridor appears congested for 4+ consecutive ticks, it is a structural constraint requiring road_rail_hub investment.

**Shortages and Class Impact**
- This sheet leads Trust/Legitimacy by 3–6 ticks. Problems here are early warnings.
- Check scarcity_burden_workers and scarcity_burden_informal first — they move before headline unrest.
- Check demand_bloc_household_pressure vs rationing_intensity and informal_market_response — high adaptation means the system is coping but the underlying shortage has not been fixed.

**Trade/FX/Reserves**
- Reserve coverage is the number to watch every tick.
- Check current_account sign. If negative 3+ ticks in a row, you have a structural deficit.
- fx_delta > 0.03 per tick is a currency stress signal — watch import prices.
- external_stress above 0.25 requires active attention.

**Class and Inequality Dynamics**
- Check class support for each class. A falling class indicates a policy or scarcity pressure specific to that class.
- Check class_conflict_pressure. Above 0.40, it will start feeding trust decline independent of legitimacy.
- Check building_owner_output distribution. If capitalist output share is rising and worker income share falling, redistributive pressure will build.

**Trust/Legitimacy/Unrest**
- Legitimacy below 40 is an active crisis. Below 25 is state failure territory.
- Trust below 30 means even correct policy signals are being discounted by the population.
- Unrest above 55 with legitimacy below 45 is the standard cascade setup.
- Check policy_graveyard_grievance — if this is above 30, a recent policy repeal is amplifying your unrest pressure.

**Events, Crises, and Victory**
- Crisis intensity above 55: activate emergency protocol.
- Check the consequence queue (if visible) for policies with matured unintended effects this tick.
- Victory conditions: sustained legitimacy and unrest within bounds for the required tick count.

---

## 15) Symptom -> Action Playbook

Use this section during live play as a decision reference.

---

**Symptom: Inflation rising while production is flat**
- Check: sector_shortage_pressure by sector, logistics congestion, commodity deficits (especially fuel and power)
- Rule out: demand overheating — if output is flat, demand stimulus will only worsen prices
- Try: bottleneck relief first (infrastructure, corridor investment); strategic commodity stabilization for the top 2 constrained inputs; only reduce demand after supply constraint is addressed

---

**Symptom: Reserves falling and risk premium rising**
- Check: current_account sign and trend; import_shock level; external_stress; sanctions/diplomacy posture
- Rule out: random shock — if this has been falling 5+ ticks, it is structural
- Try: moderate import pressure (reduce import_shock toward 0.85); improve trade partner relations; if debt_to_GDP > 0.75, signal fiscal consolidation but do not implement cutting until supply chain is stable

---

**Symptom: Trust falls faster than legitimacy**
- Check: polarization level; class_conflict_pressure; info_quality
- This pattern means institutional credibility is eroding even though the state is delivering services
- Try: improve info_quality (statistical bureau, reduce corruption_signal); reduce polarization drivers (reduce class income gap pressure, reduce repression that inflames class tensions)

---

**Symptom: Workers and informal class support declining but capitalist support stable**
- Check: scarcity_burden_workers; scarcity_burden_informal; wage vs inflation gap; household_pressure
- This is a distributional crisis — growth is happening but not reaching lower classes
- Try: increase social ministry budget for upkeep; enact or maintain labor protections; target food and medicine scarcity directly; consider progressive_tax if capitalist income share is growing

---

**Symptom: High national averages but sudden regional unrest spikes**
- Check: State Explorer; regional_inequality_index; regional_service_gap_index; building distribution by archetype
- National averages hide fragile_frontier or neglected periphery regions
- Try: targeted construction investment in the lagging region; decentralized_governance policy to route fiscal authority there; road_rail_hub to fix supply access; check if a corridor chokepoint is cutting off that region

---

**Symptom: Debt grows despite stable spending ratio**
- Check: risk_premium trend (rising borrowing cost); interest_payment share of GDP; nominal GDP growth rate; fx_delta (valuation effects on foreign debt)
- Stable spending ratio does not mean stable debt if GDP is shrinking or interest costs are rising
- Try: restore confidence channels first (reserves, legitimacy, conflict pressure reduction); only then retune the fiscal mix; avoid pro-cyclical cuts that shrink GDP faster than spending

---

**Symptom: Policy vitality collapsing on multiple policies simultaneously**
- Check: ministry budget coverage vs upkeep obligations; institutional quality; recent legitimacy trend
- This is a governance crisis — your state cannot sustain its commitments
- Try: prioritize upkeep for the 2–3 most critical policies (labor protections, infrastructure maintenance, basic fiscal regime); let lower-priority policies lapse rather than spreading underfunding evenly; consider technocratic_modernism bandwidth discounts to reduce upkeep costs

---

**Symptom: Construction projects are completing but output is not improving**
- Check: building condition levels; human_capital score vs building skill_thresholds; whether the right building type is being built for the regional archetype
- New buildings at low condition or below skill threshold contribute little to output
- Try: ensure maintenance spending accompanies construction; check if universities are present (they improve human capital that unlocks higher-skill buildings); ensure you are building the right archetype for the region (do not build oil_gas_well in agro_periphery without resource endowment)

---

**Symptom: Unintended consequences manifesting from 12+ ticks ago**
- Check: what signature policies were enacted near tick (current - delay) and what their unintended effects are
- Common offenders: import_substitution triggering shortages at tick +18; five_year_plan triggering corruption rise at tick +12; land_redistribution triggering production disruption at tick +18
- Try: have countermeasures ready (corruption_adjustment before five_year_plan matures; import buffer before import_substitution matures); invest in statistical_bureau early to shorten and reduce magnitude of future unintended effects

---

## 16) Glossary

**bandwidth**
Political executive capacity to enact and manage policies. Regenerates each tick based on legitimacy and coalition cohesion. Finite — you cannot do everything at once.

**building condition**
0–1 measure of physical state of a building. Degrades each tick without maintenance. Directly multiplies building output. Critical to maintain above 0.60.

**building quality / quality_modifier**
Output quality factor driven by human_capital relative to the building's skill_threshold. A hospital needs human_capital ≥ 0.60 to operate at full quality.

**class_conflict_pressure**
Aggregate intensity of cross-class political-economic tension. Feeds directly into trust decline and unrest mobilization.

**credibility multiplier**
0.2–1.0 scalar on policy implementation speed. Lost through policy collapses and failed laws. Recovered slowly over time.

**demand bloc**
One of three aggregate demand categories: household, institutional, productive. Each has different commodity weights and feeds different class scarcity burdens.

**elite_capture**
Fraction of policy enforcement hollowed out by elites. High capture means formal policies (especially labor, fiscal, land) have low realized effect even if vitality is healthy.

**external_stress**
Composite index of external vulnerability: current account deficit, FX depreciation pressure, and reserve coverage shortfall.

**formal vs. realized value**
Every policy has a stated (formal) value and an actual (realized) value. The shadow gap between them is driven by state capacity, legitimacy, vitality, and elite capture.

**fx_delta**
Monthly exchange rate depreciation pressure. Positive values increase import costs and feed into inflation and foreign debt valuation losses.

**goods_shortage_pressure**
Composite supply stress index from unmet demand and logistics constraints. A leading indicator for scarcity burden and unrest pressure.

**informal_market_response**
0–1 measure of extra-formal adaptation under shortages. Reduces measured household pressure but expands the informal economy at the cost of the formal tax base.

**logistics_bottleneck_index**
Friction/capacity stress in the movement of goods. High values signal that goods are being produced but not reaching where they are needed.

**needs_gap**
Composite social shortfall indicator. Blends household, institutional, and productive demand bloc pressures. Direct input into the unrest risk formula.

**policy graveyard**
Repository of collapsed or repealed policies. Each entry generates grievance that adds to unrest pressure for months after the policy ends.

**policy vitality**
0–100 measure of how actively a policy is being enforced. Decays without upkeep. At vitality 0, a policy collapses into the graveyard.

**rationing_intensity**
0–1 measure of formal state-managed scarcity response. Partially offsets household scarcity pressure. Requires state capacity to work.

**reserve coverage**
Months of import value covered by current foreign reserves. Below 3 months: risk premium rises. Below 1 month: balance-of-payments crisis.

**risk_premium**
Additional borrowing cost imposed by markets on perceived macro or external risk. Feeds into the effective debt rate and widens the fiscal deficit.

**scarcity_burden_[class]**
Class-specific exposure to commodity shortfall effects. Workers and informal carry household scarcity. Professionals carry institutional. Capitalists carry productive.

**shadow gap**
Difference between formal policy value and realized policy value. Wide shadow gaps indicate state capacity failure or elite capture.

**tradition influence**
0–100 score per ideology. The dominant tradition (highest score) shapes bandwidth costs and crisis responses.

**vitality decay / drift**
When policy vitality falls below 40 without funding, the policy drifts toward the beneficiary class of its family — effectively working against its stated purpose.

---

## Appendix A: Recommended Learning Path

**Session 1: Diagnosis and stabilization baseline**
- Open each sheet in the diagnosis order from Section 14.
- Practice reading direction, not level. Track 5 key metrics and note which are trending vs. stable.
- Do not change any policy. Play 6 ticks observing only.

**Session 2: Shortage and logistics stabilization**
- Start a run where goods_shortage_pressure > 0.25 in tick 1.
- Practice the supply-chain diagnosis chain: sector output → commodity coverage → logistics chokepoints → class scarcity burdens.
- Enact one construction project (road_rail_hub in most congested corridor) and track its effect over 10 ticks.

**Session 3: External balance crisis recovery**
- Start or engineer a scenario with reserve_cover < 2 months.
- Practice the reserve stabilization sequence: current account diagnosis → import moderation → trade access → risk premium feedback.
- Avoid fiscal austerity until reserves are stable.

**Session 4: Class coalition management under dual pressure**
- Practice managing a simultaneous inflation + unemployment shock.
- Track each class's support trend separately. Identify which class is most at risk each tick.
- Practice choosing one tradition and using its bandwidth discount to implement a coherent policy bundle rather than piecemeal adjustments.

**Session 5: Full governance run with unintended consequences**
- Enact 3 signature policies across different traditions in the first 20 ticks.
- Track the consequence queue. Prepare countermeasures before each consequence matures.
- Practice credibility management: do not let failed policies accumulate.

---

## Appendix B: Manual Scope Notes

This manual describes currently implemented systems in the codebase and UI.
Future expansions should append, not overwrite, this baseline.

Key areas not yet fully implemented (as of v2):
- Military and security detailed mechanics (military_barracks output channels are seeded but not fully wired)
- Full election and coalition system (coalition_cohesion affects bandwidth but elections are not yet turn-sequenced)
- Technology tree and research point accumulation details

These sections will be expanded in v3 when implementation is confirmed.
