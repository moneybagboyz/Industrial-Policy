from __future__ import annotations

from tools.run_scenario_comparison import build_report


def test_build_report_contains_baseline_and_deltas() -> None:
    report = build_report(seed=42)

    assert "baseline" in report["results"]
    assert "sanctions" in report["results"]
    assert "energy_shock" in report["deltas_vs_baseline"]
    assert "reserves" in report["deltas_vs_baseline"]["sanctions"]
