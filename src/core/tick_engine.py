"""Monthly deterministic tick engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .rng import DeterministicRNG
from .state_store import StateStore

StageFn = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


@dataclass
class TickEngine:
    """Executes ordered simulation stages and commits next state."""

    base_seed: int
    stages: list[tuple[str, StageFn]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.rng = DeterministicRNG(self.base_seed)
        self.store = StateStore()

    def register_stage(self, name: str, stage_fn: StageFn) -> None:
        self.stages.append((name, stage_fn))

    def initialize(self, initial_state: dict[str, Any]) -> None:
        self.store.load_initial(initial_state)

    def run_tick(self, tick: int) -> str:
        prior_state = self.store.state
        next_state = _copy_state(prior_state)

        context: dict[str, Any] = {
            "tick": tick,
            "rng": self.rng,
            "previous_state": prior_state,
        }

        for stage_name, stage_fn in self.stages:
            patch = stage_fn(next_state, context)
            if not isinstance(patch, dict):
                raise TypeError(f"Stage '{stage_name}' must return a dict patch")
            next_state.update(patch)

        return self.store.commit(next_state)


def _copy_state(state: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in state.items()}
