from __future__ import annotations

import math

from src.core.default_engine import build_engine_from_scenario


def _run_baseline(seed: int = 123, ticks: int = 120) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=123, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return engine.store.state


def _run_shocked(shock_patch: dict[str, float], seed: int = 123, ticks: int = 120) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=seed, scenario_path="data/scenarios/baseline_1990_country_a.yaml")

    state = engine.store.state
    for key, value in shock_patch.items():
        state[key] = value

    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return engine.store.state


def _assert_no_invalids(final_state: dict[str, float], scenario_name: str) -> None:
    numeric_fields = [
        "price",
        "wage",
        "unemployment",
        "debt",
        "reserves",
        "population",
        "trust",
        "legitimacy",
        "unrest",
    ]
    for field in numeric_fields:
        value = float(final_state[field])
        assert not math.isnan(value), f"{scenario_name}: NaN in {field}"
        assert not math.isinf(value), f"{scenario_name}: Inf in {field}"

    assert final_state["population"] >= 0.0
    assert 0.0 <= final_state["unemployment"] <= 1.0
    assert 0.0 <= final_state["trust"] <= 100.0
    assert 0.0 <= final_state["legitimacy"] <= 100.0
    assert 0.0 <= final_state["unrest"] <= 100.0


def test_sanctions_response_direction() -> None:
    baseline = _run_baseline()
    shocked = _run_shocked({"exports": 5_000_000_000.0, "imports": 14_000_000_000.0})
    _assert_no_invalids(shocked, "sanctions")
    assert shocked["reserves"] < baseline["reserves"]
    assert shocked["debt"] > baseline["debt"]
    assert shocked["legitimacy"] < baseline["legitimacy"]
    assert shocked["unrest"] > baseline["unrest"]


def test_energy_shock_response_direction() -> None:
    baseline = _run_baseline()
    shocked = _run_shocked({"cost_delta": 0.03})
    _assert_no_invalids(shocked, "energy_shock")
    assert shocked["price"] > baseline["price"]
    assert shocked["debt"] >= baseline["debt"] * 0.995
    assert shocked["legitimacy"] <= baseline["legitimacy"]
    assert shocked["unrest"] >= baseline["unrest"]


def test_sudden_stop_response_direction() -> None:
    baseline = _run_baseline()
    shocked = _run_shocked({"capital_account": -5_000_000_000.0})
    _assert_no_invalids(shocked, "sudden_stop")
    assert shocked["reserves"] < baseline["reserves"]
    assert shocked["reserves"] >= 0.0


def test_drought_response_direction() -> None:
    baseline = _run_baseline()
    shocked = _run_shocked({"capacity_output": 70.0})
    _assert_no_invalids(shocked, "drought")
    assert shocked["production"] < baseline["production"]
    assert shocked["production"] <= 72.0


def test_banking_panic_response_direction() -> None:
    baseline = _run_baseline()
    shocked = _run_shocked({"matches": 0.004, "separations": 0.02})
    _assert_no_invalids(shocked, "banking_panic")
    assert shocked["unemployment"] > baseline["unemployment"]
    assert shocked["unemployment"] >= 0.05


def test_disinformation_response_direction() -> None:
    baseline = _run_baseline()
    shocked = _run_shocked({"info_quality": 0.1, "polarization": 80.0})
    _assert_no_invalids(shocked, "disinformation_wave")
    assert shocked["trust"] <= baseline["trust"]
    assert shocked["trust"] <= 60.0


def test_identity_polarization_response_direction() -> None:
    baseline = _run_baseline()
    shocked = _run_shocked({"polarization": 90.0, "inequality_shock": 0.9})
    _assert_no_invalids(shocked, "identity_polarization")
    assert shocked["unrest"] >= baseline["unrest"]
    assert 0.0 <= shocked["unrest"] <= 100.0
