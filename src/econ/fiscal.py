"""Fiscal identity utilities."""

from __future__ import annotations


def primary_balance(revenue: float, non_interest_spending: float) -> float:
    """Primary balance: T - G_nonint."""
    return revenue - non_interest_spending


def interest_payment(debt_stock: float, effective_rate_annual: float) -> float:
    """Monthly interest payment from annualized rate."""
    return debt_stock * effective_rate_annual / 12.0


def fiscal_deficit(revenue: float, non_interest_spending: float, interest: float) -> float:
    """Total deficit: G_nonint + Int - T."""
    return non_interest_spending + interest - revenue
