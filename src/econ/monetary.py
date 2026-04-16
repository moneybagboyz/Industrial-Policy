"""Monetary policy transmission helpers."""

from __future__ import annotations


def real_policy_rate(nominal_rate: float, expected_inflation: float) -> float:
    return nominal_rate - expected_inflation


def credit_cost(base_spread: float, policy_rate: float, risk_spread: float) -> float:
    """Aggregate borrowing cost approximation."""
    return base_spread + policy_rate + risk_spread


def investment_modifier(real_rate: float, sensitivity: float = 0.5) -> float:
    """Simple negative relationship between real rates and investment impulse."""
    return 1.0 - sensitivity * real_rate
