"""Sector balance residual checks for stock-flow consistency."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SectorBalances:
    households: float
    firms: float
    government: float
    financial_sector: float
    rest_of_world: float


def net_sector_balance(balances: SectorBalances) -> float:
    """Aggregate net lending/borrowing across sectors.

    In a closed accounting system, this should sum to zero.
    """

    return (
        balances.households
        + balances.firms
        + balances.government
        + balances.financial_sector
        + balances.rest_of_world
    )


def passes_sector_gate(balances: SectorBalances, tolerance_abs: float = 1e-6) -> bool:
    """Return True if aggregate sector residual is within absolute tolerance."""
    return abs(net_sector_balance(balances)) <= tolerance_abs
