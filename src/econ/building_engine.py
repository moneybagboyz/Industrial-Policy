"""Per-tick update engine for physical building instances.

Each tick a building:
  1. Degrades in condition based on maintenance spend vs degradation rate.
  2. Adjusts utilization toward sector demand signal.
  3. Computes output as: capacity × utilization × condition × quality_modifier.
  4. Computes effective workers actually employed (utilization × baseline headcount).
  5. Tracks the owner class for income routing into class dynamics.

The module also provides aggregation helpers that roll building data up to
subregion and sector totals consumed by sector_network.py.
"""

from __future__ import annotations

from typing import Any

from src.econ.building_types import (
    BUILDING_ARCHETYPES,
    SECTOR_DEFAULT_BUILDINGS,
    get_archetype,
    scaled_capacity,
    scaled_workers,
    scaled_workers_skilled,
)
from src.econ.industry_recipes import (
    get_active_recipe,
    compute_input_availability,
    compute_commodity_outputs,
    compute_commodity_inputs_consumed,
)
from src.econ.commodity_registry import build_empty_commodity_state

_OWNER_CLASSES = ("capitalist", "state", "cooperative", "informal")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _deterministic_noise(seed_int: int, idx: int, salt: int) -> float:
    raw = ((seed_int + idx * 31 + salt * 17) % 101) / 100.0
    return raw - 0.5


# ---------------------------------------------------------------------------
# Initial building seeding
# ---------------------------------------------------------------------------

def seed_buildings_for_subregion(
    subregion_name: str,
    state_archetype: str,
    population: float,
    human_capital: float,
    infrastructure: float,
    scenario_seed: int,
    subregion_idx: int,
    resource_endowment: float = 0.5,
    land_availability: float = 0.5,
    geo_profile: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Return a seed list of building instances appropriate for a subregion.

    Building counts are constrained by three physical bounds:
    - ``land_availability`` (0-1): caps land-intensive buildings (farms,
      industrial yards, power plants).  Derived from 1 - land_concentration.
    - ``resource_endowment`` (0-1): gates resource-extractive buildings
      (coal/oil, steel mills).  Buildings whose sector is energy or whose
      type is ``steel_mill`` or ``oil_gas_well`` are blocked when this is low.
    - Labour capacity: total seeded workers are bounded to
      ``population × 0.65`` so buildings never exceed the available labour
      force.

    Uses fully deterministic pseudo-random seeding so replay is stable.
    """
    buildings: list[dict[str, Any]] = []

    geo = _coerce_geo_profile(
        geo_profile=geo_profile,
        resource_endowment=resource_endowment,
        land_availability=land_availability,
        infrastructure=infrastructure,
        human_capital=human_capital,
    )
    noise_base = (scenario_seed + subregion_idx * 37) % 997

    # Intensity multipliers by archetype (controls how many buildings of each
    # sector are seeded in a subregion).
    archetype_intensity: dict[str, dict[str, float]] = {
        "agro_periphery":   {"agriculture": 2.0, "energy": 0.6, "manufacturing": 0.5, "construction": 0.6, "services": 0.6},
        "resource_core":    {"agriculture": 0.7, "energy": 2.5, "manufacturing": 0.8, "construction": 0.7, "services": 0.7},
        "industrial_belt":  {"agriculture": 0.6, "energy": 1.2, "manufacturing": 2.5, "construction": 1.2, "services": 0.9},
        "service_metro":    {"agriculture": 0.3, "energy": 0.8, "manufacturing": 0.9, "construction": 0.8, "services": 2.5},
        "fragile_frontier": {"agriculture": 1.2, "energy": 0.5, "manufacturing": 0.4, "construction": 0.5, "services": 0.5},
    }
    intensities = archetype_intensity.get(state_archetype, {s: 1.0 for s in SECTOR_DEFAULT_BUILDINGS})

    pop_scale = _clamp(population / 300_000.0, 0.3, 4.0)

    # Land-use cost per archetype tag: "high" land use is reduced by land scarcity.
    land_cost = {"high": 1.0, "medium": 0.5, "low": 0.0}

    # Labour capacity bound: total workers seeded must not exceed this.
    labour_capacity = max(1.0, population * 0.65)
    total_workers_so_far = 0.0

    building_uid = 0

    for sector, btype_list in SECTOR_DEFAULT_BUILDINGS.items():
        intensity = intensities.get(sector, 1.0)
        count = max(1, int(round(intensity * pop_scale)))
        for btype in btype_list:
            arch = get_archetype(btype)

            if not _passes_hard_constraints(btype, geo):
                continue

            viability = _building_viability_score(btype, sector, geo)
            if viability <= 0.12:
                continue

            # --- Land cap and viability scaling ---
            # High land-use buildings are scaled down when land is scarce.
            lu = str(arch.get("land_use", "low"))
            land_penalty = land_cost.get(lu, 0.0)
            # land_availability of 0 → 0 high-land buildings; of 1 → full count
            effective_count = max(0, int(round(
                count
                * (1.0 - land_penalty * (1.0 - land_availability))
                * viability
            )))
            if effective_count <= 0:
                continue

            for i in range(effective_count):
                noise_val = _deterministic_noise(noise_base, building_uid, 7)
                level = 1
                condition = _clamp(infrastructure * 0.6 + 0.3 + noise_val * 0.15, 0.25, 0.98)
                utilization = _clamp(0.65 + noise_val * 0.18, 0.30, 0.95)
                quality = _clamp(human_capital * 0.7 + 0.2 + noise_val * 0.10, 0.15, 0.98)
                owner_idx = int(len(arch.get("owner_classes", ["state"])) * abs(noise_val)) % len(arch.get("owner_classes", ["state"]))
                owner = arch["owner_classes"][owner_idx]
                workers_base = scaled_workers(btype, level)
                workers_skilled_base = scaled_workers_skilled(btype, level)
                cap = scaled_capacity(btype, level)

                # --- Labour capacity bound ---
                # Stop adding buildings once the subregion labour force is full.
                workers_this = int(workers_base * utilization)
                if total_workers_so_far + workers_this > labour_capacity:
                    building_uid += 1
                    continue
                total_workers_so_far += workers_this

                buildings.append({
                    "id": f"{btype}_{i:02d}_{subregion_name}",
                    "type": btype,
                    "sector": arch["sector"],
                    "level": level,
                    "condition": condition,
                    "capacity": cap,
                    "utilization": utilization,
                    "output_quality": quality,
                    "workers": workers_this,
                    "workers_max": workers_base,
                    "workers_skilled": int(workers_skilled_base * utilization),
                    "workers_skilled_max": workers_skilled_base,
                    "age_ticks": int(abs(noise_val) * 48),
                    "owner_class": owner,
                    "maintenance_deficit": 0.0,
                    "output": cap * utilization * condition * quality,
                    "geo_viability": viability,
                })
                building_uid += 1

    return buildings


def _coerce_geo_profile(
    geo_profile: dict[str, float] | None,
    resource_endowment: float,
    land_availability: float,
    infrastructure: float,
    human_capital: float,
) -> dict[str, float]:
    defaults = {
        "fertility": _clamp(0.45 + (land_availability - 0.5) * 0.40, 0.0, 1.0),
        "water_access": 0.50,
        "oil_endowment": resource_endowment,
        "gas_endowment": resource_endowment,
        "iron_endowment": resource_endowment,
        "coal_endowment": resource_endowment,
        "stone_endowment": _clamp(0.40 + resource_endowment * 0.40, 0.0, 1.0),
        "coastal_access": 0.20,
        "river_access": 0.40,
        "transport_connectivity": _clamp(infrastructure * 0.80 + 0.15, 0.0, 1.0),
        "grid_reliability": _clamp(infrastructure * 0.85 + 0.10, 0.0, 1.0),
        "market_access": _clamp(infrastructure * 0.50 + 0.30, 0.0, 1.0),
        "state_capacity": _clamp(infrastructure * 0.55 + 0.25, 0.0, 1.0),
        "human_capital": _clamp(human_capital, 0.0, 1.0),
        "insecurity": 0.35,
    }
    if isinstance(geo_profile, dict):
        for key, value in geo_profile.items():
            try:
                defaults[key] = _clamp(float(value), 0.0, 1.0)
            except (TypeError, ValueError):
                continue
    return defaults


def _passes_hard_constraints(building_type: str, geo: dict[str, float]) -> bool:
    if building_type == "oil_gas_well":
        return max(geo.get("oil_endowment", 0.0), geo.get("gas_endowment", 0.0)) >= 0.40
    if building_type == "coal_power_plant":
        return geo.get("coal_endowment", 0.0) >= 0.30 and geo.get("grid_reliability", 0.0) >= 0.25
    if building_type == "steel_mill":
        return geo.get("iron_endowment", 0.0) >= 0.35 and geo.get("coal_endowment", 0.0) >= 0.25
    if building_type == "farm":
        return geo.get("fertility", 0.0) >= 0.25 and geo.get("water_access", 0.0) >= 0.20
    if building_type == "irrigation_district":
        return geo.get("water_access", 0.0) >= 0.35
    return True


def _building_viability_score(building_type: str, sector: str, geo: dict[str, float]) -> float:
    infra = geo.get("transport_connectivity", 0.5)
    grid = geo.get("grid_reliability", 0.5)
    market = geo.get("market_access", 0.5)
    state_cap = geo.get("state_capacity", 0.5)
    human = geo.get("human_capital", 0.5)
    insecurity = geo.get("insecurity", 0.35)
    insecurity_penalty = 1.0 - insecurity * 0.45

    if building_type == "farm":
        score = 0.55 * geo.get("fertility", 0.5) + 0.30 * geo.get("water_access", 0.5) + 0.15 * infra
    elif building_type == "irrigation_district":
        score = 0.60 * geo.get("water_access", 0.5) + 0.25 * state_cap + 0.15 * infra
    elif building_type == "oil_gas_well":
        score = 0.65 * max(geo.get("oil_endowment", 0.5), geo.get("gas_endowment", 0.5)) + 0.20 * infra + 0.15 * state_cap
    elif building_type == "coal_power_plant":
        score = 0.45 * geo.get("coal_endowment", 0.5) + 0.30 * grid + 0.15 * state_cap + 0.10 * infra
    elif building_type == "steel_mill":
        ore_base = min(geo.get("iron_endowment", 0.5), geo.get("coal_endowment", 0.5))
        score = 0.45 * ore_base + 0.20 * grid + 0.15 * infra + 0.10 * human + 0.10 * market
    elif building_type in {"factory", "construction_yard"}:
        score = 0.35 * market + 0.25 * infra + 0.20 * grid + 0.10 * human + 0.10 * state_cap
    elif building_type in {"hospital", "university", "market_bazaar", "military_barracks"}:
        score = 0.45 * market + 0.25 * state_cap + 0.20 * human + 0.10 * infra
    elif building_type == "road_rail_hub":
        score = 0.45 * infra + 0.25 * market + 0.20 * state_cap + 0.10 * grid
    else:
        # Sector-level fallback keeps behavior deterministic for new archetypes.
        if sector == "agriculture":
            score = 0.55 * geo.get("fertility", 0.5) + 0.25 * geo.get("water_access", 0.5) + 0.20 * infra
        elif sector == "energy":
            score = 0.40 * max(geo.get("oil_endowment", 0.5), geo.get("gas_endowment", 0.5), geo.get("coal_endowment", 0.5)) + 0.30 * grid + 0.30 * infra
        elif sector == "manufacturing":
            score = 0.35 * market + 0.25 * infra + 0.20 * grid + 0.20 * human
        elif sector == "construction":
            score = 0.40 * infra + 0.30 * market + 0.30 * state_cap
        else:
            score = 0.45 * market + 0.30 * state_cap + 0.25 * human

    return _clamp(score * insecurity_penalty, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Per-tick update
# ---------------------------------------------------------------------------

def update_building(
    building: dict[str, Any],
    sector_demand_signal: float,
    maintenance_spend: float,
    human_capital: float,
    prior_state: dict[str, Any],
    regional_stocks: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute the next state for a single building instance.

    Args:
        building: current building dict (NOT mutated; returns new dict).
        sector_demand_signal: 0-1 normalized demand for this sector this tick.
        maintenance_spend: 0-1 fraction of rated maintenance actually funded.
        human_capital: subregion human capital score (0-1).
        prior_state: national state dict for policy overrides.
        regional_stocks: current commodity stocks for the subregion; used to
            compute input availability for the building's recipe.  If None,
            unlimited inputs are assumed (backward-compatible behaviour).
    """
    arch = get_archetype(str(building["type"]))
    degrad_rate = float(arch["degradation_rate"])
    skill_threshold = float(arch["skill_threshold"])

    # 1. Condition update
    effective_maintenance = _clamp(maintenance_spend, 0.0, 1.0)
    condition_delta = effective_maintenance * degrad_rate * 2.0 - degrad_rate
    condition = _clamp(float(building["condition"]) + condition_delta, 0.0, 1.0)

    # 2. Utilization: mean-reverts toward demand signal
    current_util = float(building["utilization"])
    target_util = _clamp(sector_demand_signal, 0.0, 1.0)
    utilization = _clamp(current_util * 0.70 + target_util * 0.30, 0.0, 1.0)

    # 3. Skill quality modifier: degrades if human_capital below threshold
    hc_gap = max(0.0, skill_threshold - human_capital)
    quality_modifier = _clamp(1.0 - hc_gap * 1.2, 0.20, 1.0)
    output_quality = _clamp(float(building["output_quality"]) * 0.80 + quality_modifier * 0.20, 0.10, 1.0)

    # 4. Output
    capacity = float(building["capacity"])
    output = capacity * utilization * condition * output_quality

    # 5. Effective workforce
    workers_max = int(building.get("workers_max", arch["base_workers"]))
    workers_skilled_max = int(building.get("workers_skilled_max", arch["base_workers_skilled"]))
    workers = int(workers_max * utilization)
    workers_skilled = int(workers_skilled_max * min(utilization, human_capital / max(skill_threshold, 0.01)))

    # 6. Maintenance deficit tracking (used for deterioration spiral)
    deficit_delta = (1.0 - effective_maintenance) * 0.05
    maintenance_deficit = _clamp(float(building.get("maintenance_deficit", 0.0)) + deficit_delta, 0.0, 1.0)
    if maintenance_deficit > 0.5:
        condition = max(0.0, condition - maintenance_deficit * 0.01)

    # --- Commodity recipe layer ---
    # Compute named commodity flows in parallel with the legacy output float.
    recipe = get_active_recipe(building)
    stocks = regional_stocks if isinstance(regional_stocks, dict) else {}
    power_draw = float(recipe.get("power_draw", 0.0))
    power_available = min(1.0, stocks.get("power", 1e9) / max(output * power_draw, 1e-9)) if power_draw > 0 else 1.0
    power_availability = _clamp(power_available, 0.0, 1.0) if power_draw > 0 else 1.0
    input_availability = compute_input_availability(recipe, stocks, output)
    commodity_outputs = compute_commodity_outputs(recipe, output, input_availability, power_availability)
    commodity_inputs_consumed = compute_commodity_inputs_consumed(recipe, output, input_availability, power_availability)

    return {
        **building,
        "condition": condition,
        "utilization": utilization,
        "output_quality": output_quality,
        "output": output,
        "workers": workers,
        "workers_skilled": workers_skilled,
        "age_ticks": int(building.get("age_ticks", 0)) + 1,
        "maintenance_deficit": maintenance_deficit,
        "commodity_outputs": commodity_outputs,
        "commodity_inputs_consumed": commodity_inputs_consumed,
        "input_availability": input_availability,
    }


def update_subregion_buildings(
    buildings: list[dict[str, Any]],
    sector_demand_signals: dict[str, float],
    maintenance_spend: float,
    human_capital: float,
    prior_state: dict[str, Any],
    regional_stocks: dict[str, float] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, float], dict[str, float]]:
    """Update all buildings in a subregion and return (updated_buildings, net_produced, net_consumed).

    The returned commodity dicts represent the *total* commodity flows across
    all buildings this tick, before storage decay is applied.  Callers should
    add net_produced to stocks and deduct net_consumed from stocks.

    For backward compatibility the function also accepts callers that ignore
    the extra return values.
    """
    # Use a mutable copy of stocks so each building within the tick sees the
    # same starting stocks (no intra-tick ordering dependency).
    stocks_snapshot: dict[str, float] = dict(regional_stocks) if isinstance(regional_stocks, dict) else {}

    updated: list[dict[str, Any]] = []
    total_produced: dict[str, float] = build_empty_commodity_state()
    total_consumed: dict[str, float] = build_empty_commodity_state()

    for b in buildings:
        if not isinstance(b, dict):
            continue
        sector = str(b.get("sector", b.get("type", "services")))
        demand_signal = sector_demand_signals.get(sector, 0.65)
        updated_b = update_building(b, demand_signal, maintenance_spend, human_capital, prior_state, stocks_snapshot)
        updated.append(updated_b)
        for cid, amount in updated_b.get("commodity_outputs", {}).items():
            total_produced[cid] = total_produced.get(cid, 0.0) + amount
        for cid, amount in updated_b.get("commodity_inputs_consumed", {}).items():
            total_consumed[cid] = total_consumed.get(cid, 0.0) + amount

    return updated, total_produced, total_consumed


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def aggregate_subregion_buildings(
    buildings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate per-building data into subregion-level building summary."""
    sector_output: dict[str, float] = {}
    sector_workers: dict[str, int] = {}
    sector_workers_skilled: dict[str, int] = {}
    total_workers = 0
    total_workers_skilled = 0
    total_output = 0.0
    health_index = 0.0
    research_output = 0.0
    transport_modifier = 1.0
    owner_output: dict[str, float] = {}

    for b in buildings:
        if not isinstance(b, dict):
            continue
        btype = str(b.get("type", "factory"))
        sector = str(b.get("sector", BUILDING_ARCHETYPES.get(btype, {}).get("sector", "services")))
        out = max(0.0, float(b.get("output", 0.0)))
        workers = int(b.get("workers", 0))
        workers_skilled = int(b.get("workers_skilled", 0))
        owner = str(b.get("owner_class", "state"))
        metric = str(BUILDING_ARCHETYPES.get(btype, {}).get("output_metric", "goods_units"))

        sector_output[sector] = sector_output.get(sector, 0.0) + out
        sector_workers[sector] = sector_workers.get(sector, 0) + workers
        sector_workers_skilled[sector] = sector_workers_skilled.get(sector, 0) + workers_skilled
        owner_output[owner] = owner_output.get(owner, 0.0) + out
        total_workers += workers
        total_workers_skilled += workers_skilled
        total_output += out

        if metric == "health_index":
            health_index += out
        elif metric == "research_points":
            research_output += out
        elif metric == "transport_friction_modifier":
            transport_modifier *= max(0.5, 1.0 - out * 0.05)

    avg_condition = 0.0
    if buildings:
        avg_condition = sum(float(b.get("condition", 0.5)) for b in buildings if isinstance(b, dict)) / len(buildings)

    return {
        "sector_output": sector_output,
        "sector_workers": sector_workers,
        "sector_workers_skilled": sector_workers_skilled,
        "total_workers": total_workers,
        "total_workers_skilled": total_workers_skilled,
        "total_output": total_output,
        "health_index": health_index,
        "research_output": research_output,
        "transport_modifier": _clamp(transport_modifier, 0.5, 1.0),
        "avg_condition": avg_condition,
        "owner_output": owner_output,
    }


def aggregate_region_buildings(
    region: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate building data from all subregions of a state into state-level summary."""
    subregions = region.get("subregions", {})
    combined: dict[str, Any] = {
        "sector_output": {},
        "sector_workers": {},
        "total_workers": 0,
        "total_output": 0.0,
        "health_index": 0.0,
        "research_output": 0.0,
        "transport_modifier": 1.0,
        "avg_condition": 0.0,
        "owner_output": {},
    }
    n_subs = 0
    cond_sum = 0.0

    if not isinstance(subregions, dict):
        return combined

    for sub in subregions.values():
        if not isinstance(sub, dict):
            continue
        buildings = sub.get("buildings", [])
        if not isinstance(buildings, list):
            continue
        agg = aggregate_subregion_buildings(buildings)
        for sector, val in agg["sector_output"].items():
            combined["sector_output"][sector] = combined["sector_output"].get(sector, 0.0) + val
        for sector, val in agg["sector_workers"].items():
            combined["sector_workers"][sector] = combined["sector_workers"].get(sector, 0) + val
        for owner, val in agg["owner_output"].items():
            combined["owner_output"][owner] = combined["owner_output"].get(owner, 0.0) + val
        combined["total_workers"] += agg["total_workers"]
        combined["total_output"] += agg["total_output"]
        combined["health_index"] += agg["health_index"]
        combined["research_output"] += agg["research_output"]
        combined["transport_modifier"] *= agg["transport_modifier"]
        cond_sum += agg["avg_condition"]
        n_subs += 1

    if n_subs > 0:
        combined["avg_condition"] = cond_sum / n_subs

    return combined


def national_building_aggregates(
    region_state: dict[str, Any],
) -> dict[str, Any]:
    """Roll up building data from all states into national totals."""
    regions = region_state.get("regions", {}) if isinstance(region_state, dict) else {}
    nat: dict[str, Any] = {
        "sector_output": {},
        "sector_workers": {},
        "total_workers": 0,
        "total_output": 0.0,
        "health_index": 0.0,
        "research_output": 0.0,
        "transport_modifier": 1.0,
        "owner_output": {},
    }

    for region in regions.values():
        if not isinstance(region, dict):
            continue
        agg = aggregate_region_buildings(region)
        for sector, val in agg["sector_output"].items():
            nat["sector_output"][sector] = nat["sector_output"].get(sector, 0.0) + val
        for sector, val in agg["sector_workers"].items():
            nat["sector_workers"][sector] = nat["sector_workers"].get(sector, 0) + val
        for owner, val in agg["owner_output"].items():
            nat["owner_output"][owner] = nat["owner_output"].get(owner, 0.0) + val
        nat["total_workers"] += agg["total_workers"]
        nat["total_output"] += agg["total_output"]
        nat["health_index"] += agg["health_index"]
        nat["research_output"] += agg["research_output"]
        nat["transport_modifier"] *= agg["transport_modifier"]

    return nat


def make_building_from_queue_item(
    item: dict[str, Any],
    subregion_name: str,
    human_capital: float,
    infrastructure: float,
) -> dict[str, Any]:
    """Convert a completed construction queue item into a new building instance."""
    btype = str(item.get("type", "factory"))
    arch = get_archetype(btype)
    level = int(item.get("level", 1))
    noise = 0.1   # new buildings start with a slight quality head start
    condition = _clamp(infrastructure * 0.5 + 0.45 + noise, 0.40, 0.98)
    quality = _clamp(human_capital * 0.6 + 0.30, 0.20, 0.95)
    cap = scaled_capacity(btype, level)
    workers_base = scaled_workers(btype, level)
    workers_skilled_base = scaled_workers_skilled(btype, level)
    return {
        "id": f"{btype}_new_{subregion_name}",
        "type": btype,
        "sector": arch["sector"],
        "level": level,
        "condition": condition,
        "capacity": cap,
        "utilization": 0.60,
        "output_quality": quality,
        "workers": int(workers_base * 0.60),
        "workers_max": workers_base,
        "workers_skilled": int(workers_skilled_base * 0.60),
        "workers_skilled_max": workers_skilled_base,
        "age_ticks": 0,
        "owner_class": str(item.get("owner_class", arch["owner_classes"][0])),
        "maintenance_deficit": 0.0,
        "output": cap * 0.60 * condition * quality,
    }
