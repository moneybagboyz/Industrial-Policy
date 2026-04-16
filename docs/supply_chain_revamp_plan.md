# Supply Chain Revamp Plan

## Purpose
Revamp the simulation from a broad five-sector macro supply chain into a layered production economy with region-specific industries, intermediate goods, logistics bottlenecks, and social consequences.

The target level of depth is closer to FIRS for OpenTTD than to a standard strategy-game macro model:
- multiple viable production chains instead of one abstract pipeline
- geography and endowments that shape what can exist where
- intermediate goods that matter politically and economically
- visible bottlenecks and substitution paths
- different economy presets with distinct industrial identities
- town and household demand that feeds back into legitimacy, class politics, and unrest

This plan is written against the current codebase, where the main extension points are:
- `src/econ/sector_network.py`
- `src/econ/building_engine.py`
- `src/econ/building_types.py`
- `src/core/scenario_loader.py`
- `src/core/stages.py`
- `src/ui/tui_app.py`

## Diagnosis Of The Current Model
The current model already has useful foundations, but the supply chain is still too aggregated for the kind of economic and social storytelling the simulation wants.

### Current strengths
- A deterministic tick pipeline already exists.
- The simulation already tracks buildings, construction, logistics proxies, region state, and policy levers.
- The UI already exposes production, shortages, sector prices, buildings, and the construction pipeline.
- The building system gives a natural bridge from abstract sectors to physical industry.

### Current limitations
- `sector_network.py` operates on five broad sectors only: agriculture, energy, manufacturing, construction, services.
- Inputs are represented as small coefficient matrices rather than named commodities or industrial chains.
- Regions do not yet specialize through actual industry graphs.
- Buildings mostly contribute generic sector output, not specific upstream or downstream commodities.
- Trade and logistics are summarized through indexes rather than route capacity, corridor friction, or commodity-specific dependence.
- Household life is indirectly represented through aggregate demand, but not through differentiated consumption baskets, informal markets, or scarcity politics.

### Why this matters economically
A real supply chain crisis is rarely "manufacturing is down" in the abstract. It is more often:
- fertilizer shortages cutting farm yield six months later
- cement scarcity delaying housing and infrastructure
- refined fuel shortages crippling trucking and generators
- imported machine parts disabling domestic industry maintenance
- food distribution failures driving urban discontent even when national production looks adequate

### Why this matters sociologically
Scarcity is experienced by groups, places, and institutions unevenly.
- Urban workers react differently to shortages than rural producers.
- Peripheral regions may be rich in extractive output but poor in consumer supply.
- Informal markets may stabilize survival while undermining tax collection and state legitimacy.
- Elite control of ports, depots, or import licenses can convert logistics into patronage.

## FIRS-Inspired Design Principles
The simulation should borrow FIRS-style structure, not copy OpenTTD mechanics literally.

Use FIRS as inspiration for legibility, branching, and chain identity, but not as literal economic truth. Real supply chains in this simulation should be constrained by labor, maintenance, state capacity, import finance, political allocation, storage loss, and regional inequality in ways that transport games do not need to model.

### Principle 1: Named chains, not generic sectors
Players should be able to say: coal powers cement, cement enables construction, construction expands logistics and housing, housing reduces urban stress.

### Principle 2: Several valid economies
Like FIRS economy sets, the simulation should support multiple national economic identities instead of one universal chain.

### Principle 3: Intermediate goods are political
Fertilizer, fuel, steel, cement, machine parts, medicine, and consumer staples should matter more than abstract output.

### Principle 4: Geography creates strategy
A dry frontier, an industrial belt, a port city, and a mining basin should not play the same.

### Principle 5: Complexity should be layered
The baseline economy must be readable. Advanced chains should deepen the simulation without making every run incomprehensible.

### Principle 6: Demand is social
Households, cities, farms, industry, construction, and the state should all pull on the system differently.

### Principle 7: Shortages create institutions
Black markets, rationing, hoarding, corruption, cartelization, and emergency procurement should emerge naturally from chain stress.

### Principle 8: Realism beats neat symmetry
Not every commodity needs a perfect upstream-downstream loop. Some goods should be import dominated, some sectors should be structurally inefficient, and some regions should remain locked into low value-add roles unless policy and infrastructure change the development path.

## Target Architecture
The revamp should move from:
- sector aggregates -> commodity networks
- generic buildings -> industry nodes
- generic logistics index -> corridor and distribution capacity
- single national demand anchor -> segmented demand blocs

### New simulation layers
1. Economy preset layer
Different national industrial structures, comparable to FIRS economy sets.

2. Commodity layer
Named raw materials, intermediates, utilities, and final goods.

3. Industry node layer
Buildings and regional complexes that consume and produce specific commodities.

4. Logistics layer
Ports, depots, rail hubs, roads, storage, cold chain, and distribution bottlenecks.

5. Demand layer
Households, farms, industry, construction, state services, and export markets as separate buyers.

6. Social mediation layer
Rationing, informal markets, unrest, patronage, and class/regional conflict generated by shortages.

## Proposed Commodity Taxonomy
Do not start with 50-plus cargos. Start with a tight but expressive set.

### Tier 1: Raw materials
- grain
- cash_crops
- livestock
- timber
- stone
- iron_ore
- coal
- crude_oil
- gas

### Tier 2: Basic processed inputs
- flour_food_inputs
- fertilizer
- fuel
- power
- steel
- cement
- lumber
- chemicals
- textiles

### Tier 3: Strategic intermediates
- machine_parts
- construction_materials
- industrial_components
- packaging
- medical_inputs
- farm_supplies

### Tier 4: Final goods and services bundles
- staple_food
- consumer_goods
- housing_services
- mobility_services
- healthcare_services
- education_services

### Tier 5: State and external channels
- military_supplies
- export_contracts
- imported_essentials
- aid_shipments

## Proposed Industry Node Families
Each building type should eventually map to one or more named industry node templates.

### Extraction
- grain_farms
- livestock_ranches
- forestry_camps
- quarries
- iron_mines
- coal_mines
- oil_fields
- gas_fields

### Basic processing
- mills
- fertilizer_plants
- refineries
- power_plants
- sawmills
- steelworks
- cement_plants
- textile_mills

### Secondary manufacturing
- machine_shops
- tools_factories
- food_processing_plants
- consumer_goods_factories
- pharma_plants
- prefab_housing_plants

### Logistics and market institutions
- warehouses
- cold_storage
- trucking_depots
- rail_hubs
- ports
- wholesale_markets
- municipal_markets

### Social distribution nodes
- public_distribution_centers
- clinics
- schools
- housing_authorities
- military_depots

## Regional Geography And Industry Generation
Yes, this constraint is necessary. Industries should not be generated because the abstract chain says they are useful. They should be generated because a region can plausibly support them.

The core rule should be:
- resources determine what is possible
- infrastructure determines what is scalable
- labor and institutions determine what is sustainable
- markets determine what is profitable or politically worth subsidizing

That prevents broken worlds such as inland refinery clusters with no crude access, steel belts with no ore, fuel, or rail, or large food-processing complexes in regions that cannot source inputs or distribute outputs.

### Industry placement should use four layers of constraints

#### 1. Hard geographic constraints
These decide whether an industry can exist at all.

Examples:
- oil_fields require oil endowment above a threshold
- gas_fields require gas endowment above a threshold
- iron_mines require ore deposits
- quarries require stone deposits
- fisheries require coastline, major lakes, or river systems
- ports require coast or navigable major river access
- hydropower requires river gradient and water flow
- irrigated agriculture requires water access, not just farmland

If a hard constraint fails, the industry does not spawn except through a rare explicit scenario override.

#### 2. Soft structural constraints
These decide whether the industry is viable at small, medium, or large scale.

Examples:
- refineries prefer port access, pipeline links, grid reliability, and engineering labor
- steelworks prefer ore, coal, power, rail, water, and a large labor pool
- cement plants prefer quarry access, fuel, and proximity to construction markets
- consumer goods factories prefer urban labor, market density, power, and import access
- food-processing plants prefer farm belts plus logistics to cities

Soft constraints should not prohibit existence entirely. They should lower scale, reliability, and efficiency.

#### 3. Institutional constraints
These decide whether the region can operate complex industry without collapse.

Examples:
- low state capacity reduces throughput of ports, depots, and public distribution nodes
- low human capital hurts machine shops, refineries, chemical plants, and hospitals
- high corruption raises leakage for import-dependent or rationed sectors
- insecurity damages trucking, warehouses, and rural extraction first

This matters because some regions should be resource rich but operationally weak.

#### 4. Demand and corridor constraints
These decide whether a viable chain has a reason to exist.

Examples:
- urban regions justify food processing, wholesale markets, and consumer goods assembly
- export corridors justify mines, ports, and cash crop estates
- construction booms justify cement and builders yards
- isolated low-demand regions may only sustain primary extraction and basic markets

An industry should not scale just because it can technically exist. It should also need either nearby demand or reliable corridor access to distant demand.

### Region tags should drive generation
Each state or subregion should be built from a structured profile rather than random building lists.

Recommended region attributes:
- land_fertility
- rainfall_and_water_access
- forest_cover
- stone_endowment
- iron_endowment
- coal_endowment
- oil_endowment
- gas_endowment
- fishery_access
- coastal_access
- river_access
- elevation_and_terrain_cost
- population_density
- urbanization_level
- human_capital
- transport_connectivity
- grid_reliability
- state_capacity
- corruption_pressure
- insecurity_risk
- market_access
- export_corridor_access

These tags should exist before industry placement. Industry generation should read them, not invent them on the fly.

### Industry generation should be score-based, not binary-only
For each candidate industry node, compute:
- eligibility score: do the hard constraints pass?
- viability score: how well does the region support this industry?
- scale score: how large should this node be if placed?
- reliability score: how often will it underperform?

Conceptually:
- hard constraints gate existence
- viability determines spawn probability
- scale determines starting size and upgrade ceiling
- reliability determines how brittle the node is during stress

Example logic:
- a subregion with high oil endowment and poor roads can spawn oil extraction, but not a world-class petrochemical hub
- a port city with weak crude access can host import-fed refining, but it will be externally vulnerable
- an inland industrial belt with rail, coal, and labor can support steel, machine parts, and construction materials

### Prefer clusters, not isolated industries
Industries should be generated in regional clusters.

Examples:
- oil basin cluster: oil fields, service workshops, fuel depot, export terminal or refinery
- agrarian belt cluster: grain farms, livestock, milling, food processing, storage, trucking depots
- mining belt cluster: ore mine, coal mine, steelworks, rail hub, workers' town
- port city cluster: port, warehouse, wholesale market, assembly plants, refinery, customs administration

This avoids worlds where a single downstream node appears with no local ecosystem around it.

### Use chain templates with anchor nodes
Do not attempt to generate the full economy one building at a time from scratch. Start from anchor nodes and grow outward.

Anchor examples:
- if a region has strong oil endowment, start with `oil_fields`
- if a region has strong fertility and population, start with `grain_farms`
- if a region has coast plus corridor access, start with `port`
- if a region has ore plus coal plus rail plus labor, start with `steelworks_cluster`

Then add second-order nodes only if support conditions pass.

Example:
- oil_fields can exist with weak support
- refinery requires either local crude flow or strong import-port access
- petrochemicals require refinery output plus engineering labor plus large demand or export access

### Allow incomplete but believable economies
Not every country should generate a complete domestic chain.

That is realistic.

Examples:
- an oil producer may export crude and import fuel
- an agrarian state may mill grain domestically but import fertilizer and machinery
- a mining state may export ore and import finished steel
- a port-commercial state may assemble consumer goods from imported intermediates

The rule should be: incomplete is acceptable, impossible is not.

### Make import substitution a development path, not a starting assumption
If a region has the geography for extraction but not the support base for processing, the simulation should start with extraction only.

Later, policy and investment can build the missing prerequisites:
- roads
- rail
- power
- technical schools
- ports
- machine shops
- warehousing

Only after those prerequisites improve should heavier downstream industries appear or scale up.

### Recommended generation pipeline
1. Generate regional geography and endowment tags.
2. Assign settlement hierarchy and corridor network.
3. Assign labor, human capital, and state-capacity profiles.
4. Pick economy preset for the scenario.
5. Spawn anchor industries from hard endowments.
6. Spawn support industries where viability scores are strong.
7. Spawn downstream processing only where both input access and market access are credible.
8. Validate that every spawned node has at least one plausible input path and one plausible output sink.
9. Downgrade or remove nodes that fail validation.

### Chain validation rules
This is the direct answer to avoiding broken industry chains.

Before finalizing world generation, each industry should pass these checks:
- input plausibility: can its main inputs be sourced locally, regionally, or through imports?
- corridor plausibility: can those inputs physically reach the site?
- sink plausibility: is there local demand, state demand, export access, or a downstream user?
- support plausibility: does the region have enough power, labor, and maintenance capacity?
- resilience plausibility: if one import is disrupted, does the industry become fragile rather than magically stable?

If an industry fails most of these checks, it should not spawn.

### Examples

#### Oil region
- high oil endowment
- medium coast access or pipeline access
- medium engineering labor
- medium export corridor access

Likely industries:
- oil_fields
- fuel depot
- export terminal

Possible later industries:
- refinery
- petrochemical plant

Unlikely early industries:
- advanced machine tools
- heavy consumer manufacturing

#### Interior grain belt
- high fertility
- moderate rainfall
- low industrial labor
- medium road access
- rising urban demand nearby

Likely industries:
- grain_farms
- livestock_ranches
- mills
- food-processing plants
- warehouses

Possible later industries:
- fertilizer blending
- farm-supply depots

Unlikely early industries:
- steelworks
- refinery

#### Inland mining belt
- high ore and coal
- strong rail corridor
- medium power reliability
- large labor pool

Likely industries:
- iron_mines
- coal_mines
- steelworks
- machine shops
- rail hub

Possible later industries:
- cement plant
- heavy fabrication

Unlikely early industries:
- fisheries
- port-led assembly cluster

## Design Rule
Generate regions first, then industries from regions, then chains from industries.

Do not generate a complete chain first and spray its pieces across the map. That is exactly how you get broken worlds.

## Economy Presets
Like FIRS economy sets, the simulation should support several curated economic graphs. They should reuse the same engine but differ in commodity availability, industry mix, import dependence, and political risks.

### 1. Agrarian-Importing State
Profile:
- strong agriculture
- weak heavy industry
- high dependency on imported fuel, fertilizer, machinery, and medicine
- politically vulnerable urban food markets

Main dynamics:
- food stability matters more than export sophistication
- ports and roads are more important than steel depth
- fertilizer and fuel shocks quickly destabilize production and legitimacy

### 2. Resource Extractive State
Profile:
- strong oil, gas, coal, or ore output
- narrow export base
- weak domestic processing
- regional enclave politics

Main dynamics:
- export corridors matter more than domestic balance at first
- rent allocation shapes class and regional conflict
- imported essentials can coexist with headline growth

### 3. Import-Substituting Industrializer
Profile:
- strong state role
- active construction and industrial policy
- expanding steel, cement, machine parts, and consumer manufacturing
- recurring foreign exchange and bottleneck crises

Main dynamics:
- construction and machine parts become strategic chokepoints
- infrastructure and energy constraints determine takeoff speed
- shortages can strengthen both planning arguments and black markets

### 4. Port-Commercial Mixed Economy
Profile:
- services, trade, assembly, and processing dominate
- strong port cities and trade corridors
- high sensitivity to external demand and exchange rate pressure

Main dynamics:
- imported intermediates are central
- warehousing and customs efficiency matter
- urban inequality and housing stress become major political drivers

### 5. Heavy Industry Complex
Profile:
- steel, power, cement, engineering, rail, machinery
- high capital intensity
- huge maintenance and logistics needs

Main dynamics:
- coal, power, steel, cement, and machine parts form the core chain
- failures propagate widely and visibly
- labor organization and environmental damage become politically central

## Core Production Graph For The Baseline Scenario
The first implementation should ship one curated baseline graph rather than many partial systems.

### Agriculture and food
- grain_farms -> grain
- livestock_ranches -> livestock
- fertilizer_plants -> fertilizer
- fuel -> farms and trucking
- grain + livestock + power + packaging -> food_processing_plants -> staple_food
- staple_food -> households, barracks, schools, hospitals

### Materials and construction
- quarries -> stone
- cement_plants consume stone + power + fuel -> cement
- steelworks consume iron_ore + coal + power -> steel
- sawmills consume timber + power -> lumber
- cement + steel + lumber + machine_parts -> construction_materials
- construction_materials + fuel -> construction_yards -> housing, roads, logistics, public works

### Energy
- coal_mines -> coal
- oil_fields -> crude_oil
- refineries consume crude_oil -> fuel
- coal + gas + fuel -> power_plants -> power
- power is required by nearly every industrial node

### Industry
- steel + power -> machine_shops -> machine_parts
- machine_parts + chemicals + textiles + power -> consumer_goods_factories -> consumer_goods
- machine_parts are also a maintenance input for mines, power, transport, and factories

### Distribution and urban life
- ports, rail_hubs, trucking_depots, warehouses move commodities
- municipal_markets convert delivered staples and consumer goods into household access
- weak delivery can produce urban scarcity even when national output looks acceptable

## Baseline Economy Flow Network
This section is the level of depth the implementation should target. It is deliberately more explicit than the architecture sections above.

The baseline scenario should resemble a lower-middle-income mixed economy with:
- one export-oriented coastal corridor
- one interior agrarian belt
- one mining and heavy-industry belt
- one dense urban consumer region
- one neglected peripheral region with weak state penetration

The goal is not to make every chain equally important. The goal is to create a few strategic systems whose failures propagate in realistic ways.

### Chain A: Farm Reproduction And Food Security
This chain should be central because food politics is almost always regime politics.

Primary nodes:
- grain_farms produce `grain`
- cash_crop_estates produce `cash_crops`
- livestock_ranches produce `livestock`
- fisheries produce `fish`

Support inputs:
- fertilizer_plants produce `fertilizer`
- refineries produce `fuel`
- machine_shops produce `machine_parts`
- farm_supply_depots bundle `fertilizer + fuel + machine_parts + credit_access` into `farm_supplies`

Core flow:
- grain_farms consume `farm_supplies + seasonal_labor + water_access` -> `grain`
- livestock_ranches consume `feed_inputs + veterinary_inputs + fuel` -> `livestock`
- fisheries consume `fuel + cold_chain_access` -> `fish`
- mills consume `grain + power` -> `flour_food_inputs`
- food_processing_plants consume `flour_food_inputs + livestock_or_fish + packaging + power` -> `staple_food`
- cold_storage and warehouses preserve `staple_food`
- municipal_markets and public_distribution_centers convert delivered `staple_food` into household access

Realistic dynamics:
- fertilizer shocks should hit yields with a lag, not instantly
- fuel shortages should disrupt planting, harvest, and trucking more than biological production itself
- poor storage should turn adequate harvests into urban scarcity
- export cash crops should compete with food acreage when foreign exchange pressure rises

### Chain B: Oil, Fuel, Power, And General Logistics
This chain should sit underneath almost every other chain because energy is the universal bottleneck.

Primary nodes:
- oil_fields produce `crude_oil`
- gas_fields produce `gas`
- coal_mines produce `coal`

Processing nodes:
- refineries consume `crude_oil + power + chemicals` -> `fuel`
- thermal_power_plants consume `coal_or_gas_or_fuel + water + maintenance_inputs` -> `power`
- grid_substations convert `power` into regional delivery with transmission losses

Logistics nodes:
- trucking_depots consume `fuel + machine_parts + labor` -> `road_freight_capacity`
- rail_hubs consume `power_or_fuel + steel + maintenance_inputs` -> `rail_freight_capacity`
- ports consume `fuel + machine_parts + customs_capacity` -> `port_throughput`

Core flow:
- `fuel` feeds farms, mines, trucking, backup generation, construction, and military logistics
- `power` feeds mills, cement, steel, machine shops, water systems, hospitals, telecoms, and cold storage
- logistics nodes use `fuel` and `machine_parts` to deliver every strategic good downstream

Realistic dynamics:
- fuel scarcity should raise route costs before it fully collapses output
- power shortages should force load-shedding that protects elites and strategic industry first
- imported fuel can stabilize the core corridor while peripheral regions black out

### Chain C: Minerals, Materials, And Construction Capacity
This chain determines whether the country can build out of crisis or remain trapped in scarcity.

Primary nodes:
- quarries produce `stone`
- iron_mines produce `iron_ore`
- forestry_camps produce `timber`

Processing nodes:
- cement_plants consume `stone + fuel + power` -> `cement`
- sawmills consume `timber + power` -> `lumber`
- steelworks consume `iron_ore + coal + power + refractory_inputs` -> `steel`
- machine_shops consume `steel + power + skilled_labor` -> `machine_parts`

Assembly and deployment nodes:
- builders_yards consume `cement + steel + lumber + fuel + machine_parts` -> `construction_materials`
- construction_yards consume `construction_materials + labor + fuel` -> `housing_services + infrastructure_progress + industrial_capacity_expansion`

Realistic dynamics:
- cement is bulky and local; its bottleneck is often transport and energy, not trade alone
- machine parts should be low-volume but strategic because they gate maintenance and repair
- construction should compete with military works and prestige projects for the same material base
- housing backlogs should be persistent and path-dependent, not instantly fixable by one policy tick

### Chain D: Consumer Industry And Urban Stability
This chain determines whether growth translates into everyday legitimacy.

Primary nodes:
- textile_mills consume `cash_crops_or_imported_fibers + power` -> `textiles`
- chemical_plants consume `gas_or_oil_derivatives + power` -> `chemicals`
- packaging_plants consume `paper_or_plastics_inputs + power` -> `packaging`

Manufacturing nodes:
- consumer_goods_factories consume `textiles + chemicals + packaging + machine_parts + power` -> `consumer_goods`
- pharma_plants consume `chemicals + medical_inputs + power` -> `essential_medicines`

Distribution nodes:
- wholesale_markets route `consumer_goods` and `essential_medicines`
- municipal_markets distribute mass goods
- hospitals and clinics absorb medicines as institutional sinks

Realistic dynamics:
- consumer scarcity should hurt trust and urban order before it kills output
- medicine scarcity should have outsized legitimacy effects despite low volume
- the informal sector should be able to substitute part of consumer goods demand with lower quality locally assembled goods

### Chain E: Trade Corridor, Imports, And Export Earnings
This chain should prevent autarkic fantasy. Some critical goods must remain import dependent for a long time.

Import channels:
- ports receive `imported_fuel`, `imported_fertilizer`, `imported_machine_parts`, `imported_medicines`, `imported_consumer_goods`
- inland_dry_ports and warehouses redistribute imports inland

Export channels:
- ports ship `cash_crops`, `minerals`, `fuel_exports`, and later `processed_exports`

Core flow:
- export earnings -> foreign exchange -> import capacity
- import capacity -> access to strategic goods -> domestic production continuity

Realistic dynamics:
- export booms can coexist with domestic scarcity if corridor allocation is enclave-oriented
- currency crisis should reduce import availability before it reduces physical desire to import
- customs corruption and port patronage should distort who gets access to scarce imports

## Support Loops And Reproductive Inputs
FIRS is strong at showing that industries often need support cargoes, not just one obvious raw material. The simulation should adopt that logic in a more realistic form.

### Farm support loop
- fertilizer_plants + refineries + machine_shops -> farm_supply_depots -> farms
- higher farm supplies improve yield, reduce spoilage, and stabilize acreage
- prolonged shortages reduce next-season output, not just current stock

### Industrial maintenance loop
- steelworks + machine_shops -> machine_parts
- machine_parts -> mines, refineries, power plants, logistics hubs, factories
- machine-parts scarcity should reduce reliability first, then capacity, then safety

### Construction reproduction loop
- cement + steel + lumber + machine_parts -> construction materials
- construction materials -> roads, ports, depots, power grids, housing, factories
- better infrastructure reduces future route costs and expands future supply capacity

### Port and corridor support loop
- ports and rail hubs require continuous `fuel + machine_parts + administrative_capacity`
- if any of these fail, throughput drops and import dependence becomes more painful

### Social reproduction loop
- staple_food + mobility_services + healthcare_services + education_services sustain labor quality
- labor quality feeds back into productivity, unrest, absenteeism, and migration

## Final Demand Sinks
The current plan mentions households and institutions, but the revamp should make sinks explicit so flows can be traced all the way to where goods disappear.

### Household sinks
- rural_households consume `staple_food + fuel + basic_consumer_goods`
- urban_worker_households consume `staple_food + transit_access + basic_consumer_goods + rent-sensitive housing services`
- middle_class_households consume `staple_food + durable_consumer_goods + mobility_services + education_services`

### Institutional sinks
- hospitals consume `power + essential_medicines + staple_food + water_services`
- schools consume `power + staple_food + education_inputs`
- barracks consume `staple_food + fuel + military_supplies`
- public_distribution_centers consume `staple_food + fuel + administrative_capacity`

### Productive sinks
- farms consume `farm_supplies`
- industry consumes `power + fuel + machine_parts + chemicals`
- construction consumes `construction_materials + fuel`
- logistics consumes `fuel + machine_parts`

### External sinks
- export contracts consume designated shares of `cash_crops`, `minerals`, or `processed_exports`
- debt service and import finance should constrain how much of this export value actually improves domestic welfare

## Baseline Flow Table
This is the target level of explicitness for the first economy preset.

| Node | Main Inputs | Main Outputs | Main Failure Modes |
| --- | --- | --- | --- |
| Grain Farms | farm_supplies, labor, land, water | grain | fertilizer shortage, fuel scarcity, drought, land conflict |
| Livestock Ranches | feed, veterinary inputs, fuel | livestock | feed inflation, disease, insecurity |
| Fisheries | fuel, cold chain, boats | fish | fuel scarcity, spoilage, export diversion |
| Mills | grain, power | flour_food_inputs | power cuts, transport delays |
| Food Processing Plants | flour_food_inputs, livestock or fish, packaging, power | staple_food | packaging shortage, blackouts, cold chain failure |
| Refineries | crude_oil, power, chemicals | fuel | import dependency, maintenance shortages |
| Power Plants | coal or gas or fuel, maintenance, water | power | fuel shortage, machine-parts shortage, grid instability |
| Cement Plants | stone, power, fuel | cement | energy cost spike, route bottlenecks |
| Steelworks | iron_ore, coal, power | steel | coking and power bottlenecks, maintenance decay |
| Machine Shops | steel, power, skilled labor | machine_parts | skilled labor shortages, steel scarcity |
| Builders Yards | cement, steel, lumber, machine_parts | construction_materials | material mismatches, logistics delays |
| Construction Yards | construction_materials, fuel, labor | housing and infrastructure progress | budget cuts, corruption, fuel shortages |
| Ports | fuel, machine_parts, customs capacity | import and export throughput | patronage, sanctions, congestion |
| Warehouses | delivered goods, power, administration | storage and distribution capacity | spoilage, theft, grid failure |
| Municipal Markets | delivered goods, local security, working capital | household access | hoarding, informal capture, local unrest |

## Realism Guardrails
The simulation should remain intelligible, but these guardrails keep it grounded.

### 1. Avoid perfectly closed loops
Real economies import catalysts, spare parts, medicines, and know-how even when they industrialize.

### 2. Model time lags
Key delays should exist between:
- fertilizer shortages and harvest collapse
- cement shortages and housing backlog
- machine-parts shortages and industrial breakdown
- education investment and skilled labor gains

### 3. Distinguish flow bottlenecks from stock bottlenecks
A country can have grain in aggregate and still have urban hunger because trucking and storage failed.

### 4. Make political allocation matter
Scarcity should be mediated by who gets priority access:
- export corridor first
- capital city first
- military first
- regime-aligned regions first
- everyone else later

### 5. Preserve structural dependence
Import substitution should be possible, but difficult. Early industrialization should often deepen dependence on imported machinery, chemicals, and fuel before it reduces it.

### 6. Let informality stabilize and corrode
The informal sector should soften collapse while undermining state revenue, quality control, and formal legitimacy.

### 7. Keep some waste and redundancy
Not every investment should maximize efficiency. States build prestige projects, elites hoard, and agencies duplicate functions. Those frictions are part of realism.

## Social And Sociological Layer
This revamp should not stop at engineering flows. It should model who absorbs shock and how institutions respond.

### Demand blocs
Replace one `household_demand_proxy` with separate demand blocs:
- rural households
- urban workers
- middle class / formal sector
- state institutions
- industrial users
- construction sector
- export buyers

### Social effects of shortage
Commodity shortages should map into different social outcomes.

- staple_food shortage -> needs_gap, unrest, trust decline, black market growth
- fuel shortage -> transport_cost_index, goods scarcity, rural isolation, security risk
- cement shortage -> housing backlog, infrastructure delay, urban rent pressure
- medicine shortage -> mortality pressure, trust collapse, legitimacy loss
- power shortage -> industrial output loss, service decay, nighttime insecurity

### Informal economy and patronage
The system should explicitly model alternative allocation channels.

- informal markets can soften household hardship but raise prices and reduce tax capture
- patronage networks can redirect scarce imports to favored regions or classes
- corruption becomes more damaging when strategic goods are rationed administratively
- smuggling becomes more attractive when tariff gaps and scarcity are high

### Class and regional politics
The supply chain should create distributional conflict.

- farmers want fertilizer, fuel, and roads
- industrialists want power, import licenses, and machine parts
- urban workers want affordable food, transport, and housing
- peripheral regions want investment and local processing rather than pure extraction
- state planners want coherence, buffers, and strategic autonomy

## Mechanics To Add

### 1. Commodity registry
Add a commodity definition layer with:
- id
- category
- perishability
- strategic_priority
- storage_decay
- importability
- exportability
- substitution_group

### 2. Recipe-based production
Each industry node should declare:
- consumed commodities per unit output
- produced commodities
- labor requirements
- skilled labor share
- power requirement
- maintenance requirement
- emissions or pollution signal
- location constraints

### 3. Maintenance inputs
Large industry should require upkeep inputs, not just labor and budget.
Examples:
- machine_parts maintain factories, steelworks, refineries, power plants
- cement and steel maintain infrastructure durability
- fuel maintains logistics throughput

### 4. Storage and buffers
Inventories should be commodity-specific.
- food can spoil
- fuel can buffer shocks for a while
- machine parts are low-volume but high-strategy
- emergency reserves should exist for a few critical commodities

### 5. Logistics capacity by corridor
Replace part of the generic logistics index with route classes:
- local roads
- state highways
- rail corridors
- ports
- inland depots

Each corridor should track:
- throughput capacity
- reliability
- cost
- security risk
- maintenance backlog

### 6. Market-clearing by place, not only nation
National abundance should not guarantee local access.
At minimum the model should clear goods at:
- national level
- state level
- subregion or urban-market cluster level

### 7. Substitution and adaptation
Agents should adapt, but at a cost.
Examples:
- diesel generators can partly substitute for grid power
- imported food can partly replace domestic shortfall if reserves and ports allow
- low-quality informal goods can substitute for formal consumer goods
- wood or charcoal can substitute for fuel in poorer regions, with ecological penalties

## Implementation Strategy In This Codebase

### Phase 1: Introduce named commodities without deleting the old sector model
Files:
- `src/econ/sector_network.py`
- new `src/econ/commodity_registry.py`
- new `src/econ/industry_recipes.py`

Tasks:
- add a commodity catalog and recipe definitions
- compute commodity production and demand in parallel with current sector outputs
- preserve legacy outputs by aggregating commodities back into sector metrics for compatibility

Deliverable:
- sector model still works
- state now includes `commodity_state`

### Phase 2: Promote buildings into industry nodes
Files:
- `src/econ/building_types.py`
- `src/econ/building_engine.py`

Tasks:
- map each building archetype to one or more recipe families
- add new building archetypes for extraction, processing, logistics, storage, and distribution
- track per-building input constraints and named outputs

Deliverable:
- buildings produce and consume named commodities, not only generic sector output

### Phase 3: Add logistics and storage
Files:
- new `src/econ/logistics_network.py`
- `src/core/scenario_loader.py`
- `src/core/stages.py`

Tasks:
- define corridor capacities and regional storage
- move commodities through routes before final demand is satisfied
- expose failures as route congestion, spoilage, and local scarcity

Deliverable:
- shortages can be regional even when national totals are positive

### Phase 4: Split demand socially and institutionally
Files:
- `src/core/stages.py`
- social-state modules already handling trust, unrest, and class dynamics

Tasks:
- create separate demand blocs and scarcity burdens
- link food, fuel, medicine, housing, and transport access to needs, trust, legitimacy, and unrest
- add informal-market and rationing responses

Deliverable:
- supply shocks generate differentiated class and regional politics

### Phase 5: Add economy presets
Files:
- `data/scenarios/`
- `src/core/scenario_loader.py`

Tasks:
- define several preset economy graphs and regional endowment mixes
- keep each preset curated and intelligible
- let scenarios choose one preset plus modifiers

Deliverable:
- replayability through distinct economic identities

### Phase 6: Revamp UI and observability
Files:
- `src/ui/tui_app.py`
- `src/ui/insight_views.py`

Tasks:
- add commodity flow sheets
- add chokepoint dashboards
- show top shortages by commodity, region, and class impact
- display corridor utilization, storage days, and import dependency for strategic goods

Deliverable:
- the player can actually understand the chain they are managing

## Minimal Viable Revamp
Do not begin with the full heavy-industry dream. The first playable version should include only a few strategic commodities and a small number of node types.

### Recommended MVP commodities
- staple_food
- fuel
- power
- cement
- steel
- machine_parts
- consumer_goods

### Recommended MVP node families
- farms
- refineries
- power_plants
- steelworks
- cement_plants
- machine_shops
- food_processing_plants
- warehouses
- ports
- trucking_depots
- municipal_markets

### Why this MVP works
It creates visible chokepoints in:
- food security
- energy security
- construction capacity
- industrial maintenance
- urban living standards

That is enough to generate meaningful economics and sociology without overwhelming the implementation.

## Metrics To Track
The revamp needs new state variables that are explainable in the UI and test suite.

### Commodity metrics
- production by commodity
- delivered demand by commodity
- shortage by commodity
- import share by commodity
- reserve cover in months by commodity
- spoilage and loss by commodity

### Logistics metrics
- corridor utilization
- corridor reliability
- storage occupancy
- average delivery delay
- local market access score

### Social metrics
- food stress by class
- fuel stress by region
- housing backlog
- black market share
- ration dependence
- scarcity-driven unrest contribution

### Structural metrics
- upstream concentration risk
- import dependence for strategic goods
- industrial diversification index
- domestic value-add share
- regional production concentration

## Policy Layer Implications
A deeper supply chain should make policy more concrete.

### New policy families
- strategic reserve management
- rationing intensity
- import licensing regime
- anti-hoarding enforcement
- freight subsidy or priority routing
- fertilizer support
- refinery and power maintenance push
- local processing requirements
- industrial localization mandates
- emergency food import program

### Trade-offs to preserve
- cheap imports can stabilize cities but weaken domestic producers
- protection can nurture industry but intensify short-run shortages
- rationing can preserve survival but fuel corruption and elite capture
- infrastructure spending can relieve bottlenecks but crowd out social spending
- regional balancing can improve legitimacy but lower short-run efficiency

## Test And Validation Strategy
The revamp should be validated like an economic engine, not only like a game feature.

### Deterministic tests
- identical seed and policy path produce identical commodity histories
- route and inventory updates are stable and reproducible

### Economic logic tests
- fertilizer shortage reduces farm output with lag
- machine-parts shortage degrades heavy industry capacity over time
- port closure raises import shortages before national production adjusts
- cement shortage delays construction completion and housing expansion

### Social logic tests
- food shortage increases needs gap and unrest faster in urban-heavy states
- rationing reduces mortality pressure but increases corruption pressure
- regional allocation bias increases representation gap and peripheral unrest

### UI validation
- the player can identify the top three chokepoints from one dashboard pass
- every major shortage can be traced to a cause chain

## Recommended Sequencing Decision
The cleanest path is:
1. keep current sector outputs as compatibility wrappers
2. add commodity-state underneath them
3. route buildings into named commodity recipes
4. add logistics and social scarcity next
5. only then add more economy presets and advanced chains

That avoids a full rewrite while still moving the simulation toward a richer, FIRS-like industrial economy.

## Final Recommendation
Build the revamp around a small number of named strategic goods, region-specific industry graphs, and socially differentiated demand.

If the simulation gets those three things right, it will stop feeling like a macro dashboard with building flavor and start feeling like a political economy simulator where production, geography, institutions, and class conflict genuinely interact.
