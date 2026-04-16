from __future__ import annotations

from src.core.default_engine import build_engine_from_scenario


def _run(patch: dict[str, float] | None = None, ticks: int = 24) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=303, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    if patch:
        engine.store.state.update(patch)
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return engine.store.state


def test_region_state_exists_and_has_heterogeneity() -> None:
    state = _run(ticks=12)
    region_state = state["region_state"]

    assert isinstance(region_state, dict)
    assert int(region_state["region_count"]) >= 3
    regions = region_state["regions"]
    assert isinstance(regions, dict)
    assert len(regions) == int(region_state["region_count"])

    resources = [float(row["resource_endowment"]) for row in regions.values()]
    infrastructures = [float(row["infrastructure"]) for row in regions.values()]
    xs = [float(row["coord_x"]) for row in regions.values()]
    ys = [float(row["coord_y"]) for row in regions.values()]
    neighbor_counts = [len(row.get("neighbors", [])) for row in regions.values()]

    assert max(resources) > min(resources)
    assert max(infrastructures) > min(infrastructures)
    assert all(0.0 <= x <= 100.0 for x in xs)
    assert all(0.0 <= y <= 100.0 for y in ys)
    assert min(neighbor_counts) >= 1
    assert "transport_edges" in region_state
    assert isinstance(region_state["transport_edges"], dict)


def test_regional_metrics_bounded() -> None:
    state = _run(ticks=36)

    assert 0.0 <= float(state["regional_output_gini"]) <= 1.0
    assert 0.0 <= float(state["regional_inequality_index"]) <= 1.0
    assert 0.0 <= float(state["regional_service_gap_index"]) <= 1.0
    assert 0.0 <= float(state["regional_employment_gap_index"]) <= 1.0
    assert 0.0 <= float(state["regional_representation_gap"]) <= 2.0
    assert 0.0 <= float(state["map_connectivity_index"]) <= 1.0
    assert 0.0 <= float(state["transport_cost_index"]) <= 2.0
    assert float(state["mean_route_cost"]) >= 0.0


def test_regional_equity_bias_changes_allocation_pattern() -> None:
    low_equity = _run(patch={"regional_equity_bias": 0.05}, ticks=24)
    high_equity = _run(patch={"regional_equity_bias": 0.95}, ticks=24)

    low_gap = float(low_equity["regional_representation_gap"])
    high_gap = float(high_equity["regional_representation_gap"])

    # Distinct policy settings should lead to a measurably different allocation profile.
    assert abs(low_gap - high_gap) > 1e-4


def test_each_state_contains_normalized_subregions() -> None:
    state = _run(ticks=6)
    regions = state["region_state"]["regions"]

    for payload in regions.values():
        subregions = payload.get("subregions")
        assert isinstance(subregions, dict)
        assert len(subregions) >= 3
        share_total = sum(float(row.get("population_share", 0.0)) for row in subregions.values())
        assert abs(share_total - 1.0) < 1e-6
