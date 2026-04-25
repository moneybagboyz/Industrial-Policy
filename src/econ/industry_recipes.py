"""Industry recipe definitions for the supply chain system.

Each building archetype maps to one or more *recipes* that describe what
commodities it consumes as inputs and produces as outputs per tick of
full operation.

Recipe fields:
    inputs      : dict[commodity_id -> units_per_capacity_point]
                  These are consumed from regional stocks each tick.
    outputs     : dict[commodity_id -> units_per_capacity_point]
                  These are added to regional stocks each tick.
    power_draw  : float, fraction of building's output capacity consumed as
                  power per tick (requires "power" commodity to be available).
    labor_skill : minimum human_capital required before output efficiency degrades.
    maintenance_commodity : commodity used for maintenance (usually machine_parts
                            or fuel); absence reduces maintenance effectiveness.
    notes       : human-readable description of the chain position.

Production calculation:
    actual_output_units[commodity] = recipe.outputs[commodity]
                                     × building.output        (the aggregate 0-1 float)
                                     × input_availability     (0-1, based on input stocks)
                                     × power_availability     (0-1, depends on power stock)

A building that has no recipe (e.g. a hospital) still contributes its generic
sector output to the legacy sector_network path.  Recipes add a *parallel*
named-commodity layer; they do not replace the legacy path in Phase 2.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Recipe definitions
# ---------------------------------------------------------------------------

BUILDING_RECIPES: dict[str, list[dict[str, Any]]] = {
    # ── Agriculture ──────────────────────────────────────────────────────────
    "farm": [
        {
            "inputs": {
                "fertilizer": 0.10,     # 0.10 fertilizer units per output point
                "fuel": 0.05,           # machinery fuel
            },
            "outputs": {
                "staple_food": 1.00,
            },
            "power_draw": 0.05,
            "labor_skill": 0.30,
            "maintenance_commodity": "machine_parts",
            "notes": "Basic crop farming. Fertilizer significantly boosts yield.",
        },
    ],
    "irrigation_district": [
        {
            "inputs": {
                "power": 0.20,          # pumping power
            },
            "outputs": {
                # Irrigation multiplies farm output rather than producing food directly.
                # This is tracked as a yield_boost signal, not a commodity stock.
                # We represent it here as a small fertilizer-equivalent output.
                "fertilizer": 0.15,
            },
            "power_draw": 0.20,
            "labor_skill": 0.35,
            "maintenance_commodity": "machine_parts",
            "notes": "Pumped irrigation. Raises effective soil fertility for nearby farms.",
        },
    ],

    # ── Energy ──────────────────────────────────────────────────────────────
    "coal_power_plant": [
        {
            "inputs": {
                "coal": 0.80,
            },
            "outputs": {
                "power": 1.00,
            },
            "power_draw": 0.0,          # zero: power plants don't consume their own output
            "labor_skill": 0.45,
            "maintenance_commodity": "machine_parts",
            "notes": "Burns coal to generate grid power.",
        },
    ],
    "oil_gas_well": [
        {
            "inputs": {},               # extraction; raw endowment is the 'input'
            "outputs": {
                "crude_oil": 0.90,
            },
            "power_draw": 0.08,
            "labor_skill": 0.50,
            "maintenance_commodity": "machine_parts",
            "notes": "Extracts crude oil. Output scaled by geo oil/gas endowment.",
        },
    ],

    # ── Manufacturing ────────────────────────────────────────────────────────
    "factory": [
        {
            # Consumer goods factory: needs steel for tooling, fuel for heat, power for machines.
            "inputs": {
                "steel": 0.08,
                "fuel": 0.10,
                "power": 0.25,
            },
            "outputs": {
                "consumer_goods": 1.00,
            },
            "power_draw": 0.25,
            "labor_skill": 0.45,
            "maintenance_commodity": "machine_parts",
            "notes": "Light-to-medium consumer goods manufacturing.",
        },
        {
            # Machine parts factory variant: needs iron ore + power, outputs machine_parts.
            "inputs": {
                "iron_ore": 0.30,
                "steel": 0.15,
                "power": 0.30,
            },
            "outputs": {
                "machine_parts": 0.60,
            },
            "power_draw": 0.30,
            "labor_skill": 0.55,
            "maintenance_commodity": "machine_parts",
            "notes": "Capital goods / machine-parts variant factory (needs skilled labor).",
        },
    ],
    "steel_mill": [
        {
            "inputs": {
                "iron_ore": 0.70,
                "coal": 0.40,
                "power": 0.20,
            },
            "outputs": {
                "steel": 1.00,
            },
            "power_draw": 0.20,
            "labor_skill": 0.50,
            "maintenance_commodity": "machine_parts",
            "notes": "Converts iron ore + coal into steel. Core industrial-belt node.",
        },
    ],

    # ── Construction ─────────────────────────────────────────────────────────
    "construction_yard": [
        {
            "inputs": {
                "cement": 0.50,
                "steel": 0.20,
                "fuel": 0.10,
            },
            "outputs": {
                # Construction yards consume commodities and produce built capacity,
                # which is tracked via the legacy build_capacity metric.
                # We also model a small 'stone_aggregate' return as rubble/spoil.
                "stone_aggregate": 0.05,
            },
            "power_draw": 0.10,
            "labor_skill": 0.38,
            "maintenance_commodity": "fuel",
            "notes": "Consumes cement and steel to build infrastructure and housing.",
        },
    ],
    "road_rail_hub": [
        {
            "inputs": {
                "fuel": 0.15,
                "machine_parts": 0.05,
            },
            "outputs": {
                # Hubs reduce transport friction; no commodity 'output' per se.
                # We represent the logistics throughput as a small consumer_goods
                # redistribution bonus (downstream effect is in logistics layer).
            },
            "power_draw": 0.05,
            "labor_skill": 0.35,
            "maintenance_commodity": "machine_parts",
            "notes": "Fuel + parts upkeep reduces transport friction across region.",
        },
    ],

    # ── Services (no commodity recipes — legacy sector path only) ────────────
    # hospital, university, market_bazaar, military_barracks intentionally omitted.
    # They contribute to the legacy sector_output path and Phase 4 social demand.
}

# Fallback recipe used when a building type has no explicit recipe entry.
# Returns empty inputs/outputs so the legacy sector_output path is the only output.
_NULL_RECIPE: dict[str, Any] = {
    "inputs": {},
    "outputs": {},
    "power_draw": 0.0,
    "labor_skill": 0.0,
    "maintenance_commodity": None,
    "notes": "No commodity recipe — legacy sector output only.",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_recipes(building_type: str) -> list[dict[str, Any]]:
    """Return the recipe list for a building type.

    Most buildings have a single primary recipe (index 0).  Some (like factory)
    have multiple variants; the engine uses the first recipe by default unless
    the building has a ``recipe_variant`` field set to a non-zero index.
    """
    return BUILDING_RECIPES.get(building_type, [_NULL_RECIPE])


def get_active_recipe(building: dict[str, Any]) -> dict[str, Any]:
    """Return the active recipe for a building dict.

    Reads the building's ``recipe_variant`` field (default 0) to select from
    the archetype's recipe list.
    """
    btype = str(building.get("type", ""))
    recipes = get_recipes(btype)
    variant = int(building.get("recipe_variant", 0))
    variant = max(0, min(variant, len(recipes) - 1))
    return recipes[variant]


def compute_input_availability(
    recipe: dict[str, Any],
    regional_stocks: dict[str, float],
    building_output: float,
) -> float:
    """Compute 0-1 input availability ratio for this recipe given current stocks.

    Returns 1.0 if all inputs are satisfied, lower if any input is scarce.
    The most constraining input determines overall availability.
    The function does NOT deduct from stocks; deduction happens in the caller.

    ``building_output`` is the building's computed output float (capacity ×
    utilization × condition × quality) used to scale required input quantities.
    """
    inputs: dict[str, float] = recipe.get("inputs", {})
    if not inputs:
        return 1.0

    min_ratio = 1.0
    for commodity_id, rate in inputs.items():
        required = rate * building_output
        if required <= 0.0:
            continue
        available = max(0.0, float(regional_stocks.get(commodity_id, 0.0)))
        ratio = min(1.0, available / required) if required > 0 else 1.0
        if ratio < min_ratio:
            min_ratio = ratio

    return min_ratio


def compute_commodity_outputs(
    recipe: dict[str, Any],
    building_output: float,
    input_availability: float,
    power_availability: float,
) -> dict[str, float]:
    """Compute actual commodity outputs for one building tick.

    Returns a dict of {commodity_id: units_produced}.
    """
    effective_scale = building_output * input_availability * power_availability
    result: dict[str, float] = {}
    for commodity_id, rate in recipe.get("outputs", {}).items():
        result[commodity_id] = max(0.0, rate * effective_scale)
    return result


def compute_commodity_inputs_consumed(
    recipe: dict[str, Any],
    building_output: float,
    input_availability: float,
    power_availability: float,
) -> dict[str, float]:
    """Compute actual commodities consumed from stocks for one building tick."""
    effective_scale = building_output * input_availability * power_availability
    result: dict[str, float] = {}
    for commodity_id, rate in recipe.get("inputs", {}).items():
        result[commodity_id] = max(0.0, rate * effective_scale)
    return result
