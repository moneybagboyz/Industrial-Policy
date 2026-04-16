"""Regional profile generation and state-level economic updates."""

from __future__ import annotations

import math
from heapq import heappop, heappush
from typing import Any

from src.econ.building_engine import (
    aggregate_subregion_buildings,
    seed_buildings_for_subregion,
    update_subregion_buildings,
)

ARCHETYPES: tuple[str, ...] = (
    "agro_periphery",
    "resource_core",
    "industrial_belt",
    "service_metro",
    "fragile_frontier",
)

ARCHETYPE_BASE: dict[str, dict[str, float]] = {
    "agro_periphery": {
        "resource_endowment": 0.72,
        "infrastructure": 0.44,
        "institutional_quality": 0.46,
        "logistics_access": 0.40,
        "human_capital": 0.45,
        "land_concentration": 0.62,
        "primary_specialization": 0.62,
        "secondary_specialization": 0.24,
        "tertiary_specialization": 0.14,
    },
    "resource_core": {
        "resource_endowment": 0.86,
        "infrastructure": 0.52,
        "institutional_quality": 0.48,
        "logistics_access": 0.56,
        "human_capital": 0.50,
        "land_concentration": 0.68,
        "primary_specialization": 0.58,
        "secondary_specialization": 0.28,
        "tertiary_specialization": 0.14,
    },
    "industrial_belt": {
        "resource_endowment": 0.56,
        "infrastructure": 0.68,
        "institutional_quality": 0.58,
        "logistics_access": 0.66,
        "human_capital": 0.62,
        "land_concentration": 0.40,
        "primary_specialization": 0.18,
        "secondary_specialization": 0.62,
        "tertiary_specialization": 0.20,
    },
    "service_metro": {
        "resource_endowment": 0.34,
        "infrastructure": 0.82,
        "institutional_quality": 0.72,
        "logistics_access": 0.80,
        "human_capital": 0.76,
        "land_concentration": 0.34,
        "primary_specialization": 0.10,
        "secondary_specialization": 0.24,
        "tertiary_specialization": 0.66,
    },
    "fragile_frontier": {
        "resource_endowment": 0.48,
        "infrastructure": 0.30,
        "institutional_quality": 0.34,
        "logistics_access": 0.32,
        "human_capital": 0.36,
        "land_concentration": 0.58,
        "primary_specialization": 0.50,
        "secondary_specialization": 0.22,
        "tertiary_specialization": 0.28,
    },
}

ARCHETYPE_GEO_BASE: dict[str, dict[str, float]] = {
    "agro_periphery": {
        "fertility": 0.78,
        "water_access": 0.66,
        "oil_endowment": 0.22,
        "gas_endowment": 0.20,
        "iron_endowment": 0.30,
        "coal_endowment": 0.28,
        "stone_endowment": 0.46,
        "coastal_access": 0.20,
        "river_access": 0.62,
        "market_access": 0.40,
    },
    "resource_core": {
        "fertility": 0.44,
        "water_access": 0.48,
        "oil_endowment": 0.68,
        "gas_endowment": 0.60,
        "iron_endowment": 0.66,
        "coal_endowment": 0.62,
        "stone_endowment": 0.58,
        "coastal_access": 0.36,
        "river_access": 0.40,
        "market_access": 0.46,
    },
    "industrial_belt": {
        "fertility": 0.40,
        "water_access": 0.52,
        "oil_endowment": 0.34,
        "gas_endowment": 0.34,
        "iron_endowment": 0.62,
        "coal_endowment": 0.60,
        "stone_endowment": 0.64,
        "coastal_access": 0.34,
        "river_access": 0.44,
        "market_access": 0.66,
    },
    "service_metro": {
        "fertility": 0.28,
        "water_access": 0.54,
        "oil_endowment": 0.18,
        "gas_endowment": 0.18,
        "iron_endowment": 0.22,
        "coal_endowment": 0.20,
        "stone_endowment": 0.30,
        "coastal_access": 0.70,
        "river_access": 0.56,
        "market_access": 0.86,
    },
    "fragile_frontier": {
        "fertility": 0.56,
        "water_access": 0.40,
        "oil_endowment": 0.30,
        "gas_endowment": 0.28,
        "iron_endowment": 0.36,
        "coal_endowment": 0.34,
        "stone_endowment": 0.40,
        "coastal_access": 0.14,
        "river_access": 0.30,
        "market_access": 0.30,
    },
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _gini(values: list[float]) -> float:
    ordered = sorted(max(0.0, v) for v in values)
    n = len(ordered)
    if n == 0:
        return 0.0
    total = sum(ordered)
    if total <= 0.0:
        return 0.0
    rank_weighted = 0.0
    for idx, val in enumerate(ordered, start=1):
        rank_weighted += idx * val
    return (2.0 * rank_weighted) / (n * total) - (n + 1.0) / n


def _deterministic_noise(seed_int: int, idx: int, salt: int) -> float:
    raw = ((seed_int + idx * 31 + salt * 17) % 101) / 100.0
    return raw - 0.5


def _euclid(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def _link_key(a: str, b: str) -> str:
    return "|".join(sorted((a, b)))


def _build_spatial_topology(
    region_rows: dict[str, dict[str, float | str]],
    scenario_seed: int,
) -> dict[str, Any]:
    names = list(region_rows.keys())
    if not names:
        return {"transport_edges": {}, "mean_route_cost": 0.0, "connectivity_index": 0.0}

    # Place regions in a deterministic pseudo-Voronoi-like spread on a 100x100 map.
    count = len(names)
    for idx, name in enumerate(names):
        angle = (idx / max(1, count)) * 2.0 * math.pi
        radius = 28.0 + ((scenario_seed + idx * 19) % 31)
        cx = 50.0 + math.cos(angle) * min(44.0, radius * 0.70) + _deterministic_noise(scenario_seed, idx, 41) * 6.0
        cy = 50.0 + math.sin(angle) * min(44.0, radius * 0.70) + _deterministic_noise(scenario_seed, idx, 43) * 6.0
        region_rows[name]["coord_x"] = _clamp(cx, 2.0, 98.0)
        region_rows[name]["coord_y"] = _clamp(cy, 2.0, 98.0)

    # Approximate Voronoi adjacency by k-nearest neighbors (k=3) with reciprocal links.
    neighbors: dict[str, set[str]] = {n: set() for n in names}
    for name in names:
        x1 = float(region_rows[name]["coord_x"])
        y1 = float(region_rows[name]["coord_y"])
        ranked: list[tuple[float, str]] = []
        for other in names:
            if other == name:
                continue
            x2 = float(region_rows[other]["coord_x"])
            y2 = float(region_rows[other]["coord_y"])
            ranked.append((_euclid(x1, y1, x2, y2), other))
        ranked.sort(key=lambda t: t[0])
        for _, other in ranked[:3]:
            neighbors[name].add(other)
            neighbors[other].add(name)

    # Build transport edges with distance-based friction/capacity.
    edges: dict[str, dict[str, float]] = {}
    for name in names:
        x1 = float(region_rows[name]["coord_x"])
        y1 = float(region_rows[name]["coord_y"])
        for other in neighbors[name]:
            key = _link_key(name, other)
            if key in edges:
                continue
            x2 = float(region_rows[other]["coord_x"])
            y2 = float(region_rows[other]["coord_y"])
            dist = max(1.0, _euclid(x1, y1, x2, y2))
            infra_pair = (float(region_rows[name]["infrastructure"]) + float(region_rows[other]["infrastructure"])) / 2.0
            friction = _clamp(dist / 120.0 + (1.0 - infra_pair) * 0.30, 0.02, 1.4)
            capacity = _clamp((1.0 - friction / 1.4) * 1.2, 0.10, 1.20)
            edges[key] = {
                "distance": dist,
                "friction": friction,
                "capacity": capacity,
            }

    for name in names:
        region_rows[name]["neighbors"] = sorted(neighbors[name])

    # Compute map-wide mean shortest path friction.
    graph: dict[str, list[tuple[str, float]]] = {n: [] for n in names}
    for key, payload in edges.items():
        left, right = key.split("|")
        w = max(0.01, float(payload["friction"]))
        graph[left].append((right, w))
        graph[right].append((left, w))

    total_cost = 0.0
    pair_count = 0
    for src in names:
        dist_map = _shortest_paths(src, graph)
        for dst in names:
            if dst <= src:
                continue
            if dst in dist_map:
                total_cost += dist_map[dst]
                pair_count += 1

    mean_route = total_cost / max(1, pair_count)
    possible_pairs = (count * (count - 1)) / 2.0
    connectivity = pair_count / max(1.0, possible_pairs)
    return {
        "transport_edges": edges,
        "mean_route_cost": mean_route,
        "connectivity_index": _clamp(connectivity, 0.0, 1.0),
    }


def _shortest_paths(source: str, graph: dict[str, list[tuple[str, float]]]) -> dict[str, float]:
    dist: dict[str, float] = {source: 0.0}
    queue: list[tuple[float, str]] = [(0.0, source)]
    while queue:
        cost, node = heappop(queue)
        if cost > dist.get(node, 1e18):
            continue
        for nxt, weight in graph.get(node, []):
            ncost = cost + weight
            if ncost < dist.get(nxt, 1e18):
                dist[nxt] = ncost
                heappush(queue, (ncost, nxt))
    return dist


def _derive_geo_profile(archetype: str, row: dict[str, float | str], seed_int: int, idx: int) -> dict[str, float]:
    base = ARCHETYPE_GEO_BASE.get(archetype, ARCHETYPE_GEO_BASE["agro_periphery"])
    geo: dict[str, float] = {}
    for key, value in base.items():
        jitter = _deterministic_noise(seed_int, idx, 101 + len(key)) * 0.14
        geo[key] = _clamp(float(value) + jitter, 0.02, 0.98)

    infra = _clamp(float(row.get("infrastructure", 0.45)), 0.10, 0.95)
    inst = _clamp(float(row.get("institutional_quality", 0.45)), 0.10, 0.95)
    human = _clamp(float(row.get("human_capital", 0.45)), 0.10, 0.95)
    logistics = _clamp(float(row.get("logistics_access", 0.45)), 0.10, 0.95)

    geo["transport_connectivity"] = _clamp(logistics * 0.70 + infra * 0.30, 0.02, 0.98)
    geo["grid_reliability"] = _clamp(infra * 0.60 + inst * 0.25 + human * 0.15, 0.02, 0.98)
    geo["state_capacity"] = _clamp(inst * 0.65 + infra * 0.20 + human * 0.15, 0.02, 0.98)
    geo["insecurity"] = _clamp(1.0 - (inst * 0.55 + infra * 0.25 + logistics * 0.20), 0.02, 0.90)
    geo["human_capital"] = human
    geo["market_access"] = _clamp(geo.get("market_access", 0.5) * 0.60 + logistics * 0.40, 0.02, 0.98)

    return geo


def _build_subregions(state_name: str, state_row: dict[str, float | str], scenario_seed: int, idx: int) -> dict[str, dict[str, float | str]]:
    names = ("north", "central", "south")
    subregions: dict[str, dict[str, float | str]] = {}
    base_x = float(state_row.get("coord_x", 50.0))
    base_y = float(state_row.get("coord_y", 50.0))
    base_output = float(state_row.get("output", 1.0))
    base_unemployment = float(state_row.get("unemployment", 0.09))
    base_infra = float(state_row.get("infrastructure", 0.4))
    base_support = float(state_row.get("support_score", 50.0))
    base_unrest = float(state_row.get("unrest_score", 32.0))

    archetype = str(state_row.get("archetype", "agro_periphery"))
    base_human_cap = float(state_row.get("human_capital", 0.45))
    base_pop = float(state_row.get("population", 300_000.0))
    base_resource = float(state_row.get("resource_endowment", 0.5))
    # land_availability is inverse of land_concentration:
    # high concentration → less free land for new buildings.
    base_land_avail = 1.0 - float(state_row.get("land_concentration", 0.5))
    base_geo = state_row.get("geo_profile", {}) if isinstance(state_row.get("geo_profile", {}), dict) else {}

    for j, name in enumerate(names):
        local_noise = _deterministic_noise(scenario_seed, idx * 10 + j, 57)
        share = _clamp(0.33 + local_noise * 0.10, 0.20, 0.45)
        offset_x = (j - 1) * 4.0 + _deterministic_noise(scenario_seed, idx * 10 + j, 59) * 2.0
        offset_y = (1 - j) * 3.0 + _deterministic_noise(scenario_seed, idx * 10 + j, 61) * 2.0
        sub_name = f"{state_name}_{name}"
        sub_pop = max(10_000.0, base_pop * share)
        sub_geo = {}
        if isinstance(base_geo, dict):
            for key, value in base_geo.items():
                try:
                    sub_geo[key] = _clamp(float(value) + local_noise * 0.08, 0.02, 0.98)
                except (TypeError, ValueError):
                    continue
        buildings = seed_buildings_for_subregion(
            subregion_name=sub_name,
            state_archetype=archetype,
            population=sub_pop,
            human_capital=_clamp(base_human_cap + local_noise * 0.05, 0.10, 0.95),
            infrastructure=_clamp(base_infra + local_noise * 0.10, 0.10, 0.95),
            scenario_seed=scenario_seed,
            subregion_idx=idx * 10 + j,
            resource_endowment=_clamp(base_resource + local_noise * 0.05, 0.10, 0.95),
            land_availability=_clamp(base_land_avail + local_noise * 0.05, 0.05, 0.95),
            geo_profile=sub_geo,
        )
        subregions[sub_name] = {
            "name": sub_name,
            "population_share": share,
            "output": max(0.1, base_output * share),
            "unemployment": _clamp(base_unemployment + local_noise * 0.03, 0.02, 0.40),
            "service_quality": _clamp(base_infra + local_noise * 0.10, 0.05, 0.98),
            "support_score": _clamp(base_support + local_noise * 8.0, 0.0, 100.0),
            "unrest_score": _clamp(base_unrest - local_noise * 8.0, 0.0, 100.0),
            "coord_x": _clamp(base_x + offset_x, 0.0, 100.0),
            "coord_y": _clamp(base_y + offset_y, 0.0, 100.0),
            "geo_profile": sub_geo,
            "buildings": buildings,
        }

    total = sum(float(v["population_share"]) for v in subregions.values())
    for row in subregions.values():
        row["population_share"] = float(row["population_share"]) / max(total, 1e-9)
    return subregions


def build_initial_region_state(region_count: int, population: float, scenario_id: str) -> dict[str, Any]:
    count = max(3, min(24, int(region_count)))
    scenario_seed = sum(ord(ch) for ch in scenario_id)
    start_shift = scenario_seed % len(ARCHETYPES)

    weights: list[float] = []
    region_rows: dict[str, dict[str, float | str]] = {}

    for idx in range(count):
        archetype = ARCHETYPES[(idx + start_shift) % len(ARCHETYPES)]
        base = ARCHETYPE_BASE[archetype]
        noise = _deterministic_noise(scenario_seed, idx, 3)
        pop_weight = max(0.2, 1.0 + noise * 0.35)
        weights.append(pop_weight)

        region_row: dict[str, float | str] = {
            "archetype": archetype,
            "resource_endowment": _clamp(base["resource_endowment"] + _deterministic_noise(scenario_seed, idx, 4) * 0.08, 0.15, 0.95),
            "infrastructure": _clamp(base["infrastructure"] + _deterministic_noise(scenario_seed, idx, 5) * 0.08, 0.10, 0.95),
            "institutional_quality": _clamp(base["institutional_quality"] + _deterministic_noise(scenario_seed, idx, 6) * 0.08, 0.10, 0.95),
            "logistics_access": _clamp(base["logistics_access"] + _deterministic_noise(scenario_seed, idx, 7) * 0.08, 0.10, 0.95),
            "human_capital": _clamp(base["human_capital"] + _deterministic_noise(scenario_seed, idx, 8) * 0.08, 0.10, 0.95),
            "land_concentration": _clamp(base["land_concentration"] + _deterministic_noise(scenario_seed, idx, 9) * 0.08, 0.15, 0.90),
            "primary_specialization": base["primary_specialization"],
            "secondary_specialization": base["secondary_specialization"],
            "tertiary_specialization": base["tertiary_specialization"],
            "support_score": 50.0,
            "unrest_score": 32.0,
            "output": 1.0,
            "unemployment": 0.09,
        }
        region_row["geo_profile"] = _derive_geo_profile(archetype, region_row, scenario_seed, idx)
        region_rows[f"state_{idx + 1:02d}"] = region_row

    total_weight = sum(weights)
    for idx, region_name in enumerate(region_rows):
        pop_share = weights[idx] / max(total_weight, 1e-9)
        region_rows[region_name]["population"] = max(10_000.0, population * pop_share)
        region_rows[region_name]["population_share"] = pop_share
        region_rows[region_name]["subregions"] = _build_subregions(region_name, region_rows[region_name], scenario_seed, idx)

    topo = _build_spatial_topology(region_rows, scenario_seed)

    return {
        "region_count": count,
        "regions": region_rows,
        "transport_edges": topo["transport_edges"],
        "mean_route_cost": topo["mean_route_cost"],
        "connectivity_index": topo["connectivity_index"],
    }


def coerce_region_state(prior_state: dict[str, Any]) -> dict[str, Any]:
    raw = prior_state.get("region_state")
    if isinstance(raw, dict) and isinstance(raw.get("regions"), dict):
        regions = raw.get("regions", {})
        if isinstance(regions, dict) and regions:
            first = next(iter(regions.values()))
            if isinstance(first, dict) and "coord_x" in first and "coord_y" in first and "transport_edges" in raw:
                return raw

    region_count = int(prior_state.get("region_count", 6))
    population = float(prior_state.get("population", 1_000_000.0))
    scenario_id = str(prior_state.get("scenario_id", "baseline"))
    return build_initial_region_state(region_count=region_count, population=population, scenario_id=scenario_id)


def update_region_economies(
    prior_state: dict[str, Any],
    total_output: float,
    total_primary: float,
    total_secondary: float,
    total_tertiary: float,
) -> dict[str, Any]:
    region_state = coerce_region_state(prior_state)
    regions_raw = region_state.get("regions", {})
    transport_edges = region_state.get("transport_edges", {}) if isinstance(region_state, dict) else {}
    mean_route_cost = float(region_state.get("mean_route_cost", 0.35)) if isinstance(region_state, dict) else 0.35
    connectivity_index = float(region_state.get("connectivity_index", 0.8)) if isinstance(region_state, dict) else 0.8
    if not isinstance(regions_raw, dict) or not regions_raw:
        return {
            "region_state": region_state,
            "regional_output_gini": 0.0,
            "regional_service_gap_index": 0.0,
            "regional_employment_gap_index": 0.0,
            "regional_representation_gap": 0.0,
            "regional_inequality_index": 0.0,
            "transport_cost_index": 0.0,
            "map_connectivity_index": 0.0,
        }

    equity_bias = _clamp(float(prior_state.get("regional_equity_bias", 0.50)), 0.0, 1.0)
    corruption = _clamp(float(prior_state.get("corruption_signal", 0.3)), 0.0, 1.0)
    national_unemployment = _clamp(float(prior_state.get("unemployment", 0.08)), 0.0, 0.4)
    class_conflict = _clamp(float(prior_state.get("class_conflict_pressure", 0.3)), 0.0, 1.0)

    names = list(regions_raw.keys())
    raw_scores: list[float] = []
    transport_penalties: dict[str, float] = {}

    # Build graph from edge list once per tick.
    graph: dict[str, list[tuple[str, float]]] = {n: [] for n in names}
    if isinstance(transport_edges, dict):
        for key, payload in transport_edges.items():
            if not isinstance(payload, dict) or "|" not in key:
                continue
            left, right = key.split("|", 1)
            if left not in graph or right not in graph:
                continue
            w = max(0.01, float(payload.get("friction", 0.2)))
            graph[left].append((right, w))
            graph[right].append((left, w))

    # Find capital-like core for route-cost penalties.
    capital_name = max(
        names,
        key=lambda n: float(regions_raw[n].get("infrastructure", 0.0)) + float(regions_raw[n].get("institutional_quality", 0.0)),
    )
    route_costs = _shortest_paths(capital_name, graph)
    norm = max(0.05, mean_route_cost)
    for name in names:
        transport_penalties[name] = _clamp(route_costs.get(name, norm * 2.0) / norm, 0.2, 3.0)

    for name in names:
        region = regions_raw[name]
        if not isinstance(region, dict):
            region = {}
        infra = float(region.get("infrastructure", 0.4))
        inst = float(region.get("institutional_quality", 0.4))
        logistic = float(region.get("logistics_access", 0.4))
        resource = float(region.get("resource_endowment", 0.4))
        pop_share = float(region.get("population_share", 0.1))
        distance_penalty = transport_penalties[name]

        efficiency = 0.38 * infra + 0.28 * inst + 0.20 * logistic + 0.10 * resource + (1.0 / distance_penalty) * 0.04
        deprivation = _clamp((1.0 - infra) * 0.5 + (1.0 - inst) * 0.3 + pop_share * 0.2, 0.0, 1.0)
        raw_scores.append(max(0.01, (1.0 - equity_bias) * efficiency + equity_bias * deprivation))

    score_total = sum(raw_scores)
    region_next: dict[str, dict[str, float | str]] = {}
    outputs_pc: list[float] = []
    infra_levels: list[float] = []
    unemployment_levels: list[float] = []
    representation_abs_gap = 0.0

    for idx, name in enumerate(names):
        region = regions_raw[name]
        if not isinstance(region, dict):
            region = {}
        allocation_share = raw_scores[idx] / max(score_total, 1e-9)

        pop = max(1.0, float(region.get("population", 100_000.0)))
        pop_share = float(region.get("population_share", 0.1))
        infra = _clamp(float(region.get("infrastructure", 0.4)), 0.1, 0.95)
        inst = _clamp(float(region.get("institutional_quality", 0.4)), 0.1, 0.95)
        logistics = _clamp(float(region.get("logistics_access", 0.4)), 0.1, 0.95)
        distance_penalty = transport_penalties[name]
        human = _clamp(float(region.get("human_capital", 0.4)), 0.1, 0.95)
        land_conc = _clamp(float(region.get("land_concentration", 0.5)), 0.15, 0.90)

        p_spec = _clamp(float(region.get("primary_specialization", 0.3)), 0.05, 0.8)
        s_spec = _clamp(float(region.get("secondary_specialization", 0.3)), 0.05, 0.8)
        t_spec = _clamp(float(region.get("tertiary_specialization", 0.3)), 0.05, 0.8)
        spec_sum = p_spec + s_spec + t_spec
        p_spec, s_spec, t_spec = p_spec / spec_sum, s_spec / spec_sum, t_spec / spec_sum

        base_output = total_output * allocation_share
        primary_output = total_primary * allocation_share * (0.65 + 0.70 * p_spec)
        secondary_output = total_secondary * allocation_share * (0.65 + 0.70 * s_spec)
        tertiary_output = total_tertiary * allocation_share * (0.65 + 0.70 * t_spec)

        realized_output = max(1.0, ((base_output * 0.45) + (primary_output + secondary_output + tertiary_output) * 0.55) / distance_penalty)

        service_quality = _clamp(0.45 * infra + 0.35 * inst + 0.20 * logistics - corruption * 0.20 - (distance_penalty - 1.0) * 0.05, 0.05, 0.98)
        unemployment = _clamp(
            national_unemployment
            + (0.50 - infra) * 0.06
            + (0.50 - human) * 0.04
            + (0.50 - inst) * 0.03
            + class_conflict * 0.01,
            0.02,
            0.35,
        )
        support_score = _clamp(
            float(region.get("support_score", 50.0))
            + (service_quality - 0.5) * 6.0
            - unemployment * 18.0
            - land_conc * 4.0,
            0.0,
            100.0,
        )
        unrest_score = _clamp(100.0 - support_score + (1.0 - service_quality) * 22.0 + land_conc * 12.0, 0.0, 100.0)

        outputs_pc.append(realized_output / pop)
        infra_levels.append(service_quality)
        unemployment_levels.append(unemployment)
        representation_abs_gap += abs(allocation_share - pop_share)

        region_next[name] = {
            "archetype": str(region.get("archetype", "mixed")),
            "population": pop,
            "population_share": pop_share,
            "allocation_share": allocation_share,
            "distance_penalty": distance_penalty,
            "coord_x": float(region.get("coord_x", 50.0)),
            "coord_y": float(region.get("coord_y", 50.0)),
            "neighbors": list(region.get("neighbors", [])),
            "resource_endowment": float(region.get("resource_endowment", 0.4)),
            "infrastructure": infra,
            "institutional_quality": inst,
            "logistics_access": logistics,
            "human_capital": human,
            "land_concentration": land_conc,
            "geo_profile": region.get("geo_profile", {}),
            "primary_specialization": p_spec,
            "secondary_specialization": s_spec,
            "tertiary_specialization": t_spec,
            "output": realized_output,
            "primary_output": primary_output,
            "secondary_output": secondary_output,
            "tertiary_output": tertiary_output,
            "service_quality": service_quality,
            "unemployment": unemployment,
            "support_score": support_score,
            "unrest_score": unrest_score,
        }

        # Update subregions — run building engine then update social/economic signals.
        sub_raw = region.get("subregions", {})
        subregions: dict[str, dict[str, float | str]] = {}

        # Sector demand signals used by building engine
        _demand_signals = {
            "agriculture": _clamp((total_primary / max(total_output, 1.0)) * 1.5, 0.2, 1.0),
            "energy":      _clamp((total_primary / max(total_output, 1.0)) * 1.2, 0.2, 1.0),
            "manufacturing": _clamp((total_secondary / max(total_output, 1.0)) * 1.5, 0.2, 1.0),
            "construction":  _clamp((total_secondary / max(total_output, 1.0)) * 1.0, 0.2, 1.0),
            "services":      _clamp((total_tertiary / max(total_output, 1.0)) * 1.4, 0.2, 1.0),
        }
        _maintenance_spend = _clamp(
            float(prior_state.get("infrastructure_spend_share", 0.25)) * 0.6, 0.05, 1.0
        )
        _human_cap = float(region.get("human_capital", 0.45))

        if isinstance(sub_raw, dict) and sub_raw:
            share_total = 0.0
            for sub_name, sub in sub_raw.items():
                if not isinstance(sub, dict):
                    continue
                share = _clamp(float(sub.get("population_share", 0.33)), 0.10, 0.70)
                share_total += share
                local_noise = _deterministic_noise(int(pop) % 997, idx * 10 + len(subregions), 73)
                prev_output = max(0.1, float(sub.get("output", realized_output * share)))
                prev_unemployment = _clamp(float(sub.get("unemployment", unemployment)), 0.02, 0.40)
                prev_service = _clamp(float(sub.get("service_quality", service_quality)), 0.05, 0.98)
                prev_support = _clamp(float(sub.get("support_score", support_score)), 0.0, 100.0)
                prev_unrest = _clamp(float(sub.get("unrest_score", unrest_score)), 0.0, 100.0)

                # Run building engine for this subregion
                prev_buildings = sub.get("buildings", [])
                updated_buildings = update_subregion_buildings(
                    buildings=prev_buildings if isinstance(prev_buildings, list) else [],
                    sector_demand_signals=_demand_signals,
                    maintenance_spend=_maintenance_spend,
                    human_capital=_human_cap,
                    prior_state=prior_state,
                ) if prev_buildings else []

                # Aggregate building outputs for this subregion
                bldg_agg = aggregate_subregion_buildings(updated_buildings) if updated_buildings else {}
                bldg_total_output = float(bldg_agg.get("total_output", 0.0))
                bldg_workers = int(bldg_agg.get("total_workers", 0))
                bldg_health = float(bldg_agg.get("health_index", 0.0))
                bldg_research = float(bldg_agg.get("research_output", 0.0))
                bldg_transport = float(bldg_agg.get("transport_modifier", 1.0))

                # Blend building-derived output with top-down allocated output
                blended_output = prev_output * 0.60 + max(realized_output * share, bldg_total_output) * 0.40

                # Sub-region labor: if we have buildings, derive unemployment from them
                sub_pop = max(1.0, pop * share)
                if bldg_workers > 0:
                    participation = 0.65
                    labor_force = max(1.0, sub_pop * participation)
                    sub_unemployment = _clamp(1.0 - bldg_workers / labor_force, 0.02, 0.40)
                else:
                    sub_unemployment = _clamp(prev_unemployment * 0.65 + unemployment * 0.35 + local_noise * 0.02, 0.02, 0.40)

                # Service quality gets a boost from hospitals
                health_boost = _clamp(bldg_health / max(1.0, sub_pop) * 200.0, 0.0, 0.15)
                sub_service = _clamp(prev_service * 0.65 + (service_quality + health_boost) * 0.35 + local_noise * 0.08, 0.05, 0.98)

                subregions[sub_name] = {
                    "name": str(sub.get("name", sub_name)),
                    "population_share": share,
                    "output": max(0.1, blended_output),
                    "unemployment": sub_unemployment,
                    "service_quality": sub_service,
                    "support_score": _clamp(prev_support * 0.65 + support_score * 0.35 + local_noise * 6.0, 0.0, 100.0),
                    "unrest_score": _clamp(prev_unrest * 0.65 + unrest_score * 0.35 - local_noise * 6.0, 0.0, 100.0),
                    "coord_x": _clamp(float(sub.get("coord_x", region_next[name]["coord_x"])) + local_noise * 1.5, 0.0, 100.0),
                    "coord_y": _clamp(float(sub.get("coord_y", region_next[name]["coord_y"])) - local_noise * 1.5, 0.0, 100.0),
                    "geo_profile": sub.get("geo_profile", {}),
                    "buildings": updated_buildings,
                    "building_workers": bldg_workers,
                    "building_research": bldg_research,
                    "building_transport_modifier": bldg_transport,
                }
            norm = max(1e-9, share_total)
            for sub in subregions.values():
                sub["population_share"] = float(sub["population_share"]) / norm
        else:
            subregions = _build_subregions(name, region_next[name], int(pop) % 997, idx)
        region_next[name]["subregions"] = subregions

    service_gap = max(infra_levels) - min(infra_levels) if infra_levels else 0.0
    employment_gap = max(unemployment_levels) - min(unemployment_levels) if unemployment_levels else 0.0
    output_gini = _gini(outputs_pc)
    transport_cost_index = _clamp(mean_route_cost * (2.0 - connectivity_index), 0.0, 2.0)

    # Bottom-up national feedback: aggregate state/subregion outcomes back into macro signals.
    national_pop = 0.0
    national_output = 0.0
    unemployment_sum = 0.0
    support_sum = 0.0
    unrest_sum = 0.0
    service_sum = 0.0
    for state_row in region_next.values():
        pop = max(1.0, float(state_row.get("population", 1.0)))
        sub = state_row.get("subregions", {})
        if isinstance(sub, dict) and sub:
            sub_output = 0.0
            sub_unemployment = 0.0
            sub_support = 0.0
            sub_unrest = 0.0
            sub_service = 0.0
            for sub_row in sub.values():
                if not isinstance(sub_row, dict):
                    continue
                share = _clamp(float(sub_row.get("population_share", 0.0)), 0.0, 1.0)
                sub_output += max(0.0, float(sub_row.get("output", 0.0)))
                sub_unemployment += _clamp(float(sub_row.get("unemployment", state_row.get("unemployment", 0.08))), 0.02, 0.40) * share
                sub_support += _clamp(float(sub_row.get("support_score", state_row.get("support_score", 50.0))), 0.0, 100.0) * share
                sub_unrest += _clamp(float(sub_row.get("unrest_score", state_row.get("unrest_score", 35.0))), 0.0, 100.0) * share
                sub_service += _clamp(float(sub_row.get("service_quality", state_row.get("service_quality", 0.5))), 0.05, 0.98) * share

            state_output = max(1.0, sub_output) if sub_output > 0.0 else max(1.0, float(state_row.get("output", 1.0)))
            state_unemployment = _clamp(sub_unemployment if sub_unemployment > 0.0 else float(state_row.get("unemployment", 0.08)), 0.02, 0.40)
            state_support = _clamp(sub_support if sub_support > 0.0 else float(state_row.get("support_score", 50.0)), 0.0, 100.0)
            state_unrest = _clamp(sub_unrest if sub_unrest > 0.0 else float(state_row.get("unrest_score", 35.0)), 0.0, 100.0)
            state_service = _clamp(sub_service if sub_service > 0.0 else float(state_row.get("service_quality", 0.5)), 0.05, 0.98)
        else:
            state_output = max(1.0, float(state_row.get("output", 1.0)))
            state_unemployment = _clamp(float(state_row.get("unemployment", 0.08)), 0.02, 0.40)
            state_support = _clamp(float(state_row.get("support_score", 50.0)), 0.0, 100.0)
            state_unrest = _clamp(float(state_row.get("unrest_score", 35.0)), 0.0, 100.0)
            state_service = _clamp(float(state_row.get("service_quality", 0.5)), 0.05, 0.98)

        national_pop += pop
        national_output += state_output
        unemployment_sum += state_unemployment * pop
        support_sum += state_support * pop
        unrest_sum += state_unrest * pop
        service_sum += state_service * pop

    avg_unemployment = unemployment_sum / max(1.0, national_pop)
    avg_support = support_sum / max(1.0, national_pop)
    avg_unrest = unrest_sum / max(1.0, national_pop)
    avg_service = service_sum / max(1.0, national_pop)

    feedback_strength = _clamp(float(prior_state.get("regional_feedback_strength", 0.45)), 0.0, 1.0)
    production_feedback = max(1.0, min(total_output, total_output * (1.0 - feedback_strength) + national_output * feedback_strength))
    unemployment_feedback = _clamp(
        national_unemployment * (1.0 - feedback_strength) + avg_unemployment * feedback_strength,
        0.02,
        0.40,
    )
    trust_feedback = _clamp(
        float(prior_state.get("trust", 50.0)) * (1.0 - feedback_strength) + avg_support * feedback_strength,
        0.0,
        100.0,
    )
    unrest_feedback = _clamp(
        float(prior_state.get("unrest", 35.0)) * (1.0 - feedback_strength) + avg_unrest * feedback_strength,
        0.0,
        100.0,
    )
    service_feedback = _clamp(
        float(prior_state.get("service_perf", 0.60)) * (1.0 - feedback_strength) + avg_service * feedback_strength,
        0.05,
        0.98,
    )

    return {
        "region_state": {
            "region_count": int(region_state.get("region_count", len(region_next))),
            "regions": region_next,
            "transport_edges": transport_edges,
            "mean_route_cost": mean_route_cost,
            "connectivity_index": connectivity_index,
        },
        "regional_output_gini": output_gini,
        "regional_service_gap_index": service_gap,
        "regional_employment_gap_index": employment_gap,
        "regional_representation_gap": representation_abs_gap,
        "regional_inequality_index": output_gini,
        "regional_average_unrest": sum(float(r["unrest_score"]) for r in region_next.values()) / max(1, len(region_next)),
        "transport_cost_index": transport_cost_index,
        "map_connectivity_index": _clamp(connectivity_index, 0.0, 1.0),
        "mean_route_cost": mean_route_cost,
        "regional_output_total": national_output,
        "production": production_feedback,
        "unemployment": unemployment_feedback,
        "trust": trust_feedback,
        "unrest": unrest_feedback,
        "service_perf": service_feedback,
    }
