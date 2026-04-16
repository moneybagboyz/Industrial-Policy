from __future__ import annotations

from pathlib import Path

from src.core.scenario_loader import initial_state_from_scenario, load_scenario_file


def test_load_scenario_file_and_map_initial_state() -> None:
    scenario_path = Path("data/scenarios/baseline_1990_country_a.yaml")
    data = load_scenario_file(scenario_path)
    state = initial_state_from_scenario(data)

    assert data["scenario_id"] == "baseline_1990_country_a"
    assert state["debt"] > 0
    assert state["population"] > 0
    assert "expected_inflation" in state
    assert state["structural_exports"] == state["exports"]
    assert state["structural_imports"] == state["imports"]
    assert state["tax_ratio"] > 0.0
    assert state["spend_ratio"] > 0.0
    assert state["region_count"] == data["country"]["regions"]
    assert "region_state" in state
    assert isinstance(state["region_state"], dict)
    assert len(state["region_state"]["regions"]) == data["country"]["regions"]
