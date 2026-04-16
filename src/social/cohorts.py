"""Cohort stock transitions and conservation checks."""

from __future__ import annotations


def next_population(current: float, births: float, deaths: float, migration_net: float) -> float:
    """Population update with non-negative floor."""
    return max(0.0, current + births - deaths + migration_net)


def population_residual(total_before: float, total_after: float, births: float, deaths: float, migration_net: float) -> float:
    """Residual for conservation check."""
    expected_after = total_before + births - deaths + migration_net
    return total_after - expected_after
