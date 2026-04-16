"""Deterministic random stream utilities."""

from __future__ import annotations

import hashlib
import random


class DeterministicRNG:
    """Seeded RNG with deterministic event-keyed substreams."""

    def __init__(self, base_seed: int) -> None:
        self.base_seed = int(base_seed)

    def stream(self, tick: int, event_id: str) -> random.Random:
        payload = f"{self.base_seed}:{tick}:{event_id}".encode("ascii", errors="ignore")
        digest = hashlib.sha256(payload).hexdigest()
        # Keep seed in integer range accepted by Python's random.
        seed_value = int(digest[:16], 16)
        return random.Random(seed_value)

    def uniform(self, tick: int, event_id: str, low: float = 0.0, high: float = 1.0) -> float:
        rng = self.stream(tick=tick, event_id=event_id)
        return rng.uniform(low, high)
