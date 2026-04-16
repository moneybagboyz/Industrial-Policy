from __future__ import annotations

from src.econ.households import consumption_demand
from src.econ.labor import bounded_next_wage, next_unemployment, next_wage, wage_growth_rate
from src.econ.pricing import PricingParams, cpi_inflation, inflation_rate, next_price


def test_next_price_rises_with_positive_channels() -> None:
    params = PricingParams(
        lambda_cost=0.4,
        lambda_demand=0.2,
        lambda_fx=0.1,
        lambda_expectations=0.2,
    )
    p1 = next_price(
        current_price=100.0,
        cost_delta=0.02,
        demand_gap=0.01,
        fx_delta=0.0,
        expected_inflation=0.01,
        params=params,
    )
    assert p1 > 100.0


def test_cpi_inflation_weighted_average() -> None:
    prices_prev = {"food": 100.0, "energy": 100.0}
    prices_now = {"food": 110.0, "energy": 95.0}
    weights = {"food": 0.7, "energy": 0.3}

    cpi = cpi_inflation(prices_now, prices_prev, weights)
    assert round(cpi, 6) == round(0.7 * 0.10 + 0.3 * -0.05, 6)


def test_wage_and_unemployment_updates() -> None:
    g = wage_growth_rate(
        productivity_growth=0.01,
        unemployment_rate=0.08,
        natural_unemployment=0.06,
        expected_inflation=0.005,
        phi_productivity=0.6,
        phi_slack=0.4,
        phi_expectations=0.5,
    )
    wage = next_wage(1000.0, g)
    unemployment = next_unemployment(0.08, separations=0.01, matches=0.015)

    assert wage > 0.0
    assert 0.0 <= unemployment <= 1.0
    assert unemployment < 0.08


def test_consumption_demand_positive() -> None:
    demand = consumption_demand(
        base_share=0.3,
        disposable_income=2000.0,
        good_price=50.0,
        basket_price=40.0,
        elasticity=0.6,
    )
    assert demand > 0.0


def test_inflation_rate() -> None:
    assert inflation_rate(105.0, 100.0) == 0.05


def test_bounded_next_wage_limits_one_step_collapse() -> None:
    wage = bounded_next_wage(current_wage=1000.0, growth_rate=-0.50, max_drop=0.03)
    assert wage == 970.0
