from __future__ import annotations

from pathlib import Path

from src.core.scenario_loader import (
    DEFAULT_ECONOMY_PRESET,
    initial_state_from_scenario,
    load_scenario_file,
)


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


def test_preset_applies_when_sections_are_sparse() -> None:
    data = {
        "scenario_id": "preset_sparse",
        "economy_preset": "resource_exporter",
        "country": {
            "id": "country_x",
            "name": "X",
            "population": 8_000_000,
        },
    }
    state = initial_state_from_scenario(data)
    assert state["economy_preset"] == "resource_exporter"
    assert state["exports"] > 0.0
    assert state["imports"] > 0.0
    assert state["population"] == 8_000_000


def test_scenario_values_override_preset_defaults() -> None:
    data = {
        "scenario_id": "preset_override",
        "economy_preset": "agrarian_frontier",
        "country": {
            "id": "country_x",
            "name": "X",
            "population": 7_000_000,
            "regions": 5,
        },
        "macro": {
            "policy_rate": 0.05,
        },
        "trade": {
            "exports": 123_456.0,
            "imports": 654_321.0,
        },
    }
    state = initial_state_from_scenario(data)
    assert state["policy_rate"] == 0.05
    assert state["exports"] == 123_456.0
    assert state["imports"] == 654_321.0
    assert state["region_count"] == 5


def test_preset_modifiers_override_scenario_and_preset() -> None:
    data = {
        "scenario_id": "preset_modifiers_override",
        "economy_preset": "balanced_baseline",
        "country": {
            "id": "country_x",
            "name": "X",
            "population": 9_000_000,
        },
        "macro": {
            "industrial_policy_bias": 0.40,
        },
        "preset_modifiers": {
            "macro": {
                "industrial_policy_bias": 0.77,
            },
            "trade": {
                "imports": 9_999_999.0,
            },
        },
    }
    state = initial_state_from_scenario(data)
    assert state["industrial_policy_bias"] == 0.77
    assert state["imports"] == 9_999_999.0


def test_unknown_preset_falls_back_to_default() -> None:
    data = {
        "scenario_id": "preset_unknown",
        "economy_preset": "does_not_exist",
        "country": {
            "id": "country_x",
            "name": "X",
            "population": 6_000_000,
        },
    }
    state = initial_state_from_scenario(data)
    assert state["economy_preset"] == DEFAULT_ECONOMY_PRESET


def test_new_preset_scenario_files_load() -> None:
    paths = [
        Path("data/scenarios/resource_exporter_1990_country_a.yaml"),
        Path("data/scenarios/import_substitution_1990_country_a.yaml"),
        Path("data/scenarios/agrarian_frontier_1990_country_a.yaml"),
    ]
    for scenario_path in paths:
        data = load_scenario_file(scenario_path)
        state = initial_state_from_scenario(data)
        assert state["scenario_id"] == data["scenario_id"]
        assert state["economy_preset"] == data["economy_preset"]
        assert state["region_count"] > 0
