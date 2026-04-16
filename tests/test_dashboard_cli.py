from __future__ import annotations

from src.core.default_engine import build_engine_from_scenario
from src.ui.dashboard_cli import (
    advance_ticks,
    process_command,
    render_filtered_sheet_detail,
    render_help,
    render_metric_history,
    render_scenario_comparison,
    render_sheet_detail,
    render_sheets,
    render_summary,
)


def test_render_summary_contains_core_metrics() -> None:
    out = render_summary(
        {
            "price": 101.2,
            "wage": 1002.5,
            "unemployment": 0.09,
            "debt": 120.0,
            "reserves": 5.0,
            "trust": 50.0,
            "legitimacy": 52.0,
            "unrest": 33.0,
        }
    )
    assert "Country Simulation Dashboard" in out
    assert "price" in out
    assert "unrest" in out


def test_render_sheets_has_expected_lines() -> None:
    out = render_sheets()
    assert "Available Sheets" in out
    assert "National Accounts" in out


def test_render_help_lists_commands() -> None:
    out = render_help()
    assert "Dashboard Commands" in out
    assert "compare [ticks]" in out


def test_advance_ticks_updates_tick_and_state() -> None:
    engine = build_engine_from_scenario(seed=11, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    engine.store.state["last_tick"] = 0
    state = advance_ticks(engine, 3)

    assert state["last_tick"] == 3
    assert "price" in state


def test_process_command_step_and_exit() -> None:
    engine = build_engine_from_scenario(seed=11, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    engine.store.state["last_tick"] = 0

    msg_step, done_step = process_command("step 2", engine)
    msg_exit, done_exit = process_command("q", engine)

    assert "Country Simulation Dashboard" in msg_step
    assert done_step is False
    assert done_exit is True
    assert "Exiting dashboard" in msg_exit


def test_render_sheet_detail_and_command_sheet() -> None:
    engine = build_engine_from_scenario(seed=11, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    detail = render_sheet_detail("Public Finance and Debt", engine.store.state)
    msg, done = process_command("sheet public finance and debt", engine)

    assert "Sheet: Public Finance and Debt" in detail
    assert "debt" in detail
    assert "Sheet: Public Finance and Debt" in msg
    assert done is False


def test_render_filtered_sheet_detail_and_history() -> None:
    engine = build_engine_from_scenario(seed=11, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    engine.store.state["last_tick"] = 0
    advance_ticks(engine, 2)

    filtered = render_filtered_sheet_detail("Public Finance and Debt", engine.store.state, "debt")
    history = render_metric_history(engine, "debt", 2)
    msg, done = process_command("history debt 2", engine)

    assert "debt" in filtered
    assert "History: debt" in history
    assert "History: debt" in msg
    assert done is False


def test_sector_sheet_commands_render_expected_fields() -> None:
    engine = build_engine_from_scenario(seed=11, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    advance_ticks(engine, 1)

    msg_sector, done_sector = process_command("sheet sector output and capacity", engine)
    msg_stress, done_stress = process_command("sheet supply chain stress map", engine)

    assert "sector_output_primary" in msg_sector
    assert "manufacturing_output" in msg_sector
    assert done_sector is False
    assert "agriculture_output" in msg_stress
    assert "sector_price_index" in msg_stress
    assert done_stress is False


def test_overview_and_state_explorer_sheets_render() -> None:
    engine = build_engine_from_scenario(seed=11, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    advance_ticks(engine, 1)

    msg_overview, done_overview = process_command("sheet executive overview", engine)
    msg_states, done_states = process_command("sheet state explorer", engine)

    assert "Executive Overview" in msg_overview
    assert "Debt/GDP" in msg_overview
    assert done_overview is False
    assert "State Explorer" in msg_states
    assert "risk_01" in msg_states
    assert done_states is False


def test_render_scenario_comparison_and_command() -> None:
    engine = build_engine_from_scenario(seed=11, scenario_path="data/scenarios/baseline_1990_country_a.yaml")

    report = render_scenario_comparison(seed=11, ticks=3)
    msg, done = process_command("compare 3", engine)

    assert "Scenario Comparison (3 ticks)" in report
    assert "banking_panic" in report
    assert "Scenario Deltas vs Baseline" in msg
    assert done is False
