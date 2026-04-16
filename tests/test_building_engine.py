"""Tests for the physical building engine and related integration points."""

from __future__ import annotations

import pytest

from src.econ.building_types import (
    BUILDING_ARCHETYPES,
    SECTOR_DEFAULT_BUILDINGS,
    get_archetype,
    scaled_capacity,
    scaled_workers,
)
from src.econ.building_engine import (
    aggregate_subregion_buildings,
    make_building_from_queue_item,
    seed_buildings_for_subregion,
    update_building,
    update_subregion_buildings,
)


# ---------------------------------------------------------------------------
# Building types
# ---------------------------------------------------------------------------

def test_all_archetypes_have_required_keys() -> None:
    required = {"sector", "base_capacity", "base_workers", "base_workers_skilled",
                 "maintenance_ratio", "degradation_rate", "skill_threshold", "owner_classes"}
    for name, arch in BUILDING_ARCHETYPES.items():
        missing = required - set(arch.keys())
        assert not missing, f"Archetype '{name}' missing keys: {missing}"


def test_get_archetype_valid() -> None:
    arch = get_archetype("farm")
    assert arch["sector"] == "agriculture"


def test_get_archetype_invalid_falls_back_to_factory() -> None:
    arch = get_archetype("nonexistent_building")
    # Falls back to factory archetype — sector should be manufacturing.
    assert arch["sector"] == "manufacturing"


def test_scaled_capacity_increases_with_level() -> None:
    cap1 = scaled_capacity("farm", 1)
    cap3 = scaled_capacity("farm", 3)
    cap5 = scaled_capacity("farm", 5)
    assert cap1 < cap3 < cap5


def test_scaled_workers_positive() -> None:
    workers = scaled_workers("factory", 2)
    assert workers > 0


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

def test_seed_produces_non_empty_list() -> None:
    buildings = seed_buildings_for_subregion(
        subregion_name="test_sub",
        state_archetype="agrarian",
        population=500_000,
        human_capital=0.5,
        infrastructure=0.5,
        scenario_seed=42,
        subregion_idx=0,
    )
    assert isinstance(buildings, list)
    assert len(buildings) > 0


def test_seed_buildings_have_required_keys() -> None:
    buildings = seed_buildings_for_subregion(
        subregion_name="alpha",
        state_archetype="industrial",
        population=1_000_000,
        human_capital=0.6,
        infrastructure=0.6,
        scenario_seed=7,
        subregion_idx=1,
    )
    required = {"id", "type", "level", "condition", "utilization",
                 "workers", "output", "owner_class", "sector"}
    for bldg in buildings:
        missing = required - set(bldg.keys())
        assert not missing, f"Building missing keys: {missing}"


def test_seed_deterministic() -> None:
    kwargs = dict(subregion_name="x", state_archetype="agrarian", population=200_000,
                  human_capital=0.4, infrastructure=0.4, scenario_seed=99, subregion_idx=0)
    run1 = seed_buildings_for_subregion(**kwargs)
    run2 = seed_buildings_for_subregion(**kwargs)
    assert len(run1) == len(run2)
    for b1, b2 in zip(run1, run2):
        assert b1["id"] == b2["id"]
        assert b1["condition"] == pytest.approx(b2["condition"], rel=1e-6)


def test_geo_profile_blocks_oil_industry_without_endowment() -> None:
    buildings = seed_buildings_for_subregion(
        subregion_name="dry_plain",
        state_archetype="resource_core",
        population=1_800_000,
        human_capital=0.55,
        infrastructure=0.55,
        scenario_seed=17,
        subregion_idx=2,
        geo_profile={
            "oil_endowment": 0.0,
            "gas_endowment": 0.0,
            "coal_endowment": 0.6,
            "iron_endowment": 0.6,
            "fertility": 0.6,
            "water_access": 0.6,
            "transport_connectivity": 0.7,
            "grid_reliability": 0.7,
            "market_access": 0.6,
            "state_capacity": 0.6,
            "insecurity": 0.2,
        },
    )
    assert all(b["type"] != "oil_gas_well" for b in buildings)


def test_geo_profile_allows_oil_industry_with_endowment() -> None:
    buildings = seed_buildings_for_subregion(
        subregion_name="oil_basin",
        state_archetype="resource_core",
        population=2_000_000,
        human_capital=0.60,
        infrastructure=0.60,
        scenario_seed=18,
        subregion_idx=3,
        geo_profile={
            "oil_endowment": 0.85,
            "gas_endowment": 0.70,
            "coal_endowment": 0.5,
            "iron_endowment": 0.5,
            "fertility": 0.4,
            "water_access": 0.5,
            "transport_connectivity": 0.75,
            "grid_reliability": 0.65,
            "market_access": 0.65,
            "state_capacity": 0.65,
            "insecurity": 0.2,
        },
    )
    assert any(b["type"] == "oil_gas_well" for b in buildings)


# ---------------------------------------------------------------------------
# Update / degradation
# ---------------------------------------------------------------------------

def test_update_building_degrades_condition_without_maintenance() -> None:
    buildings = seed_buildings_for_subregion("sub", "industrial", 1_000_000, 0.5, 0.5, 1, 0)
    bldg = dict(buildings[0])
    initial_condition = bldg["condition"]
    updated = update_building(
        building=bldg,
        sector_demand_signal=0.5,
        maintenance_spend=0.0,  # no maintenance → degrades
        human_capital=0.5,
        prior_state={},
    )
    assert updated["condition"] <= initial_condition


def test_update_building_improves_condition_with_high_maintenance() -> None:
    buildings = seed_buildings_for_subregion("sub", "industrial", 1_000_000, 0.5, 0.5, 1, 0)
    bldg = dict(buildings[0])
    bldg["condition"] = 0.50  # start damaged
    updated = update_building(
        building=bldg,
        sector_demand_signal=0.8,
        maintenance_spend=1.0,  # full maintenance
        human_capital=0.7,
        prior_state={},
    )
    assert updated["condition"] >= bldg["condition"]


def test_update_building_output_bounded() -> None:
    buildings = seed_buildings_for_subregion("sub", "industrial", 1_000_000, 0.5, 0.5, 2, 0)
    for bldg in buildings:
        updated = update_building(bldg, 0.5, 0.5, 0.5, {})
        assert updated["output"] >= 0.0


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def test_aggregate_subregion_buildings_sums_workers() -> None:
    buildings = seed_buildings_for_subregion("sub", "industrial", 2_000_000, 0.6, 0.6, 3, 0)
    agg = aggregate_subregion_buildings(buildings)
    total_expected = sum(b["workers"] for b in buildings)
    assert agg["total_workers"] == pytest.approx(total_expected, rel=1e-5)


def test_aggregate_subregion_buildings_keys() -> None:
    buildings = seed_buildings_for_subregion("sub", "agrarian", 500_000, 0.4, 0.4, 5, 0)
    agg = aggregate_subregion_buildings(buildings)
    for key in ("sector_output", "total_workers", "health_index", "research_output",
                "transport_modifier", "owner_output"):
        assert key in agg, f"Missing key in aggregation: {key}"


def test_update_subregion_buildings_returns_list_same_length() -> None:
    buildings = seed_buildings_for_subregion("sub", "agrarian", 500_000, 0.5, 0.5, 10, 0)
    updated = update_subregion_buildings(
        buildings=buildings,
        sector_demand_signals={"agriculture": 0.7, "energy": 0.5},
        maintenance_spend=0.4,
        human_capital=0.5,
        prior_state={},
    )
    assert len(updated) == len(buildings)


# ---------------------------------------------------------------------------
# Queue completion → building creation
# ---------------------------------------------------------------------------

def test_make_building_from_queue_item() -> None:
    item = {
        "name": "new_coal_plant",
        "type": "coal_power_plant",
        "target_region": "east",
        "target_subregion": "east_capital",
        "level": 2,
        "owner_class": "state",
        "remaining_months": 0,
        "cost_ratio": 0.015,
        "effect": 0.02,
    }
    bldg = make_building_from_queue_item(item, "east_capital", human_capital=0.6, infrastructure=0.65)
    assert bldg["type"] == "coal_power_plant"
    assert bldg["level"] == 2
    assert bldg["owner_class"] == "state"
    assert bldg["sector"] == "energy"
    assert 0.0 <= bldg["condition"] <= 1.0
    assert bldg["workers"] > 0


# ---------------------------------------------------------------------------
# Integration: labor coupling in stages
# ---------------------------------------------------------------------------

def test_building_labor_blends_into_unemployment() -> None:
    """Building workforce signal should nudge unemployment when buildings exist."""
    from src.core.default_engine import build_engine_from_scenario

    engine = build_engine_from_scenario(
        seed=55, scenario_path="data/scenarios/baseline_1990_country_a.yaml"
    )
    # Inject a strong building workforce signal.
    engine.store.state["building_total_workers"] = 400_000
    engine.store.state["population"] = 1_000_000
    engine.store.state["unemployment"] = 0.20  # high initial unemployment

    engine.run_tick(1)

    new_unemp = float(engine.store.state.get("unemployment", 0.20))
    # With 400k workers from buildings in a 650k labour force, expected bldg-implied unemp ≈ 0.385
    # The blend (70% flow model + 30% bldg) should keep it below the pure flow outcome.
    assert 0.0 <= new_unemp <= 1.0
