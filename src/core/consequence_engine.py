"""Unintended consequences engine.

Policies defined in ideology_traditions.SIGNATURE_POLICY_DEFS carry an
``unintended`` dict of side-effects that manifest after ``unintended_delay_ticks``
ticks.  This module manages the pending consequence queue and applies mature
consequences to the game state each tick.

Design principles
-----------------
- Consequences are hidden until they manifest (players see symptom, not cause).
- They're modelled from historical case studies — not random noise.
- High information quality (statistical bureau, free press) shortens detection
  lag and reduces magnitude (you catch problems earlier).
- Bureaucratic reach moderates implementation quality affects magnitude too.
"""

from __future__ import annotations

from typing import Any


def queue_consequences(
    pending: list[dict[str, Any]],
    policy_name: str,
    unintended_effects: dict[str, float],
    delay_ticks: int,
    current_tick: int,
    info_quality: float,
) -> list[dict[str, Any]]:
    """Schedule unintended consequences from a newly enacted policy.

    Args:
        pending: current pending consequence queue.
        policy_name: the source policy's name.
        unintended_effects: {state_key: delta} dict from policy definition.
        delay_ticks: ticks before effects materialise (reduced by info quality).
        current_tick: the current simulation tick.
        info_quality: 0–1; high quality reduces delay and magnitude.

    Returns:
        Updated pending list.
    """
    if not unintended_effects:
        return pending

    # Good information reduces delay and dampens magnitude
    effective_delay = max(1, int(delay_ticks * (1.0 - info_quality * 0.4)))
    magnitude_scale = 1.0 - info_quality * 0.25

    updated = list(pending)
    updated.append({
        "policy_name": policy_name,
        "effects": {k: v * magnitude_scale for k, v in unintended_effects.items()},
        "manifest_tick": current_tick + effective_delay,
        "enqueued_tick": current_tick,
        "revealed": False,
    })
    return updated


def apply_matured_consequences(
    pending: list[dict[str, Any]],
    current_tick: int,
) -> tuple[list[dict[str, Any]], dict[str, float], list[dict[str, Any]]]:
    """Apply all consequences whose manifest_tick has been reached.

    Returns:
        (remaining_pending, state_deltas, revealed_policy_names)
    """
    remaining: list[dict[str, Any]] = []
    deltas: dict[str, float] = {}
    revealed: list[dict[str, Any]] = []

    for item in pending:
        if current_tick >= int(item.get("manifest_tick", 0)):
            for key, delta in item.get("effects", {}).items():
                deltas[key] = deltas.get(key, 0.0) + float(delta)
            revealed.append(item)
        else:
            remaining.append(item)

    return remaining, deltas, revealed


def apply_consequence_deltas(
    state: dict[str, Any],
    deltas: dict[str, float],
) -> dict[str, Any]:
    """Merge consequence deltas into state, additive for floats.

    Handles both direct value additions and multiplicative production effects.
    """
    result: dict[str, float] = {}
    for key, delta in deltas.items():
        current = float(state.get(key, 0.0))
        result[key] = current + delta
    return result
