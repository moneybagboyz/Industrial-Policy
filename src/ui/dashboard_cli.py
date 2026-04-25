"""Simple interactive CLI for spreadsheet-style model inspection."""

from __future__ import annotations

import argparse
from typing import Any

from src.core.default_engine import build_engine_from_scenario
from src.ui.insight_views import (
    build_commodity_flow_rows,
    build_executive_overview_rows,
    build_logistics_chokepoint_rows,
    build_shortage_class_impact_rows,
    build_state_explorer_rows,
)
from src.ui.map_ascii import render_region_ascii_map
from src.ui.sheets import default_sheet_names
from src.ui.table_dashboard import render_matrix_table, render_table

DEFAULT_SCENARIO_PATH = "data/scenarios/baseline_1990_country_a.yaml"
COMPARISON_METRICS = ["price", "wage", "unemployment", "debt", "reserves", "trust", "legitimacy", "unrest"]
COMPARISON_PATCHES = {
    "baseline": {},
    "sanctions": {"exports": 5_000_000_000.0, "imports": 14_000_000_000.0},
    "energy_shock": {"cost_delta": 0.03},
    "banking_panic": {"matches": 0.004, "separations": 0.02},
}


def render_summary(state: dict[str, Any]) -> str:
    rows = [
        ("tick", int(state.get("last_tick", 0))),
        ("price", f"{float(state.get('price', 0.0)):.4f}"),
        ("wage", f"{float(state.get('wage', 0.0)):.4f}"),
        ("unemployment", f"{float(state.get('unemployment', 0.0)):.4f}"),
        ("debt", f"{float(state.get('debt', 0.0)):.2f}"),
        ("reserves", f"{float(state.get('reserves', 0.0)):.2f}"),
        ("trust", f"{float(state.get('trust', 0.0)):.2f}"),
        ("legitimacy", f"{float(state.get('legitimacy', 0.0)):.2f}"),
        ("unrest", f"{float(state.get('unrest', 0.0)):.2f}"),
    ]
    return render_table("Country Simulation Dashboard", rows)


def render_sheets() -> str:
    lines = ["Available Sheets"]
    for idx, name in enumerate(default_sheet_names(), start=1):
        lines.append(f"{idx}. {name}")
    return "\n".join(lines)


def render_sheet_detail(sheet_name: str, state: dict[str, Any]) -> str:
    sheet_map = {
        "national accounts": ["price", "debt", "reserves"],
        "production and supply chains": ["production", "inventory", "unmet_demand"],
        "sector output and capacity": [
            "sector_output_primary",
            "sector_output_secondary",
            "sector_output_tertiary",
            "manufacturing_output",
            "capacity_output",
            "production",
        ],
        "sector prices and shortages": [
            "sector_price_primary",
            "sector_price_secondary",
            "sector_price_tertiary",
            "sector_shortage_primary",
            "sector_shortage_secondary",
            "sector_shortage_tertiary",
        ],
        "supply chain stress map": [
            "agriculture_output",
            "energy_output",
            "manufacturing_output",
            "construction_output",
            "services_output",
            "sector_price_index",
            "transport_cost_index",
            "map_connectivity_index",
            "mean_route_cost",
            "regional_output_gini",
            "regional_service_gap_index",
            "regional_employment_gap_index",
            "regional_representation_gap",
        ],
        "world diplomacy and external risks": [
            "trade_access_index",
            "sanctions_index",
            "war_risk_index",
            "external_stress",
            "state_failure_risk",
        ],
        "laws and interest groups": [
            "law_stability_index",
            "reform_momentum",
            "interest_group_conflict",
            "class_conflict_pressure",
            "belief_in_system",
        ],
        "technology and innovation": [
            "technology_tier",
            "research_progress",
            "innovation_adoption",
            "prod_growth",
            "capital_flight_rate",
        ],
        "military and security": [
            "military_readiness",
            "internal_security_risk",
            "security_posture",
            "military_spend_share",
            "war_risk_index",
        ],
        "events, crises, and victory": [
            "active_crisis",
            "crisis_intensity",
            "state_failure_risk",
            "victory_progress",
            "game_over",
            "game_over_reason",
        ],
        "prices and inflation drivers": ["price", "expected_inflation"],
        "labor and income distribution": [
            "wage",
            "unemployment",
            "household_demand_proxy",
            "worker_income_share",
            "professional_income_share",
            "capitalist_income_share",
            "informal_income_share",
        ],
        "public finance and debt": ["interest_payment", "deficit", "debt"],
        "trade, fx, and reserves": ["current_account", "balance_of_payments", "reserves"],
        "demography and social mobility": ["population", "births", "deaths", "migration_net"],
        "trust, legitimacy, polarization, unrest": [
            "trust",
            "legitimacy",
            "polarization",
            "unrest",
            "class_conflict_pressure",
            "belief_in_system",
        ],
        "class and inequality dynamics": [
            "wealth_gini",
            "wealth_top10pct",
            "poverty_headcount",
            "class_support_workers",
            "class_support_professionals",
            "class_support_capitalists",
            "class_support_informal",
            "capital_flight_rate",
        ],
        "events and causality log": ["policy_active", "consistency_ok", "consistency_tick"],
    }
    normalized = sheet_name.strip().lower()
    if normalized == "executive overview":
        return render_table("Sheet: Executive Overview", build_executive_overview_rows(state))
    if normalized == "state explorer":
        return render_table("Sheet: State Explorer", build_state_explorer_rows(state))
    if normalized == "commodity flows and storage":
        return render_table("Sheet: Commodity Flows and Storage", build_commodity_flow_rows(state))
    if normalized == "logistics chokepoints":
        return render_table("Sheet: Logistics Chokepoints", build_logistics_chokepoint_rows(state))
    if normalized == "shortages and class impact":
        return render_table("Sheet: Shortages and Class Impact", build_shortage_class_impact_rows(state))
    if normalized == "regional map (ascii)":
        return f"Sheet: Regional Map (ASCII)\n{render_region_ascii_map(state)}"
    keys = sheet_map.get(normalized)
    if keys is None:
        return "Unknown sheet. Use 'sheets' to list available sheets."
    rows = [(key, state.get(key, "n/a")) for key in keys]
    return render_table(f"Sheet: {sheet_name}", rows)


def render_filtered_sheet_detail(sheet_name: str, state: dict[str, Any], filter_text: str) -> str:
    detail = render_sheet_detail(sheet_name, state)
    lines = detail.splitlines()
    if filter_text.strip() == "":
        return detail
    filtered = [lines[0]]
    needle = filter_text.strip().lower()
    filtered.extend(line for line in lines[1:] if needle in line.lower())
    return "\n".join(filtered)


def render_metric_history(engine: Any, metric_name: str, limit: int = 5) -> str:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    rows = []
    history = engine.store.state_history[-limit:]
    for idx, state in enumerate(history, start=max(1, len(engine.store.state_history) - len(history) + 1)):
        rows.append((f"snapshot {idx}", state.get(metric_name, "n/a")))
    return render_table(f"History: {metric_name}", rows)


def render_help() -> str:
    rows = [
        ("show", "render macro summary table"),
        ("sheets", "list available sheets"),
        ("sheet <n|name>[|filter]", "open a sheet and optionally filter rows"),
        ("history <metric> [n]", "show recent metric history"),
        ("step [n]", "advance the simulation by n ticks"),
        ("compare [ticks]", "run side-by-side stress comparison table"),
        ("q", "exit dashboard"),
    ]
    return render_table("Dashboard Commands", rows)


def _run_case(scenario_path: str, seed: int, patch: dict[str, float], ticks: int) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=seed, scenario_path=scenario_path)
    engine.store.state.update(patch)
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return {metric: float(engine.store.state.get(metric, 0.0)) for metric in COMPARISON_METRICS}


def render_scenario_comparison(scenario_path: str = DEFAULT_SCENARIO_PATH, seed: int = 42, ticks: int = 24) -> str:
    if ticks < 1:
        raise ValueError("ticks must be >= 1")

    results = {name: _run_case(scenario_path, seed, patch, ticks) for name, patch in COMPARISON_PATCHES.items()}
    baseline = results["baseline"]
    rows: list[list[object]] = []
    for metric in COMPARISON_METRICS:
        rows.append(
            [
                metric,
                f"{baseline[metric]:.4f}",
                f"{results['sanctions'][metric]:.4f}",
                f"{results['energy_shock'][metric]:.4f}",
                f"{results['banking_panic'][metric]:.4f}",
            ]
        )
    header = ["metric", "baseline", "sanctions", "energy_shock", "banking_panic"]
    summary = render_matrix_table(f"Scenario Comparison ({ticks} ticks)", header, rows)

    delta_rows: list[list[object]] = []
    for scenario_name in ("sanctions", "energy_shock", "banking_panic"):
        delta_rows.append(
            [
                scenario_name,
                f"{results[scenario_name]['price'] - baseline['price']:.4f}",
                f"{results[scenario_name]['reserves'] - baseline['reserves']:.4f}",
                f"{results[scenario_name]['trust'] - baseline['trust']:.4f}",
                f"{results[scenario_name]['unrest'] - baseline['unrest']:.4f}",
            ]
        )
    deltas = render_matrix_table(
        "Scenario Deltas vs Baseline",
        ["scenario", "price_delta", "reserves_delta", "trust_delta", "unrest_delta"],
        delta_rows,
    )
    return f"{summary}\n\n{deltas}"


def run_interactive(state: dict[str, Any]) -> None:
    print(render_summary(state))
    print()
    print(render_sheets())
    print()
    print(render_help())
    while True:
        value = input("select> ").strip().lower()
        if value in {"q", "quit", "exit"}:
            print("Exiting dashboard.")
            return
        print("Sheet navigation placeholder. Use 'q' to exit.")


def advance_ticks(engine: Any, count: int) -> dict[str, Any]:
    if count < 1:
        raise ValueError("count must be >= 1")
    current_tick = int(engine.store.state.get("last_tick", 0))
    for _ in range(count):
        current_tick += 1
        engine.run_tick(current_tick)
    engine.store.state["last_tick"] = current_tick
    return engine.store.state


def process_command(command: str, engine: Any) -> tuple[str, bool]:
    command = command.strip().lower()
    if command in {"q", "quit", "exit"}:
        return "Exiting dashboard.", True
    if command in {"help", "?"}:
        return render_help(), False
    if command in {"show", "summary"}:
        return render_summary(engine.store.state), False
    if command == "sheets":
        return render_sheets(), False
    if command.startswith("sheet"):
        raw = command[5:].strip()
        if not raw:
            return "Specify a sheet number or exact name after 'sheet'.", False
        sheet_names = default_sheet_names()
        if "|" in raw:
            raw_name, raw_filter = [part.strip() for part in raw.split("|", 1)]
        else:
            raw_name, raw_filter = raw, ""
        if raw_name.isdigit():
            idx = int(raw_name) - 1
            if 0 <= idx < len(sheet_names):
                return render_filtered_sheet_detail(sheet_names[idx], engine.store.state, raw_filter), False
            return "Sheet index out of range.", False
        for name in sheet_names:
            if name.lower() == raw_name:
                return render_filtered_sheet_detail(name, engine.store.state, raw_filter), False
        return "Unknown sheet. Use 'sheets' to list available sheets.", False
    if command.startswith("history"):
        parts = command.split()
        if len(parts) < 2:
            return "Specify a metric after 'history'.", False
        metric_name = parts[1]
        limit = 5
        if len(parts) > 2:
            limit = int(parts[2])
        return render_metric_history(engine, metric_name, limit), False
    if command.startswith("step"):
        parts = command.split()
        step_count = 1
        if len(parts) > 1:
            step_count = int(parts[1])
        state = advance_ticks(engine, step_count)
        return render_summary(state), False
    if command.startswith("compare"):
        parts = command.split()
        compare_ticks = 24
        if len(parts) > 1:
            compare_ticks = int(parts[1])
        return render_scenario_comparison(scenario_path=DEFAULT_SCENARIO_PATH, seed=engine.base_seed, ticks=compare_ticks), False
    return "Unknown command. Use: help, show, sheets, sheet <n|name>[|filter], history <metric> [n], step [n], compare [ticks], q", False


def run_interactive_engine(scenario_path: str, seed: int = 42) -> None:
    engine = build_engine_from_scenario(seed=seed, scenario_path=scenario_path)
    engine.store.state["last_tick"] = 0

    print(render_summary(engine.store.state))
    print()
    print(render_sheets())
    print()
    print(render_help())

    while True:
        value = input("select> ")
        message, should_exit = process_command(value, engine)
        print(message)
        if should_exit:
            return


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Country Simulation terminal dashboard.")
    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO_PATH,
        help="Path to the scenario YAML file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic simulation seed.",
    )
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()
    run_interactive_engine(scenario_path=args.scenario, seed=args.seed)


if __name__ == "__main__":
    main()
