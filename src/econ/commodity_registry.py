"""Named commodity catalog for the supply chain system.

Each commodity has a fixed id string used as a key throughout the simulation.
The registry defines the physical and economic properties that govern how
commodities are produced, stored, traded, and consumed.

Fields per commodity:
    category            : broad group ("food", "energy", "material", "industrial", "social")
    perishability       : 0-1; fraction of stored stock lost per tick (higher = spoils faster)
    strategic_priority  : 1-5; how critical a shortage is (5 = state-level crisis trigger)
    storage_decay       : alias for perishability at the storage layer (same value)
    importability       : 0-1; how easily this commodity can be sourced from imports
    exportability       : 0-1; how easily this commodity can be sold abroad
    substitution_group  : set of commodity ids that can partially substitute for this one
    base_price          : relative price index at equilibrium (used for value-flow accounting)
    unit                : human-readable unit label

The module also exposes helpers for resolving substitution chains and checking
whether a commodity is strategic.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Commodity catalog
# ---------------------------------------------------------------------------

COMMODITY_CATALOG: dict[str, dict[str, Any]] = {
    # ── Food ────────────────────────────────────────────────────────────────
    "staple_food": {
        "category": "food",
        "perishability": 0.04,          # 4 % of stored stock spoils per tick
        "strategic_priority": 5,
        "importability": 0.70,
        "exportability": 0.50,
        "substitution_group": {"imported_food"},
        "base_price": 1.0,
        "unit": "food_tonnes",
    },
    "imported_food": {
        "category": "food",
        "perishability": 0.03,
        "strategic_priority": 4,
        "importability": 1.00,
        "exportability": 0.00,
        "substitution_group": {"staple_food"},
        "base_price": 1.3,
        "unit": "food_tonnes",
    },
    "fertilizer": {
        "category": "food",
        "perishability": 0.01,
        "strategic_priority": 3,
        "importability": 0.80,
        "exportability": 0.40,
        "substitution_group": set(),
        "base_price": 0.8,
        "unit": "fertilizer_tonnes",
    },
    # ── Energy ──────────────────────────────────────────────────────────────
    "fuel": {
        "category": "energy",
        "perishability": 0.005,
        "strategic_priority": 5,
        "importability": 0.85,
        "exportability": 0.75,
        "substitution_group": {"charcoal"},
        "base_price": 1.4,
        "unit": "fuel_units",
    },
    "power": {
        "category": "energy",
        "perishability": 1.0,           # electricity cannot be stored (simplified)
        "strategic_priority": 5,
        "importability": 0.20,
        "exportability": 0.20,
        "substitution_group": {"diesel_power"},
        "base_price": 1.2,
        "unit": "mwh",
    },
    "diesel_power": {
        "category": "energy",
        "perishability": 1.0,
        "strategic_priority": 3,
        "importability": 0.30,
        "exportability": 0.10,
        "substitution_group": {"power"},
        "base_price": 1.8,
        "unit": "mwh",
    },
    "coal": {
        "category": "energy",
        "perishability": 0.002,
        "strategic_priority": 3,
        "importability": 0.65,
        "exportability": 0.70,
        "substitution_group": {"charcoal"},
        "base_price": 0.7,
        "unit": "coal_tonnes",
    },
    "charcoal": {
        "category": "energy",
        "perishability": 0.008,
        "strategic_priority": 1,
        "importability": 0.30,
        "exportability": 0.20,
        "substitution_group": {"coal", "fuel"},
        "base_price": 0.5,
        "unit": "charcoal_units",
    },
    # ── Raw materials ────────────────────────────────────────────────────────
    "crude_oil": {
        "category": "material",
        "perishability": 0.001,
        "strategic_priority": 4,
        "importability": 0.75,
        "exportability": 0.80,
        "substitution_group": set(),
        "base_price": 1.1,
        "unit": "oil_barrels",
    },
    "iron_ore": {
        "category": "material",
        "perishability": 0.001,
        "strategic_priority": 3,
        "importability": 0.70,
        "exportability": 0.70,
        "substitution_group": set(),
        "base_price": 0.6,
        "unit": "ore_tonnes",
    },
    "stone_aggregate": {
        "category": "material",
        "perishability": 0.0,
        "strategic_priority": 2,
        "importability": 0.35,
        "exportability": 0.30,
        "substitution_group": set(),
        "base_price": 0.3,
        "unit": "aggregate_tonnes",
    },
    # ── Industrial intermediates ─────────────────────────────────────────────
    "steel": {
        "category": "industrial",
        "perishability": 0.002,
        "strategic_priority": 4,
        "importability": 0.75,
        "exportability": 0.65,
        "substitution_group": set(),
        "base_price": 2.0,
        "unit": "steel_tonnes",
    },
    "cement": {
        "category": "industrial",
        "perishability": 0.01,
        "strategic_priority": 4,
        "importability": 0.55,
        "exportability": 0.45,
        "substitution_group": set(),
        "base_price": 0.9,
        "unit": "cement_tonnes",
    },
    "machine_parts": {
        "category": "industrial",
        "perishability": 0.003,
        "strategic_priority": 4,
        "importability": 0.80,
        "exportability": 0.50,
        "substitution_group": set(),
        "base_price": 3.5,
        "unit": "parts_units",
    },
    # ── Consumer goods ────────────────────────────────────────────────────────
    "consumer_goods": {
        "category": "social",
        "perishability": 0.012,
        "strategic_priority": 3,
        "importability": 0.85,
        "exportability": 0.40,
        "substitution_group": {"informal_goods"},
        "base_price": 1.6,
        "unit": "goods_units",
    },
    "informal_goods": {
        "category": "social",
        "perishability": 0.015,
        "strategic_priority": 1,
        "importability": 0.00,
        "exportability": 0.00,
        "substitution_group": {"consumer_goods"},
        "base_price": 0.7,
        "unit": "goods_units",
    },
    "medicine": {
        "category": "social",
        "perishability": 0.02,
        "strategic_priority": 5,
        "importability": 0.90,
        "exportability": 0.20,
        "substitution_group": set(),
        "base_price": 4.0,
        "unit": "medicine_units",
    },
}

# All commodity ids, for iteration.
COMMODITY_IDS: frozenset[str] = frozenset(COMMODITY_CATALOG.keys())

# Strategic commodities (priority >= 4) — shortages trigger political consequences.
STRATEGIC_COMMODITIES: frozenset[str] = frozenset(
    cid for cid, props in COMMODITY_CATALOG.items()
    if props["strategic_priority"] >= 4
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_commodity(commodity_id: str) -> dict[str, Any]:
    """Return the catalog entry for a commodity, raising KeyError if unknown."""
    if commodity_id not in COMMODITY_CATALOG:
        raise KeyError(f"Unknown commodity: {commodity_id!r}")
    return COMMODITY_CATALOG[commodity_id]


def is_strategic(commodity_id: str) -> bool:
    """Return True if the commodity is strategic (priority >= 4)."""
    return commodity_id in STRATEGIC_COMMODITIES


def can_substitute(commodity_id: str, available: set[str]) -> set[str]:
    """Return which available commodities can substitute for *commodity_id*.

    Only returns substitutes that are listed in the commodity's
    ``substitution_group`` *and* present in *available*.
    """
    entry = COMMODITY_CATALOG.get(commodity_id)
    if entry is None:
        return set()
    return entry["substitution_group"] & available


def build_empty_commodity_state() -> dict[str, float]:
    """Return a zeroed commodity stock dict covering all catalog commodities."""
    return {cid: 0.0 for cid in COMMODITY_CATALOG}


def apply_storage_decay(stocks: dict[str, float]) -> dict[str, float]:
    """Apply one tick of perishability decay to a commodity stock dict.

    Returns a new dict; does not mutate the input.
    """
    result = {}
    for cid, amount in stocks.items():
        decay = COMMODITY_CATALOG.get(cid, {}).get("perishability", 0.0)
        result[cid] = max(0.0, amount * (1.0 - decay))
    return result
