"""Debt stock evolution functions."""

from __future__ import annotations


def next_debt_stock(previous_debt: float, deficit: float, valuation_fx: float = 0.0) -> float:
    """Debt transition equation with valuation effects."""
    return previous_debt + deficit + valuation_fx


def debt_to_gdp(debt_stock: float, nominal_gdp: float) -> float:
    """Debt burden ratio against nominal GDP."""
    if nominal_gdp <= 0:
        raise ValueError("nominal_gdp must be positive")
    return debt_stock / nominal_gdp
