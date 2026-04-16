"""National accounts identities and residual checks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpenditureComponents:
    consumption: float
    investment: float
    government: float
    exports: float
    imports: float


@dataclass(frozen=True)
class IncomeComponents:
    wages: float
    profits: float
    taxes_production: float
    taxes_imports: float
    subsidies: float


def gdp_expenditure(components: ExpenditureComponents) -> float:
    """GDP by expenditure identity: Y = C + I + G + X - M."""
    return (
        components.consumption
        + components.investment
        + components.government
        + components.exports
        - components.imports
    )


def gdp_income(components: IncomeComponents) -> float:
    """GDP by income identity: Y = W + Pi + Tprod + Timp - Subsidies."""
    return (
        components.wages
        + components.profits
        + components.taxes_production
        + components.taxes_imports
        - components.subsidies
    )


def accounting_residual(expenditure_gdp: float, income_gdp: float) -> float:
    """Signed residual between GDP accounting approaches."""
    return expenditure_gdp - income_gdp


def accounting_residual_ratio(expenditure_gdp: float, income_gdp: float) -> float:
    """Absolute residual ratio against average GDP level."""
    scale = max((abs(expenditure_gdp) + abs(income_gdp)) / 2.0, 1e-9)
    return abs(accounting_residual(expenditure_gdp, income_gdp)) / scale


def passes_identity_gate(
    expenditure_gdp: float,
    income_gdp: float,
    tolerance_ratio: float = 0.001,
) -> bool:
    """Return True when GDP identity residual is inside tolerance."""
    return accounting_residual_ratio(expenditure_gdp, income_gdp) <= tolerance_ratio
