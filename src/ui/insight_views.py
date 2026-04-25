"""High-level insight views for easier gameplay interpretation."""

from __future__ import annotations

from typing import Any

from src.econ.commodity_registry import COMMODITY_CATALOG, STRATEGIC_COMMODITIES
from src.econ.logistics_network import (
    aggregate_region_stocks,
    corridor_summary,
    estimate_region_demand,
    top_shortfalls,
)


def _risk_bucket(value: float, low: float, medium: float, high: float) -> str:
    if value <= low:
        return "Low"
    if value <= medium:
        return "Guarded"
    if value <= high:
        return "High"
    return "Critical"


def build_executive_overview_rows(state: dict[str, Any]) -> list[tuple[str, str]]:
    debt = float(state.get("debt", 0.0))
    gdp_m = max(float(state.get("nominal_gdp_monthly", 1.0)), 1.0)
    debt_gdp = debt / (gdp_m * 12.0)
    unrest = float(state.get("unrest", 35.0))
    legitimacy = float(state.get("legitimacy", 50.0))
    shortages = float(state.get("goods_shortage_pressure", 0.2))
    ext = float(state.get("external_stress", 0.2))
    failure = float(state.get("state_failure_risk", 0.1))
    victory = float(state.get("victory_progress", 0.0))

    risk_score = min(1.0, 0.25 * debt_gdp + 0.30 * (unrest / 100.0) + 0.20 * shortages + 0.15 * ext + 0.10 * failure)
    momentum = "Improving" if legitimacy >= 55 and unrest <= 45 else "Fragile" if legitimacy >= 40 else "Destabilizing"

    return [
        ("Regime Stability", f"{momentum} ({_risk_bucket(unrest, 30.0, 50.0, 70.0)})"),
        ("Debt/GDP", f"{debt_gdp * 100:.1f}% ({_risk_bucket(debt_gdp, 0.6, 0.9, 1.2)})"),
        ("Supply Pressure", f"{shortages:.3f} ({_risk_bucket(shortages, 0.20, 0.40, 0.60)})"),
        ("External Stress", f"{ext:.3f} ({_risk_bucket(ext, 0.20, 0.40, 0.60)})"),
        ("Failure Risk", f"{failure:.3f} ({_risk_bucket(failure, 0.20, 0.45, 0.70)})"),
        ("Victory Progress", f"{victory * 100:.1f}%"),
        ("Headline", f"Legitimacy {legitimacy:.1f} | Unrest {unrest:.1f} | Risk Score {risk_score * 100:.1f}"),
    ]


def build_state_explorer_rows(state: dict[str, Any], top_n: int = 8) -> list[tuple[str, str]]:
    region_state = state.get("region_state")
    if not isinstance(region_state, dict):
        return [("info", "No region state available")]
    regions = region_state.get("regions")
    if not isinstance(regions, dict) or not regions:
        return [("info", "No regions found")]

    scope_type = str(state.get("scope_type", "nation"))
    scope_key = str(state.get("scope_key", ""))

    rows: list[tuple[str, str]] = []
    region_data: list[tuple[str, float, float, float, float, float]] = []
    if scope_type == "state" and scope_key in regions and isinstance(regions[scope_key], dict):
        subregions = regions[scope_key].get("subregions", {})
        if isinstance(subregions, dict) and subregions:
            parent_pop = max(float(regions[scope_key].get("population", 1.0)), 1.0)
            for name, payload in subregions.items():
                if not isinstance(payload, dict):
                    continue
                pop_share = float(payload.get("population_share", 0.33))
                output = float(payload.get("output", 0.0))
                pop = max(1.0, parent_pop * pop_share)
                unrest = float(payload.get("unrest_score", 0.0))
                support = float(payload.get("support_score", 0.0))
                service = float(payload.get("service_quality", 0.0))
                unemployment = float(payload.get("unemployment", 0.0))
                output_pc = output / pop
                region_data.append((name, unrest, support, service, unemployment, output_pc))
            rows.append(("Scope", f"Subregions inside {scope_key}"))
    else:
        for name, payload in regions.items():
            if not isinstance(payload, dict):
                continue
            output = float(payload.get("output", 0.0))
            pop = max(float(payload.get("population", 1.0)), 1.0)
            unrest = float(payload.get("unrest_score", 0.0))
            support = float(payload.get("support_score", 0.0))
            service = float(payload.get("service_quality", 0.0))
            unemployment = float(payload.get("unemployment", 0.0))
            output_pc = output / pop
            region_data.append((name, unrest, support, service, unemployment, output_pc))
        rows.append(("Scope", "State-level regions"))

    if not region_data:
        return [("info", "No valid region payloads")]

    highest_unrest = sorted(region_data, key=lambda x: x[1], reverse=True)[:top_n]
    strongest_support = sorted(region_data, key=lambda x: x[2], reverse=True)[:3]

    rows.append(("Top Risk Regions", "(sorted by unrest)"))
    for idx, (name, unrest, support, service, unemp, output_pc) in enumerate(highest_unrest, start=1):
        rows.append(
            (
                f"risk_{idx:02d}_{name}",
                f"unrest={unrest:.1f} support={support:.1f} service={service:.2f} unemp={unemp:.3f} out_pc={output_pc:.6f}",
            )
        )

    rows.append(("Top Support Regions", "(political anchors)"))
    for idx, (name, unrest, support, service, unemp, output_pc) in enumerate(strongest_support, start=1):
        rows.append(
            (
                f"anchor_{idx:02d}_{name}",
                f"support={support:.1f} unrest={unrest:.1f} service={service:.2f} out_pc={output_pc:.6f}",
            )
        )

    return rows


def build_building_inventory_rows(state: dict[str, Any], max_rows: int = 40) -> list[tuple[str, str]]:
    """Aggregate buildings across all subregions into a display table."""
    region_state = state.get("region_state")
    if not isinstance(region_state, dict):
        return [("info", "No region state available")]
    regions = region_state.get("regions", {})
    if not isinstance(regions, dict) or not regions:
        return [("info", "No regions found")]

    scope_type = str(state.get("scope_type", "nation"))
    scope_key = str(state.get("scope_key", ""))
    scope_parent = str(state.get("scope_parent", ""))

    # Collect all buildings relevant to the current scope.
    all_buildings: list[dict] = []
    for region_name, region_data in regions.items():
        if not isinstance(region_data, dict):
            continue
        # State scope: only buildings inside that state.
        if scope_type == "state" and region_name != scope_key:
            continue
        # Region scope: only buildings inside the specific subregion.
        if scope_type == "region" and region_name != scope_parent:
            continue
        subregions = region_data.get("subregions", {})
        for sub_name, sub_data in (subregions.items() if isinstance(subregions, dict) else {}.items()):
            if not isinstance(sub_data, dict):
                continue
            if scope_type == "region" and sub_name != scope_key:
                continue
            for bldg in sub_data.get("buildings", []):
                if isinstance(bldg, dict):
                    all_buildings.append({**bldg, "_region": region_name, "_subregion": sub_name})

    if not all_buildings:
        return [("info", "No buildings seeded yet — region_state may still be initialising")]

    # Summarise by archetype.
    from collections import defaultdict
    summary: dict[str, dict] = defaultdict(lambda: {"count": 0, "workers": 0.0, "output": 0.0, "condition": 0.0, "utilization": 0.0})
    for bldg in all_buildings:
        t = str(bldg.get("type", bldg.get("building_type", "unknown")))
        summary[t]["count"] += 1
        summary[t]["workers"] += float(bldg.get("workers", 0.0))
        summary[t]["output"] += float(bldg.get("output", 0.0))
        summary[t]["condition"] += float(bldg.get("condition", 0.0))
        summary[t]["utilization"] += float(bldg.get("utilization", 0.0))

    rows: list[tuple[str, str]] = [
        ("Total Buildings", str(len(all_buildings))),
        ("Total Workers", f"{sum(s['workers'] for s in summary.values()):,.0f}"),
        ("Total Output", f"{sum(s['output'] for s in summary.values()):.4f}"),
        ("─── By Type ───", "count | workers | output | avg_cond | avg_util"),
    ]
    for btype, s in sorted(summary.items(), key=lambda kv: kv[1]["output"], reverse=True)[:max_rows]:
        n = max(s["count"], 1)
        rows.append((
            btype,
            f"n={s['count']}  workers={s['workers']:,.0f}  out={s['output']:.4f}  "
            f"cond={s['condition']/n:.2f}  util={s['utilization']/n:.2f}",
        ))
    return rows


def build_construction_pipeline_rows(state: dict[str, Any]) -> list[tuple[str, str]]:
    """Display the current construction queue with progress and expected completion."""
    queue = state.get("construction_queue", [])
    if not isinstance(queue, list) or not queue:
        return [("info", "Construction queue is empty")]

    rows: list[tuple[str, str]] = [
        ("Queue Length", str(len(queue))),
        ("Completions (total)", str(state.get("construction_completion_count", 0))),
        ("─── Active Projects ───", "months_left | type | target | owner | cost_ratio"),
    ]
    for item in sorted(queue, key=lambda x: int(x.get("remaining_months", 999)) if isinstance(x, dict) else 999):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "unnamed"))
        months = int(item.get("remaining_months", 0))
        btype = str(item.get("type", "—"))
        target_r = str(item.get("target_region", "—"))
        target_s = str(item.get("target_subregion", "—"))
        owner = str(item.get("owner_class", "—"))
        cost_ratio = float(item.get("cost_ratio", 0.0))
        rows.append((
            name,
            f"{months}mo  type={btype}  {target_r}/{target_s}  owner={owner}  cost={cost_ratio:.4f}",
        ))
    return rows


def build_policy_dashboard_rows(state: dict[str, Any]) -> list[tuple[str, str]]:
    """Active policies with vitality, formal vs realized values, and bandwidth."""
    rows: list[tuple[str, str]] = [
        ("Bandwidth",   str(state.get("policy_bandwidth", "—"))),
        ("Credibility", f"{float(state.get('policy_credibility', 1.0)):.2f}"),
        ("Shadow Gap",  f"{float(state.get('policy_shadow_gap', 0.0)):.3f}"),
        ("Grievance",   f"{float(state.get('policy_grievance', 0.0)):.1f}"),
        ("Active Trad.", str(state.get("active_tradition", "—"))),
        ("─── Active Policies ───", "vitality | formal → realized | family"),
    ]
    active = state.get("active_policies", [])
    if not isinstance(active, list) or not active:
        rows.append(("(none)", ""))
        return rows
    for pol in active:
        if not isinstance(pol, dict):
            continue
        name     = str(pol.get("name", "?"))
        vitality = float(pol.get("vitality", 0.0))
        formal   = float(pol.get("formal_value", 0.0))
        realized = float(pol.get("realized_value", 0.0))
        family   = str(pol.get("family", "?"))
        rows.append((name, f"vit={vitality:.0f}  {formal:.2f}→{realized:.2f}  [{family}]"))
    return rows


def build_tradition_influence_rows(state: dict[str, Any]) -> list[tuple[str, str]]:
    """Ideological tradition influence scores and dominant tradition."""
    influence: dict[str, float] = state.get("tradition_influence", {})
    active = str(state.get("active_tradition", "—"))
    rows: list[tuple[str, str]] = [
        ("Dominant Tradition", active),
        ("─── Tradition Scores ───", "influence"),
    ]
    if not isinstance(influence, dict) or not influence:
        rows.append(("(no data)", ""))
        return rows
    for trad, score in sorted(influence.items(), key=lambda x: -x[1]):
        marker = " ◄" if trad == active else ""
        rows.append((trad, f"{score:.3f}{marker}"))
    return rows


def build_policy_graveyard_rows(state: dict[str, Any]) -> list[tuple[str, str]]:
    """Repealed/collapsed policies with remaining grievance."""
    graveyard = state.get("policy_graveyard", [])
    rows: list[tuple[str, str]] = [
        ("Graveyard Entries", str(len(graveyard) if isinstance(graveyard, list) else 0)),
        ("─── Buried Policies ───", "grievance | reason | ticks_remaining"),
    ]
    if not isinstance(graveyard, list) or not graveyard:
        rows.append(("(empty)", ""))
        return rows
    for entry in graveyard:
        if not isinstance(entry, dict):
            continue
        name    = str(entry.get("name", "?"))
        griev   = float(entry.get("grievance", 0.0))
        reason  = str(entry.get("burial_reason", "?"))
        ticks   = int(entry.get("scar_ticks_remaining", 0))
        rows.append((name, f"griev={griev:.1f}  {reason}  {ticks}ticks"))
    return rows


def build_consequence_queue_rows(state: dict[str, Any]) -> list[tuple[str, str]]:
    """Pending and recently revealed unintended consequences."""
    pending  = state.get("consequence_queue", [])
    revealed = state.get("consequence_revealed", [])
    rows: list[tuple[str, str]] = [
        ("Pending",  str(len(pending) if isinstance(pending, list) else 0)),
        ("Revealed", str(len(revealed) if isinstance(revealed, list) else 0)),
        ("─── Pending Consequences ───", "policy | due_tick | effects"),
    ]
    if not isinstance(pending, list) or not pending:
        rows.append(("(none pending)", ""))
    else:
        for item in pending:
            if not isinstance(item, dict):
                continue
            pname   = str(item.get("policy_name", "?"))
            due     = int(item.get("due_tick", 0))
            effects = str(item.get("effects", {}))[:60]
            rows.append((pname, f"due@{due}  {effects}"))
    if isinstance(revealed, list) and revealed:
        rows.append(("─── Recently Revealed ───", "policy | effects"))
        for item in revealed:
            if not isinstance(item, dict):
                continue
            pname   = str(item.get("policy_name", "?"))
            effects = str(item.get("effects", {}))[:60]
            rows.append((pname, effects))
    return rows


def _collect_national_commodity_totals(region_state: dict[str, Any]) -> tuple[dict[str, float], dict[str, float]]:
    """Return (stock_totals, demand_totals) across all regions."""
    regions = region_state.get("regions", {}) if isinstance(region_state, dict) else {}
    if not isinstance(regions, dict):
        return {}, {}

    stock_totals: dict[str, float] = {}
    demand_totals: dict[str, float] = {}

    for region_name, payload in regions.items():
        if not isinstance(payload, dict):
            continue
        pop = max(1.0, float(payload.get("population", 1.0)))
        region_stocks = aggregate_region_stocks(payload)
        for cid, amount in region_stocks.items():
            stock_totals[cid] = stock_totals.get(cid, 0.0) + max(0.0, float(amount))
        for cid in COMMODITY_CATALOG:
            demand_totals[cid] = demand_totals.get(cid, 0.0) + estimate_region_demand(pop, cid)

    return stock_totals, demand_totals


def _storage_days(stock: float, demand_per_tick: float) -> float:
    if demand_per_tick <= 1e-9:
        return 365.0
    return min(365.0, stock / demand_per_tick * 30.0)


def build_commodity_flow_rows(state: dict[str, Any], top_n: int = 10) -> list[tuple[str, str]]:
    """Commodity flow sheet: stocks, deficits, and import dependency anchors."""
    region_state = state.get("region_state", {})
    logistics = region_state.get("logistics_state", {}) if isinstance(region_state, dict) else {}
    stocks, demand = _collect_national_commodity_totals(region_state if isinstance(region_state, dict) else {})

    deficits = top_shortfalls(logistics, n=top_n)
    sorted_stock = sorted(stocks.items(), key=lambda x: -x[1])[:top_n]

    rows: list[tuple[str, str]] = [
        ("Tracked Commodities", str(len(COMMODITY_CATALOG))),
        ("Strategic Commodities", str(len(STRATEGIC_COMMODITIES))),
        ("Flow Snapshot", "stocks + deficits + dependency"),
        ("─── Top National Stocks ───", "commodity | stock | est_storage_days"),
    ]
    if not sorted_stock:
        rows.append(("(none)", "No commodity stocks recorded yet"))
    for cid, amount in sorted_stock:
        rows.append((
            cid,
            f"stock={amount:.4f}  est_days={_storage_days(amount, demand.get(cid, 0.0)):.1f}",
        ))

    rows.append(("─── Top National Deficits ───", "commodity | deficit"))
    if not deficits:
        rows.append(("(none)", "No deficit entries yet"))
    for row in deficits:
        cid = str(row.get("commodity", "?"))
        deficit = float(row.get("deficit", 0.0))
        rows.append((cid, f"deficit={deficit:.4f}"))

    rows.append(("─── Strategic Import Dependency ───", "commodity | importability | storage_days"))
    for cid in sorted(STRATEGIC_COMMODITIES):
        importability = float(COMMODITY_CATALOG.get(cid, {}).get("importability", 0.0))
        amount = stocks.get(cid, 0.0)
        rows.append((
            cid,
            f"importability={importability:.2f}  est_days={_storage_days(amount, demand.get(cid, 0.0)):.1f}",
        ))
    return rows


def build_logistics_chokepoint_rows(state: dict[str, Any], top_n: int = 12) -> list[tuple[str, str]]:
    """Logistics chokepoint sheet: corridor utilization and congestion."""
    region_state = state.get("region_state", {})
    logistics = region_state.get("logistics_state", {}) if isinstance(region_state, dict) else {}
    rows = [
        ("Chokepoint View", "corridor congestion and throughput"),
        ("Constrained Corridors", str(len(logistics.get("congested_corridors", [])) if isinstance(logistics, dict) else 0)),
        ("─── Top Corridors by Congestion ───", "edge | util | congestion | flow | friction"),
    ]

    summary = corridor_summary(logistics if isinstance(logistics, dict) else {})[:top_n]
    if not summary:
        rows.append(("(none)", "No corridor metrics available"))
        return rows

    for entry in summary:
        edge = str(entry.get("edge", "?"))
        util = float(entry.get("utilization", 0.0))
        cong = float(entry.get("congestion_ratio", 0.0))
        flow = float(entry.get("total_flow", 0.0))
        friction = float(entry.get("friction", 0.0))
        rows.append((edge, f"util={util:.3f}  cong={cong:.3f}  flow={flow:.4f}  friction={friction:.3f}"))
    return rows


def build_shortage_class_impact_rows(state: dict[str, Any]) -> list[tuple[str, str]]:
    """Shortages and class-impact sheet: scarcity burdens plus adaptation channels."""
    sw = float(state.get("scarcity_burden_workers", 0.0))
    sp = float(state.get("scarcity_burden_professionals", 0.0))
    sc = float(state.get("scarcity_burden_capitalists", 0.0))
    si = float(state.get("scarcity_burden_informal", 0.0))
    burdens = {
        "workers": sw,
        "professionals": sp,
        "capitalists": sc,
        "informal": si,
    }
    hardest = max(burdens.items(), key=lambda x: x[1])[0] if burdens else "n/a"

    rows = [
        ("Demand Pressure (Household)", f"{float(state.get('demand_bloc_household_pressure', 0.0)):.3f}"),
        ("Demand Pressure (Institutional)", f"{float(state.get('demand_bloc_institutional_pressure', 0.0)):.3f}"),
        ("Demand Pressure (Productive)", f"{float(state.get('demand_bloc_productive_pressure', 0.0)):.3f}"),
        ("Needs Gap (From Blocs)", f"{float(state.get('needs_gap_from_blocs', state.get('needs_gap', 0.0))):.3f}"),
        ("Rationing Intensity", f"{float(state.get('rationing_intensity', 0.0)):.3f}"),
        ("Informal Market Response", f"{float(state.get('informal_market_response', 0.0)):.3f}"),
        ("Hardest-hit Class", hardest),
        ("─── Scarcity Burden by Class ───", "0=none | 1=severe"),
        ("workers", f"{sw:.3f}"),
        ("professionals", f"{sp:.3f}"),
        ("capitalists", f"{sc:.3f}"),
        ("informal", f"{si:.3f}"),
        ("─── Political Impact (Current) ───", "support | unrest"),
        (
            "workers",
            f"support={float(state.get('class_support_workers', 0.0)):.1f}  unrest={float(state.get('class_unrest_workers', 0.0)):.1f}",
        ),
        (
            "professionals",
            f"support={float(state.get('class_support_professionals', 0.0)):.1f}  unrest={float(state.get('class_unrest_professionals', 0.0)):.1f}",
        ),
        (
            "capitalists",
            f"support={float(state.get('class_support_capitalists', 0.0)):.1f}  unrest={float(state.get('class_unrest_capitalists', 0.0)):.1f}",
        ),
        (
            "informal",
            f"support={float(state.get('class_support_informal', 0.0)):.1f}  unrest={float(state.get('class_unrest_informal', 0.0)):.1f}",
        ),
    ]
    return rows
