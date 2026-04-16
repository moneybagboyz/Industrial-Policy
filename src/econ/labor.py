"""Labor market transition helpers."""

from __future__ import annotations


def wage_growth_rate(
    productivity_growth: float,
    unemployment_rate: float,
    natural_unemployment: float,
    expected_inflation: float,
    phi_productivity: float,
    phi_slack: float,
    phi_expectations: float,
) -> float:
    """Compute wage growth from productivity, slack, and expectations."""
    slack = unemployment_rate - natural_unemployment
    return (
        phi_productivity * productivity_growth
        - phi_slack * slack
        + phi_expectations * expected_inflation
    )


def next_wage(current_wage: float, growth_rate: float) -> float:
    return max(0.0, current_wage * (1.0 + growth_rate))


def bounded_next_wage(current_wage: float, growth_rate: float, max_drop: float = 0.03) -> float:
    """Update wage with a floor on one-period collapse.

    `max_drop` is the maximum fractional decline allowed in one step.
    """
    if not 0.0 <= max_drop < 1.0:
        raise ValueError("max_drop must be in [0, 1)")
    bounded_growth = max(growth_rate, -max_drop)
    return next_wage(current_wage, bounded_growth)


def next_unemployment(current_unemployment: float, separations: float, matches: float) -> float:
    """Update unemployment share and clamp into [0, 1]."""
    value = current_unemployment + separations - matches
    return min(1.0, max(0.0, value))
