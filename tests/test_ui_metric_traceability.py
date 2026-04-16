from __future__ import annotations

from src.ui.causality_explorer import decompose_metric, has_hidden_modifiers
from src.ui.sheets import default_sheet_names


def test_default_sheets_present() -> None:
    sheets = default_sheet_names()
    assert len(sheets) == 21
    assert "Executive Overview" in sheets
    assert "State Explorer" in sheets
    assert "Sector Output and Capacity" in sheets
    assert "Supply Chain Stress Map" in sheets
    assert "Regional Map (ASCII)" in sheets
    assert "Class and Inequality Dynamics" in sheets
    assert "World Diplomacy and External Risks" in sheets
    assert "Events, Crises, and Victory" in sheets
    assert "Events and Causality Log" in sheets


def test_trace_payload_has_no_hidden_modifiers() -> None:
    payload = decompose_metric(
        metric_name="inflation",
        contributions={
            "cost_push": 0.02,
            "demand_pull": 0.01,
            "fx_pass_through": 0.005,
        },
    )
    assert not has_hidden_modifiers(payload)
