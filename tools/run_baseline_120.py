"""Run baseline scenario for 120 ticks and write calibration artifacts."""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.default_engine import build_engine_from_scenario

REPORTS_DIR = PROJECT_ROOT / "reports"


def run_baseline_120(seed: int = 42) -> dict:
    engine = build_engine_from_scenario(
        seed=seed,
        scenario_path=str(PROJECT_ROOT / "data" / "scenarios" / "baseline_1990_country_a.yaml"),
    )
    for tick in range(1, 121):
        engine.run_tick(tick)

    state = engine.store.state
    snapshot = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "ticks": 120,
        "state": {
            "price": float(state.get("price", 0.0)),
            "wage": float(state.get("wage", 0.0)),
            "unemployment": float(state.get("unemployment", 0.0)),
            "debt": float(state.get("debt", 0.0)),
            "reserves": float(state.get("reserves", 0.0)),
            "population": float(state.get("population", 0.0)),
            "trust": float(state.get("trust", 0.0)),
            "legitimacy": float(state.get("legitimacy", 0.0)),
            "unrest": float(state.get("unrest", 0.0)),
        },
    }
    return snapshot


def write_artifacts(snapshot: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "baseline_120_snapshot.json"
    json_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    log_path = REPORTS_DIR / "calibration_log.md"
    log_entry = (
        "\n## Iteration 1\n"
        f"- Date: {snapshot['timestamp_utc']}\n"
        "- Scenario: baseline_1990_country_a\n"
        "- Run: 120 ticks\n"
        f"- Price: {snapshot['state']['price']:.6f}\n"
        f"- Wage: {snapshot['state']['wage']:.6f}\n"
        f"- Unemployment: {snapshot['state']['unemployment']:.6f}\n"
        f"- Debt: {snapshot['state']['debt']:.6f}\n"
        f"- Reserves: {snapshot['state']['reserves']:.6f}\n"
        f"- Population: {snapshot['state']['population']:.6f}\n"
        f"- Trust: {snapshot['state']['trust']:.6f}\n"
        f"- Legitimacy: {snapshot['state']['legitimacy']:.6f}\n"
        f"- Unrest: {snapshot['state']['unrest']:.6f}\n"
    )
    if log_path.exists():
        previous = log_path.read_text(encoding="utf-8")
    else:
        previous = "# Calibration Log\n"
    log_path.write_text(previous + log_entry, encoding="utf-8")


if __name__ == "__main__":
    result = run_baseline_120(seed=42)
    write_artifacts(result)
    print(json.dumps(result, indent=2))
