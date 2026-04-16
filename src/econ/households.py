"""Household demand functions."""

from __future__ import annotations


def consumption_demand(
    base_share: float,
    disposable_income: float,
    good_price: float,
    basket_price: float,
    elasticity: float,
) -> float:
    """Compute demand level with relative-price substitution."""
    if good_price <= 0 or basket_price <= 0:
        raise ValueError("Prices must be positive")
    real_income = disposable_income / good_price
    relative_price_term = (good_price / basket_price) ** (-elasticity)
    return max(0.0, base_share * real_income * relative_price_term)
