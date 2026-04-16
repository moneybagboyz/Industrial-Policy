"""Default stage implementations wiring econ and social modules."""

from __future__ import annotations

from typing import Any

from src.econ.debt import next_debt_stock
from src.econ.external_sector import balance_of_payments, current_account, fx_pressure, next_reserves
from src.econ.fiscal import fiscal_deficit, interest_payment
from src.econ.households import consumption_demand
from src.econ.inventory import next_inventory, unmet_demand
from src.econ.labor import bounded_next_wage, next_unemployment, wage_growth_rate
from src.econ.pricing import PricingParams, next_price
from src.econ.sector_network import simulate_sector_network
from src.econ.building_types import get_archetype
from src.econ.building_engine import make_building_from_queue_item
from src.social.cohorts import next_population
from src.social.trust_legitimacy import next_legitimacy, next_trust
from src.social.unrest import unrest_risk
from src.core.policy_system import (
    DEFAULT_ACTIVE_POLICIES,
    MINISTRIES,
    add_to_graveyard,
    bandwidth_cost,
    bandwidth_recharge,
    decay_graveyard,
    initial_ministry_budgets,
    update_active_policies,
    update_credibility,
    update_ministry_budgets,
)
from src.core.ideology_traditions import (
    SIGNATURE_POLICY_DEFS,
    TRADITIONS,
    bandwidth_discount_for_action,
    dominant_tradition,
    initial_tradition_influence,
    update_tradition_influence,
)
from src.core.consequence_engine import (
    apply_consequence_deltas,
    apply_matured_consequences,
    queue_consequences,
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def apply_policies(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    return {"policy_active": prior_state.get("policy_active", "baseline")}


def update_expectations(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    tick = context["tick"]
    rng = context["rng"]
    expected_inflation = float(prior_state.get("expected_inflation", 0.01))
    shock = rng.uniform(tick=tick, event_id="inflation_expectation_shock", low=-0.002, high=0.002)
    cost_delta = float(prior_state.get("cost_delta", 0.005))
    fx_delta = float(prior_state.get("fx_delta", 0.0))
    unemployment = float(prior_state.get("unemployment", 0.08))
    target_inflation = 0.008
    updated = (
        expected_inflation * 0.65
        + target_inflation * 0.35
        + shock
        + cost_delta * 0.08
        + fx_delta * 0.05
        + max(0.0, unemployment - 0.08) * 0.01
    )
    return {"expected_inflation": max(-0.03, min(0.08, updated))}


def compute_real_economy(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    sector_results = simulate_sector_network(prior_state)
    production = float(sector_results.get("production", prior_state.get("production", 90.0)))
    demand = float(sector_results.get("demand", prior_state.get("demand", 95.0)))
    inv_prev = float(prior_state.get("inventory", 10.0))
    inv_next = next_inventory(inv_prev, production, demand)
    shortage = unmet_demand(inv_prev, production, demand)
    return {
        **sector_results,
        "production": production,
        "inventory": max(inv_next, float(sector_results.get("inventory", inv_next))),
        "unmet_demand": max(shortage, float(sector_results.get("unmet_demand", shortage))),
    }


def update_prices_labor(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    params = PricingParams(0.28, 0.16, 0.08, 0.10)
    price_prev = float(prior_state.get("price", 100.0))
    price_next = next_price(
        current_price=price_prev,
        cost_delta=float(prior_state.get("cost_delta", 0.005)),
        demand_gap=float(prior_state.get("demand_gap", 0.002)),
        fx_delta=float(prior_state.get("fx_delta", 0.0)),
        expected_inflation=float(prior_state.get("expected_inflation", 0.01)),
        params=params,
    )

    wage_growth = wage_growth_rate(
        productivity_growth=float(prior_state.get("prod_growth", 0.003)),
        unemployment_rate=float(prior_state.get("unemployment", 0.08)),
        natural_unemployment=float(prior_state.get("natural_unemployment", 0.06)),
        expected_inflation=float(prior_state.get("expected_inflation", 0.01)),
        phi_productivity=0.6,
        phi_slack=0.35,
        phi_expectations=0.18,
    )
    panic_intensity = max(0.0, float(prior_state.get("separations", 0.01)) - float(prior_state.get("matches", 0.0105)))
    wage_floor_drop = 0.02 + min(0.03, panic_intensity)
    wage_growth = min(wage_growth, 0.01)
    wage_next = bounded_next_wage(float(prior_state.get("wage", 1000.0)), wage_growth, max_drop=wage_floor_drop)
    current_unemployment = float(prior_state.get("unemployment", 0.08))
    natural_unemployment = float(prior_state.get("natural_unemployment", 0.06))
    separations = float(prior_state.get("separations", 0.01))
    base_matches = float(prior_state.get("matches", 0.0105))
    employment_floor = natural_unemployment * 0.75
    effective_matches = min(base_matches, max(0.0, current_unemployment + separations - employment_floor))
    unemployment_next = next_unemployment(
        current_unemployment,
        separations=separations,
        matches=effective_matches,
    )

    # Blend building-derived employment signal when available.
    building_total_workers = float(prior_state.get("building_total_workers", 0.0))
    if building_total_workers > 0:
        population = max(float(prior_state.get("population", 1_000_000.0)), 1.0)
        labor_force = population * 0.65
        bldg_unemployment = max(0.0, 1.0 - building_total_workers / labor_force)
        # 30% weight on building-derived signal; 70% on flow-based model.
        unemployment_next = 0.70 * unemployment_next + 0.30 * bldg_unemployment

    disposable_income = float(prior_state.get("disposable_income", 2000.0))
    household_demand = consumption_demand(
        base_share=0.3,
        disposable_income=disposable_income,
        good_price=max(price_next, 1e-9),
        basket_price=float(prior_state.get("basket_price", 100.0)),
        elasticity=0.6,
    )

    inflation_proxy = (price_next / max(price_prev, 1e-9)) - 1.0

    return {
        "price": price_next,
        "inflation_proxy": inflation_proxy,
        "wage": wage_next,
        "unemployment": unemployment_next,
        "household_demand_proxy": household_demand,
    }


def update_public_external(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    debt_prev = float(prior_state.get("debt", 500.0))
    rate = float(prior_state.get("debt_rate", 0.06))

    nominal_gdp_prev = max(float(prior_state.get("nominal_gdp_monthly", 1_000_000_000.0)), 1.0)
    production = float(prior_state.get("production", prior_state.get("capacity_output", 100.0)))
    capacity_output = max(float(prior_state.get("capacity_output", 100.0)), 1.0)
    inflation_proxy = float(prior_state.get("inflation_proxy", 0.0))
    unemployment = float(prior_state.get("unemployment", 0.08))
    natural_unemployment = float(prior_state.get("natural_unemployment", 0.06))
    cost_delta = float(prior_state.get("cost_delta", 0.005))

    activity_ratio = min(1.2, max(0.55, production / capacity_output))
    slack = max(0.0, unemployment - natural_unemployment)
    real_growth = (activity_ratio - 0.95) * 0.03 - slack * 0.04 - cost_delta * 0.20
    nominal_gdp_monthly = max(1.0, nominal_gdp_prev * (1.0 + real_growth + inflation_proxy * 0.55))

    tax_ratio = float(prior_state.get("tax_ratio", 0.20))
    spend_ratio = float(prior_state.get("spend_ratio", 0.205))
    stabilizer_strength = float(prior_state.get("automatic_stabilizer_strength", 0.018))

    revenue = nominal_gdp_monthly * tax_ratio * max(0.75, 1.0 - slack * 1.5 + inflation_proxy * 0.08)
    spending = nominal_gdp_monthly * spend_ratio + nominal_gdp_monthly * stabilizer_strength * slack

    annual_gdp = nominal_gdp_monthly * 12.0
    debt_ratio_proxy = debt_prev / annual_gdp
    if debt_ratio_proxy > 0.75:
        spending *= 0.993
        revenue *= 1.004

    intr = interest_payment(debt_prev, rate)

    structural_exports = max(float(prior_state.get("structural_exports", prior_state.get("exports", 120.0))), 1.0)
    structural_imports = max(float(prior_state.get("structural_imports", prior_state.get("imports", 130.0))), 1.0)
    current_exports = float(prior_state.get("exports", structural_exports))
    current_imports = float(prior_state.get("imports", structural_imports))
    export_override = current_exports / structural_exports
    import_override = current_imports / structural_imports
    stored_export_shock = float(prior_state.get("trade_shock_exports", export_override))
    stored_import_shock = float(prior_state.get("trade_shock_imports", import_override))
    export_shock_factor = stored_export_shock
    import_shock_factor = stored_import_shock
    if abs(export_override - 1.0) > 1e-9 and abs(stored_export_shock - 1.0) <= 1e-9:
        export_shock_factor = export_override
    if abs(import_override - 1.0) > 1e-9 and abs(stored_import_shock - 1.0) <= 1e-9:
        import_shock_factor = import_override
    export_shock_factor = max(0.1, export_shock_factor)
    import_shock_factor = max(0.1, import_shock_factor)
    exports = structural_exports * export_shock_factor * max(0.65, 1.0 + (activity_ratio - 1.0) * 0.25 - slack * 0.15)
    imports = structural_imports * import_shock_factor * max(0.80, 1.0 + inflation_proxy * 0.12 + cost_delta * 0.15 + (activity_ratio - 1.0) * 0.10)

    ca = current_account(
        exports=exports,
        imports=imports,
        net_factor_income=float(prior_state.get("net_factor_income", 5.0)),
        transfers=float(prior_state.get("transfers", 3.0)),
    )
    bop = balance_of_payments(ca, float(prior_state.get("capital_account", 8.0)))
    reserves_next = max(0.0, next_reserves(float(prior_state.get("reserves", 80.0)), bop))

    if ca < 0.0:
        spending *= 1.002
        revenue *= 0.999

    reserve_cover = reserves_next / max(imports, 1.0)
    base_risk_premium = float(prior_state.get("risk_premium", 0.02))
    risk_premium = min(0.15, max(0.0, base_risk_premium + max(0.0, 1.0 - reserve_cover / 3.0) * 0.02 + max(0.0, debt_ratio_proxy - 0.6) * 0.03))
    fx_delta = max(
        0.0,
        min(
            0.12,
            fx_pressure(
                bop_to_gdp=bop / annual_gdp,
                inflation_differential=max(0.0, float(prior_state.get("expected_inflation", 0.01)) - 0.01),
                risk_premium=risk_premium,
                psi1=0.5,
                psi2=0.2,
                psi3=0.4,
            ),
        ),
    )
    external_stress = min(1.0, max(0.0, (-ca / annual_gdp) * 0.35 + fx_delta * 2.0 + (0.2 if reserve_cover < 3.0 else 0.0)))

    policy_rate = float(prior_state.get("policy_rate", 0.08))
    debt_rate_next = max(0.01, min(0.20, rate * 0.75 + (policy_rate + risk_premium) * 0.25))
    valuation_fx = debt_prev * float(prior_state.get("foreign_debt_share", 0.25)) * fx_delta * 0.08
    deficit = fiscal_deficit(revenue, spending, intr)
    debt_next = next_debt_stock(debt_prev, deficit, valuation_fx)
    debt_service_pressure = intr / annual_gdp

    return {
        "nominal_gdp_monthly": nominal_gdp_monthly,
        "interest_payment": intr,
        "deficit": deficit,
        "non_interest_spending": spending,
        "debt": debt_next,
        "debt_rate": debt_rate_next,
        "current_account": ca,
        "balance_of_payments": bop,
        "reserves": reserves_next,
        "debt_service_pressure": debt_service_pressure,
        "fx_delta": fx_delta,
        "external_stress": external_stress,
        "revenue": revenue,
        "exports": exports,
        "imports": imports,
        "trade_shock_exports": export_shock_factor,
        "trade_shock_imports": import_shock_factor,
        "risk_premium": risk_premium,
        "valuation_fx": valuation_fx,
    }


def update_class_dynamics(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    unemployment = float(prior_state.get("unemployment", 0.08))
    inflation_proxy = float(prior_state.get("inflation_proxy", 0.0))
    spend_ratio = float(prior_state.get("spend_ratio", 0.205))
    tax_ratio = float(prior_state.get("tax_ratio", 0.20))
    corruption = float(prior_state.get("corruption_signal", 0.3))
    info_quality = float(prior_state.get("info_quality", 0.6))
    repression = float(prior_state.get("repression", 20.0))
    risk_premium = float(prior_state.get("risk_premium", 0.02))
    external_stress = float(prior_state.get("external_stress", 0.0))
    regional_inequality = float(prior_state.get("regional_inequality_index", 0.25))
    regional_service_gap = float(prior_state.get("regional_service_gap_index", 0.20))

    nominal_gdp_annual = max(1.0, float(prior_state.get("nominal_gdp_monthly", 1_000_000_000.0)) * 12.0)
    debt_ratio = float(prior_state.get("debt", 0.0)) / nominal_gdp_annual
    real_wage_growth_signal = float(prior_state.get("prod_growth", 0.003)) - inflation_proxy

    # Building owner output signals (normalised 0-1 fractions of building income).
    _bldg_cap = _clamp(float(prior_state.get("building_owner_output_capitalist", 0.0)), 0.0, 1e12)
    _bldg_st = _clamp(float(prior_state.get("building_owner_output_state", 0.0)), 0.0, 1e12)
    _bldg_co = _clamp(float(prior_state.get("building_owner_output_cooperative", 0.0)), 0.0, 1e12)
    _bldg_inf = _clamp(float(prior_state.get("building_owner_output_informal", 0.0)), 0.0, 1e12)
    _bldg_total = _bldg_cap + _bldg_st + _bldg_co + _bldg_inf + 1e-9
    bldg_cap_frac = _bldg_cap / _bldg_total
    bldg_coop_frac = _bldg_co / _bldg_total
    bldg_inf_frac = _bldg_inf / _bldg_total

    worker_share = _clamp(
        float(prior_state.get("worker_income_share", 0.58))
        + spend_ratio * 0.015
        - unemployment * 0.020
        - inflation_proxy * 0.25
        + bldg_coop_frac * 0.02,   # cooperative buildings raise wage share
        0.45,
        0.68,
    )
    professional_share = _clamp(
        float(prior_state.get("professional_income_share", 0.22))
        + info_quality * 0.003
        - external_stress * 0.01,
        0.16,
        0.30,
    )
    informal_share = _clamp(
        float(prior_state.get("informal_income_share", 0.04))
        + unemployment * 0.06
        + external_stress * 0.02
        + bldg_inf_frac * 0.015,   # informal buildings raise informal share
        0.03,
        0.12,
    )
    capitalist_share = _clamp(1.0 - (worker_share + professional_share + informal_share), 0.08, 0.30)
    # Privately owned buildings directly boost capitalist share.
    capitalist_share = _clamp(capitalist_share + bldg_cap_frac * 0.02, 0.08, 0.30)
    total_share = worker_share + professional_share + informal_share + capitalist_share
    worker_share /= total_share
    professional_share /= total_share
    informal_share /= total_share
    capitalist_share /= total_share

    inequality = _clamp(
        float(prior_state.get("wealth_gini", 0.58))
        + capitalist_share * 0.02
        + corruption * 0.03
        + external_stress * 0.02
        - spend_ratio * 0.02
        - tax_ratio * 0.015,
        0.35,
        0.80,
    )
    wealth_top10pct = _clamp(
        float(prior_state.get("wealth_top10pct", 0.55))
        + (capitalist_share - worker_share) * 0.05
        + corruption * 0.02
        - tax_ratio * 0.01,
        0.35,
        0.85,
    )
    poverty_headcount = _clamp(
        float(prior_state.get("poverty_headcount", 0.24))
        + unemployment * 0.03
        + max(0.0, inflation_proxy) * 0.10
        + inequality * 0.015
        + regional_service_gap * 0.015
        - spend_ratio * 0.12,
        0.04,
        0.70,
    )

    support_workers = _clamp(
        float(prior_state.get("class_support_workers", 52.0))
        + real_wage_growth_signal * 120.0
        - unemployment * 20.0
        + spend_ratio * 20.0
        - inequality * 6.0,
        0.0,
        100.0,
    )
    support_professionals = _clamp(
        float(prior_state.get("class_support_professionals", 50.0))
        + info_quality * 8.0
        - corruption * 10.0
        - external_stress * 8.0,
        0.0,
        100.0,
    )
    support_capitalists = _clamp(
        float(prior_state.get("class_support_capitalists", 48.0))
        + float(prior_state.get("policy_rate", 0.08)) * 15.0
        - tax_ratio * 25.0
        - max(0.0, debt_ratio - 0.75) * 30.0
        - risk_premium * 10.0,
        0.0,
        100.0,
    )
    support_informal = _clamp(
        float(prior_state.get("class_support_informal", 46.0))
        + spend_ratio * 16.0
        - poverty_headcount * 20.0
        - max(0.0, inflation_proxy) * 40.0,
        0.0,
        100.0,
    )

    unrest_workers = _clamp(100.0 - support_workers + inequality * 35.0 + unemployment * 20.0, 0.0, 100.0)
    unrest_professionals = _clamp(100.0 - support_professionals + corruption * 20.0 + external_stress * 10.0, 0.0, 100.0)
    unrest_capitalists = _clamp(100.0 - support_capitalists + tax_ratio * 30.0 + risk_premium * 40.0, 0.0, 100.0)
    unrest_informal = _clamp(100.0 - support_informal + poverty_headcount * 40.0 + inflation_proxy * 20.0, 0.0, 100.0)

    class_conflict_pressure = _clamp(
        (
            unrest_workers * 0.40
            + unrest_professionals * 0.20
            + unrest_capitalists * 0.15
            + unrest_informal * 0.25
        )
        / 100.0,
        0.0,
        1.0,
    )
    class_conflict_pressure = _clamp(class_conflict_pressure + regional_inequality * 0.08 + regional_service_gap * 0.06, 0.0, 1.0)

    belief_in_system = _clamp(
        float(prior_state.get("belief_in_system", 0.50))
        + info_quality * 0.05
        - corruption * 0.06
        - class_conflict_pressure * 0.04
        - external_stress * 0.03
        - max(0.0, repression - 40.0) * 0.0008,
        0.0,
        1.0,
    )
    distrust_shock_buildup = _clamp(
        float(prior_state.get("distrust_shock_buildup", 0.20))
        + max(0.0, 0.5 - belief_in_system) * 0.05
        + max(0.0, repression - 35.0) * 0.001
        - info_quality * 0.01,
        0.0,
        1.0,
    )
    capital_flight_rate = _clamp(
        float(prior_state.get("capital_flight_rate", 0.01))
        + max(0.0, 45.0 - support_capitalists) * 0.0008
        + risk_premium * 0.10
        + external_stress * 0.03
        - info_quality * 0.01,
        0.0,
        0.30,
    )

    migration_net = float(prior_state.get("migration_net", 0.0)) - (capital_flight_rate * 1000.0) + (support_workers - 50.0) * 8.0

    return {
        "worker_income_share": worker_share,
        "professional_income_share": professional_share,
        "capitalist_income_share": capitalist_share,
        "informal_income_share": informal_share,
        "wealth_gini": inequality,
        "wealth_top10pct": wealth_top10pct,
        "poverty_headcount": poverty_headcount,
        "inequality": inequality * 100.0,
        "class_support_workers": support_workers,
        "class_support_professionals": support_professionals,
        "class_support_capitalists": support_capitalists,
        "class_support_informal": support_informal,
        "class_unrest_workers": unrest_workers,
        "class_unrest_professionals": unrest_professionals,
        "class_unrest_capitalists": unrest_capitalists,
        "class_unrest_informal": unrest_informal,
        "class_conflict_pressure": class_conflict_pressure,
        "belief_in_system": belief_in_system,
        "distrust_shock_buildup": distrust_shock_buildup,
        "capital_flight_rate": capital_flight_rate,
        "fairness_signal": _clamp(1.0 - inequality * 0.85, 0.05, 0.95),
        "repression_excess": max(0.0, repression - 30.0) / 100.0,
        "migration_net": migration_net,
    }


def update_social_political(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    population = next_population(
        current=float(prior_state.get("population", 1_000_000.0)),
        births=float(prior_state.get("births", 1200.0)),
        deaths=float(prior_state.get("deaths", 800.0)),
        migration_net=float(prior_state.get("migration_net", -100.0)),
    )

    current_account = float(prior_state.get("current_account", 0.0))
    reserves = float(prior_state.get("reserves", 0.0))
    external_stress = float(prior_state.get("external_stress", 0.0))
    reserve_pressure = 1.0 if reserves <= 1.0 else 0.0
    inflation_proxy = float(prior_state.get("inflation_proxy", 0.0))
    service_perf = max(0.0, float(prior_state.get("service_perf", 0.6)) - reserve_pressure * 0.1 - external_stress * 0.05)
    real_income_signal = (
        float(prior_state.get("real_income_signal", 0.5))
        - max(0.0, float(prior_state.get("expected_inflation", 0.01)) - 0.01) * 0.6
        - inflation_proxy * 0.25
        - external_stress * 0.05
    )
    needs_gap = min(
        1.0,
        max(
            0.0,
            float(prior_state.get("needs_gap", 0.2))
            + (0.05 if current_account < 0.0 else 0.0)
            + inflation_proxy * 0.10
            + external_stress * 0.06,
        ),
    )

    legitimacy = next_legitimacy(
        current=float(prior_state.get("legitimacy", 50.0)),
        service_performance=service_perf,
        real_income=real_income_signal,
        corruption=float(prior_state.get("corruption_signal", 0.3)),
        repression_excess=float(prior_state.get("repression_excess", 0.1)),
        fairness=float(prior_state.get("fairness_signal", 0.45)),
        l1=0.2,
        l2=0.2,
        l3=0.1,
        l4=0.1,
        l5=0.2,
    )
    trust = next_trust(
        current=float(prior_state.get("trust", 45.0)),
        legitimacy=min(1.0, max(0.0, legitimacy / 100.0 + (float(prior_state.get("belief_in_system", 0.50)) - 0.5) * 0.2)),
        info_quality=max(
            0.0,
            float(prior_state.get("info_quality", 0.5))
            - external_stress * 0.1
            - float(prior_state.get("distrust_shock_buildup", 0.2)) * 0.03,
        ),
        polarization=min(1.0, float(prior_state.get("polarization", 55.0)) / 100.0 + external_stress * 0.05),
        inequality_shock=min(
            1.0,
            float(prior_state.get("inequality_shock", 0.4))
            + float(prior_state.get("class_conflict_pressure", 0.3)) * 0.15,
        ),
        z1=0.01,
        z2=0.2,
        z3=0.05,
        z4=0.05,
    )

    unrest = unrest_risk(
        theta0=20.0,
        needs_gap=needs_gap,
        inflation=float(prior_state.get("expected_inflation", 0.01)),
        unemployment=float(prior_state.get("unemployment", 0.08)),
        inequality=float(prior_state.get("inequality", 45.0)) / 100.0,
        legitimacy=legitimacy / 100.0,
        capacity=float(prior_state.get("capacity", 50.0)) / 100.0,
        repression=float(prior_state.get("repression", 20.0)),
        theta1=20.0,
        theta2=40.0,
        theta3=30.0,
        theta4=12.0,
        theta5=18.0,
        theta6=10.0,
        theta7=0.1,
    )

    return {
        "population": population,
        "legitimacy": legitimacy,
        "trust": trust,
        "unrest": unrest,
        "needs_gap": needs_gap,
        "real_income_signal": real_income_signal,
        "service_perf": service_perf,
    }


def update_world_diplomacy(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    tick = int(context["tick"])
    world_state = prior_state.get("world_state", {})
    partners = world_state.get("partners", {}) if isinstance(world_state, dict) else {}
    diplomacy_posture = _clamp(float(prior_state.get("diplomacy_posture", 0.5)), 0.0, 1.0)
    external_stress = float(prior_state.get("external_stress", 0.0))
    sanctions_shock = max(0.0, float(prior_state.get("trade_shock_exports", 1.0)) - 1.0)

    updated_partners: dict[str, dict[str, float]] = {}
    relation_sum = 0.0
    access_sum = 0.0
    sanction_sum = 0.0
    n = 0
    for name, payload in partners.items():
        if not isinstance(payload, dict):
            continue
        relation = _clamp(float(payload.get("relation", 0.4)) + (diplomacy_posture - 0.5) * 0.04 - external_stress * 0.02, 0.05, 0.95)
        trade_access = _clamp(float(payload.get("trade_access", 0.6)) + (relation - 0.5) * 0.03 - sanctions_shock * 0.06, 0.10, 0.95)
        sanction_pressure = _clamp(float(payload.get("sanction_pressure", 0.1)) + external_stress * 0.02 - diplomacy_posture * 0.02, 0.0, 1.0)
        updated_partners[name] = {
            "relation": relation,
            "trade_access": trade_access,
            "sanction_pressure": sanction_pressure,
        }
        relation_sum += relation
        access_sum += trade_access
        sanction_sum += sanction_pressure
        n += 1

    avg_access = access_sum / max(1, n)
    avg_sanctions = sanction_sum / max(1, n)
    avg_relation = relation_sum / max(1, n)
    global_trade_cycle = _clamp(float(world_state.get("global_trade_cycle", 0.0)) * 0.85 + (0.5 - abs((tick % 24) - 12) / 12.0) * 0.12, -0.2, 0.2)
    war_risk_external = _clamp(float(world_state.get("war_risk_external", 0.08)) + max(0.0, 0.5 - avg_relation) * 0.04 + avg_sanctions * 0.02, 0.0, 1.0)

    return {
        "world_state": {
            "partners": updated_partners,
            "global_trade_cycle": global_trade_cycle,
            "war_risk_external": war_risk_external,
        },
        "trade_access_index": avg_access,
        "sanctions_index": avg_sanctions,
        "war_risk_index": _clamp(float(prior_state.get("war_risk_index", 0.1)) * 0.8 + war_risk_external * 0.2, 0.0, 1.0),
    }


def update_logistics_and_market(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    infrastructure = 0.5
    region_state = prior_state.get("region_state", {})
    if isinstance(region_state, dict) and isinstance(region_state.get("regions"), dict):
        rows = [v for v in region_state["regions"].values() if isinstance(v, dict)]
        if rows:
            infrastructure = sum(float(r.get("infrastructure", 0.5)) for r in rows) / len(rows)

    trade_access = _clamp(float(prior_state.get("trade_access_index", 0.65)), 0.0, 1.0)
    sanctions = _clamp(float(prior_state.get("sanctions_index", 0.08)), 0.0, 1.0)
    unmet = float(prior_state.get("unmet_demand", 0.0))
    demand = max(1.0, float(prior_state.get("demand", 100.0)))
    fx_delta = float(prior_state.get("fx_delta", 0.0))

    goods_shortage_pressure = _clamp(unmet / demand + sanctions * 0.15 + fx_delta * 0.8, 0.0, 1.0)
    logistics_bottleneck = _clamp((1.0 - infrastructure) * 0.55 + (1.0 - trade_access) * 0.25 + sanctions * 0.20, 0.0, 1.0)
    market_tightness = _clamp(goods_shortage_pressure * 0.7 + logistics_bottleneck * 0.3, 0.0, 1.0)

    return {
        "goods_shortage_pressure": goods_shortage_pressure,
        "logistics_bottleneck_index": logistics_bottleneck,
        "market_tightness": market_tightness,
        "cost_delta": float(prior_state.get("cost_delta", 0.005)) + goods_shortage_pressure * 0.01,
    }


def update_construction_queue(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    queue_raw = prior_state.get("construction_queue", [])
    queue = list(queue_raw) if isinstance(queue_raw, list) else []
    construction_spend = _clamp(float(prior_state.get("construction_spend_share", 0.12)), 0.0, 0.40)
    corruption = _clamp(float(prior_state.get("corruption_signal", 0.3)), 0.0, 1.0)
    capacity_patch = 0.0
    completed: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []

    for item in queue:
        if not isinstance(item, dict):
            continue
        months = int(item.get("remaining_months", 0))
        cost_ratio = float(item.get("cost_ratio", 0.01))
        speed = max(0.2, min(2.0, (construction_spend / max(cost_ratio, 1e-6)) * (1.0 - corruption * 0.4)))
        months_next = months - int(round(speed))
        if months_next <= 0:
            completed.append(item)
            target = str(item.get("target", ""))
            effect = float(item.get("effect", 0.01))
            if target == "infrastructure":
                capacity_patch += effect * 20.0
            elif target == "human_capital":
                capacity_patch += effect * 8.0
        else:
            new_item = dict(item)
            new_item["remaining_months"] = months_next
            remaining.append(new_item)

    # Materialise completed items as physical building instances.
    region_state = prior_state.get("region_state", {})
    regions_map = {}
    if isinstance(region_state, dict):
        regions_map = region_state.get("regions", {})

    for item in completed:
        building_type = item.get("type", "")
        target_region = str(item.get("target_region", ""))
        target_subregion = str(item.get("target_subregion", ""))
        if not building_type or not target_region or not target_subregion:
            continue
        try:
            get_archetype(building_type)  # validate type exists
        except KeyError:
            continue
        region_data = regions_map.get(target_region, {})
        subregions = region_data.get("subregions", {})
        subregion_data = subregions.get(target_subregion)
        if not isinstance(subregion_data, dict):
            continue
        human_capital = float(subregion_data.get("human_capital", region_data.get("human_capital", 0.5)))
        infrastructure = float(subregion_data.get("infrastructure", region_data.get("infrastructure_index", 0.5)))
        new_building = make_building_from_queue_item(item, target_subregion, human_capital, infrastructure)
        if "buildings" not in subregion_data or not isinstance(subregion_data["buildings"], list):
            subregion_data["buildings"] = []
        subregion_data["buildings"].append(new_building)

    # Keep queue alive with procedural projects.
    if len(remaining) < 2:
        remaining.append(
            {
                "name": "state_warehouse_program",
                "target": "infrastructure",
                "type": "construction_yard",
                "target_region": "",
                "target_subregion": "",
                "remaining_months": 16,
                "cost_ratio": 0.009,
                "effect": 0.010,
                "level": 1,
                "owner_class": "state",
            }
        )

    return {
        "construction_queue": remaining,
        "region_state": region_state,
        "capacity_output": max(1.0, float(prior_state.get("capacity_output", 100.0)) + capacity_patch),
        "construction_completion_count": int(prior_state.get("construction_completion_count", 0)) + len(completed),
    }


def update_laws_and_interest_groups(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    law_state = prior_state.get("law_state", {})
    groups = prior_state.get("interest_group_power", {})
    if not isinstance(law_state, dict):
        law_state = {}
    if not isinstance(groups, dict):
        groups = {}

    legitimacy = float(prior_state.get("legitimacy", 50.0)) / 100.0
    unrest = float(prior_state.get("unrest", 35.0)) / 100.0
    corruption = _clamp(float(prior_state.get("corruption_signal", 0.3)), 0.0, 1.0)
    repression = _clamp(float(prior_state.get("repression", 20.0)) / 100.0, 0.0, 1.0)

    cap = _clamp(float(groups.get("capital", 0.36)) + corruption * 0.01 - unrest * 0.01, 0.05, 0.75)
    labor = _clamp(float(groups.get("labor", 0.34)) + unrest * 0.02 + legitimacy * 0.01 - repression * 0.02, 0.05, 0.75)
    rural = _clamp(float(groups.get("rural", 0.18)) + float(prior_state.get("poverty_headcount", 0.2)) * 0.03, 0.05, 0.60)
    security = _clamp(float(groups.get("security", 0.12)) + repression * 0.04 + unrest * 0.03, 0.05, 0.60)
    total = cap + labor + rural + security
    cap, labor, rural, security = cap / total, labor / total, rural / total, security / total

    enactment_pressure = _clamp(float(law_state.get("enactment_pressure", 0.40)) + unrest * 0.04 - legitimacy * 0.02, 0.0, 1.0)
    labor_law = _clamp(float(law_state.get("labor_law", 0.45)) + labor * 0.01 - cap * 0.006, 0.0, 1.0)
    property_rights = _clamp(float(law_state.get("property_rights", 0.52)) + cap * 0.008 - unrest * 0.004, 0.0, 1.0)
    media_freedom = _clamp(float(law_state.get("media_freedom", 0.48)) + (1.0 - repression) * 0.007 - security * 0.006, 0.0, 1.0)
    welfare_rights = _clamp(float(law_state.get("welfare_rights", 0.42)) + labor * 0.008 + rural * 0.004 - cap * 0.005, 0.0, 1.0)

    conflict = _clamp(abs(cap - labor) + abs(security - labor) * 0.5 + enactment_pressure * 0.3, 0.0, 1.0)
    law_stability = _clamp(1.0 - conflict * 0.7 - corruption * 0.2, 0.0, 1.0)

    return {
        "interest_group_power": {
            "capital": cap,
            "labor": labor,
            "rural": rural,
            "security": security,
        },
        "law_state": {
            "labor_law": labor_law,
            "property_rights": property_rights,
            "media_freedom": media_freedom,
            "welfare_rights": welfare_rights,
            "enactment_pressure": enactment_pressure,
        },
        "interest_group_conflict": conflict,
        "law_stability_index": law_stability,
        "reform_momentum": _clamp(enactment_pressure * 0.6 + (1.0 - conflict) * 0.4, 0.0, 1.0),
    }


def update_technology(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    research_spend = _clamp(float(prior_state.get("research_spend_share", 0.04)), 0.0, 0.20)
    law_stability = _clamp(float(prior_state.get("law_stability_index", 0.5)), 0.0, 1.0)
    info_quality = _clamp(float(prior_state.get("info_quality", 0.6)), 0.0, 1.0)
    brain_drain = _clamp(float(prior_state.get("capital_flight_rate", 0.01)) * 1.8, 0.0, 0.5)

    research_state = prior_state.get("research_state", {})
    if not isinstance(research_state, dict):
        research_state = {}

    progress = _clamp(float(research_state.get("progress", 0.0)) + research_spend * 0.8 + law_stability * 0.05 + info_quality * 0.04 - brain_drain * 0.08, 0.0, 2.0)
    tier = int(research_state.get("tier", 1))
    if progress >= 1.0:
        tier = min(8, tier + 1)
        progress -= 1.0

    adoption = _clamp(float(prior_state.get("innovation_adoption", 0.35)) + info_quality * 0.01 + law_stability * 0.008 - float(prior_state.get("logistics_bottleneck_index", 0.2)) * 0.006, 0.0, 1.0)
    prod_growth_boost = (tier - 1) * 0.0006 + adoption * 0.0008

    return {
        "research_state": {
            "progress": progress,
            "tier": tier,
            "focus": str(research_state.get("focus", "industrial")),
        },
        "research_progress": progress,
        "technology_tier": tier,
        "innovation_adoption": adoption,
        "prod_growth": float(prior_state.get("prod_growth", 0.003)) + prod_growth_boost,
    }


def update_military_security(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del context
    military = prior_state.get("military_state", {})
    if not isinstance(military, dict):
        military = {}

    military_spend = _clamp(float(prior_state.get("military_spend_share", 0.16)), 0.0, 0.50)
    security_posture = _clamp(float(prior_state.get("security_posture", 0.45)), 0.0, 1.0)
    logistics_integrity = _clamp(float(military.get("logistics_integrity", 0.50)) + (1.0 - float(prior_state.get("logistics_bottleneck_index", 0.2))) * 0.01, 0.0, 1.0)
    equipment = _clamp(float(military.get("equipment_stock", 0.46)) + military_spend * 0.02 - float(prior_state.get("goods_shortage_pressure", 0.2)) * 0.01, 0.0, 1.0)
    readiness = _clamp(float(military.get("readiness", 0.52)) + military_spend * 0.015 + logistics_integrity * 0.01 - float(prior_state.get("war_risk_index", 0.1)) * 0.008, 0.0, 1.0)
    internal_load = _clamp(
        float(military.get("internal_security_load", 0.18))
        + float(prior_state.get("unrest", 35.0)) / 100.0 * 0.02
        - security_posture * 0.012,
        0.0,
        1.0,
    )

    return {
        "military_state": {
            "readiness": readiness,
            "equipment_stock": equipment,
            "logistics_integrity": logistics_integrity,
            "internal_security_load": internal_load,
        },
        "military_readiness": readiness,
        "internal_security_risk": _clamp(internal_load * 0.6 + (1.0 - readiness) * 0.2 + float(prior_state.get("unrest", 35.0)) / 100.0 * 0.2, 0.0, 1.0),
    }


def update_events_and_crises(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    tick = int(context["tick"])
    event_state = prior_state.get("event_state", {})
    if not isinstance(event_state, dict):
        event_state = {}

    stress = _clamp(
        float(prior_state.get("external_stress", 0.0)) * 0.35
        + float(prior_state.get("goods_shortage_pressure", 0.2)) * 0.25
        + float(prior_state.get("internal_security_risk", 0.2)) * 0.20
        + float(prior_state.get("regional_inequality_index", 0.25)) * 0.20,
        0.0,
        1.0,
    )

    crisis_intensity = _clamp(float(event_state.get("crisis_intensity", 0.0)) * 0.85 + stress * 0.25, 0.0, 1.0)
    active = "none"
    if crisis_intensity > 0.70:
        active = "systemic_crisis"
    elif float(prior_state.get("goods_shortage_pressure", 0.2)) > 0.55:
        active = "supply_crisis"
    elif float(prior_state.get("internal_security_risk", 0.2)) > 0.55:
        active = "security_crisis"
    elif float(prior_state.get("regional_inequality_index", 0.25)) > 0.50:
        active = "regional_crisis"

    state_failure = _clamp(
        float(prior_state.get("state_failure_risk", 0.12)) * 0.9
        + crisis_intensity * 0.12
        + max(0.0, float(prior_state.get("unrest", 35.0)) - 65.0) * 0.003
        + max(0.0, float(prior_state.get("debt", 0.0)) / max(float(prior_state.get("nominal_gdp_monthly", 1.0)) * 12.0, 1.0) - 1.2) * 0.05,
        0.0,
        1.0,
    )

    return {
        "event_state": {
            "active_crisis": active,
            "crisis_intensity": crisis_intensity,
            "event_counter": int(event_state.get("event_counter", 0)) + (1 if active != "none" else 0),
            "last_tick": tick,
        },
        "active_crisis": active,
        "crisis_intensity": crisis_intensity,
        "state_failure_risk": state_failure,
    }


def update_victory_failure(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    tick = int(context["tick"])
    obj = prior_state.get("objectives", {})
    if not isinstance(obj, dict):
        obj = {}
    min_legitimacy = float(obj.get("min_legitimacy", 45.0))
    max_debt_gdp = float(obj.get("max_debt_gdp", 1.0))
    max_unrest = float(obj.get("max_unrest", 65.0))
    survival_ticks = max(1, int(obj.get("survival_ticks", 360)))

    debt_gdp = float(prior_state.get("debt", 0.0)) / max(float(prior_state.get("nominal_gdp_monthly", 1.0)) * 12.0, 1.0)
    legitimacy = float(prior_state.get("legitimacy", 50.0))
    unrest = float(prior_state.get("unrest", 35.0))

    score_legit = _clamp(legitimacy / max(min_legitimacy, 1.0), 0.0, 1.2)
    score_debt = _clamp(max_debt_gdp / max(debt_gdp, 0.1), 0.0, 1.2)
    score_unrest = _clamp(max_unrest / max(unrest, 1.0), 0.0, 1.2)
    score_time = _clamp(tick / survival_ticks, 0.0, 1.0)
    victory_progress = _clamp((score_legit * 0.25 + score_debt * 0.25 + score_unrest * 0.20 + score_time * 0.30), 0.0, 1.0)

    game_over = bool(prior_state.get("game_over", False))
    game_over_reason = str(prior_state.get("game_over_reason", ""))
    if not game_over:
        if float(prior_state.get("state_failure_risk", 0.1)) > 0.92:
            game_over = True
            game_over_reason = "state_failure"
        elif legitimacy < 20.0 and unrest > 80.0:
            game_over = True
            game_over_reason = "regime_collapse"
        elif debt_gdp > 1.8 and float(prior_state.get("reserves", 0.0)) <= 0.0:
            game_over = True
            game_over_reason = "debt_external_collapse"
        elif tick >= survival_ticks and victory_progress >= 0.75:
            game_over = True
            game_over_reason = "victory"

    return {
        "victory_progress": victory_progress,
        "game_over": game_over,
        "game_over_reason": game_over_reason,
    }


def run_consistency_checks(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    del prior_state
    return {"consistency_ok": True, "consistency_tick": context["tick"]}


def apply_building_policies(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Apply nationalisation and construction subsidy policies to physical buildings."""
    del context
    nationalize_rate = _clamp(float(prior_state.get("nationalize_industry", 0.0)), 0.0, 1.0)
    construction_subsidy = _clamp(float(prior_state.get("construction_subsidy", 0.0)), 0.0, 1.0)

    region_state = prior_state.get("region_state", {})
    if not isinstance(region_state, dict):
        return {}
    regions_map = region_state.get("regions", {})

    for region_data in regions_map.values():
        subregions = region_data.get("subregions", {}) if isinstance(region_data, dict) else {}
        for subregion_data in subregions.values():
            if not isinstance(subregion_data, dict):
                continue
            buildings = subregion_data.get("buildings", [])
            if not isinstance(buildings, list):
                continue
            for bldg in buildings:
                if not isinstance(bldg, dict):
                    continue
                # Nationalisation: transfer private/capitalist buildings to state ownership.
                if nationalize_rate > 0.0 and bldg.get("owner_class") == "capitalist":
                    if _clamp(float(bldg.get("_nationalize_roll", 0.0)), 0.0, 1.0) < nationalize_rate:
                        bldg["owner_class"] = "state"
                # Construction subsidy: subsidy boosts maintenance_spend_ratio for all buildings.
                if construction_subsidy > 0.0:
                    current_maint = float(bldg.get("maintenance_spend_ratio", 0.5))
                    bldg["maintenance_spend_ratio"] = min(1.0, current_maint + construction_subsidy * 0.2)

    return {"region_state": region_state}


# ---------------------------------------------------------------------------
# Policy system stages
# ---------------------------------------------------------------------------

def update_policy_state(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Advance bandwidth, vitality, shadow gap, graveyard, and credibility for one tick."""
    tick = context["tick"]

    # --- state keys --------------------------------------------------------
    active_policies: list[dict[str, Any]] = list(prior_state.get("active_policies", list(DEFAULT_ACTIVE_POLICIES)))
    ministry_budgets: dict[str, float]    = dict(prior_state.get("ministry_budget_allocations", {}))
    bandwidth: int                        = int(prior_state.get("policy_bandwidth", 60))
    graveyard: list[dict[str, Any]]       = list(prior_state.get("policy_graveyard", []))
    credibility: float                    = float(prior_state.get("policy_credibility", 1.0))

    # --- context metrics ---------------------------------------------------
    legitimacy: float    = float(prior_state.get("legitimacy", 50.0)) / 100.0
    iq: float            = float(prior_state.get("info_quality", 0.6))
    corruption: float    = float(prior_state.get("corruption_signal", 0.3))
    coalition_cohesion   = float(prior_state.get("belief_in_system", 0.5))
    spend_ratio: float   = float(prior_state.get("spend_ratio", 0.20))
    monthly_gdp: float   = float(prior_state.get("nominal_gdp_monthly", 1_000_000.0))
    bureaucratic_reach   = max(0.1, iq - corruption * 0.3)
    elite_capture        = min(0.9, corruption * 0.6)

    # --- ministry budgets --------------------------------------------------
    if not ministry_budgets:
        ministry_budgets = initial_ministry_budgets(spend_ratio, monthly_gdp)
    else:
        total_budget = spend_ratio * monthly_gdp
        ministry_budgets = update_ministry_budgets(ministry_budgets, total_budget)

    # --- bandwidth recharge ------------------------------------------------
    recharge = bandwidth_recharge(legitimacy * 100.0, coalition_cohesion)
    bandwidth = min(100, bandwidth + recharge)

    # --- active policy update ----------------------------------------------
    updated_active, collapsed = update_active_policies(
        active_policies=active_policies,
        ministry_budgets=ministry_budgets,
        institutional_quality=iq,
        legitimacy_norm=legitimacy,
        bureaucratic_reach=bureaucratic_reach,
        elite_capture=elite_capture,
    )

    # --- graveyard processing ----------------------------------------------
    for pol in collapsed:
        graveyard = add_to_graveyard(graveyard, pol, pol.get("collapse_reason", "collapsed"), tick)

    graveyard, total_grievance = decay_graveyard(graveyard)

    # --- credibility -------------------------------------------------------
    credibility = update_credibility(credibility, len(collapsed), 0)

    # --- aggregate shadow gap (average across active policies) -------------
    if updated_active:
        avg_shadow_gap = sum(
            abs(p.get("formal_value", 0.5) - p.get("realized_value", 0.0))
            for p in updated_active
        ) / len(updated_active)
    else:
        avg_shadow_gap = 0.0

    return {
        "active_policies":           updated_active,
        "ministry_budget_allocations": ministry_budgets,
        "policy_bandwidth":          bandwidth,
        "policy_graveyard":          graveyard,
        "policy_credibility":        credibility,
        "policy_grievance":          total_grievance,
        "policy_shadow_gap":         avg_shadow_gap,
    }


def update_ideology_traditions(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Update tradition influence scores and derive active tradition."""
    del context

    influence: dict[str, float] = dict(prior_state.get("tradition_influence", {}))
    active_tradition: str       = str(prior_state.get("active_tradition", ""))

    iq: float         = float(prior_state.get("info_quality", 0.6))
    corruption: float = float(prior_state.get("corruption_signal", 0.3))
    inequality: float = float(prior_state.get("inequality", 45.0))
    legitimacy: float = float(prior_state.get("legitimacy", 50.0))
    gdp_growth: float = float(prior_state.get("gdp_growth_rate", 0.0))
    crisis_active     = str(prior_state.get("active_crisis", "none")) != "none"

    # Seed if empty
    if not influence:
        influence = initial_tradition_influence(iq, corruption)

    # Summarise state for tradition dynamics
    prior_summary = {
        "inequality": inequality,
        "legitimacy": legitimacy,
        "gdp_growth": gdp_growth,
        "crisis_active": crisis_active,
    }
    influence = update_tradition_influence(influence, prior_summary, active_tradition)
    active_tradition = dominant_tradition(influence)

    # Apply dominant tradition modifiers to key indicators
    tradition_data  = TRADITIONS.get(active_tradition, {})
    growth_bonus    = float(tradition_data.get("growth_bonus", 0.0))
    inequality_eff  = float(tradition_data.get("inequality_effect", 0.0))

    delta_gdp       = gdp_growth + growth_bonus
    delta_inequality = inequality + inequality_eff

    return {
        "tradition_influence":  influence,
        "active_tradition":     active_tradition,
        "gdp_growth_rate":      delta_gdp,
        "inequality":           max(0.0, min(100.0, delta_inequality)),
    }


def update_consequence_queue(prior_state: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Queue consequences from newly enacted signature policies; mature pending ones."""
    tick: int = context["tick"]

    pending: list[dict[str, Any]] = list(prior_state.get("consequence_queue", []))
    active_policies: list[dict[str, Any]] = list(prior_state.get("active_policies", []))
    iq: float = float(prior_state.get("info_quality", 0.6))

    # Track which policies have already been queued via their name+enact_tick
    known_keyed = {e.get("policy_name") + "#" + str(e.get("enqueued_tick", -1)) for e in pending}

    for pol in active_policies:
        pname = str(pol.get("name", ""))
        sig_def = SIGNATURE_POLICY_DEFS.get(pname)
        if sig_def is None:
            continue
        enact_tick = int(pol.get("age_ticks", 0))
        # Only queue the first tick the policy exists (age_ticks == 1 means just enacted)
        if enact_tick != 1:
            continue
        key = pname + "#" + str(tick)
        if key in known_keyed:
            continue
        unintended = sig_def.get("unintended", {})
        delay      = int(sig_def.get("unintended_delay_ticks", 12))
        pending = queue_consequences(pending, pname, unintended, delay, tick, iq)

    # Mature consequences due this tick
    pending, deltas, revealed = apply_matured_consequences(pending, tick)

    # Apply deltas -- result is a patch dict we can merge
    patch = apply_consequence_deltas(prior_state, deltas)

    patch["consequence_queue"]      = pending
    patch["consequence_revealed"]   = revealed

    return patch
