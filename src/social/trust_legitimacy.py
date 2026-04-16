"""Trust and legitimacy state updates."""

from __future__ import annotations


def clamp_index(value: float) -> float:
    return min(100.0, max(0.0, value))


def next_legitimacy(
    current: float,
    service_performance: float,
    real_income: float,
    corruption: float,
    repression_excess: float,
    fairness: float,
    l1: float,
    l2: float,
    l3: float,
    l4: float,
    l5: float,
) -> float:
    delta = (
        l1 * service_performance
        + l2 * real_income
        - l3 * corruption
        - l4 * repression_excess
        + l5 * fairness
    )
    return clamp_index(current + delta)


def next_trust(
    current: float,
    legitimacy: float,
    info_quality: float,
    polarization: float,
    inequality_shock: float,
    z1: float,
    z2: float,
    z3: float,
    z4: float,
) -> float:
    delta = z1 * legitimacy + z2 * info_quality - z3 * polarization - z4 * inequality_shock
    return clamp_index(current + delta)
