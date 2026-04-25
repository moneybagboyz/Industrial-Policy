"""Logistics network layer for inter-region commodity flows.

Phase 3 of the supply chain revamp.

Responsibility:
  Each tick, after buildings produce and consume commodities within their own
  subregion, the logistics network redistributes surplus commodities from
  regions with excess stock to regions with deficit stock.  Redistribution
  is constrained by:

  - Corridor capacity: each transport edge has a max throughput per tick.
  - Transit friction/spoilage: a fraction of goods in transit is lost based on
    the corridor's friction score and each commodity's perishability.
  - Congestion: if demanded throughput exceeds capacity, flows are scaled
    down proportionally and the corridor's congestion ratio rises.
  - Transfer limit: at most ``max_transfer_fraction`` (default 25 %) of a
    region's surplus of any commodity is shipped per tick to prevent
    oscillation.

Key data structures:

    corridor : dict
        {
            "capacity": float,          # max normalized throughput per tick
            "friction": float,          # 0-1 transit cost / spoilage multiplier
            "utilization": float,       # fraction of capacity used last tick
            "congestion_ratio": float,  # 0-1; 1 = fully congested
            "total_flow": float,        # total commodity units shipped last tick
        }

    regional_stocks : dict[region_name, dict[commodity_id, float]]
        Aggregated stocks per region (sum of all subregion stocks).

    incoming_flows / outgoing_flows : dict[region_name, dict[commodity_id, float]]
        Net commodity amounts arriving at / leaving each region this tick.

This module is purely functional: all functions accept prior state and return
new state without mutation.
"""

from __future__ import annotations

from typing import Any

from src.econ.commodity_registry import COMMODITY_CATALOG


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _link_key(a: str, b: str) -> str:
    """Canonical sorted edge key matching the one used in regional_profiles."""
    return "|".join(sorted([a, b]))


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def build_initial_logistics_state(
    transport_edges: dict[str, dict[str, float]],
    region_names: list[str],
) -> dict[str, Any]:
    """Build the initial logistics state from the spatial topology.

    Args:
        transport_edges: output of ``_build_spatial_topology`` — dict of
            ``edge_key -> {distance, friction, capacity}``.
        region_names: ordered list of all region names.

    Returns:
        logistics_state dict containing corridors and summary metrics.
    """
    corridors: dict[str, dict[str, float]] = {}
    for edge_key, edge in transport_edges.items():
        corridors[edge_key] = {
            "capacity": float(edge.get("capacity", 0.5)),
            "friction": float(edge.get("friction", 0.3)),
            "distance": float(edge.get("distance", 20.0)),
            "utilization": 0.0,
            "congestion_ratio": 0.0,
            "total_flow": 0.0,
        }

    return {
        "corridors": corridors,
        "region_names": list(region_names),
        "tick_flows": {},           # region -> commodity -> net_received last tick
        "national_shortfall": {},   # commodity -> total deficit across all regions
        "congested_corridors": [],  # edge keys with congestion_ratio > 0.7
    }


# ---------------------------------------------------------------------------
# Stock aggregation helpers
# ---------------------------------------------------------------------------

def aggregate_region_stocks(region: dict[str, Any]) -> dict[str, float]:
    """Sum commodity_stocks across all subregions of a single region.

    Returns a flat dict of {commodity_id: total_amount}.
    """
    totals: dict[str, float] = {}
    subregions = region.get("subregions", {})
    if not isinstance(subregions, dict):
        return totals
    for sub in subregions.values():
        if not isinstance(sub, dict):
            continue
        stocks = sub.get("commodity_stocks", {})
        if not isinstance(stocks, dict):
            continue
        for cid, amount in stocks.items():
            totals[cid] = totals.get(cid, 0.0) + max(0.0, float(amount))
    return totals


def build_regional_stock_map(
    regions: dict[str, Any],
) -> dict[str, dict[str, float]]:
    """Build a region_name -> commodity_stocks map from the full region dict."""
    return {name: aggregate_region_stocks(region) for name, region in regions.items() if isinstance(region, dict)}


# ---------------------------------------------------------------------------
# Demand estimation helpers
# ---------------------------------------------------------------------------

# Rough per-capita daily demand weights used to estimate regional deficit.
# These are relative weights; absolute scale doesn't matter — only which
# regions have MORE vs. LESS per-unit stock relative to demand.
_DEMAND_WEIGHTS: dict[str, float] = {
    "staple_food":    1.0,
    "imported_food":  0.3,
    "fuel":           0.6,
    "power":          0.8,
    "medicine":       0.4,
    "consumer_goods": 0.5,
    "machine_parts":  0.2,
    "cement":         0.15,
    "steel":          0.15,
    "fertilizer":     0.10,
    "coal":           0.20,
    "crude_oil":      0.20,
    "diesel_power":   0.15,
    "iron_ore":       0.10,
    "stone_aggregate": 0.08,
    "charcoal":       0.05,
    "informal_goods": 0.10,
}


def estimate_region_demand(
    population: float,
    commodity_id: str,
) -> float:
    """Estimate per-tick demand for a commodity in a region of given population.

    Returns a rough demand quantity in the same units as commodity_stocks.
    """
    weight = _DEMAND_WEIGHTS.get(commodity_id, 0.1)
    # Scale: 1 million pop needs approximately ``weight`` units per tick.
    return (population / 1_000_000.0) * weight * 0.5


# ---------------------------------------------------------------------------
# Core flow computation
# ---------------------------------------------------------------------------

def compute_logistics_flows(
    regional_stocks: dict[str, dict[str, float]],
    region_populations: dict[str, float],
    corridors: dict[str, dict[str, float]],
    region_neighbors: dict[str, list[str]],
    max_transfer_fraction: float = 0.25,
) -> tuple[
    dict[str, dict[str, float]],    # incoming_flows: region -> commodity -> units arriving
    dict[str, dict[str, float]],    # outgoing_flows: region -> commodity -> units shipped
    dict[str, dict[str, float]],    # updated_corridors
    dict[str, float],               # national_shortfall: commodity -> total deficit
]:
    """Compute inter-region commodity transfers for one tick.

    Algorithm:
      For each commodity, identify surplus regions (stock > demand) and
      deficit regions (stock < demand).  Route surplus along available
      edges, prioritising the most-deficit destinations and closest sources,
      respecting corridor capacity and the per-region transfer cap.

    Args:
        regional_stocks: aggregated per-region commodity stocks (from
            ``build_regional_stock_map``).
        region_populations: region_name -> population float.
        corridors: current corridor state dict (not mutated; returns updated copy).
        region_neighbors: region_name -> [neighbor_name, ...] adjacency list.
        max_transfer_fraction: max fraction of surplus to ship per tick.

    Returns:
        Tuple of (incoming_flows, outgoing_flows, updated_corridors, national_shortfall).
    """
    incoming: dict[str, dict[str, float]] = {r: {} for r in regional_stocks}
    outgoing: dict[str, dict[str, float]] = {r: {} for r in regional_stocks}
    updated_corridors: dict[str, dict[str, float]] = {k: dict(v) for k, v in corridors.items()}
    # Remaining corridor capacity budget this tick (resets each tick).
    corridor_remaining: dict[str, float] = {k: float(v["capacity"]) for k, v in corridors.items()}
    national_shortfall: dict[str, float] = {}

    all_commodities = set(COMMODITY_CATALOG.keys())

    for cid in all_commodities:
        region_demand: dict[str, float] = {}
        region_surplus: dict[str, float] = {}
        region_deficit: dict[str, float] = {}

        for region_name, stocks in regional_stocks.items():
            pop = float(region_populations.get(region_name, 1_000_000.0))
            demand = estimate_region_demand(pop, cid)
            stock = float(stocks.get(cid, 0.0))
            region_demand[region_name] = demand
            surplus = stock - demand
            if surplus > 0:
                region_surplus[region_name] = surplus
            else:
                region_deficit[region_name] = abs(surplus)

        total_deficit = sum(region_deficit.values())
        if total_deficit > 0:
            national_shortfall[cid] = total_deficit

        if not region_surplus or not region_deficit:
            continue

        # Sort: most deficit first (highest priority destination).
        deficit_sorted = sorted(region_deficit.items(), key=lambda x: -x[1])

        for dest, deficit_amount in deficit_sorted:
            remaining_need = deficit_amount
            dest_neighbors = region_neighbors.get(dest, [])

            # Sort potential senders by surplus (most surplus first).
            candidate_sources = [
                (src, surplus)
                for src, surplus in region_surplus.items()
                if src in dest_neighbors and surplus > 0
            ]
            candidate_sources.sort(key=lambda x: -x[1])

            for src, available_surplus in candidate_sources:
                if remaining_need <= 0:
                    break

                edge_key = _link_key(src, dest)
                cap_remaining = corridor_remaining.get(edge_key, 0.0)
                if cap_remaining <= 0:
                    continue

                corridor = updated_corridors.get(edge_key, {})
                friction = float(corridor.get("friction", 0.30))
                perishability = float(COMMODITY_CATALOG.get(cid, {}).get("perishability", 0.01))

                # How much to ship: bounded by surplus cap, corridor capacity, and demand.
                ship_limit = min(
                    available_surplus * max_transfer_fraction,
                    cap_remaining,
                    remaining_need,
                )
                if ship_limit <= 0:
                    continue

                # Transit spoilage: higher friction + higher perishability → more loss.
                spoilage_rate = _clamp(friction * perishability * 5.0, 0.0, 0.40)
                arrived = ship_limit * (1.0 - spoilage_rate)

                # Record flows.
                outgoing[src][cid] = outgoing[src].get(cid, 0.0) + ship_limit
                incoming[dest][cid] = incoming[dest].get(cid, 0.0) + arrived

                # Update corridor capacity budget.
                corridor_remaining[edge_key] = max(0.0, cap_remaining - ship_limit)

                # Reduce available surplus so the same source isn't over-committed.
                region_surplus[src] = max(0.0, available_surplus - ship_limit)

                remaining_need -= arrived

    # Update corridor metrics from actual usage.
    corridor_flow: dict[str, float] = {}
    for region_name, out in outgoing.items():
        for cid, amount in out.items():
            for neighbor in region_neighbors.get(region_name, []):
                edge_key = _link_key(region_name, neighbor)
                if edge_key in updated_corridors:
                    corridor_flow[edge_key] = corridor_flow.get(edge_key, 0.0) + amount

    for edge_key, corridor in updated_corridors.items():
        cap = float(corridor["capacity"])
        flow = corridor_flow.get(edge_key, 0.0)
        util = _clamp(flow / max(cap, 1e-9), 0.0, 1.0)
        congestion = _clamp(util - 0.75, 0.0, 0.25) / 0.25   # 0 below 75% util, 1 at 100%
        corridor["utilization"] = util
        corridor["congestion_ratio"] = congestion
        corridor["total_flow"] = flow

    return incoming, outgoing, updated_corridors, national_shortfall


# ---------------------------------------------------------------------------
# Applying flows back to subregion stocks
# ---------------------------------------------------------------------------

def distribute_incoming_to_subregions(
    subregions: dict[str, Any],
    incoming: dict[str, float],
    outgoing: dict[str, float],
) -> dict[str, Any]:
    """Apply inter-region flows to subregion commodity_stocks.

    Incoming commodities are distributed proportionally to population share.
    Outgoing commodities are deducted proportionally from subregion stocks.

    Returns a new subregions dict; does not mutate inputs.
    """
    total_pop_share = sum(
        float(sub.get("population_share", 1.0))
        for sub in subregions.values()
        if isinstance(sub, dict)
    )
    total_pop_share = max(total_pop_share, 1e-9)

    updated: dict[str, Any] = {}
    for sub_name, sub in subregions.items():
        if not isinstance(sub, dict):
            updated[sub_name] = sub
            continue

        pop_weight = float(sub.get("population_share", 1.0)) / total_pop_share
        stocks = dict(sub.get("commodity_stocks", {}))

        for cid, amount in incoming.items():
            share = amount * pop_weight
            stocks[cid] = max(0.0, stocks.get(cid, 0.0) + share)

        for cid, amount in outgoing.items():
            share = amount * pop_weight
            stocks[cid] = max(0.0, stocks.get(cid, 0.0) - share)

        updated[sub_name] = {**sub, "commodity_stocks": stocks}

    return updated


# ---------------------------------------------------------------------------
# Logistics state update (single tick)
# ---------------------------------------------------------------------------

def update_logistics_state(
    logistics_state: dict[str, Any],
    regions: dict[str, Any],
    region_populations: dict[str, float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one tick of logistics redistribution.

    Reads commodity stocks from subregions of each region, computes
    inter-region flows, and returns updated region dict and logistics state.

    Args:
        logistics_state: current logistics state (corridors, etc.).
        regions: full regions dict from region_state["regions"].
        region_populations: region_name -> population.

    Returns:
        (updated_regions, updated_logistics_state)
    """
    corridors = logistics_state.get("corridors", {})

    # Build adjacency list from corridors.
    region_neighbors: dict[str, list[str]] = {r: [] for r in regions}
    for edge_key in corridors:
        parts = edge_key.split("|")
        if len(parts) == 2:
            a, b = parts
            if a in region_neighbors:
                if b not in region_neighbors[a]:
                    region_neighbors[a].append(b)
            if b in region_neighbors:
                if a not in region_neighbors[b]:
                    region_neighbors[b].append(a)

    # Aggregate stocks per region.
    regional_stocks = build_regional_stock_map(regions)

    # Compute flows.
    incoming, outgoing, updated_corridors, national_shortfall = compute_logistics_flows(
        regional_stocks=regional_stocks,
        region_populations=region_populations,
        corridors=corridors,
        region_neighbors=region_neighbors,
    )

    # Apply flows to each region's subregion stocks.
    updated_regions: dict[str, Any] = {}
    for region_name, region in regions.items():
        if not isinstance(region, dict):
            updated_regions[region_name] = region
            continue
        region_incoming = incoming.get(region_name, {})
        region_outgoing = outgoing.get(region_name, {})
        updated_subregions = distribute_incoming_to_subregions(
            subregions=region.get("subregions", {}),
            incoming=region_incoming,
            outgoing=region_outgoing,
        )
        updated_regions[region_name] = {**region, "subregions": updated_subregions}

    # Identify congested corridors.
    congested = [
        k for k, c in updated_corridors.items()
        if float(c.get("congestion_ratio", 0.0)) > 0.7
    ]

    updated_logistics = {
        **logistics_state,
        "corridors": updated_corridors,
        "tick_flows": {
            r: {
                "incoming": incoming.get(r, {}),
                "outgoing": outgoing.get(r, {}),
            }
            for r in regions
        },
        "national_shortfall": national_shortfall,
        "congested_corridors": congested,
    }

    return updated_regions, updated_logistics


# ---------------------------------------------------------------------------
# Summary helpers (for UI / observability)
# ---------------------------------------------------------------------------

def corridor_summary(logistics_state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a sorted list of corridor summaries for display.

    Sorted by congestion_ratio descending (worst first).
    """
    corridors = logistics_state.get("corridors", {})
    result = []
    for edge_key, corridor in corridors.items():
        parts = edge_key.split("|")
        result.append({
            "edge": edge_key,
            "from": parts[0] if parts else "",
            "to": parts[1] if len(parts) > 1 else "",
            "capacity": round(float(corridor.get("capacity", 0.0)), 3),
            "utilization": round(float(corridor.get("utilization", 0.0)), 3),
            "congestion_ratio": round(float(corridor.get("congestion_ratio", 0.0)), 3),
            "friction": round(float(corridor.get("friction", 0.0)), 3),
            "total_flow": round(float(corridor.get("total_flow", 0.0)), 4),
        })
    result.sort(key=lambda x: -x["congestion_ratio"])
    return result


def top_shortfalls(logistics_state: dict[str, Any], n: int = 5) -> list[dict[str, Any]]:
    """Return the top-n commodities by national shortfall magnitude."""
    shortfall = logistics_state.get("national_shortfall", {})
    sorted_items = sorted(shortfall.items(), key=lambda x: -x[1])
    return [
        {"commodity": cid, "deficit": round(amount, 4)}
        for cid, amount in sorted_items[:n]
    ]
