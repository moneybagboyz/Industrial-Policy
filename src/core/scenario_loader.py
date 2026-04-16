"""Scenario loading utilities for engine initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from src.econ.regional_profiles import build_initial_region_state
from src.core.policy_system import DEFAULT_ACTIVE_POLICIES, initial_ministry_budgets
from src.core.ideology_traditions import initial_tradition_influence


def load_scenario_file(path: str | Path) -> dict[str, Any]:
    scenario_path = Path(path)
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    with scenario_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError("Scenario file must contain a top-level mapping")

    return data


def initial_state_from_scenario(data: dict[str, Any]) -> dict[str, Any]:
    macro = data.get("macro", {})
    trade = data.get("trade", {})
    social = data.get("social", {})
    country = data.get("country", {})

    population = float(social.get("population", country.get("population", 1_000_000.0)))
    nominal_gdp = float(macro.get("nominal_gdp", 12_000_000_000.0))
    monthly_gdp = nominal_gdp / 12.0
    imports = float(trade.get("imports", 1_000_000.0))
    reserve_months = float(macro.get("reserves", 6.0))
    reserve_nominal = imports * reserve_months
    capacity_output = float(macro.get("capacity_output", 100.0))
    base_price = 100.0
    scenario_id = str(data.get("scenario_id", "baseline"))
    region_count = int(country.get("regions", 6))
    region_state = build_initial_region_state(region_count=region_count, population=population, scenario_id=scenario_id)

    sector_output_primary = capacity_output * 0.28
    sector_output_secondary = capacity_output * 0.40
    sector_output_tertiary = capacity_output * 0.32

    return {
        "scenario_id": scenario_id,
        "region_count": region_count,
        "region_state": region_state,
        "world_state": {
            "partners": {
                "north_union": {
                    "relation": 0.55,
                    "trade_access": 0.75,
                    "sanction_pressure": 0.05,
                },
                "east_compact": {
                    "relation": 0.42,
                    "trade_access": 0.62,
                    "sanction_pressure": 0.08,
                },
                "south_bloc": {
                    "relation": 0.35,
                    "trade_access": 0.58,
                    "sanction_pressure": 0.12,
                },
            },
            "global_trade_cycle": 0.0,
            "war_risk_external": 0.08,
        },
        "construction_queue": [
            {
                "name": "logistics_corridor",
                "target": "infrastructure",
                "remaining_months": 18,
                "cost_ratio": 0.012,
                "effect": 0.015,
            },
            {
                "name": "technical_colleges",
                "target": "human_capital",
                "remaining_months": 24,
                "cost_ratio": 0.010,
                "effect": 0.012,
            },
        ],
        "law_state": {
            "labor_law": 0.45,
            "property_rights": 0.52,
            "media_freedom": 0.48,
            "welfare_rights": 0.42,
            "enactment_pressure": 0.40,
        },
        "interest_group_power": {
            "capital": 0.36,
            "labor": 0.34,
            "rural": 0.18,
            "security": 0.12,
        },
        "research_state": {
            "progress": 0.0,
            "tier": 1,
            "focus": "industrial",
        },
        "military_state": {
            "readiness": 0.52,
            "equipment_stock": 0.46,
            "logistics_integrity": 0.50,
            "internal_security_load": 0.18,
        },
        "event_state": {
            "active_crisis": "none",
            "crisis_intensity": 0.0,
            "event_counter": 0,
        },
        "objectives": {
            "min_legitimacy": 45.0,
            "max_debt_gdp": 1.00,
            "max_unrest": 65.0,
            "survival_ticks": 360,
        },
        "policy_active": "baseline",
        "nominal_gdp_monthly": monthly_gdp,
        "expected_inflation": float(macro.get("inflation_expectation", 0.01)),
        "price": 100.0,
        "wage": 1000.0,
        "unemployment": float(social.get("unemployment", 0.08)),
        "debt": float(macro.get("debt_stock", 100_000_000.0)),
        "debt_rate": float(macro.get("debt_rate", 0.04)),
        "reserves": reserve_nominal,
        "exports": float(trade.get("exports", 1_000_000.0)),
        "imports": imports,
        "structural_exports": float(trade.get("exports", 1_000_000.0)),
        "structural_imports": imports,
        "trade_shock_exports": 1.0,
        "trade_shock_imports": 1.0,
        "net_factor_income": float(trade.get("net_factor_income", 0.0)),
        "transfers": float(trade.get("transfers", 0.0)),
        "capital_account": float(trade.get("capital_account", max(0.0, imports * 0.06))),
        "revenue": float(macro.get("revenue", monthly_gdp * 0.20)),
        "non_interest_spending": float(macro.get("non_interest_spending", monthly_gdp * 0.205)),
        "tax_ratio": float(macro.get("tax_ratio", 0.20)),
        "spend_ratio": float(macro.get("spend_ratio", 0.205)),
        "automatic_stabilizer_strength": float(macro.get("automatic_stabilizer_strength", 0.018)),
        "foreign_debt_share": float(macro.get("foreign_debt_share", 0.25)),
        "risk_premium": float(macro.get("risk_premium", 0.02)),
        "policy_rate": float(macro.get("policy_rate", 0.08)),
        "infrastructure_spend_share": float(macro.get("infrastructure_spend_share", 0.25)),
        "industrial_policy_bias": float(macro.get("industrial_policy_bias", 0.50)),
        "food_price_stabilization": float(macro.get("food_price_stabilization", 0.40)),
        "regional_equity_bias": float(macro.get("regional_equity_bias", 0.50)),
        "diplomacy_posture": float(macro.get("diplomacy_posture", 0.50)),
        "military_spend_share": float(macro.get("military_spend_share", 0.16)),
        "security_posture": float(macro.get("security_posture", 0.45)),
        "research_spend_share": float(macro.get("research_spend_share", 0.04)),
        "construction_spend_share": float(macro.get("construction_spend_share", 0.12)),
        "corruption_signal": float(social.get("corruption", 0.3)),
        "repression": float(social.get("repression", 20.0)),
        "capacity_output": capacity_output,
        "available_input": float(macro.get("available_input", 100.0)),
        "input_per_unit": float(macro.get("input_per_unit", 1.0)),
        "demand": float(macro.get("demand", 95.0)),
        "inventory": float(macro.get("inventory", 10.0)),
        "sector_price_index": base_price,
        "sector_output_primary": sector_output_primary,
        "sector_output_secondary": sector_output_secondary,
        "sector_output_tertiary": sector_output_tertiary,
        "sector_shortage_primary": 0.0,
        "sector_shortage_secondary": 0.0,
        "sector_shortage_tertiary": 0.0,
        "sector_price_primary": base_price,
        "sector_price_secondary": base_price,
        "sector_price_tertiary": base_price,
        "agriculture_output": capacity_output * 0.16,
        "energy_output": capacity_output * 0.12,
        "manufacturing_output": capacity_output * 0.28,
        "construction_output": capacity_output * 0.12,
        "services_output": capacity_output * 0.32,
        "agriculture_price": base_price,
        "energy_price": base_price,
        "manufacturing_price": base_price,
        "construction_price": base_price,
        "services_price": base_price,
        "regional_output_gini": 0.25,
        "regional_service_gap_index": 0.20,
        "regional_employment_gap_index": 0.06,
        "regional_representation_gap": 0.10,
        "regional_inequality_index": 0.25,
        "regional_average_unrest": 35.0,
        "transport_cost_index": 0.45,
        "map_connectivity_index": 0.80,
        "mean_route_cost": 0.30,
        "trade_access_index": 0.65,
        "sanctions_index": 0.08,
        "logistics_bottleneck_index": 0.24,
        "market_tightness": 0.20,
        "goods_shortage_pressure": 0.18,
        "law_stability_index": 0.50,
        "reform_momentum": 0.42,
        "interest_group_conflict": 0.30,
        "research_progress": 0.0,
        "technology_tier": 1,
        "innovation_adoption": 0.35,
        "military_readiness": 0.52,
        "internal_security_risk": 0.20,
        "war_risk_index": 0.10,
        "active_crisis": "none",
        "crisis_intensity": 0.0,
        "state_failure_risk": 0.12,
        "victory_progress": 0.0,
        "game_over": False,
        "game_over_reason": "",
        "population": population,
        "inequality": float(social.get("inequality", 45.0)),
        "trust": float(social.get("trust", 45.0)),
        "legitimacy": float(social.get("legitimacy", 50.0)),
        "capacity": 50.0,
        "info_quality": float(social.get("info_quality", 0.6)),
        "polarization": float(social.get("polarization", 45.0)),
        "inequality_shock": float(social.get("inequality_shock", 0.2)),
        "needs_gap": float(social.get("needs_gap", 0.15)),
        "wealth_gini": float(social.get("wealth_gini", 0.58)),
        "wealth_top10pct": float(social.get("wealth_top10pct", 0.55)),
        "poverty_headcount": float(social.get("poverty_headcount", 0.24)),
        "belief_in_system": float(social.get("belief_in_system", 0.50)),
        "media_capture": float(social.get("media_capture", 0.35)),
        "distrust_shock_buildup": float(social.get("distrust_shock_buildup", 0.20)),
        "worker_income_share": float(social.get("worker_income_share", 0.58)),
        "professional_income_share": float(social.get("professional_income_share", 0.22)),
        "capitalist_income_share": float(social.get("capitalist_income_share", 0.16)),
        "informal_income_share": float(social.get("informal_income_share", 0.04)),
        "class_support_workers": float(social.get("class_support_workers", 52.0)),
        "class_support_professionals": float(social.get("class_support_professionals", 50.0)),
        "class_support_capitalists": float(social.get("class_support_capitalists", 48.0)),
        "class_support_informal": float(social.get("class_support_informal", 46.0)),
        "class_unrest_workers": float(social.get("class_unrest_workers", 34.0)),
        "class_unrest_professionals": float(social.get("class_unrest_professionals", 28.0)),
        "class_unrest_capitalists": float(social.get("class_unrest_capitalists", 20.0)),
        "class_unrest_informal": float(social.get("class_unrest_informal", 38.0)),
        "capital_flight_rate": float(social.get("capital_flight_rate", 0.01)),
        "class_conflict_pressure": float(social.get("class_conflict_pressure", 0.30)),
        "births": population * float(social.get("population_growth_monthly", 0.0004)),
        "deaths": population * 0.0003,
        "migration_net": 0.0,
        # --- policy system -------------------------------------------------
        "active_policies":             [dict(p) for p in DEFAULT_ACTIVE_POLICIES],
        "ministry_budget_allocations": initial_ministry_budgets(
            float(macro.get("spend_ratio", 0.205)), monthly_gdp
        ),
        "policy_bandwidth":            60,
        "policy_graveyard":            [],
        "policy_credibility":          1.0,
        "policy_grievance":            0.0,
        "policy_shadow_gap":           0.0,
        "tradition_influence":         initial_tradition_influence(
            float(social.get("info_quality", 0.6)),
            float(social.get("corruption", 0.3)),
        ),
        "active_tradition":            "",
        "consequence_queue":           [],
        "consequence_revealed":        [],
        "gdp_growth_rate":             0.0,
    }
