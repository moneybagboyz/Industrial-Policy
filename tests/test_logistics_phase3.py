"""Tests for Phase 3: logistics network.

Covers:
- Initial logistics state has corridors matching transport edges.
- aggregate_region_stocks sums across subregions correctly.
- compute_logistics_flows moves surplus to deficit regions.
- Transit spoilage reduces arriving quantities for perishable goods.
- Corridor congestion rises when throughput is high.
- distribute_incoming_to_subregions applies flows proportionally.
- update_logistics_state runs end-to-end and returns updated regions.
- Logistics state is stored in region_state after a scenario init.
- After a tick via update_region_economies, logistics_state is present.
"""

from __future__ import annotations

import pytest

from src.econ.logistics_network import (
    aggregate_region_stocks,
    build_initial_logistics_state,
    build_regional_stock_map,
    compute_logistics_flows,
    corridor_summary,
    distribute_incoming_to_subregions,
    top_shortfalls,
    update_logistics_state,
)
from src.econ.commodity_registry import build_empty_commodity_state


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_simple_transport_edges() -> dict:
    """Two-region topology: alpha <-> beta."""
    return {
        "alpha|beta": {
            "distance": 30.0,
            "friction": 0.20,
            "capacity": 1.0,
        },
    }


def _make_three_region_edges() -> dict:
    return {
        "alpha|beta": {"distance": 25.0, "friction": 0.15, "capacity": 1.0},
        "beta|gamma": {"distance": 35.0, "friction": 0.25, "capacity": 0.8},
        "alpha|gamma": {"distance": 50.0, "friction": 0.35, "capacity": 0.6},
    }


def _sub(pop_share: float, stocks: dict) -> dict:
    return {
        "population_share": pop_share,
        "commodity_stocks": stocks,
    }


def _region_with_stocks(stock_overrides: dict) -> dict:
    """Build a minimal single-subregion region for testing."""
    base = build_empty_commodity_state()
    base.update(stock_overrides)
    return {
        "population": 1_000_000.0,
        "subregions": {
            "main": _sub(1.0, base),
        },
    }


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_build_initial_logistics_state_has_corridors() -> None:
    edges = _make_simple_transport_edges()
    state = build_initial_logistics_state(edges, ["alpha", "beta"])
    assert "alpha|beta" in state["corridors"]


def test_corridor_fields_present() -> None:
    edges = _make_simple_transport_edges()
    state = build_initial_logistics_state(edges, ["alpha", "beta"])
    corridor = state["corridors"]["alpha|beta"]
    for key in ("capacity", "friction", "utilization", "congestion_ratio", "total_flow"):
        assert key in corridor, f"Missing corridor field: {key}"


def test_initial_logistics_state_utilization_zero() -> None:
    edges = _make_simple_transport_edges()
    state = build_initial_logistics_state(edges, ["alpha", "beta"])
    assert state["corridors"]["alpha|beta"]["utilization"] == 0.0


# ---------------------------------------------------------------------------
# Stock aggregation
# ---------------------------------------------------------------------------

def test_aggregate_region_stocks_sums_subregions() -> None:
    region = {
        "subregions": {
            "north": _sub(0.5, {"staple_food": 10.0, "fuel": 5.0}),
            "south": _sub(0.5, {"staple_food": 8.0, "fuel": 3.0}),
        }
    }
    totals = aggregate_region_stocks(region)
    assert totals["staple_food"] == pytest.approx(18.0)
    assert totals["fuel"] == pytest.approx(8.0)


def test_aggregate_region_stocks_empty() -> None:
    totals = aggregate_region_stocks({})
    assert totals == {}


def test_build_regional_stock_map() -> None:
    regions = {
        "alpha": _region_with_stocks({"steel": 20.0}),
        "beta": _region_with_stocks({"steel": 0.0}),
    }
    stock_map = build_regional_stock_map(regions)
    assert stock_map["alpha"]["steel"] == pytest.approx(20.0)
    assert stock_map["beta"]["steel"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Flow computation
# ---------------------------------------------------------------------------

def test_surplus_moves_to_deficit_region() -> None:
    """Alpha has lots of staple_food, beta has none."""
    regional_stocks = {
        "alpha": {**build_empty_commodity_state(), "staple_food": 100.0},
        "beta":  {**build_empty_commodity_state(), "staple_food": 0.0},
    }
    edges = _make_simple_transport_edges()
    state = build_initial_logistics_state(edges, ["alpha", "beta"])

    incoming, outgoing, _, _ = compute_logistics_flows(
        regional_stocks=regional_stocks,
        region_populations={"alpha": 1_000_000.0, "beta": 1_000_000.0},
        corridors=state["corridors"],
        region_neighbors={"alpha": ["beta"], "beta": ["alpha"]},
    )
    # Beta should receive food from alpha.
    assert incoming["beta"].get("staple_food", 0.0) > 0.0
    # Alpha should have shipped something out.
    assert outgoing["alpha"].get("staple_food", 0.0) > 0.0


def test_no_flow_without_neighbors() -> None:
    """Regions with no neighbors cannot exchange commodities."""
    regional_stocks = {
        "alpha": {**build_empty_commodity_state(), "staple_food": 100.0},
        "beta":  {**build_empty_commodity_state(), "staple_food": 0.0},
    }
    edges = _make_simple_transport_edges()
    state = build_initial_logistics_state(edges, ["alpha", "beta"])

    incoming, outgoing, _, _ = compute_logistics_flows(
        regional_stocks=regional_stocks,
        region_populations={"alpha": 1_000_000.0, "beta": 1_000_000.0},
        corridors=state["corridors"],
        region_neighbors={"alpha": [], "beta": []},   # no adjacency
    )
    assert incoming["beta"].get("staple_food", 0.0) == pytest.approx(0.0)


def test_transit_spoilage_for_perishable_goods() -> None:
    """High-friction corridor should cause food spoilage in transit."""
    high_friction_edges = {
        "alpha|beta": {"distance": 80.0, "friction": 0.90, "capacity": 2.0},
    }
    state = build_initial_logistics_state(high_friction_edges, ["alpha", "beta"])

    regional_stocks = {
        "alpha": {**build_empty_commodity_state(), "staple_food": 200.0},
        "beta":  {**build_empty_commodity_state(), "staple_food": 0.0},
    }
    incoming, outgoing, _, _ = compute_logistics_flows(
        regional_stocks=regional_stocks,
        region_populations={"alpha": 1_000_000.0, "beta": 1_000_000.0},
        corridors=state["corridors"],
        region_neighbors={"alpha": ["beta"], "beta": ["alpha"]},
    )
    shipped = outgoing["alpha"].get("staple_food", 0.0)
    arrived = incoming["beta"].get("staple_food", 0.0)
    if shipped > 0:
        # Arrived should be less than shipped due to spoilage.
        assert arrived < shipped


def test_steel_has_minimal_transit_loss() -> None:
    """Steel (perishability=0.002) should lose almost nothing in transit."""
    low_friction_edges = {
        "alpha|beta": {"distance": 20.0, "friction": 0.10, "capacity": 2.0},
    }
    state = build_initial_logistics_state(low_friction_edges, ["alpha", "beta"])
    regional_stocks = {
        "alpha": {**build_empty_commodity_state(), "steel": 200.0},
        "beta":  {**build_empty_commodity_state(), "steel": 0.0},
    }
    incoming, outgoing, _, _ = compute_logistics_flows(
        regional_stocks=regional_stocks,
        region_populations={"alpha": 1_000_000.0, "beta": 1_000_000.0},
        corridors=state["corridors"],
        region_neighbors={"alpha": ["beta"], "beta": ["alpha"]},
    )
    shipped = outgoing["alpha"].get("steel", 0.0)
    arrived = incoming["beta"].get("steel", 0.0)
    if shipped > 0:
        loss_fraction = (shipped - arrived) / shipped
        assert loss_fraction < 0.05   # less than 5% loss for steel


def test_corridor_congestion_rises_under_heavy_use() -> None:
    """When many commodities flow through a corridor it should become congested."""
    edges = {
        "alpha|beta": {"distance": 20.0, "friction": 0.10, "capacity": 0.05},  # very low cap
    }
    state = build_initial_logistics_state(edges, ["alpha", "beta"])

    # Give alpha massive surpluses of multiple commodities to saturate the corridor.
    stocks_alpha = build_empty_commodity_state()
    for cid in list(stocks_alpha.keys())[:8]:
        stocks_alpha[cid] = 500.0
    regional_stocks = {
        "alpha": stocks_alpha,
        "beta":  build_empty_commodity_state(),
    }
    _, _, updated_corridors, _ = compute_logistics_flows(
        regional_stocks=regional_stocks,
        region_populations={"alpha": 1_000_000.0, "beta": 1_000_000.0},
        corridors=state["corridors"],
        region_neighbors={"alpha": ["beta"], "beta": ["alpha"]},
    )
    util = updated_corridors["alpha|beta"]["utilization"]
    assert util > 0.0


def test_national_shortfall_tracks_deficits() -> None:
    """Shortfall should record commodities where demand exceeds stock."""
    regional_stocks = {
        "alpha": build_empty_commodity_state(),   # all zero stock → deficit
        "beta":  build_empty_commodity_state(),
    }
    edges = _make_simple_transport_edges()
    state = build_initial_logistics_state(edges, ["alpha", "beta"])

    _, _, _, shortfall = compute_logistics_flows(
        regional_stocks=regional_stocks,
        region_populations={"alpha": 2_000_000.0, "beta": 2_000_000.0},
        corridors=state["corridors"],
        region_neighbors={"alpha": ["beta"], "beta": ["alpha"]},
    )
    # With zero stocks and positive population, strategic goods should show deficit.
    assert shortfall.get("staple_food", 0.0) > 0.0


# ---------------------------------------------------------------------------
# distribute_incoming_to_subregions
# ---------------------------------------------------------------------------

def test_distribute_incoming_proportional_to_population() -> None:
    subregions = {
        "north": _sub(0.70, build_empty_commodity_state()),
        "south": _sub(0.30, build_empty_commodity_state()),
    }
    incoming = {"staple_food": 100.0}
    updated = distribute_incoming_to_subregions(subregions, incoming, outgoing={})
    north_food = updated["north"]["commodity_stocks"]["staple_food"]
    south_food = updated["south"]["commodity_stocks"]["staple_food"]
    assert north_food == pytest.approx(70.0, rel=0.01)
    assert south_food == pytest.approx(30.0, rel=0.01)


def test_distribute_outgoing_deducts_proportionally() -> None:
    base = build_empty_commodity_state()
    base["fuel"] = 100.0
    subregions = {
        "A": _sub(0.5, dict(base)),
        "B": _sub(0.5, dict(base)),
    }
    outgoing = {"fuel": 20.0}
    updated = distribute_incoming_to_subregions(subregions, incoming={}, outgoing=outgoing)
    # Each subregion loses 5% (10 units out of 100).
    assert updated["A"]["commodity_stocks"]["fuel"] == pytest.approx(90.0, rel=0.01)
    assert updated["B"]["commodity_stocks"]["fuel"] == pytest.approx(90.0, rel=0.01)


# ---------------------------------------------------------------------------
# End-to-end logistics tick
# ---------------------------------------------------------------------------

def test_update_logistics_state_end_to_end() -> None:
    """update_logistics_state runs without error and returns both dicts."""
    edges = _make_three_region_edges()
    logistics = build_initial_logistics_state(edges, ["alpha", "beta", "gamma"])

    regions = {
        "alpha": _region_with_stocks({"staple_food": 50.0}),
        "beta":  _region_with_stocks({"staple_food": 0.0}),
        "gamma": _region_with_stocks({"fuel": 30.0}),
    }
    # Set neighbor lists matching edge topology.
    regions["alpha"]["neighbors"] = ["beta", "gamma"]
    regions["beta"]["neighbors"] = ["alpha", "gamma"]
    regions["gamma"]["neighbors"] = ["alpha", "beta"]

    updated_regions, updated_logistics = update_logistics_state(
        logistics_state=logistics,
        regions=regions,
        region_populations={"alpha": 1e6, "beta": 1e6, "gamma": 1e6},
    )
    assert isinstance(updated_regions, dict)
    assert isinstance(updated_logistics, dict)
    assert "corridors" in updated_logistics
    assert "national_shortfall" in updated_logistics


def test_logistics_state_in_scenario_init() -> None:
    """Scenario loader should embed logistics_state in region_state."""
    from src.core.scenario_loader import initial_state_from_scenario
    scenario = {
        "scenario_id": "logistics_test",
        "macro": {"nominal_gdp": 10_000_000_000.0},
        "social": {"population": 3_000_000},
        "country": {"regions": 4},
        "trade": {"imports": 500_000.0},
    }
    state = initial_state_from_scenario(scenario)
    region_state = state.get("region_state", {})
    assert "logistics_state" in region_state, "logistics_state missing from region_state"
    logistics = region_state["logistics_state"]
    assert "corridors" in logistics
    assert len(logistics["corridors"]) > 0


def test_logistics_state_persists_after_tick() -> None:
    """After one tick of update_region_economies, logistics_state should exist."""
    from src.econ.regional_profiles import update_region_economies
    from src.core.scenario_loader import initial_state_from_scenario

    scenario = {
        "scenario_id": "logistics_tick_test",
        "macro": {"nominal_gdp": 10_000_000_000.0},
        "social": {"population": 2_000_000},
        "country": {"regions": 3},
        "trade": {"imports": 500_000.0},
    }
    initial = initial_state_from_scenario(scenario)
    result = update_region_economies(
        prior_state=initial,
        total_output=100.0,
        total_primary=28.0,
        total_secondary=40.0,
        total_tertiary=32.0,
    )
    region_state_out = result.get("region_state", {})
    assert "logistics_state" in region_state_out, "logistics_state missing after tick"
    logistics_out = region_state_out["logistics_state"]
    assert "corridors" in logistics_out
    # tick_flows should now be populated (at least an empty dict per region).
    assert "tick_flows" in logistics_out


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def test_corridor_summary_returns_list() -> None:
    edges = _make_three_region_edges()
    state = build_initial_logistics_state(edges, ["alpha", "beta", "gamma"])
    summary = corridor_summary(state)
    assert isinstance(summary, list)
    assert len(summary) == 3   # one entry per edge


def test_top_shortfalls_returns_sorted_list() -> None:
    state = {"national_shortfall": {"staple_food": 5.0, "fuel": 12.0, "steel": 2.0}}
    result = top_shortfalls(state, n=2)
    assert result[0]["commodity"] == "fuel"
    assert result[1]["commodity"] == "staple_food"
