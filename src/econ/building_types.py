"""Static archetype catalog for physical buildings in the simulation.

Each archetype defines the structural characteristics of a building type.  The
building_engine module uses these to simulate per-tick degradation, utilization,
labor demand, and output quality.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------
# Fields per archetype:
#   sector              : matches SECTOR_NAMES in sector_network.py
#   base_workers        : baseline headcount at level-1, full capacity
#   base_workers_skilled: subset of base_workers requiring human capital
#   base_capacity       : normalized output units at level-1, condition=1, util=1
#   build_cost          : months of national budget share to construct at level-1
#   maintenance_ratio   : fraction of build_cost per tick to hold condition steady
#   degradation_rate    : condition points lost per tick at zero maintenance
#   land_use            : "low" | "medium" | "high"  (flavour / future zoning)
#   output_metric       : human-readable description of what this building produces
#   level_scale         : capacity multiplier per level above 1  (e.g. 1.5 → each
#                         level adds 50% capacity over the previous)
#   owner_classes       : list of plausible owner classes for randomised seeding
#   skill_threshold     : minimum human_capital score before quality degrades

BUILDING_ARCHETYPES: dict[str, dict[str, Any]] = {
    # ── Agriculture ────────────────────────────────────────────────────────
    "farm": {
        "sector": "agriculture",
        "base_workers": 320,
        "base_workers_skilled": 30,
        "base_capacity": 1.0,
        "build_cost": 0.008,
        "maintenance_ratio": 0.12,
        "degradation_rate": 0.006,
        "land_use": "high",
        "output_metric": "food_tonnage",
        "level_scale": 1.4,
        "owner_classes": ["capitalist", "cooperative", "state"],
        "skill_threshold": 0.30,
    },
    "irrigation_district": {
        "sector": "agriculture",
        "base_workers": 80,
        "base_workers_skilled": 20,
        "base_capacity": 0.4,      # multiplier on adjacent farm output
        "build_cost": 0.012,
        "maintenance_ratio": 0.14,
        "degradation_rate": 0.005,
        "land_use": "high",
        "output_metric": "yield_multiplier",
        "level_scale": 1.3,
        "owner_classes": ["state", "cooperative"],
        "skill_threshold": 0.35,
    },
    # ── Energy ─────────────────────────────────────────────────────────────
    "coal_power_plant": {
        "sector": "energy",
        "base_workers": 640,
        "base_workers_skilled": 180,
        "base_capacity": 1.0,
        "build_cost": 0.020,
        "maintenance_ratio": 0.16,
        "degradation_rate": 0.009,
        "land_use": "high",
        "output_metric": "mw_capacity",
        "level_scale": 1.5,
        "owner_classes": ["state", "capitalist"],
        "skill_threshold": 0.45,
    },
    "oil_gas_well": {
        "sector": "energy",
        "base_workers": 280,
        "base_workers_skilled": 120,
        "base_capacity": 0.9,
        "build_cost": 0.018,
        "maintenance_ratio": 0.18,
        "degradation_rate": 0.011,
        "land_use": "medium",
        "output_metric": "energy_units",
        "level_scale": 1.4,
        "owner_classes": ["capitalist", "state"],
        "skill_threshold": 0.50,
    },
    # ── Manufacturing ──────────────────────────────────────────────────────
    "factory": {
        "sector": "manufacturing",
        "base_workers": 900,
        "base_workers_skilled": 250,
        "base_capacity": 1.0,
        "build_cost": 0.016,
        "maintenance_ratio": 0.14,
        "degradation_rate": 0.008,
        "land_use": "medium",
        "output_metric": "goods_units",
        "level_scale": 1.5,
        "owner_classes": ["capitalist", "state"],
        "skill_threshold": 0.45,
    },
    "steel_mill": {
        "sector": "manufacturing",
        "base_workers": 1400,
        "base_workers_skilled": 400,
        "base_capacity": 1.2,
        "build_cost": 0.024,
        "maintenance_ratio": 0.18,
        "degradation_rate": 0.010,
        "land_use": "high",
        "output_metric": "intermediate_goods",
        "level_scale": 1.4,
        "owner_classes": ["state", "capitalist"],
        "skill_threshold": 0.50,
    },
    # ── Construction ───────────────────────────────────────────────────────
    "construction_yard": {
        "sector": "construction",
        "base_workers": 750,
        "base_workers_skilled": 150,
        "base_capacity": 1.0,
        "build_cost": 0.014,
        "maintenance_ratio": 0.12,
        "degradation_rate": 0.007,
        "land_use": "medium",
        "output_metric": "build_capacity",
        "level_scale": 1.4,
        "owner_classes": ["capitalist", "state", "cooperative"],
        "skill_threshold": 0.38,
    },
    # ── Services ───────────────────────────────────────────────────────────
    "hospital": {
        "sector": "services",
        "base_workers": 520,
        "base_workers_skilled": 380,
        "base_capacity": 1.0,
        "build_cost": 0.014,
        "maintenance_ratio": 0.15,
        "degradation_rate": 0.006,
        "land_use": "low",
        "output_metric": "health_index",
        "level_scale": 1.4,
        "owner_classes": ["state"],
        "skill_threshold": 0.60,
    },
    "university": {
        "sector": "services",
        "base_workers": 460,
        "base_workers_skilled": 400,
        "base_capacity": 0.8,       # research points per tick
        "build_cost": 0.016,
        "maintenance_ratio": 0.14,
        "degradation_rate": 0.004,
        "land_use": "low",
        "output_metric": "research_points",
        "level_scale": 1.5,
        "owner_classes": ["state"],
        "skill_threshold": 0.65,
    },
    "market_bazaar": {
        "sector": "services",
        "base_workers": 200,
        "base_workers_skilled": 30,
        "base_capacity": 0.7,
        "build_cost": 0.006,
        "maintenance_ratio": 0.08,
        "degradation_rate": 0.004,
        "land_use": "low",
        "output_metric": "trade_access",
        "level_scale": 1.3,
        "owner_classes": ["informal", "cooperative", "capitalist"],
        "skill_threshold": 0.20,
    },
    # ── Logistics / Infrastructure ─────────────────────────────────────────
    "road_rail_hub": {
        "sector": "construction",  # funded via construction budget
        "base_workers": 350,
        "base_workers_skilled": 80,
        "base_capacity": 1.0,       # transport_friction modifier
        "build_cost": 0.018,
        "maintenance_ratio": 0.10,
        "degradation_rate": 0.005,
        "land_use": "medium",
        "output_metric": "transport_friction_modifier",
        "level_scale": 1.4,
        "owner_classes": ["state"],
        "skill_threshold": 0.35,
    },
    # ── Security / Military ────────────────────────────────────────────────
    "military_barracks": {
        "sector": "services",
        "base_workers": 600,
        "base_workers_skilled": 200,
        "base_capacity": 1.0,
        "build_cost": 0.014,
        "maintenance_ratio": 0.16,
        "degradation_rate": 0.006,
        "land_use": "medium",
        "output_metric": "readiness_points",
        "level_scale": 1.4,
        "owner_classes": ["state"],
        "skill_threshold": 0.40,
    },
}

# Sectors mapped to their canonical building types for default seeding.
SECTOR_DEFAULT_BUILDINGS: dict[str, list[str]] = {
    "agriculture":    ["farm", "irrigation_district"],
    "energy":         ["coal_power_plant", "oil_gas_well"],
    "manufacturing":  ["factory", "steel_mill"],
    "construction":   ["construction_yard", "road_rail_hub"],
    "services":       ["hospital", "university", "market_bazaar"],
}

# Owner-class → income share routing key (used by class dynamics).
OWNER_CLASS_INCOME_ROUTE: dict[str, str] = {
    "capitalist":  "capitalist_income_share",
    "state":       "worker_income_share",       # state profits route to workers via services
    "cooperative": "worker_income_share",
    "informal":    "informal_income_share",
}


def get_archetype(building_type: str) -> dict[str, Any]:
    """Return a copy of the archetype dict, falling back to 'factory' if unknown."""
    return dict(BUILDING_ARCHETYPES.get(building_type, BUILDING_ARCHETYPES["factory"]))


def scaled_capacity(building_type: str, level: int) -> float:
    """Return rated capacity for a building type at a given level."""
    arch = get_archetype(building_type)
    scale = float(arch["level_scale"])
    base = float(arch["base_capacity"])
    return base * (scale ** (max(1, level) - 1))


def scaled_workers(building_type: str, level: int) -> int:
    """Return baseline workforce for a building type at a given level."""
    arch = get_archetype(building_type)
    scale = float(arch["level_scale"])
    base = int(arch["base_workers"])
    return max(1, int(base * (scale ** (max(1, level) - 1))))


def scaled_workers_skilled(building_type: str, level: int) -> int:
    """Return skilled workforce component for a building type at a given level."""
    arch = get_archetype(building_type)
    scale = float(arch["level_scale"])
    base = int(arch["base_workers_skilled"])
    return max(0, int(base * (scale ** (max(1, level) - 1))))
