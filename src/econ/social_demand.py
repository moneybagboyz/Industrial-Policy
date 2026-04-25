"""Social demand blocs and scarcity-burden signals.

Phase 4 introduces differentiated demand pressure across households,
institutions, and productive sectors, and maps scarcity into class burdens.

This module reads commodity stocks and logistics shortfalls from ``region_state``
and returns normalized indicators that downstream social stages can consume.
"""

from __future__ import annotations

from typing import Any

from src.econ.commodity_registry import COMMODITY_CATALOG
from src.econ.logistics_network import aggregate_region_stocks, estimate_region_demand


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _safe_div(num: float, den: float) -> float:
    return num / den if den > 1e-9 else 0.0


def _collect_regions(region_state: dict[str, Any]) -> dict[str, Any]:
    regions = region_state.get("regions", {}) if isinstance(region_state, dict) else {}
    return regions if isinstance(regions, dict) else {}


def _national_population(regions: dict[str, Any]) -> float:
    total = 0.0
    for row in regions.values():
        if isinstance(row, dict):
            total += max(1.0, float(row.get("population", 1.0)))
    return max(1.0, total)


def _national_coverage(region_state: dict[str, Any], commodity_id: str) -> float:
    """Return a 0..1.5 coverage ratio (stock/demand) for a commodity."""
    regions = _collect_regions(region_state)
    if not regions:
        return 0.0

    total_stock = 0.0
    total_demand = 0.0
    for region_name, row in regions.items():
        if not isinstance(row, dict):
            continue
        pop = max(1.0, float(row.get("population", 1.0)))
        total_demand += estimate_region_demand(pop, commodity_id)
        stock_map = aggregate_region_stocks(row)
        total_stock += max(0.0, float(stock_map.get(commodity_id, 0.0)))

    return _clamp(_safe_div(total_stock, total_demand), 0.0, 1.5)


def _coverage_map(region_state: dict[str, Any]) -> dict[str, float]:
    return {cid: _national_coverage(region_state, cid) for cid in COMMODITY_CATALOG}


def compute_social_demand_signals(prior_state: dict[str, Any]) -> dict[str, float]:
    """Compute social demand, scarcity burden, and adaptation signals.

    Returns normalized metrics used by ``update_logistics_and_market``,
    ``update_class_dynamics``, and ``update_social_political``.
    """
    region_state = prior_state.get("region_state", {})
    coverage = _coverage_map(region_state if isinstance(region_state, dict) else {})

    food_access = _clamp((coverage.get("staple_food", 0.0) * 0.75 + coverage.get("imported_food", 0.0) * 0.25), 0.0, 1.0)
    fuel_access = _clamp(coverage.get("fuel", 0.0), 0.0, 1.0)
    power_access = _clamp((coverage.get("power", 0.0) * 0.85 + coverage.get("diesel_power", 0.0) * 0.15), 0.0, 1.0)
    medicine_access = _clamp(coverage.get("medicine", 0.0), 0.0, 1.0)
    consumer_access = _clamp(
        coverage.get("consumer_goods", 0.0) * 0.75 + coverage.get("informal_goods", 0.0) * 0.25,
        0.0,
        1.0,
    )
    machine_access = _clamp(coverage.get("machine_parts", 0.0), 0.0, 1.0)
    materials_access = _clamp(
        coverage.get("steel", 0.0) * 0.50 + coverage.get("cement", 0.0) * 0.35 + coverage.get("stone_aggregate", 0.0) * 0.15,
        0.0,
        1.0,
    )

    logistics_bottleneck = _clamp(float(prior_state.get("logistics_bottleneck_index", 0.25)), 0.0, 1.0)
    building_transport = _clamp(float(prior_state.get("building_transport_modifier", 1.0)), 0.5, 1.0)
    # Higher building transport modifier means lower friction.
    transport_access = _clamp(1.0 - logistics_bottleneck * 0.75 - (1.0 - building_transport) * 0.25, 0.0, 1.0)

    # Demand bloc pressures (0..1): 0 = fully served, 1 = severe scarcity.
    household_pressure = _clamp(
        (1.0 - food_access) * 0.30
        + (1.0 - fuel_access) * 0.18
        + (1.0 - power_access) * 0.17
        + (1.0 - medicine_access) * 0.17
        + (1.0 - consumer_access) * 0.10
        + (1.0 - transport_access) * 0.08,
        0.0,
        1.0,
    )
    institutional_pressure = _clamp(
        (1.0 - medicine_access) * 0.30
        + (1.0 - power_access) * 0.25
        + (1.0 - fuel_access) * 0.20
        + (1.0 - transport_access) * 0.15
        + (1.0 - float(prior_state.get("service_perf", 0.6))) * 0.10,
        0.0,
        1.0,
    )
    productive_pressure = _clamp(
        (1.0 - machine_access) * 0.30
        + (1.0 - materials_access) * 0.24
        + (1.0 - power_access) * 0.18
        + (1.0 - fuel_access) * 0.16
        + (1.0 - transport_access) * 0.12,
        0.0,
        1.0,
    )

    unemployment = _clamp(float(prior_state.get("unemployment", 0.08)), 0.0, 0.5)
    state_capacity = _clamp(float(prior_state.get("capacity", 50.0)) / 100.0, 0.0, 1.0)

    # Adaptation channels.
    rationing_intensity = _clamp(household_pressure * (0.35 + state_capacity * 0.50), 0.0, 1.0)
    informal_market_response = _clamp(household_pressure * (0.45 + unemployment * 0.90) * (1.0 - state_capacity * 0.45), 0.0, 1.0)

    # Adaptation mitigates direct need pressure but has legitimacy tradeoffs downstream.
    adapted_household_pressure = _clamp(
        household_pressure - rationing_intensity * 0.20 - informal_market_response * 0.18,
        0.0,
        1.0,
    )

    scarcity_burden_workers = _clamp(adapted_household_pressure * 0.65 + institutional_pressure * 0.20, 0.0, 1.0)
    scarcity_burden_informal = _clamp(adapted_household_pressure * 0.72 + unemployment * 0.18 + (1.0 - medicine_access) * 0.10, 0.0, 1.0)
    scarcity_burden_professionals = _clamp(institutional_pressure * 0.52 + adapted_household_pressure * 0.18 + productive_pressure * 0.15, 0.0, 1.0)
    scarcity_burden_capitalists = _clamp(productive_pressure * 0.68 + (1.0 - transport_access) * 0.18 + (1.0 - machine_access) * 0.14, 0.0, 1.0)

    needs_gap_from_blocs = _clamp(
        adapted_household_pressure * 0.55 + institutional_pressure * 0.25 + productive_pressure * 0.20,
        0.0,
        1.0,
    )

    return {
        "food_access_index": food_access,
        "fuel_access_index": fuel_access,
        "power_access_index": power_access,
        "medicine_access_index": medicine_access,
        "consumer_access_index": consumer_access,
        "machine_parts_access_index": machine_access,
        "materials_access_index": materials_access,
        "transport_access_index": transport_access,
        "demand_bloc_household_pressure": household_pressure,
        "demand_bloc_institutional_pressure": institutional_pressure,
        "demand_bloc_productive_pressure": productive_pressure,
        "rationing_intensity": rationing_intensity,
        "informal_market_response": informal_market_response,
        "needs_gap_from_blocs": needs_gap_from_blocs,
        "scarcity_burden_workers": scarcity_burden_workers,
        "scarcity_burden_professionals": scarcity_burden_professionals,
        "scarcity_burden_capitalists": scarcity_burden_capitalists,
        "scarcity_burden_informal": scarcity_burden_informal,
    }
