"""External sector accounting and FX pressure helpers."""

from __future__ import annotations


def current_account(exports: float, imports: float, net_factor_income: float, transfers: float) -> float:
    return exports - imports + net_factor_income + transfers


def balance_of_payments(current_account_value: float, capital_account: float) -> float:
    return current_account_value + capital_account


def next_reserves(previous_reserves: float, bop_flow: float) -> float:
    return previous_reserves + bop_flow


def fx_pressure(
    bop_to_gdp: float,
    inflation_differential: float,
    risk_premium: float,
    psi1: float,
    psi2: float,
    psi3: float,
) -> float:
    """Positive result indicates depreciation pressure."""
    return psi1 * (-bop_to_gdp) + psi2 * inflation_differential + psi3 * risk_premium
