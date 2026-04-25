from __future__ import annotations

from src.core.stages import update_class_dynamics, update_logistics_and_market, update_social_political
from src.econ.social_demand import compute_social_demand_signals


def _state_with_commodity_level(level: float) -> dict:
    # level in 0..1 controls how stocked the subregion is.
    return {
        "unemployment": 0.10,
        "capacity": 50.0,
        "service_perf": 0.60,
        "building_transport_modifier": 0.90,
        "logistics_bottleneck_index": 0.25,
        "region_state": {
            "regions": {
                "r1": {
                    "population": 1_000_000.0,
                    "subregions": {
                        "r1_north": {
                            "population_share": 1.0,
                            "commodity_stocks": {
                                "staple_food": 0.5 * level,
                                "imported_food": 0.2 * level,
                                "fuel": 0.3 * level,
                                "power": 0.4 * level,
                                "diesel_power": 0.1 * level,
                                "medicine": 0.3 * level,
                                "consumer_goods": 0.3 * level,
                                "informal_goods": 0.2 * level,
                                "machine_parts": 0.2 * level,
                                "steel": 0.2 * level,
                                "cement": 0.2 * level,
                                "stone_aggregate": 0.1 * level,
                            },
                        }
                    },
                }
            }
        },
        "current_account": -10.0,
        "reserves": 40.0,
        "external_stress": 0.20,
        "expected_inflation": 0.03,
        "inflation_proxy": 0.02,
        "corruption_signal": 0.30,
        "repression_excess": 0.10,
        "fairness_signal": 0.45,
        "belief_in_system": 0.50,
        "info_quality": 0.60,
        "polarization": 55.0,
        "inequality_shock": 0.40,
        "inequality": 45.0,
        "repression": 20.0,
        "class_conflict_pressure": 0.30,
        "legitimacy": 50.0,
        "trust": 45.0,
        "population": 1_000_000.0,
        "births": 1200.0,
        "deaths": 800.0,
        "migration_net": -100.0,
        "spend_ratio": 0.205,
        "tax_ratio": 0.20,
        "risk_premium": 0.02,
        "policy_rate": 0.08,
        "regional_inequality_index": 0.25,
        "regional_service_gap_index": 0.20,
        "wealth_gini": 0.58,
        "wealth_top10pct": 0.55,
        "poverty_headcount": 0.24,
    }


def test_compute_social_demand_signals_returns_phase4_keys() -> None:
    state = _state_with_commodity_level(1.0)
    out = compute_social_demand_signals(state)
    required = [
        "demand_bloc_household_pressure",
        "demand_bloc_institutional_pressure",
        "demand_bloc_productive_pressure",
        "rationing_intensity",
        "informal_market_response",
        "needs_gap_from_blocs",
        "scarcity_burden_workers",
        "scarcity_burden_professionals",
        "scarcity_burden_capitalists",
        "scarcity_burden_informal",
    ]
    for key in required:
        assert key in out


def test_scarcity_burdens_rise_when_commodity_stocks_fall() -> None:
    high = compute_social_demand_signals(_state_with_commodity_level(1.0))
    low = compute_social_demand_signals(_state_with_commodity_level(0.0))
    assert low["scarcity_burden_workers"] >= high["scarcity_burden_workers"]
    assert low["needs_gap_from_blocs"] >= high["needs_gap_from_blocs"]


def test_update_logistics_and_market_emits_phase4_signals() -> None:
    state = _state_with_commodity_level(0.5)
    out = update_logistics_and_market(state, {})
    assert "demand_bloc_household_pressure" in out
    assert "scarcity_burden_workers" in out


def test_update_social_political_responds_to_high_scarcity() -> None:
    low_supply = _state_with_commodity_level(0.0)
    high_supply = _state_with_commodity_level(1.0)

    low_supply = {**low_supply, **update_logistics_and_market(low_supply, {})}
    high_supply = {**high_supply, **update_logistics_and_market(high_supply, {})}

    low_out = update_social_political(low_supply, {})
    high_out = update_social_political(high_supply, {})

    assert low_out["needs_gap"] >= high_out["needs_gap"]
    assert low_out["trust"] <= high_out["trust"]


def test_update_class_dynamics_responds_to_scarcity_burden() -> None:
    low_supply = _state_with_commodity_level(0.0)
    high_supply = _state_with_commodity_level(1.0)

    low_supply = {**low_supply, **update_logistics_and_market(low_supply, {})}
    high_supply = {**high_supply, **update_logistics_and_market(high_supply, {})}

    low_out = update_class_dynamics(low_supply, {})
    high_out = update_class_dynamics(high_supply, {})

    assert low_out["class_support_workers"] <= high_out["class_support_workers"]
    assert low_out["class_unrest_informal"] >= high_out["class_unrest_informal"]
