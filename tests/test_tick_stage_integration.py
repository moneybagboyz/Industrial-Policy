from __future__ import annotations

from src.core.default_engine import build_default_engine


def test_default_engine_runs_and_writes_stage_outputs() -> None:
    engine = build_default_engine(seed=7)
    engine.initialize(
        {
            "price": 100.0,
            "wage": 1000.0,
            "unemployment": 0.08,
            "debt": 500.0,
            "reserves": 80.0,
            "population": 1_000_000.0,
        }
    )

    for tick in range(1, 4):
        engine.run_tick(tick)

    state = engine.store.state
    assert "production" in state
    assert "price" in state
    assert "debt" in state
    assert "population" in state
    assert state["consistency_ok"] is True
    assert len(engine.store.state_history) == 4


def test_default_engine_replay_deterministic() -> None:
    def run_once(seed: int) -> tuple[list[str], dict]:
        engine = build_default_engine(seed=seed)
        engine.initialize({"price": 100.0, "debt": 500.0, "population": 1_000_000.0})
        for tick in range(1, 25):
            engine.run_tick(tick)
        return engine.store.snapshot_hashes, engine.store.state

    h1, s1 = run_once(seed=99)
    h2, s2 = run_once(seed=99)

    assert h1 == h2
    assert s1 == s2
