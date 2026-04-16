"""Canonical state storage and hashing utilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StateStore:
    """Stores current state and snapshot history for replay checks."""

    state: dict[str, Any] = field(default_factory=dict)
    snapshot_hashes: list[str] = field(default_factory=list)
    state_history: list[dict[str, Any]] = field(default_factory=list)

    def load_initial(self, initial_state: dict[str, Any]) -> None:
        self.state = _deep_copy_dict(initial_state)
        self.snapshot_hashes = [self.snapshot_hash(self.state)]
        self.state_history = [_deep_copy_dict(self.state)]

    def commit(self, next_state: dict[str, Any]) -> str:
        self.state = _deep_copy_dict(next_state)
        digest = self.snapshot_hash(self.state)
        self.snapshot_hashes.append(digest)
        self.state_history.append(_deep_copy_dict(self.state))
        return digest

    @staticmethod
    def snapshot_hash(state: dict[str, Any]) -> str:
        canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("ascii")).hexdigest()


def _deep_copy_dict(value: dict[str, Any]) -> dict[str, Any]:
    # JSON round-trip keeps deterministic key/value representation.
    return json.loads(json.dumps(value, sort_keys=True, ensure_ascii=True))
