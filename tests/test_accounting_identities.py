from __future__ import annotations

from src.econ.national_accounts import (
    ExpenditureComponents,
    IncomeComponents,
    accounting_residual_ratio,
    gdp_expenditure,
    gdp_income,
    passes_identity_gate,
)
from src.econ.sector_balances import SectorBalances, net_sector_balance, passes_sector_gate


def test_gdp_identities_match_with_consistent_inputs() -> None:
    exp = ExpenditureComponents(
        consumption=500.0,
        investment=120.0,
        government=140.0,
        exports=90.0,
        imports=70.0,
    )
    inc = IncomeComponents(
        wages=420.0,
        profits=280.0,
        taxes_production=60.0,
        taxes_imports=25.0,
        subsidies=5.0,
    )

    y_exp = gdp_expenditure(exp)
    y_inc = gdp_income(inc)

    assert y_exp == y_inc
    assert passes_identity_gate(y_exp, y_inc, tolerance_ratio=0.001)


def test_gdp_identity_gate_fails_above_point_one_percent() -> None:
    y_exp = 1000.0
    y_inc = 998.0

    ratio = accounting_residual_ratio(y_exp, y_inc)

    assert ratio > 0.001
    assert not passes_identity_gate(y_exp, y_inc, tolerance_ratio=0.001)


def test_sector_balance_passes_when_sum_is_zero() -> None:
    balances = SectorBalances(
        households=20.0,
        firms=-5.0,
        government=-10.0,
        financial_sector=2.0,
        rest_of_world=-7.0,
    )

    assert net_sector_balance(balances) == 0.0
    assert passes_sector_gate(balances, tolerance_abs=1e-9)


def test_sector_balance_fails_when_residual_too_large() -> None:
    balances = SectorBalances(
        households=10.0,
        firms=-1.0,
        government=-8.0,
        financial_sector=0.4,
        rest_of_world=-1.0,
    )

    assert abs(net_sector_balance(balances)) > 0.001
    assert not passes_sector_gate(balances, tolerance_abs=0.001)
