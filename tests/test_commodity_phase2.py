"""Tests for Phase 2: commodity registry and industry recipes.

Covers:
- Commodity catalog completeness and property bounds.
- Storage decay reduces stocks.
- Recipe input availability computation.
- Commodity output / input consumed calculation.
- Building update includes commodity_outputs and commodity_inputs_consumed.
- update_subregion_buildings accumulates net produced / consumed totals.
- Subregion commodity_stocks are populated after seeding.
"""

from __future__ import annotations

import pytest

from src.econ.commodity_registry import (
    COMMODITY_CATALOG,
    COMMODITY_IDS,
    STRATEGIC_COMMODITIES,
    apply_storage_decay,
    build_empty_commodity_state,
    can_substitute,
    get_commodity,
    is_strategic,
)
from src.econ.industry_recipes import (
    BUILDING_RECIPES,
    compute_commodity_outputs,
    compute_input_availability,
    get_active_recipe,
    get_recipes,
)
from src.econ.building_engine import (
    seed_buildings_for_subregion,
    update_building,
    update_subregion_buildings,
)


# ---------------------------------------------------------------------------
# Commodity registry
# ---------------------------------------------------------------------------

def test_commodity_catalog_not_empty() -> None:
    assert len(COMMODITY_CATALOG) > 5


def test_all_commodities_have_required_keys() -> None:
    required = {"category", "perishability", "strategic_priority", "importability",
                "exportability", "substitution_group", "base_price", "unit"}
    for cid, props in COMMODITY_CATALOG.items():
        missing = required - set(props.keys())
        assert not missing, f"Commodity {cid!r} missing keys: {missing}"


def test_perishability_bounded() -> None:
    for cid, props in COMMODITY_CATALOG.items():
        assert 0.0 <= props["perishability"] <= 1.0, f"{cid} perishability out of range"


def test_strategic_priority_range() -> None:
    for cid, props in COMMODITY_CATALOG.items():
        assert 1 <= props["strategic_priority"] <= 5, f"{cid} strategic_priority out of range"


def test_strategic_commodities_subset() -> None:
    assert "staple_food" in STRATEGIC_COMMODITIES
    assert "fuel" in STRATEGIC_COMMODITIES
    assert "power" in STRATEGIC_COMMODITIES
    # charcoal has priority 1 — should NOT be strategic
    assert "charcoal" not in STRATEGIC_COMMODITIES


def test_is_strategic_helper() -> None:
    assert is_strategic("staple_food")
    assert not is_strategic("charcoal")


def test_get_commodity_known() -> None:
    entry = get_commodity("steel")
    assert entry["category"] == "industrial"


def test_get_commodity_unknown_raises() -> None:
    with pytest.raises(KeyError):
        get_commodity("unobtanium")


def test_can_substitute_returns_available_substitutes() -> None:
    available = {"charcoal", "fuel"}
    subs = can_substitute("coal", available)
    assert "charcoal" in subs
    assert "fuel" not in subs  # fuel is not in coal's substitution_group


def test_build_empty_commodity_state_covers_all() -> None:
    state = build_empty_commodity_state()
    assert set(state.keys()) == COMMODITY_IDS
    assert all(v == 0.0 for v in state.values())


def test_apply_storage_decay_reduces_perishable_stock() -> None:
    stocks = {"staple_food": 100.0, "steel": 100.0}
    decayed = apply_storage_decay(stocks)
    # staple_food has perishability 0.04, so should drop
    assert decayed["staple_food"] < 100.0
    # steel has perishability 0.002, should also drop slightly
    assert decayed["steel"] < 100.0
    # Neither should go below zero
    assert decayed["staple_food"] >= 0.0


def test_apply_storage_decay_does_not_mutate_input() -> None:
    stocks = {"staple_food": 50.0}
    _ = apply_storage_decay(stocks)
    assert stocks["staple_food"] == 50.0


# ---------------------------------------------------------------------------
# Industry recipes
# ---------------------------------------------------------------------------

def test_farm_recipe_exists() -> None:
    recipes = get_recipes("farm")
    assert len(recipes) >= 1
    assert "staple_food" in recipes[0]["outputs"]


def test_farm_recipe_requires_fertilizer() -> None:
    recipes = get_recipes("farm")
    assert "fertilizer" in recipes[0]["inputs"]


def test_steel_mill_recipe_consumes_iron_and_coal() -> None:
    recipes = get_recipes("steel_mill")
    inputs = recipes[0]["inputs"]
    assert "iron_ore" in inputs
    assert "coal" in inputs


def test_coal_power_plant_outputs_power() -> None:
    recipes = get_recipes("coal_power_plant")
    assert "power" in recipes[0]["outputs"]


def test_hospital_has_null_recipe() -> None:
    recipes = get_recipes("hospital")
    assert recipes[0]["inputs"] == {}
    assert recipes[0]["outputs"] == {}


def test_get_active_recipe_default_variant() -> None:
    building = {"type": "farm", "recipe_variant": 0}
    recipe = get_active_recipe(building)
    assert "staple_food" in recipe["outputs"]


def test_factory_has_multiple_variants() -> None:
    recipes = get_recipes("factory")
    assert len(recipes) >= 2
    # Variant 0 → consumer_goods
    assert "consumer_goods" in recipes[0]["outputs"]
    # Variant 1 → machine_parts
    assert "machine_parts" in recipes[1]["outputs"]


def test_compute_input_availability_unlimited() -> None:
    recipe = get_recipes("farm")[0]
    # Large stocks → availability should be 1.0
    stocks = {"fertilizer": 1e6, "fuel": 1e6}
    avail = compute_input_availability(recipe, stocks, building_output=1.0)
    assert avail == pytest.approx(1.0)


def test_compute_input_availability_scarce() -> None:
    recipe = get_recipes("farm")[0]
    # No fertilizer at all → availability should be 0.0
    stocks = {"fertilizer": 0.0, "fuel": 1e6}
    avail = compute_input_availability(recipe, stocks, building_output=1.0)
    assert avail == pytest.approx(0.0)


def test_compute_commodity_outputs_scales_with_availability() -> None:
    recipe = get_recipes("farm")[0]
    full = compute_commodity_outputs(recipe, building_output=1.0, input_availability=1.0, power_availability=1.0)
    half = compute_commodity_outputs(recipe, building_output=1.0, input_availability=0.5, power_availability=1.0)
    assert full["staple_food"] > half["staple_food"]
    assert half["staple_food"] >= 0.0


# ---------------------------------------------------------------------------
# Building engine integration
# ---------------------------------------------------------------------------

def test_update_building_includes_commodity_outputs() -> None:
    buildings = seed_buildings_for_subregion(
        "test_sub", "agro_periphery", 500_000, 0.6, 0.6, 42, 0,
        geo_profile={"fertility": 0.8, "water_access": 0.7},
    )
    farms = [b for b in buildings if b["type"] == "farm"]
    assert farms, "Expected at least one farm in agro_periphery"

    farm = farms[0]
    updated = update_building(
        farm,
        sector_demand_signal=0.7,
        maintenance_spend=0.5,
        human_capital=0.6,
        prior_state={},
        regional_stocks={"fertilizer": 1000.0, "fuel": 1000.0},
    )
    assert "commodity_outputs" in updated
    assert "commodity_inputs_consumed" in updated
    assert "input_availability" in updated
    # Farm should produce some staple_food
    assert updated["commodity_outputs"].get("staple_food", 0.0) > 0.0


def test_update_building_zero_output_when_no_inputs() -> None:
    buildings = seed_buildings_for_subregion(
        "test_sub", "agro_periphery", 500_000, 0.6, 0.6, 42, 0,
        geo_profile={"fertility": 0.8, "water_access": 0.7},
    )
    farms = [b for b in buildings if b["type"] == "farm"]
    assert farms

    updated = update_building(
        farms[0],
        sector_demand_signal=0.7,
        maintenance_spend=0.5,
        human_capital=0.6,
        prior_state={},
        regional_stocks={},           # empty stocks → no fertilizer
    )
    # With zero fertilizer, input_availability = 0 → staple_food output = 0
    assert updated["commodity_outputs"].get("staple_food", 0.0) == pytest.approx(0.0)


def test_update_subregion_buildings_returns_commodity_totals() -> None:
    buildings = seed_buildings_for_subregion(
        "test_sub", "agro_periphery", 800_000, 0.6, 0.6, 7, 0,
        geo_profile={"fertility": 0.8, "water_access": 0.7},
    )
    stocks = {"fertilizer": 1e6, "fuel": 1e6, "power": 1e6}
    updated, produced, consumed = update_subregion_buildings(
        buildings=buildings,
        sector_demand_signals={"agriculture": 0.7, "energy": 0.5},
        maintenance_spend=0.5,
        human_capital=0.6,
        prior_state={},
        regional_stocks=stocks,
    )
    assert len(updated) == len(buildings)
    # With sufficient stocks, farms should produce staple_food
    assert produced.get("staple_food", 0.0) > 0.0
    # Farms consume fertilizer and fuel
    assert consumed.get("fertilizer", 0.0) > 0.0


def test_subregion_has_commodity_stocks_after_seeding() -> None:
    """Regional profiles should initialize commodity_stocks at world gen."""
    from src.econ.regional_profiles import build_initial_region_state
    state = build_initial_region_state(region_count=3, population=2_000_000, scenario_id="phase2_test")
    regions = state.get("regions", {})
    assert regions, "Expected at least one region"
    for region_name, region in regions.items():
        subregions = region.get("subregions", {})
        for sub_name, sub in subregions.items():
            assert "commodity_stocks" in sub, (
                f"Subregion {region_name}/{sub_name} missing commodity_stocks"
            )
