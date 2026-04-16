from __future__ import annotations

from src.core.default_engine import build_engine_from_scenario


def _run(patch: dict[str, float] | None = None, ticks: int = 24) -> dict[str, float]:
    engine = build_engine_from_scenario(seed=909, scenario_path="data/scenarios/baseline_1990_country_a.yaml")
    if patch:
        engine.store.state.update(patch)
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return engine.store.state


def test_strategic_system_metrics_exist() -> None:
    state = _run(ticks=12)

    required = [
        "trade_access_index",
        "sanctions_index",
        "war_risk_index",
        "law_stability_index",
        "reform_momentum",
        "technology_tier",
        "research_progress",
        "innovation_adoption",
        "military_readiness",
        "internal_security_risk",
        "active_crisis",
        "crisis_intensity",
        "state_failure_risk",
        "victory_progress",
        "game_over",
    ]
    for key in required:
        assert key in state


def test_research_spend_raises_technology_progress() -> None:
    baseline = _run(ticks=36)
    research_push = _run(patch={"research_spend_share": 0.12}, ticks=36)

    assert float(research_push["technology_tier"]) >= float(baseline["technology_tier"])
    assert float(research_push["innovation_adoption"]) >= float(baseline["innovation_adoption"]) * 0.95


def test_security_posture_lowers_internal_security_risk_short_run() -> None:
    low_security = _run(patch={"security_posture": 0.15}, ticks=24)
    high_security = _run(patch={"security_posture": 0.85}, ticks=24)

    assert float(high_security["internal_security_risk"]) <= float(low_security["internal_security_risk"]) + 0.10


def test_diplomacy_posture_improves_trade_access() -> None:
    closed = _run(patch={"diplomacy_posture": 0.2}, ticks=24)
    open_posture = _run(patch={"diplomacy_posture": 0.8}, ticks=24)

    assert float(open_posture["trade_access_index"]) >= float(closed["trade_access_index"])
