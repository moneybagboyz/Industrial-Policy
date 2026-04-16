from __future__ import annotations

from src.core.tick_engine import TickEngine


def stage_growth(prior_state: dict, context: dict) -> dict:
    tick = context["tick"]
    rng = context["rng"]
    shock = rng.uniform(tick=tick, event_id="growth_shock", low=-0.01, high=0.02)
    gdp = float(prior_state["gdp"]) * (1.0 + 0.01 + shock)
    return {"gdp": round(gdp, 8), "last_tick": tick}


def build_engine(seed: int) -> TickEngine:
    engine = TickEngine(base_seed=seed)
    engine.register_stage("growth", stage_growth)
    engine.initialize({"gdp": 100.0, "last_tick": 0})
    return engine


def run_path(seed: int, ticks: int) -> tuple[list[str], dict]:
    engine = build_engine(seed)
    for tick in range(1, ticks + 1):
        engine.run_tick(tick)
    return engine.store.snapshot_hashes, engine.store.state


def test_replay_determinism_240_ticks() -> None:
    hashes_a, state_a = run_path(seed=42, ticks=240)
    hashes_b, state_b = run_path(seed=42, ticks=240)

    assert hashes_a == hashes_b
    assert state_a == state_b


def test_different_seed_changes_path() -> None:
    hashes_a, state_a = run_path(seed=42, ticks=24)
    hashes_b, state_b = run_path(seed=43, ticks=24)

    assert hashes_a != hashes_b
    assert state_a != state_b
