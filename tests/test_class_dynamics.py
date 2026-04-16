from __future__ import annotations

from src.core.default_engine import build_engine_from_scenario


def _run_with_patch(patch: dict[str, float], ticks: int = 60) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=123, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    engine.store.state.update(patch)
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return engine.store.state


def test_class_metrics_exist_and_bounded() -> None:
    state = _run_with_patch({}, ticks=24)

    required_fields = [
        "worker_income_share",
        "professional_income_share",
        "capitalist_income_share",
        "informal_income_share",
        "wealth_gini",
        "wealth_top10pct",
        "poverty_headcount",
        "class_support_workers",
        "class_support_capitalists",
        "class_conflict_pressure",
        "capital_flight_rate",
        "belief_in_system",
    ]
    for field in required_fields:
        assert field in state

    total_share = (
        float(state["worker_income_share"])
        + float(state["professional_income_share"])
        + float(state["capitalist_income_share"])
        + float(state["informal_income_share"])
    )
    assert 0.99 <= total_share <= 1.01
    assert 0.0 <= float(state["wealth_gini"]) <= 1.0
    assert 0.0 <= float(state["poverty_headcount"]) <= 1.0
    assert 0.0 <= float(state["capital_flight_rate"]) <= 0.30
    assert 0.0 <= float(state["class_conflict_pressure"]) <= 1.0


def test_higher_spending_reduces_poverty_relative_to_austerity() -> None:
    high_spend = _run_with_patch({"spend_ratio": 0.26, "tax_ratio": 0.24}, ticks=48)
    austerity = _run_with_patch({"spend_ratio": 0.16, "tax_ratio": 0.18}, ticks=48)

    assert float(high_spend["poverty_headcount"]) < float(austerity["poverty_headcount"])


def test_high_tax_pressure_reduces_capital_support_and_raises_flight() -> None:
    moderate_tax = _run_with_patch({"tax_ratio": 0.22}, ticks=48)
    high_tax = _run_with_patch({"tax_ratio": 0.40}, ticks=48)

    assert float(high_tax["class_support_capitalists"]) <= float(moderate_tax["class_support_capitalists"])
    assert float(high_tax["capital_flight_rate"]) >= float(moderate_tax["capital_flight_rate"])
