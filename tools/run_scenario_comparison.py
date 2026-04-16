"""Generate baseline versus stress scenario comparison reports."""

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
SCENARIO_PATH = PROJECT_ROOT / "data" / "scenarios" / "baseline_1990_country_a.yaml"

SCENARIOS = {
    "baseline": {},
    "sanctions": {"exports": 5_000_000_000.0, "imports": 14_000_000_000.0},
    "energy_shock": {"cost_delta": 0.03},
    "banking_panic": {"matches": 0.004, "separations": 0.02},
}

METRICS = [
    "price",
    "wage",
    "unemployment",
    "debt",
    "reserves",
    "trust",
    "legitimacy",
    "unrest",
]


def run_case(seed: int, patch: dict[str, float], ticks: int = 120) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=seed, scenario_path=str(SCENARIO_PATH))
    engine.store.state.update(patch)
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return {metric: float(engine.store.state.get(metric, 0.0)) for metric in METRICS}


def build_report(seed: int = 42) -> dict[str, object]:
    results = {name: run_case(seed, patch) for name, patch in SCENARIOS.items()}
    baseline = results["baseline"]
    deltas = {}
    for name, values in results.items():
        if name == "baseline":
            continue
        deltas[name] = {metric: values[metric] - baseline[metric] for metric in METRICS}
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "results": results,
        "deltas_vs_baseline": deltas,
    }


def write_report(report: dict[str, object]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "scenario_comparison.json"
    md_path = REPORTS_DIR / "scenario_comparison.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = ["# Scenario Comparison Report", ""]
    lines.append(f"- Timestamp: {report['timestamp_utc']}")
    lines.append(f"- Seed: {report['seed']}")
    lines.append("")
    for name, values in report["results"].items():
        lines.append(f"## {name}")
        for metric, value in values.items():
            lines.append(f"- {metric}: {value:.6f}")
        lines.append("")
    for name, values in report["deltas_vs_baseline"].items():
        lines.append(f"## Delta vs baseline: {name}")
        for metric, value in values.items():
            lines.append(f"- {metric}: {value:.6f}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    report = build_report(seed=42)
    write_report(report)
    print(json.dumps(report, indent=2))
