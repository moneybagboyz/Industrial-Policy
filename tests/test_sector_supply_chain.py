from __future__ import annotations

from copy import deepcopy

from src.core.default_engine import build_engine_from_scenario
from src.econ.sector_network import simulate_sector_network


def _run(shock_patch: dict[str, float] | None = None, ticks: int = 48) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=77, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    if shock_patch:
        engine.store.state.update(shock_patch)
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return engine.store.state


def test_sector_outputs_and_prices_exist() -> None:
    state = _run(ticks=12)

    required = [
        "sector_output_primary",
        "sector_output_secondary",
        "sector_output_tertiary",
        "sector_price_primary",
        "sector_price_secondary",
        "sector_price_tertiary",
        "agriculture_output",
        "manufacturing_output",
        "services_output",
    ]
    for field in required:
        assert field in state

    assert float(state["sector_output_primary"]) > 0.0
    assert float(state["sector_output_secondary"]) > 0.0
    assert float(state["sector_output_tertiary"]) > 0.0


def test_import_shock_raises_secondary_shortage() -> None:
    baseline = _run(ticks=36)
    import_shocked = _run(shock_patch={"trade_shock_imports": 0.55}, ticks=36)

    assert float(import_shocked["sector_shortage_secondary"]) >= float(baseline["sector_shortage_secondary"])


def test_export_boost_improves_trade_capacity_anchor() -> None:
    baseline = _run(ticks=24)
    export_boosted = _run(shock_patch={"trade_shock_exports": 1.35}, ticks=24)

    assert float(export_boosted["exports"]) >= float(baseline["exports"])


def test_supply_chain_stress_hits_class_conflict() -> None:
    baseline = _run(ticks=48)
    stress = _run(shock_patch={"trade_shock_imports": 0.60, "cost_delta": 0.03}, ticks=48)

    assert float(stress["sector_shortage_secondary"]) >= float(baseline["sector_shortage_secondary"])
    assert float(stress["unmet_demand"]) >= float(baseline["unmet_demand"])


def test_infrastructure_spending_supports_construction_output() -> None:
    baseline = _run(ticks=36)
    infra_push = _run(shock_patch={"infrastructure_spend_share": 0.50}, ticks=36)

    assert float(infra_push["construction_output"]) >= float(baseline["construction_output"])


def test_food_stabilization_dampens_agriculture_price_spike() -> None:
    shock_no_buffer = _run(shock_patch={"cost_delta": 0.03, "food_price_stabilization": 0.0}, ticks=36)
    shock_with_buffer = _run(shock_patch={"cost_delta": 0.03, "food_price_stabilization": 0.8}, ticks=36)

    assert float(shock_with_buffer["agriculture_price"]) <= float(shock_no_buffer["agriculture_price"])


def test_subregional_stress_feeds_back_to_national_signals() -> None:
    engine = build_engine_from_scenario(seed=77, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    baseline_state = deepcopy(engine.store.state)
    stressed_state = deepcopy(engine.store.state)
    stressed_state["regional_feedback_strength"] = 1.0

    region_state = stressed_state.get("region_state", {})
    regions = region_state.get("regions", {}) if isinstance(region_state, dict) else {}
    for region_payload in regions.values():
        if not isinstance(region_payload, dict):
            continue
        subregions = region_payload.get("subregions", {})
        if not isinstance(subregions, dict):
            continue
        for sub in subregions.values():
            if not isinstance(sub, dict):
                continue
            sub["unemployment"] = 0.35
            sub["support_score"] = 8.0
            sub["unrest_score"] = 92.0
            sub["service_quality"] = 0.12
            sub["output"] = max(0.1, float(sub.get("output", 1.0)) * 0.45)

    baseline_result = simulate_sector_network(baseline_state)
    stressed_result = simulate_sector_network(stressed_state)

    assert float(stressed_result["unemployment"]) > float(baseline_result["unemployment"])
    assert float(stressed_result["trust"]) < float(baseline_result["trust"])
    assert float(stressed_result["unrest"]) > float(baseline_result["unrest"])
