"""Policy system: formal vs. shadow gap, bandwidth, decay, graveyard.

Core concepts
-------------
- Every enacted policy has a *formal* value (what the law says) and a *realized*
  value (what actually happens on the ground, shaped by state capacity).
- Policies have *vitality* (0-100): enforcement strength that decays without
  upkeep spending and drifts toward whoever is most organized to exploit it.
- The cabinet has finite *political bandwidth* each tick; major reforms cost
  more than routine adjustments.
- Repealed or collapsed policies enter the *graveyard* and generate residual
  grievance / institutional scar tissue for several ticks.
- A *credibility multiplier* (0-1) globally scales how fast new policies take
  effect, depressed by too many failures.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Bandwidth cost for each built-in policy action (0 = free tweak, 100 = constitutional moment)
BANDWIDTH_COSTS: dict[str, int] = {
    # Fiscal tweaks
    "adjust_tax_rate":          5,
    "adjust_spend_ratio":       5,
    "adjust_ministry_budget":   8,
    # Monetary
    "adjust_policy_rate":       6,
    # Investment / industrial
    "adjust_industrial_bias":   10,
    "adjust_infrastructure":    12,
    "adjust_research_spend":    8,
    "adjust_construction_spend": 8,
    # Trade
    "adjust_tariffs":           10,
    "adjust_exports":           8,
    # Governance / social
    "adjust_repression":        6,
    "adjust_corruption":        15,
    "adjust_info_quality":      10,
    # Programs (persistent commitments)
    "enact_program":            20,
    "repeal_program":           12,
    # Laws (require legislative coalition)
    "propose_law":              35,
    "constitutional_change":    80,
    # Buildings
    "nationalize_sector":       30,
    "construction_subsidy":     15,
}

# How fast vitality decays per tick when a policy is underfunded (0-1 fraction of max decay)
BASE_DECAY_RATE = 2.5   # vitality points per tick without upkeep
UPKEEP_RECOVERY  = 4.0  # vitality points per tick with full upkeep

# Drift targets by policy family when vitality falls below 40
DRIFT_BENEFICIARY: dict[str, str] = {
    "fiscal":       "capitalist",   # tax enforcement weakness → capital benefits
    "labor":        "capitalist",   # labor law erosion → capital benefits
    "land":         "capitalist",   # land reform drift → landlords recapture
    "services":     "state",        # service programs → bureaucracy captures budget
    "trade":        "informal",     # trade regulation gaps → smugglers / informal
    "monetary":     "capitalist",   # monetary policy drift → finance benefits
    "governance":   "state",        # governance drift → incumbents entrench
}

# Graveyard scar decay: grievance fades this many points per tick
GRIEVANCE_DECAY_PER_TICK = 1.5

# Credibility penalty per failed/collapsed policy (recovered 0.5%/tick naturally)
CREDIBILITY_PENALTY = 0.04
CREDIBILITY_RECOVERY = 0.005


# ---------------------------------------------------------------------------
# Bandwidth
# ---------------------------------------------------------------------------

def bandwidth_recharge(legitimacy: float, coalition_cohesion: float) -> int:
    """Bandwidth regenerated each tick (roughly 20-60 units/tick)."""
    base = 20
    bonus = int(legitimacy * 0.25 + coalition_cohesion * 15.0)
    return min(60, base + bonus)


def bandwidth_cost(action: str, institutional_quality: float) -> int:
    """Cost of a policy action, adjusted for state capacity.

    High institutional quality reduces friction (costs cheaper).
    Low institutional quality makes everything harder.
    """
    base = BANDWIDTH_COSTS.get(action, 20)
    # ±50% based on institutional quality (0-1 scale)
    modifier = 1.0 + (0.5 - institutional_quality)   # IQ=1 → 0.5×, IQ=0 → 1.5×
    return max(1, int(base * modifier))


# ---------------------------------------------------------------------------
# Shadow policy (realized vs. formal)
# ---------------------------------------------------------------------------

def realized_value(
    formal_value: float,
    bureaucratic_reach: float,
    legitimacy_norm: float,
    elite_capture: float,
    vitality: float,
) -> float:
    """Compute the realized (on-the-ground) value of a policy.

    Args:
        formal_value: what the law/decree says (0-1 normalized).
        bureaucratic_reach: state administrative capacity (0-1).
        legitimacy_norm: population compliance disposition (0-1).
        elite_capture: fraction of enforcement hollowed by elites (0-1).
        vitality: current policy vitality (0-100).

    Returns:
        Realized value, pulled toward formal_value by capacity and legitimacy
        and pushed away by capture and low vitality.
    """
    capacity_factor = (bureaucratic_reach * 0.5 + legitimacy_norm * 0.3 + vitality / 100.0 * 0.2)
    capture_drag = elite_capture * 0.4
    realized = formal_value * max(0.0, capacity_factor - capture_drag)
    return max(0.0, min(1.0, realized))


def shadow_gap(formal: float, realized: float) -> float:
    """Absolute gap between formal and realized policy value."""
    return abs(formal - realized)


# ---------------------------------------------------------------------------
# Policy vitality update
# ---------------------------------------------------------------------------

def update_policy_vitality(
    vitality: float,
    upkeep_funded: bool,
    institutional_quality: float,
    legitimacy: float,
) -> float:
    """Tick vitality of one active policy.

    Vitality decays without upkeep; institutional quality and legitimacy
    moderate decay rate.
    """
    capacity_mod = 0.5 + institutional_quality * 0.5   # 0.5-1.0
    legit_mod    = 0.7 + legitimacy * 0.3              # 0.7-1.0

    if upkeep_funded:
        delta = UPKEEP_RECOVERY * capacity_mod * legit_mod
    else:
        delta = -BASE_DECAY_RATE / (capacity_mod * legit_mod)

    return max(0.0, min(100.0, vitality + delta))


# ---------------------------------------------------------------------------
# Active policy registry helpers
# ---------------------------------------------------------------------------

def make_policy(
    name: str,
    family: str,
    formal_value: float,
    bandwidth_action: str = "adjust_tax_rate",
    upkeep_cost: float = 0.0,
    owner_tradition: str = "",
    description: str = "",
) -> dict[str, Any]:
    """Create a new active policy dict."""
    return {
        "name": name,
        "family": family,
        "formal_value": formal_value,
        "realized_value": formal_value * 0.5,   # starts below full effect
        "vitality": 50.0,
        "bandwidth_action": bandwidth_action,
        "upkeep_cost": upkeep_cost,
        "owner_tradition": owner_tradition,
        "description": description,
        "age_ticks": 0,
        "drift_target": DRIFT_BENEFICIARY.get(family, "capitalist"),
    }


def update_active_policies(
    active_policies: list[dict[str, Any]],
    ministry_budgets: dict[str, float],
    institutional_quality: float,
    legitimacy_norm: float,
    bureaucratic_reach: float,
    elite_capture: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Update all active policies for one tick.

    Returns:
        (updated_active, newly_collapsed) — collapsed policies have vitality ≤ 0.
    """
    updated: list[dict[str, Any]] = []
    collapsed: list[dict[str, Any]] = []

    for pol in active_policies:
        p = dict(pol)
        upkeep = float(p.get("upkeep_cost", 0.0))
        family = str(p.get("family", "fiscal"))
        # Funded if the relevant ministry has budget covering upkeep
        ministry = _family_to_ministry(family)
        available = float(ministry_budgets.get(ministry, 0.0))
        upkeep_funded = available >= upkeep

        p["vitality"] = update_policy_vitality(
            vitality=float(p.get("vitality", 50.0)),
            upkeep_funded=upkeep_funded,
            institutional_quality=institutional_quality,
            legitimacy=legitimacy_norm,
        )
        p["realized_value"] = realized_value(
            formal_value=float(p.get("formal_value", 0.5)),
            bureaucratic_reach=bureaucratic_reach,
            legitimacy_norm=legitimacy_norm,
            elite_capture=elite_capture,
            vitality=float(p["vitality"]),
        )
        p["age_ticks"] = int(p.get("age_ticks", 0)) + 1

        if p["vitality"] <= 0.0:
            p["collapse_reason"] = "vitality_exhausted"
            collapsed.append(p)
        else:
            updated.append(p)

    return updated, collapsed


def _family_to_ministry(family: str) -> str:
    mapping = {
        "fiscal":     "finance",
        "labor":      "social",
        "land":       "agriculture",
        "services":   "social",
        "trade":      "finance",
        "monetary":   "finance",
        "governance": "interior",
        "military":   "defense",
        "research":   "education",
        "industrial": "industry",
    }
    return mapping.get(family, "finance")


# ---------------------------------------------------------------------------
# Policy graveyard
# ---------------------------------------------------------------------------

def add_to_graveyard(
    graveyard: list[dict[str, Any]],
    policy: dict[str, Any],
    reason: str,
    tick: int,
) -> list[dict[str, Any]]:
    """Add a collapsed/repealed policy to the graveyard."""
    entry = dict(policy)
    entry["buried_tick"] = tick
    entry["burial_reason"] = reason
    # Grievance: higher for well-established (old) policies that benefited many
    age = int(policy.get("age_ticks", 0))
    entry["grievance"] = min(100.0, 20.0 + age * 0.5)
    entry["scar_ticks_remaining"] = max(12, min(60, age // 2))
    graveyard.append(entry)
    return graveyard


def decay_graveyard(graveyard: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    """Age graveyard entries; remove expired ones. Returns (updated, total_grievance)."""
    updated = []
    total_grievance = 0.0
    for entry in graveyard:
        e = dict(entry)
        e["scar_ticks_remaining"] = int(e.get("scar_ticks_remaining", 0)) - 1
        e["grievance"] = max(0.0, float(e.get("grievance", 0.0)) - GRIEVANCE_DECAY_PER_TICK)
        if e["scar_ticks_remaining"] > 0 and e["grievance"] > 0.0:
            total_grievance += e["grievance"]
            updated.append(e)
    return updated, total_grievance


# ---------------------------------------------------------------------------
# Credibility multiplier
# ---------------------------------------------------------------------------

def update_credibility(
    credibility: float,
    n_collapsed: int,
    n_failed_laws: int,
) -> float:
    """Update government credibility multiplier (0.2-1.0)."""
    penalty = (n_collapsed + n_failed_laws) * CREDIBILITY_PENALTY
    credibility = credibility - penalty + CREDIBILITY_RECOVERY
    return max(0.20, min(1.0, credibility))


# ---------------------------------------------------------------------------
# Ministry budget system
# ---------------------------------------------------------------------------

MINISTRIES = (
    "finance",
    "social",
    "agriculture",
    "industry",
    "defense",
    "interior",
    "education",
)

def initial_ministry_budgets(spend_ratio: float, gdp_monthly: float) -> dict[str, float]:
    """Reasonable default ministry budget allocation."""
    total = spend_ratio * gdp_monthly
    return {
        "finance":    total * 0.08,
        "social":     total * 0.28,
        "agriculture":total * 0.10,
        "industry":   total * 0.12,
        "defense":    total * 0.16,
        "interior":   total * 0.08,
        "education":  total * 0.18,
    }


def update_ministry_budgets(
    allocations: dict[str, float],
    total_budget: float,
) -> dict[str, float]:
    """Normalise ministry allocations to sum to total_budget."""
    total_alloc = sum(allocations.values()) or 1.0
    return {k: v / total_alloc * total_budget for k, v in allocations.items()}


# ---------------------------------------------------------------------------
# Default active policies seeded at game start
# ---------------------------------------------------------------------------

DEFAULT_ACTIVE_POLICIES: list[dict[str, Any]] = [
    make_policy("basic_tax_regime",          "fiscal",     0.20, "adjust_tax_rate",      upkeep_cost=0.005, description="Standard income and trade taxation"),
    make_policy("public_spending_program",   "services",   0.20, "adjust_spend_ratio",   upkeep_cost=0.010, description="General public expenditure"),
    make_policy("labour_standards",          "labor",      0.40, "adjust_industrial_bias",upkeep_cost=0.003, description="Minimum wage and workplace rules"),
    make_policy("infrastructure_maintenance","governance", 0.25, "adjust_infrastructure", upkeep_cost=0.008, description="Road, utility and public works upkeep"),
    make_policy("monetary_policy",           "monetary",   0.08, "adjust_policy_rate",   upkeep_cost=0.002, description="Central bank interest rate regime"),
]
