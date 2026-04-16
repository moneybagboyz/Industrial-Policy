"""Price update and inflation decomposition utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PricingParams:
    lambda_cost: float
    lambda_demand: float
    lambda_fx: float
    lambda_expectations: float


def next_price(
    current_price: float,
    cost_delta: float,
    demand_gap: float,
    fx_delta: float,
    expected_inflation: float,
    params: PricingParams,
) -> float:
    """Compute next-period price using additive channel contributions."""
    growth = (
        params.lambda_cost * cost_delta
        + params.lambda_demand * demand_gap
        + params.lambda_fx * fx_delta
        + params.lambda_expectations * expected_inflation
    )
    return max(0.0, current_price * (1.0 + growth))


def inflation_rate(current_price: float, previous_price: float) -> float:
    """Return period inflation as percentage change."""
    if previous_price <= 0:
        raise ValueError("previous_price must be positive")
    return (current_price - previous_price) / previous_price


def cpi_inflation(prices_now: dict[str, float], prices_prev: dict[str, float], weights: dict[str, float]) -> float:
    """Weighted CPI inflation across goods."""
    total = 0.0
    for good, weight in weights.items():
        total += weight * inflation_rate(prices_now[good], prices_prev[good])
    return total
