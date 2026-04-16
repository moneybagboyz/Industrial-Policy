"""Ideological traditions: coherent policy clusters that compete for influence.

Each tradition represents a school of political-economic thought.  The dominant
tradition shapes which policies are cheap to enact (lower bandwidth cost),
which coalitions support them, and what unintended consequences are most likely.

Tradition influence rises and falls based on:
- Election outcomes and class coalition power
- Crisis events (food crisis → Agrarian Populism; debt crisis → Liberal Institutionalism)
- Policy history (a tradition with long track record gains legitimacy)
- External pressure (IMF-style conditionality boosts Liberal Institutionalism)
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Tradition catalogue
# ---------------------------------------------------------------------------

TRADITIONS: dict[str, dict[str, Any]] = {
    "developmental_nationalism": {
        "label": "Developmental Nationalism",
        "core_idea": "State builds industry through directed investment and protection.",
        "signature_policies": ["five_year_plan", "strategic_soe", "export_discipline", "import_substitution"],
        "bandwidth_discount": 0.25,          # policies in family get 25% lower bandwidth cost
        "policy_families":    ["industrial", "trade", "governance"],
        "class_base":         ["state", "worker"],   # which owner classes support this
        "crisis_boost":       {"external_stress": 0.04, "goods_shortage_pressure": 0.03},
        "crisis_drag":        {"debt_ratio": 0.05},
        "inequality_effect":  -0.01,          # tends to reduce Gini
        "growth_bonus":       0.004,          # GDP growth modifier
        "repression_tendency": 0.02,          # raises repression slightly
    },
    "liberal_institutionalism": {
        "label": "Liberal Institutionalism",
        "core_idea": "Rules not rulers: independent institutions, property rights, open markets.",
        "signature_policies": ["central_bank_independence", "property_rights_reform", "anti_trust", "trade_liberalization"],
        "bandwidth_discount": 0.20,
        "policy_families":    ["fiscal", "monetary", "trade"],
        "class_base":         ["capitalist", "professional"],
        "crisis_boost":       {"debt_ratio": 0.05, "risk_premium": 0.03},
        "crisis_drag":        {"unrest": 0.02},
        "inequality_effect":  0.015,          # tends to increase Gini
        "growth_bonus":       0.002,
        "repression_tendency": -0.01,
    },
    "social_democracy": {
        "label": "Social Democracy",
        "core_idea": "Decommodify labour: universal services, collective bargaining, progressive taxes.",
        "signature_policies": ["universal_healthcare", "collective_bargaining", "progressive_tax", "public_housing"],
        "bandwidth_discount": 0.25,
        "policy_families":    ["labor", "services", "fiscal"],
        "class_base":         ["worker", "professional"],
        "crisis_boost":       {"poverty_headcount": 0.04, "unemployment": 0.03},
        "crisis_drag":        {"inflation_proxy": 0.02},
        "inequality_effect":  -0.025,
        "growth_bonus":       0.001,
        "repression_tendency": -0.02,
    },
    "agrarian_populism": {
        "label": "Agrarian Populism",
        "core_idea": "Land to the tiller: redistribution, rural credit, price floors for farmers.",
        "signature_policies": ["land_redistribution", "rural_credit_program", "food_price_floor", "cooperative_farming"],
        "bandwidth_discount": 0.20,
        "policy_families":    ["land", "agriculture", "services"],
        "class_base":         ["worker", "informal"],
        "crisis_boost":       {"food_shortage": 0.06, "poverty_headcount": 0.03},
        "crisis_drag":        {"external_stress": 0.03},
        "inequality_effect":  -0.02,
        "growth_bonus":       0.0005,
        "repression_tendency": 0.01,
    },
    "technocratic_modernism": {
        "label": "Technocratic Modernism",
        "core_idea": "Expertise governs: meritocracy, evidence-based policy, efficiency above politics.",
        "signature_policies": ["meritocratic_bureaucracy", "evidence_policy_office", "statistical_bureau", "technocrat_cabinet"],
        "bandwidth_discount": 0.30,
        "policy_families":    ["governance", "research", "fiscal"],
        "class_base":         ["professional", "state"],
        "crisis_boost":       {"corruption_signal": 0.04},
        "crisis_drag":        {"unrest": 0.03},
        "inequality_effect":  0.005,
        "growth_bonus":       0.003,
        "repression_tendency": 0.0,
    },
    "communal_solidarity": {
        "label": "Communal Solidarity",
        "core_idea": "Local self-organization: cooperatives, mutual aid, decentralised governance.",
        "signature_policies": ["cooperative_enterprises", "mutual_aid_network", "decentralized_governance", "community_land_trust"],
        "bandwidth_discount": 0.15,
        "policy_families":    ["land", "services", "labor"],
        "class_base":         ["informal", "worker", "cooperative"],
        "crisis_boost":       {"regional_inequality_index": 0.04, "unrest": 0.03},
        "crisis_drag":        {"external_stress": 0.02},
        "inequality_effect":  -0.03,
        "growth_bonus":       -0.001,  # slower aggregate growth but more equitable
        "repression_tendency": -0.03,
    },
}

TRADITION_NAMES = list(TRADITIONS.keys())


# ---------------------------------------------------------------------------
# Influence dynamics
# ---------------------------------------------------------------------------

def initial_tradition_influence(institutional_quality: float, corruption: float) -> dict[str, float]:
    """Seed starting influence scores (0-100) based on country profile."""
    base = {
        "developmental_nationalism": 40.0,
        "liberal_institutionalism":  25.0,
        "social_democracy":          20.0,
        "agrarian_populism":         30.0,
        "technocratic_modernism":    15.0,
        "communal_solidarity":       10.0,
    }
    # High institutional quality boosts technocratic modernism and liberal inst.
    base["technocratic_modernism"] += institutional_quality * 20.0
    base["liberal_institutionalism"] += institutional_quality * 15.0
    # High corruption weakens liberal inst. and technocracy
    base["liberal_institutionalism"] -= corruption * 20.0
    base["technocratic_modernism"]   -= corruption * 15.0
    return {k: max(5.0, min(100.0, v)) for k, v in base.items()}


def update_tradition_influence(
    influence: dict[str, float],
    prior_state: dict[str, Any],
    active_tradition: str,
) -> dict[str, float]:
    """Update each tradition's influence for one tick.

    Influence shifts based on whether current crises match the tradition's
    appeal (crisis_boost) or whether conditions undermine it (crisis_drag).
    The active (governing) tradition gains a small incumbency bonus but also
    faces a slow erosion from governing fatigue.
    """
    updated = dict(influence)
    unemployment = float(prior_state.get("unemployment", 0.08))
    unrest = float(prior_state.get("unrest", 35.0))
    poverty = float(prior_state.get("poverty_headcount", 0.24))
    corruption = float(prior_state.get("corruption_signal", 0.3))
    debt_gdp = float(prior_state.get("debt", 0.0)) / max(float(prior_state.get("nominal_gdp_monthly", 1.0)) * 12.0, 1.0)
    ext_stress = float(prior_state.get("external_stress", 0.0))
    inflation = float(prior_state.get("inflation_proxy", 0.0))
    food_shortage = float(prior_state.get("goods_shortage_pressure", 0.2))
    regional_ineq = float(prior_state.get("regional_inequality_index", 0.25))

    crisis_signals = {
        "unemployment":              unemployment,
        "unrest":                    unrest / 100.0,
        "poverty_headcount":         poverty,
        "corruption_signal":         corruption,
        "debt_ratio":                debt_gdp,
        "external_stress":           ext_stress,
        "inflation_proxy":           max(0.0, inflation),
        "food_shortage":             food_shortage,
        "goods_shortage_pressure":   food_shortage,
        "risk_premium":              float(prior_state.get("risk_premium", 0.02)),
        "regional_inequality_index": regional_ineq,
    }

    for tname, tdata in TRADITIONS.items():
        delta = 0.0

        # Crisis boosts
        for signal, weight in tdata.get("crisis_boost", {}).items():
            value = crisis_signals.get(signal, 0.0)
            delta += value * weight * 10.0

        # Crisis drags
        for signal, weight in tdata.get("crisis_drag", {}).items():
            value = crisis_signals.get(signal, 0.0)
            delta -= value * weight * 10.0

        # Incumbency: governing tradition gets small bump, slow fatigue over time
        if tname == active_tradition:
            delta += 0.5      # incumbency bonus
            delta -= 0.2      # governing fatigue

        # Mean reversion toward starting range
        current = updated.get(tname, 20.0)
        delta -= (current - 30.0) * 0.02   # pull toward 30

        updated[tname] = max(5.0, min(100.0, current + delta * 0.1))

    return updated


def dominant_tradition(influence: dict[str, float]) -> str:
    """Return the name of the tradition with the highest influence."""
    if not influence:
        return "developmental_nationalism"
    return max(influence, key=lambda k: influence[k])


def bandwidth_discount_for_action(action_family: str, active_tradition: str) -> float:
    """Return the bandwidth discount (0-1 multiplier) for an action given the governing tradition."""
    tdata = TRADITIONS.get(active_tradition, {})
    if action_family in tdata.get("policy_families", []):
        return 1.0 - tdata.get("bandwidth_discount", 0.0)
    return 1.0


# ---------------------------------------------------------------------------
# Signature policy catalogue (enactable through the legislative queue)
# ---------------------------------------------------------------------------

SIGNATURE_POLICY_DEFS: dict[str, dict[str, Any]] = {
    # Developmental nationalism
    "five_year_plan": {
        "family": "industrial", "tradition": "developmental_nationalism",
        "bandwidth_action": "propose_law", "upkeep_cost": 0.02,
        "formal_value": 0.7, "description": "State-directed 5-year industrial investment plan",
        "effect": {"growth_bonus": 0.005, "industrial_policy_bias": 0.2, "unrest": -3.0},
        "unintended_delay_ticks": 12,
        "unintended": {"corruption_signal": 0.04, "debt_ratio": 0.05},
    },
    "import_substitution": {
        "family": "trade", "tradition": "developmental_nationalism",
        "bandwidth_action": "adjust_tariffs", "upkeep_cost": 0.01,
        "formal_value": 0.6, "description": "High tariffs to protect domestic industry",
        "effect": {"trade_shock_imports": -0.25},
        "unintended_delay_ticks": 18,
        "unintended": {"goods_shortage_pressure": 0.06, "inflation_proxy": 0.01},
    },

    # Liberal institutionalism
    "central_bank_independence": {
        "family": "monetary", "tradition": "liberal_institutionalism",
        "bandwidth_action": "constitutional_change", "upkeep_cost": 0.005,
        "formal_value": 1.0, "description": "Independent central bank with inflation mandate",
        "effect": {"inflation_proxy": -0.005, "risk_premium": -0.01},
        "unintended_delay_ticks": 6,
        "unintended": {"unemployment": 0.01},
    },
    "trade_liberalization": {
        "family": "trade", "tradition": "liberal_institutionalism",
        "bandwidth_action": "adjust_tariffs", "upkeep_cost": 0.005,
        "formal_value": 0.8, "description": "Reduce tariffs and open markets to foreign competition",
        "effect": {"trade_shock_exports": 0.15, "trade_shock_imports": 0.20},
        "unintended_delay_ticks": 24,
        "unintended": {"unemployment": 0.02, "informal_income_share": 0.01},
    },

    # Social democracy
    "universal_healthcare": {
        "family": "services", "tradition": "social_democracy",
        "bandwidth_action": "enact_program", "upkeep_cost": 0.025,
        "formal_value": 0.8, "description": "Universal state-provided healthcare",
        "effect": {"poverty_headcount": -0.03, "trust": 5.0, "unrest": -4.0},
        "unintended_delay_ticks": 6,
        "unintended": {"debt": 0.02, "tax_ratio": 0.02},
    },
    "collective_bargaining": {
        "family": "labor", "tradition": "social_democracy",
        "bandwidth_action": "propose_law", "upkeep_cost": 0.008,
        "formal_value": 0.7, "description": "Legal right to collective wage bargaining",
        "effect": {"worker_income_share": 0.03, "unemployment": -0.005},
        "unintended_delay_ticks": 12,
        "unintended": {"informal_income_share": 0.01},
    },

    # Agrarian populism
    "land_redistribution": {
        "family": "land", "tradition": "agrarian_populism",
        "bandwidth_action": "propose_law", "upkeep_cost": 0.015,
        "formal_value": 0.6, "description": "Redistribute concentrated landholdings to smallholders",
        "effect": {"poverty_headcount": -0.04, "land_concentration": -0.08},
        "unintended_delay_ticks": 18,
        "unintended": {"production": -0.05, "unrest": 5.0},   # short-term disruption
    },
    "food_price_floor": {
        "family": "land", "tradition": "agrarian_populism",
        "bandwidth_action": "adjust_industrial_bias", "upkeep_cost": 0.01,
        "formal_value": 0.5, "description": "Guaranteed minimum price for staple crops",
        "effect": {"food_price_stabilization": 0.2, "poverty_headcount": -0.02},
        "unintended_delay_ticks": 6,
        "unintended": {"debt": 0.015},
    },

    # Technocratic modernism
    "statistical_bureau": {
        "family": "governance", "tradition": "technocratic_modernism",
        "bandwidth_action": "enact_program", "upkeep_cost": 0.005,
        "formal_value": 0.7, "description": "Independent national statistics office",
        "effect": {"info_quality": 0.08, "corruption_signal": -0.03},
        "unintended_delay_ticks": 3,
        "unintended": {},
    },
    "meritocratic_bureaucracy": {
        "family": "governance", "tradition": "technocratic_modernism",
        "bandwidth_action": "propose_law", "upkeep_cost": 0.012,
        "formal_value": 0.8, "description": "Civil service exam system, performance appraisal",
        "effect": {"corruption_signal": -0.06, "info_quality": 0.05},
        "unintended_delay_ticks": 12,
        "unintended": {"class_support_professionals": 5.0},
    },

    # Communal solidarity
    "cooperative_enterprises": {
        "family": "labor", "tradition": "communal_solidarity",
        "bandwidth_action": "enact_program", "upkeep_cost": 0.010,
        "formal_value": 0.5, "description": "Legal framework and credit for worker-owned cooperatives",
        "effect": {"worker_income_share": 0.02, "informal_income_share": -0.01},
        "unintended_delay_ticks": 18,
        "unintended": {"production": -0.02},
    },
    "decentralized_governance": {
        "family": "governance", "tradition": "communal_solidarity",
        "bandwidth_action": "propose_law", "upkeep_cost": 0.008,
        "formal_value": 0.6, "description": "Transfer fiscal authority to local governments",
        "effect": {"regional_equity_bias": 0.2, "regional_inequality_index": -0.04},
        "unintended_delay_ticks": 12,
        "unintended": {"corruption_signal": 0.02},
    },
}
