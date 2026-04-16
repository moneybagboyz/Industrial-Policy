"""Sector network simulation for primary/secondary/tertiary supply chains."""

from __future__ import annotations

from typing import Any

from src.econ.building_engine import national_building_aggregates
from src.econ.regional_profiles import update_region_economies

SECTOR_NAMES = ["agriculture", "energy", "manufacturing", "construction", "services"]

SECTOR_SHARES = {
    "agriculture": 0.16,
    "energy": 0.12,
    "manufacturing": 0.28,
    "construction": 0.12,
    "services": 0.32,
}

FINAL_DEMAND_SHARES = {
    "agriculture": 0.20,
    "energy": 0.10,
    "manufacturing": 0.28,
    "construction": 0.12,
    "services": 0.30,
}

IMPORT_DEPENDENCY = {
    "agriculture": 0.15,
    "energy": 0.35,
    "manufacturing": 0.40,
    "construction": 0.30,
    "services": 0.18,
}

# coeff[j] is units of sector j required for one unit of sector i output.
INPUT_COEFFS: dict[str, dict[str, float]] = {
    "agriculture": {"energy": 0.14, "services": 0.08},
    "energy": {"manufacturing": 0.10, "services": 0.08},
    "manufacturing": {"energy": 0.26, "agriculture": 0.12, "services": 0.12},
    "construction": {"manufacturing": 0.30, "energy": 0.18, "services": 0.10},
    "services": {"energy": 0.10, "manufacturing": 0.10},
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _default_sector_state(prior_state: dict[str, Any]) -> dict[str, dict[str, float]]:
    total_capacity = max(float(prior_state.get("capacity_output", 100.0)), 1.0)
    total_inventory = max(float(prior_state.get("inventory", 10.0)), 0.0)
    total_demand = max(float(prior_state.get("demand", 95.0)), 1.0)
    base_price = max(float(prior_state.get("price", 100.0)), 1.0)
    base_prod = max(float(prior_state.get("production", total_capacity * 0.9)), 1.0)

    sector_state: dict[str, dict[str, float]] = {}
    for name in SECTOR_NAMES:
        share = SECTOR_SHARES[name]
        sector_state[name] = {
            "capacity": total_capacity * share,
            "inventory": total_inventory * share,
            "demand": total_demand * FINAL_DEMAND_SHARES[name],
            "price": base_price,
            "output": base_prod * share,
            "import_dependency": IMPORT_DEPENDENCY[name],
            "labor_intensity": 1.0 if name in {"agriculture", "construction", "services"} else 0.8,
            "skill_intensity": 0.9 if name in {"manufacturing", "services", "energy"} else 0.6,
        }
    return sector_state


def _coerce_sector_state(prior_state: dict[str, Any]) -> dict[str, dict[str, float]]:
    raw = prior_state.get("sector_state")
    if not isinstance(raw, dict):
        return _default_sector_state(prior_state)

    state = _default_sector_state(prior_state)
    for name in SECTOR_NAMES:
        candidate = raw.get(name)
        if isinstance(candidate, dict):
            for key in ("capacity", "inventory", "demand", "price", "output", "import_dependency", "labor_intensity", "skill_intensity"):
                if key in candidate:
                    state[name][key] = float(candidate[key])
    return state


def simulate_sector_network(prior_state: dict[str, Any]) -> dict[str, Any]:
    sector_state = _coerce_sector_state(prior_state)
    exports_shock = max(0.1, float(prior_state.get("trade_shock_exports", 1.0)))
    imports_shock = max(0.1, float(prior_state.get("trade_shock_imports", 1.0)))
    fx_delta = max(0.0, float(prior_state.get("fx_delta", 0.0)))
    unemployment = float(prior_state.get("unemployment", 0.08))
    spend_ratio = float(prior_state.get("spend_ratio", 0.205))
    tax_ratio = float(prior_state.get("tax_ratio", 0.20))
    infrastructure_spend_share = _clamp(float(prior_state.get("infrastructure_spend_share", 0.25)), 0.0, 0.80)
    industrial_policy_bias = _clamp(float(prior_state.get("industrial_policy_bias", 0.50)), 0.0, 1.0)
    food_price_stabilization = _clamp(float(prior_state.get("food_price_stabilization", 0.40)), 0.0, 1.0)

    available_supply: dict[str, float] = {}
    for name in SECTOR_NAMES:
        s = sector_state[name]
        domestic_stock = max(0.0, float(s["inventory"]) + float(s["output"]))
        imported_stock = max(0.0, domestic_stock * float(s["import_dependency"]) * imports_shock * (1.0 - fx_delta * 0.5))
        available_supply[name] = domestic_stock + imported_stock

    outputs: dict[str, float] = {}
    shortages: dict[str, float] = {}
    inventories_next: dict[str, float] = {}
    sector_prices_next: dict[str, float] = {}

    demand_total_anchor = max(float(prior_state.get("household_demand_proxy", 25.0)), 1.0) * 4.0

    for name in SECTOR_NAMES:
        s = sector_state[name]
        capacity = max(0.1, float(s["capacity"]))
        required = INPUT_COEFFS.get(name, {})

        input_limit = capacity
        for input_name, coeff in required.items():
            if coeff <= 0.0:
                continue
            input_limit = min(input_limit, available_supply[input_name] / coeff)

        output = max(0.0, min(capacity, input_limit))

        demand_base = max(0.1, demand_total_anchor * FINAL_DEMAND_SHARES[name])
        if name in {"services", "construction"}:
            demand_base *= 1.0 + spend_ratio * 0.6
        if name == "construction":
            demand_base *= 1.0 + infrastructure_spend_share * 0.5
        if name == "manufacturing":
            demand_base *= 1.0 + industrial_policy_bias * 0.25
        if name in {"manufacturing", "energy"}:
            demand_base *= 1.0 - tax_ratio * 0.2
        if name == "agriculture":
            demand_base *= 1.0 + max(0.0, unemployment - 0.07) * 0.6

        available_for_final = float(s["inventory"]) + output
        shortage = max(0.0, demand_base - available_for_final)
        inventory_next = max(0.0, available_for_final - demand_base)

        shortage_ratio = shortage / max(demand_base, 1.0)
        cost_push = fx_delta * float(s["import_dependency"]) * 0.4
        price_growth = _clamp(shortage_ratio * 0.22 + cost_push + max(0.0, unemployment - 0.08) * 0.02, -0.05, 0.18)
        if name == "agriculture":
            price_growth *= 1.0 - food_price_stabilization * 0.45
        price_next = max(10.0, float(s["price"]) * (1.0 + price_growth))

        outputs[name] = output
        shortages[name] = shortage
        inventories_next[name] = inventory_next
        sector_prices_next[name] = price_next

    total_output = sum(outputs.values())
    total_capacity = sum(max(0.1, float(sector_state[n]["capacity"])) for n in SECTOR_NAMES)
    total_demand = sum(max(0.1, demand_total_anchor * FINAL_DEMAND_SHARES[n]) for n in SECTOR_NAMES)
    total_shortage = sum(shortages.values())

    price_index = 0.0
    for name in SECTOR_NAMES:
        price_index += sector_prices_next[name] * FINAL_DEMAND_SHARES[name]

    output_prev = max(1.0, sum(max(0.1, float(sector_state[n]["output"])) for n in SECTOR_NAMES))
    output_growth = (total_output / output_prev) - 1.0

    exports_weighted = (outputs["agriculture"] * 0.35 + outputs["energy"] * 0.25 + outputs["manufacturing"] * 0.30 + outputs["services"] * 0.10)
    imports_weighted = (
        outputs["manufacturing"] * float(sector_state["manufacturing"]["import_dependency"]) * 0.6
        + outputs["energy"] * float(sector_state["energy"]["import_dependency"]) * 0.7
        + outputs["services"] * float(sector_state["services"]["import_dependency"]) * 0.2
    )
    prev_structural_exports = max(1.0, float(prior_state.get("structural_exports", 9_000_000_000.0)))
    prev_structural_imports = max(1.0, float(prior_state.get("structural_imports", 10_000_000_000.0)))
    export_mix_effect = (exports_weighted / max(total_output, 1.0)) - 0.20
    import_mix_effect = (imports_weighted / max(total_output, 1.0)) - 0.10
    structural_exports_next = prev_structural_exports * (1.0 + _clamp(output_growth * 0.18 + export_mix_effect * 0.04, -0.025, 0.03))
    structural_imports_next = prev_structural_imports * (
        1.0
        + _clamp((total_demand / max(total_output, 1.0) - 1.0) * 0.06 + import_mix_effect * 0.03 + fx_delta * 0.05, -0.02, 0.04)
    )

    sector_state_next: dict[str, dict[str, float]] = {}
    for name in SECTOR_NAMES:
        s = sector_state[name]
        cap = max(0.1, float(s["capacity"]))
        investment_signal = max(0.0, outputs[name] / cap - 0.92)
        policy_boost = 0.0
        if name == "construction":
            policy_boost += infrastructure_spend_share * 0.010
        if name == "manufacturing":
            policy_boost += industrial_policy_bias * 0.012
        new_capacity = max(0.1, cap * (1.0 + investment_signal * 0.02 + policy_boost - 0.004))
        sector_state_next[name] = {
            "capacity": new_capacity,
            "inventory": inventories_next[name],
            "demand": max(0.1, demand_total_anchor * FINAL_DEMAND_SHARES[name]),
            "price": sector_prices_next[name],
            "output": outputs[name],
            "import_dependency": float(s["import_dependency"]),
            "labor_intensity": float(s["labor_intensity"]),
            "skill_intensity": float(s["skill_intensity"]),
        }

    # Pull building-level aggregates to inform sector capacity and research.
    region_state = prior_state.get("region_state", {})
    bldg_nat = national_building_aggregates(region_state) if isinstance(region_state, dict) else {}
    bldg_sector_output = bldg_nat.get("sector_output", {})
    bldg_total_workers = int(bldg_nat.get("total_workers", 0))
    bldg_research = float(bldg_nat.get("research_output", 0.0))
    bldg_transport_mod = float(bldg_nat.get("transport_modifier", 1.0))
    bldg_owner_output = bldg_nat.get("owner_output", {})

    # Blend building-derived sector outputs into simulated outputs (40% weight).
    building_blend = 0.40
    for sector_name in outputs:
        bldg_out = float(bldg_sector_output.get(sector_name, 0.0))
        if bldg_out > 0.0:
            outputs[sector_name] = outputs[sector_name] * (1.0 - building_blend) + bldg_out * building_blend

    total_output = sum(outputs.values())

    regional_patch = update_region_economies(
        prior_state=prior_state,
        total_output=total_output,
        total_primary=outputs["agriculture"] + outputs["energy"],
        total_secondary=outputs["manufacturing"] + outputs["construction"],
        total_tertiary=outputs["services"],
    )

    return {
        "sector_state": sector_state_next,
        "production": total_output,
        "capacity_output": total_capacity,
        "demand": total_demand,
        "inventory": sum(inventories_next.values()),
        "unmet_demand": total_shortage,
        "demand_gap": (total_demand - total_output) / max(total_capacity, 1.0),
        "cost_delta": (price_index / max(float(prior_state.get("price", 100.0)), 1.0) - 1.0) * 0.35,
        "sector_price_index": price_index,
        "prod_growth": _clamp(output_growth * 0.25, -0.05, 0.05),
        "structural_exports": max(1.0, structural_exports_next),
        "structural_imports": max(1.0, structural_imports_next),
        "sector_output_primary": outputs["agriculture"] + outputs["energy"],
        "sector_output_secondary": outputs["manufacturing"] + outputs["construction"],
        "sector_output_tertiary": outputs["services"],
        "sector_shortage_primary": shortages["agriculture"] + shortages["energy"],
        "sector_shortage_secondary": shortages["manufacturing"] + shortages["construction"],
        "sector_shortage_tertiary": shortages["services"],
        "sector_price_primary": (sector_prices_next["agriculture"] + sector_prices_next["energy"]) / 2.0,
        "sector_price_secondary": (sector_prices_next["manufacturing"] + sector_prices_next["construction"]) / 2.0,
        "sector_price_tertiary": sector_prices_next["services"],
        "agriculture_output": outputs["agriculture"],
        "energy_output": outputs["energy"],
        "manufacturing_output": outputs["manufacturing"],
        "construction_output": outputs["construction"],
        "services_output": outputs["services"],
        "agriculture_price": sector_prices_next["agriculture"],
        "energy_price": sector_prices_next["energy"],
        "manufacturing_price": sector_prices_next["manufacturing"],
        "construction_price": sector_prices_next["construction"],
        "services_price": sector_prices_next["services"],
        "building_total_workers": bldg_total_workers,
        "building_research_output": bldg_research,
        "building_transport_modifier": bldg_transport_mod,
        "building_owner_output_capitalist": float(bldg_owner_output.get("capitalist", 0.0)),
        "building_owner_output_state": float(bldg_owner_output.get("state", 0.0)),
        "building_owner_output_cooperative": float(bldg_owner_output.get("cooperative", 0.0)),
        "building_owner_output_informal": float(bldg_owner_output.get("informal", 0.0)),
        **regional_patch,
    }
