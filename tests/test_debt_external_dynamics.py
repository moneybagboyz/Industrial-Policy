from __future__ import annotations

from src.econ.debt import debt_to_gdp, next_debt_stock
from src.econ.external_sector import balance_of_payments, current_account, fx_pressure, next_reserves
from src.econ.fiscal import fiscal_deficit, interest_payment, primary_balance
from src.econ.monetary import credit_cost, investment_modifier, real_policy_rate


def test_fiscal_identities() -> None:
    pb = primary_balance(revenue=100.0, non_interest_spending=95.0)
    intr = interest_payment(debt_stock=240.0, effective_rate_annual=0.06)
    deficit = fiscal_deficit(revenue=100.0, non_interest_spending=95.0, interest=intr)

    assert pb == 5.0
    assert round(intr, 6) == 1.2
    assert round(deficit, 6) == round(95.0 + 1.2 - 100.0, 6)


def test_debt_transition_and_ratio() -> None:
    debt = next_debt_stock(previous_debt=500.0, deficit=10.0, valuation_fx=2.0)
    ratio = debt_to_gdp(debt_stock=debt, nominal_gdp=1000.0)

    assert debt == 512.0
    assert ratio == 0.512


def test_external_balances_and_reserves() -> None:
    ca = current_account(exports=120.0, imports=140.0, net_factor_income=10.0, transfers=5.0)
    bop = balance_of_payments(current_account_value=ca, capital_account=20.0)
    res = next_reserves(previous_reserves=80.0, bop_flow=bop)

    assert ca == -5.0
    assert bop == 15.0
    assert res == 95.0


def test_fx_pressure_sign() -> None:
    pressure = fx_pressure(
        bop_to_gdp=-0.02,
        inflation_differential=0.01,
        risk_premium=0.03,
        psi1=0.5,
        psi2=0.2,
        psi3=0.4,
    )
    assert pressure > 0.0


def test_monetary_transmission_helpers() -> None:
    real_rate = real_policy_rate(nominal_rate=0.08, expected_inflation=0.03)
    cost = credit_cost(base_spread=0.02, policy_rate=0.08, risk_spread=0.03)
    inv_mod = investment_modifier(real_rate=real_rate, sensitivity=0.5)

    assert real_rate == 0.05
    assert cost == 0.13
    assert inv_mod < 1.0
