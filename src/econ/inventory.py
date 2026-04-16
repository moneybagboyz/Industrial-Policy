"""Inventory carryover and drawdown helpers."""

from __future__ import annotations


def next_inventory(current_inventory: float, production: float, demand: float) -> float:
    """Compute end-of-period inventory with non-negative floor."""
    return max(0.0, current_inventory + production - demand)


def unmet_demand(current_inventory: float, production: float, demand: float) -> float:
    """Compute unmet demand after available supply is exhausted."""
    available = max(0.0, current_inventory + production)
    return max(0.0, demand - available)
