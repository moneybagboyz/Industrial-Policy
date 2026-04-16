"""Simple proportional allocation for constrained supply."""

from __future__ import annotations


def proportional_allocation(total_supply: float, requested: dict[str, float]) -> dict[str, float]:
    """Allocate supply proportionally when requests exceed available supply."""
    clean_requests = {k: max(0.0, v) for k, v in requested.items()}
    total_requested = sum(clean_requests.values())

    if total_requested <= 0.0:
        return {k: 0.0 for k in clean_requests}
    if total_requested <= total_supply:
        return clean_requests

    scale = total_supply / total_requested
    return {k: v * scale for k, v in clean_requests.items()}
