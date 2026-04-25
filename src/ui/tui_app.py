"""Textual TUI for the Country Simulation dashboard."""

from __future__ import annotations

import argparse
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    Tab,
    TabbedContent,
    TabPane,
)

from src.core.default_engine import build_engine_from_scenario
from src.ui.insight_views import (
    build_building_inventory_rows,
    build_commodity_flow_rows,
    build_consequence_queue_rows,
    build_construction_pipeline_rows,
    build_executive_overview_rows,
    build_logistics_chokepoint_rows,
    build_policy_dashboard_rows,
    build_policy_graveyard_rows,
    build_shortage_class_impact_rows,
    build_state_explorer_rows,
    build_tradition_influence_rows,
)
from src.ui.map_ascii import render_region_ascii_map

DEFAULT_SCENARIO_PATH = "data/scenarios/baseline_1990_country_a.yaml"

# ---------------------------------------------------------------------------
# Sheet / view definitions
# ---------------------------------------------------------------------------

SHEET_FIELDS: dict[str, list[str]] = {
    "Executive Overview": ["overview_line_00"],
    "State Explorer": ["state_line_00"],
    "National Accounts": ["price", "wage", "unemployment", "nominal_gdp_monthly"],
    "Production and Supply Chains": ["production", "inventory", "unmet_demand", "capacity_output", "sector_price_index"],
    "Sector Output and Capacity": [
        "sector_output_primary",
        "sector_output_secondary",
        "sector_output_tertiary",
        "agriculture_output",
        "energy_output",
        "manufacturing_output",
        "construction_output",
        "services_output",
        "capacity_output",
    ],
    "Sector Prices and Shortages": [
        "sector_price_primary",
        "sector_price_secondary",
        "sector_price_tertiary",
        "agriculture_price",
        "energy_price",
        "manufacturing_price",
        "construction_price",
        "services_price",
        "sector_shortage_primary",
        "sector_shortage_secondary",
        "sector_shortage_tertiary",
    ],
    "Supply Chain Stress Map": [
        "sector_shortage_primary",
        "sector_shortage_secondary",
        "sector_shortage_tertiary",
        "cost_delta",
        "demand_gap",
        "transport_cost_index",
        "map_connectivity_index",
        "mean_route_cost",
        "trade_shock_imports",
        "trade_shock_exports",
        "regional_output_gini",
        "regional_service_gap_index",
        "regional_employment_gap_index",
        "regional_representation_gap",
    ],
    "Commodity Flows and Storage": ["demand_bloc_household_pressure"],
    "Logistics Chokepoints": ["logistics_bottleneck_index"],
    "Shortages and Class Impact": ["needs_gap", "class_conflict_pressure"],
    "Regional Map (ASCII)": ["map_ascii_line_00"],
    "World Diplomacy and External Risks": [
        "trade_access_index",
        "sanctions_index",
        "war_risk_index",
        "external_stress",
        "state_failure_risk",
    ],
    "Laws and Interest Groups": [
        "law_stability_index",
        "reform_momentum",
        "interest_group_conflict",
        "class_conflict_pressure",
        "belief_in_system",
    ],
    "Technology and Innovation": [
        "technology_tier",
        "research_progress",
        "innovation_adoption",
        "prod_growth",
        "capital_flight_rate",
    ],
    "Military and Security": [
        "military_readiness",
        "internal_security_risk",
        "security_posture",
        "military_spend_share",
        "war_risk_index",
    ],
    "Events, Crises, and Victory": [
        "active_crisis",
        "crisis_intensity",
        "state_failure_risk",
        "victory_progress",
        "game_over",
        "game_over_reason",
    ],
    "Prices and Inflation Drivers": ["price", "expected_inflation", "inflation_proxy", "cost_delta"],
    "Labor and Income Distribution": [
        "wage",
        "unemployment",
        "household_demand_proxy",
        "natural_unemployment",
        "worker_income_share",
        "professional_income_share",
        "capitalist_income_share",
        "informal_income_share",
    ],
    "Public Finance and Debt": ["revenue", "non_interest_spending", "interest_payment", "deficit", "debt", "debt_rate"],
    "Trade, FX, and Reserves": ["exports", "imports", "current_account", "balance_of_payments", "reserves", "fx_delta", "risk_premium"],
    "Demography and Social Mobility": ["population", "births", "deaths", "migration_net"],
    "Trust, Legitimacy, Polarization, Unrest": [
        "trust",
        "legitimacy",
        "polarization",
        "unrest",
        "needs_gap",
        "class_conflict_pressure",
        "belief_in_system",
        "distrust_shock_buildup",
    ],
    "Class and Inequality Dynamics": [
        "wealth_gini",
        "wealth_top10pct",
        "poverty_headcount",
        "class_support_workers",
        "class_support_professionals",
        "class_support_capitalists",
        "class_support_informal",
        "capital_flight_rate",
    ],
    "Events and Causality Log": ["policy_active", "consistency_ok", "consistency_tick", "external_stress"],
}

SCOPE_VIEWS: dict[str, list[str]] = {
    "nation": [
        "Executive Overview",
        "State Explorer",
        "National Accounts",
        "Production and Supply Chains",
        "Sector Output and Capacity",
        "Sector Prices and Shortages",
        "Supply Chain Stress Map",
        "Commodity Flows and Storage",
        "Logistics Chokepoints",
        "Shortages and Class Impact",
        "Building Inventory",
        "Construction Pipeline",
        "Policy Dashboard",
        "Ideology Traditions",
        "Policy Graveyard",
        "Consequence Queue",
        "Regional Map (ASCII)",
        "World Diplomacy and External Risks",
        "Laws and Interest Groups",
        "Technology and Innovation",
        "Military and Security",
        "Events, Crises, and Victory",
        "Prices and Inflation Drivers",
        "Labor and Income Distribution",
        "Public Finance and Debt",
        "Trade, FX, and Reserves",
        "Demography and Social Mobility",
        "Trust, Legitimacy, Polarization, Unrest",
        "Class and Inequality Dynamics",
        "Events and Causality Log",
    ],
    "state": [
        "Executive Overview",
        "State Explorer",
        "National Accounts",
        "Production and Supply Chains",
        "Sector Output and Capacity",
        "Sector Prices and Shortages",
        "Supply Chain Stress Map",
        "Commodity Flows and Storage",
        "Logistics Chokepoints",
        "Shortages and Class Impact",
        "Building Inventory",
        "Construction Pipeline",
        "Policy Dashboard",
        "Ideology Traditions",
        "Policy Graveyard",
        "Consequence Queue",
        "Regional Map (ASCII)",
        "Labor and Income Distribution",
        "Trust, Legitimacy, Polarization, Unrest",
        "Class and Inequality Dynamics",
        "Events and Causality Log",
    ],
    "region": [
        "Executive Overview",
        "National Accounts",
        "Production and Supply Chains",
        "Sector Prices and Shortages",
        "Supply Chain Stress Map",
        "Commodity Flows and Storage",
        "Logistics Chokepoints",
        "Shortages and Class Impact",
        "Building Inventory",
        "Construction Pipeline",
        "Labor and Income Distribution",
        "Trust, Legitimacy, Polarization, Unrest",
        "Class and Inequality Dynamics",
        "Events and Causality Log",
    ],
}

SUMMARY_FIELDS = [
    ("Tick", "last_tick"),
    ("Price", "price"),
    ("Wage", "wage"),
    ("Unemployment %", "unemployment"),
    ("Debt", "debt"),
    ("Reserves", "reserves"),
    ("Trust", "trust"),
    ("Legitimacy", "legitimacy"),
    ("Unrest", "unrest"),
    ("GDP/mo", "nominal_gdp_monthly"),
]

# ---------------------------------------------------------------------------
# Policy lever definitions
# ---------------------------------------------------------------------------

# (label, state_key, default, description, min, max)
POLICY_LEVERS: list[tuple[str, str, float, str, float, float]] = [
    ("Tax Rate %",           "tax_ratio",                  20.0, "% of GDP collected as tax",                           5.0,  45.0),
    ("Spending %",           "spend_ratio",                20.5, "% of GDP for non-interest spending",                  5.0,  50.0),
    ("Policy Rate %",        "policy_rate",                 8.0, "Central bank base rate (annual %)",                   0.0,  30.0),
    ("Infra Spend %",        "infrastructure_spend_share", 25.0, "Gov spending share to infrastructure",                0.0,  60.0),
    ("Industrial Bias",      "industrial_policy_bias",      0.5, "Targeted support for manufacturing (0-1)",            0.0,   1.0),
    ("Food Stabilization",   "food_price_stabilization",    0.4, "Food price buffer strength (0-1)",                    0.0,   1.0),
    ("Regional Equity Bias", "regional_equity_bias",        0.5, "Allocation fairness vs efficiency (0-1)",             0.0,   1.0),
    ("Diplomacy Posture",    "diplomacy_posture",            0.5, "External engagement level (0-1)",                     0.0,   1.0),
    ("Military Spend %",     "military_spend_share",        16.0, "Defense spending share of budget",                   0.0,  50.0),
    ("Security Posture",     "security_posture",             0.45, "Domestic security intensity (0-1)",                  0.0,   1.0),
    ("Research Spend %",     "research_spend_share",         4.0, "Research spending share of budget",                  0.0,  20.0),
    ("Construction Spend %", "construction_spend_share",    12.0, "Capital project spending share",                     0.0,  40.0),
    ("Export Boost %",       "trade_shock_exports",        100.0, "Export volume vs baseline (100=normal)",            10.0, 200.0),
    ("Import Tariff %",      "trade_shock_imports",        100.0, "Import volume vs baseline (100=normal)",            10.0, 200.0),
    ("Repression",           "repression",                  20.0, "State repression level (0-100)",                     0.0, 100.0),
    ("Corruption",           "corruption_signal",            0.3, "Perceived corruption (0-1)",                         0.0,   1.0),
    ("Info Quality",         "info_quality",                 0.6, "State information quality (0-1)",                    0.0,   1.0),
    ("Nationalize Industry", "nationalize_industry",         0.0, "Fraction of private buildings to nationalise (0-1)", 0.0,   1.0),
    ("Construction Subsidy", "construction_subsidy",         0.0, "Public subsidy for private construction (0-1)",      0.0,   1.0),
]

# Fast lookup by key
POLICY_LEVERS_BY_KEY: dict[str, tuple[str, str, float, float, float]] = {
    key: (label, desc, default, mn, mx)
    for label, key, default, desc, mn, mx in POLICY_LEVERS
}

# Policy categories listed in the right-hand picker panel.
# Each entry: (display_name, [state_keys_in_this_category])
POLICY_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Fiscal & Tax",    ["tax_ratio", "spend_ratio"]),
    ("Monetary",        ["policy_rate"]),
    ("Industrial",      ["industrial_policy_bias", "infrastructure_spend_share", "construction_spend_share"]),
    ("Trade",           ["trade_shock_exports", "trade_shock_imports"]),
    ("Social Programs", ["food_price_stabilization", "regional_equity_bias", "research_spend_share"]),
    ("Governance",      ["repression", "corruption_signal", "info_quality", "diplomacy_posture"]),
    ("Military",        ["military_spend_share", "security_posture"]),
    ("Buildings",       ["nationalize_industry", "construction_subsidy"]),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lever_state_value(key: str, default: float, state: dict[str, Any]) -> float:
    """Read lever value from state, converting stored ratio back to display unit."""
    raw = float(state.get(key, default))
    if key in ("tax_ratio", "spend_ratio", "infrastructure_spend_share",
               "military_spend_share", "research_spend_share", "construction_spend_share"):
        return raw * 100.0
    if key in ("trade_shock_exports", "trade_shock_imports"):
        return raw * 100.0
    if key == "policy_rate":
        return raw * 100.0
    return raw


def _lever_to_state_value(key: str, display_val: float) -> float:
    """Convert display unit back to stored state unit."""
    if key in ("tax_ratio", "spend_ratio", "infrastructure_spend_share",
               "military_spend_share", "research_spend_share", "construction_spend_share"):
        return display_val / 100.0
    if key in ("trade_shock_exports", "trade_shock_imports"):
        return display_val / 100.0
    if key == "policy_rate":
        return display_val / 100.0
    return display_val


def _fmt(value: Any) -> str:
    if value is None or value == "n/a":
        return "—"
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, float):
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:.2f}B"
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.2f}M"
        if abs(value) >= 1_000:
            return f"{value:,.2f}"
        return f"{value:.4f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


# ---------------------------------------------------------------------------
# Widget: Summary (top-left)
# ---------------------------------------------------------------------------

class SummaryPanel(Static):
    def compose(self) -> ComposeResult:
        yield DataTable(id="summary-table", show_cursor=False)

    def on_mount(self) -> None:
        self.query_one("#summary-table", DataTable).add_columns("Metric", "Value")

    def refresh_data(self, state: dict[str, Any]) -> None:
        t = self.query_one("#summary-table", DataTable)
        t.clear()
        for label, key in SUMMARY_FIELDS:
            t.add_row(label, _fmt(state.get(key)))


# ---------------------------------------------------------------------------
# Widget: Data sheet (centre, Data tab)
# ---------------------------------------------------------------------------

class SheetPanel(Static):
    current_sheet: reactive[str] = reactive("National Accounts")

    def compose(self) -> ComposeResult:
        yield Label("", id="sheet-title")
        yield DataTable(id="sheet-table", show_cursor=False)

    def on_mount(self) -> None:
        self.query_one("#sheet-table", DataTable).add_columns("Field", "Value")

    def show_sheet(self, sheet_name: str, state: dict[str, Any]) -> None:
        self.current_sheet = sheet_name
        self.query_one("#sheet-title", Label).update(f"[bold]{sheet_name}[/bold]")
        t = self.query_one("#sheet-table", DataTable)
        t.clear()
        if sheet_name == "Executive Overview":
            for key, value in build_executive_overview_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "State Explorer":
            for key, value in build_state_explorer_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Building Inventory":
            for key, value in build_building_inventory_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Construction Pipeline":
            for key, value in build_construction_pipeline_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Commodity Flows and Storage":
            for key, value in build_commodity_flow_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Logistics Chokepoints":
            for key, value in build_logistics_chokepoint_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Shortages and Class Impact":
            for key, value in build_shortage_class_impact_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Policy Dashboard":
            for key, value in build_policy_dashboard_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Ideology Traditions":
            for key, value in build_tradition_influence_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Policy Graveyard":
            for key, value in build_policy_graveyard_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Consequence Queue":
            for key, value in build_consequence_queue_rows(state):
                t.add_row(key, value)
            return
        if sheet_name == "Regional Map (ASCII)":
            map_text = render_region_ascii_map(state)
            for i, line in enumerate(map_text.splitlines()):
                t.add_row(f"line_{i:02d}", line)
            return
        fields = SHEET_FIELDS.get(sheet_name, [])
        for field in fields:
            t.add_row(field, _fmt(state.get(field)))


# ---------------------------------------------------------------------------
# Widget: History (centre, Data tab)
# ---------------------------------------------------------------------------

class HistoryPanel(Static):
    def compose(self) -> ComposeResult:
        yield Label("[bold]History[/bold]", id="history-title")
        yield DataTable(id="history-table", show_cursor=False)

    def on_mount(self) -> None:
        self.query_one("#history-table", DataTable).add_columns("Tick", "Value")

    def show_history(self, metric: str, state_history: list[dict[str, Any]]) -> None:
        self.query_one("#history-title", Label).update(f"[bold]History: {metric}[/bold]")
        t = self.query_one("#history-table", DataTable)
        t.clear()
        for idx, snap in enumerate(state_history[-20:], start=max(1, len(state_history) - 19)):
            t.add_row(str(idx), _fmt(snap.get(metric)))


# ---------------------------------------------------------------------------
# Widget: Individual lever row (used inside PolicyWorkspacePanel)
# ---------------------------------------------------------------------------

class LeverRow(Horizontal):
    """One editable policy lever: label + input field."""

    def __init__(self, key: str, label_text: str, value_str: str) -> None:
        super().__init__(classes="lever-row")
        self._key = key
        self._label_text = label_text
        self._value_str = value_str

    def compose(self) -> ComposeResult:
        yield Label(f"{self._label_text}:", classes="lever-label")
        yield Input(value=self._value_str, id=f"lever-{self._key}", classes="lever-input")


# ---------------------------------------------------------------------------
# Widget: Policy workspace (centre, Policy tab)
# ---------------------------------------------------------------------------

class PolicyWorkspacePanel(Static):
    """Centre-panel policy editor — shows levers for the selected category."""

    def compose(self) -> ComposeResult:
        yield Label("", id="pw-status")
        yield Label("[dim]Select a policy category from the right panel.[/dim]", id="pw-cat-title")
        yield Label("", id="pw-cat-desc")
        yield ScrollableContainer(id="pw-levers")
        yield Label("", id="pw-feedback")
        yield Button("Apply Changes", id="btn-apply", variant="success")

    def update_status(self, state: dict[str, Any]) -> None:
        bw         = int(state.get("policy_bandwidth", 60))
        cred       = float(state.get("policy_credibility", 1.0))
        active_trad = str(state.get("active_tradition") or "—")
        self.query_one("#pw-status", Label).update(
            f"Bandwidth: [bold]{bw}[/bold]/100   "
            f"Credibility: [bold]{cred:.2f}[/bold]   "
            f"Tradition: [bold]{active_trad}[/bold]"
        )

    def show_category(self, cat_name: str, keys: list[str], state: dict[str, Any]) -> None:
        self.query_one("#pw-cat-title", Label).update(f"[bold]{cat_name}[/bold]")
        lever_count = sum(1 for k in keys if k in POLICY_LEVERS_BY_KEY)
        self.query_one("#pw-cat-desc", Label).update(
            f"[dim]{lever_count} lever{'s' if lever_count != 1 else ''}[/dim]"
        )

        container = self.query_one("#pw-levers", ScrollableContainer)
        # Remove previous lever rows
        for row in list(container.query(LeverRow)):
            row.remove()

        # Mount new lever rows for this category
        rows: list[LeverRow] = []
        for key in keys:
            if key not in POLICY_LEVERS_BY_KEY:
                continue
            label_txt, _desc, default, _mn, _mx = POLICY_LEVERS_BY_KEY[key]
            val_str = f"{_lever_state_value(key, default, state):.2f}"
            rows.append(LeverRow(key, label_txt, val_str))
        if rows:
            container.mount(*rows)

        self.update_status(state)
        self.query_one("#pw-feedback", Label).update("")

    def load_all_from_state(self, state: dict[str, Any]) -> None:
        """Reload currently visible lever values from state (e.g. after a tick)."""
        container = self.query_one("#pw-levers", ScrollableContainer)
        for row in container.query(LeverRow):
            key = row._key
            if key not in POLICY_LEVERS_BY_KEY:
                continue
            _label, _desc, default, _mn, _mx = POLICY_LEVERS_BY_KEY[key]
            try:
                inp = row.query_one(Input)
                inp.value = f"{_lever_state_value(key, default, state):.2f}"
            except Exception:
                pass
        self.update_status(state)

    def collect_patches(self, active_keys: list[str]) -> dict[str, float]:
        patches: dict[str, float] = {}
        for key in active_keys:
            if key not in POLICY_LEVERS_BY_KEY:
                continue
            try:
                inp = self.query_one(f"#lever-{key}", Input)
            except Exception:
                continue
            raw = inp.value.strip()
            if not raw:
                continue
            _label, _desc, default, mn, mx = POLICY_LEVERS_BY_KEY[key]
            try:
                clamped = max(mn, min(mx, float(raw)))
                patches[key] = _lever_to_state_value(key, clamped)
            except ValueError:
                pass
        return patches


# ---------------------------------------------------------------------------
# Widget: Policy category picker (right panel, yellow/accent border)
# ---------------------------------------------------------------------------

class PolicyCategoryPanel(Static):
    """Right-column category selector — clicking a category opens it in the workspace."""

    def compose(self) -> ComposeResult:
        yield Label("[bold]Policy[/bold]")
        yield Label("[dim]Choose a category[/dim]")
        yield ListView(
            *[
                ListItem(Label(name), id=f"cat-{i}")
                for i, (name, _) in enumerate(POLICY_CATEGORIES)
            ],
            id="cat-list",
        )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class CountrySimulationApp(App):
    CSS = """
    Screen { layout: vertical; }

    #main-area {
        height: 1fr;
        layout: horizontal;
    }

    /* ── Left column ── */
    #left-col {
        width: 32;
        layout: vertical;
    }
    SummaryPanel {
        height: auto;
        border: solid $primary;
        padding: 0 1;
    }
    #sheet-list-container {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }

    /* ── Centre column ── */
    #center-col {
        width: 1fr;
        layout: vertical;
    }
    #center-tabs {
        height: 1fr;
    }
    #tab-data {
        layout: vertical;
        height: 1fr;
    }
    SheetPanel {
        height: 1fr;
        border: solid $primary;
        padding: 0 1;
    }
    HistoryPanel {
        height: 14;
        border: solid $primary;
        padding: 0 1;
    }
    #tab-policy {
        layout: vertical;
        height: 1fr;
    }
    PolicyWorkspacePanel {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
        layout: vertical;
    }
    #pw-status {
        height: 1;
        color: $text-muted;
        margin-bottom: 1;
    }
    #pw-cat-title {
        height: 1;
    }
    #pw-cat-desc {
        height: 1;
        margin-bottom: 1;
    }
    #pw-levers {
        height: 1fr;
    }
    #pw-feedback {
        height: 1;
        color: $success;
        margin-top: 1;
    }

    /* ── Right column (yellow/accent border — policy category picker) ── */
    #right-col {
        width: 26;
        layout: vertical;
    }
    PolicyCategoryPanel {
        height: 1fr;
        border: solid $accent;
        padding: 1 1;
        overflow-y: auto;
    }
    #cat-list {
        height: 1fr;
    }
    #step-controls {
        height: auto;
        border: solid $primary;
        padding: 1;
        layout: vertical;
    }

    /* ── Shared lever rows ── */
    .lever-row {
        height: 3;
        margin-bottom: 0;
    }
    .lever-label {
        width: 20;
        padding-top: 1;
    }
    .lever-input {
        width: 1fr;
    }

    Button { width: 100%; margin-bottom: 1; }
    #status-bar { height: 1; background: $surface; padding: 0 2; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "step_one", "Step 1"),
        Binding("S", "step_twelve", "Step 12"),
        Binding("r", "refresh_view", "Refresh"),
        Binding("p", "open_policy", "Policy"),
        Binding("d", "open_data", "Data"),
    ]

    def __init__(self, scenario_path: str = DEFAULT_SCENARIO_PATH, seed: int = 42) -> None:
        super().__init__()
        self.scenario_path = scenario_path
        self.seed = seed
        self.engine = build_engine_from_scenario(seed=seed, scenario_path=scenario_path)
        self.engine.store.state["last_tick"] = 0
        self._current_sheet = "National Accounts"
        self._scope_type = "nation"
        self._scope_key = "nation"
        self._scope_parent = ""
        self._scope_index: dict[str, tuple[str, str, str]] = {}
        self._view_index: dict[str, str] = {}
        self._view_list_nonce = 0
        # Active policy category (name, keys)
        self._active_category: tuple[str, list[str]] = POLICY_CATEGORIES[0]
        # Category index for fast lookup: item-id → (name, keys)
        self._category_index: dict[str, tuple[str, list[str]]] = {
            f"cat-{i}": (name, keys)
            for i, (name, keys) in enumerate(POLICY_CATEGORIES)
        }

    # ── Scope helpers ────────────────────────────────────────────────────

    def _build_scope_items(self) -> list[ListItem]:
        items: list[ListItem] = []
        self._scope_index = {"scope-nation": ("nation", "nation", "")}
        items.append(ListItem(Label("Nation: Republic of Aster"), id="scope-nation"))

        region_state = self.engine.store.state.get("region_state", {})
        regions = region_state.get("regions", {}) if isinstance(region_state, dict) else {}
        if isinstance(regions, dict):
            for state_idx, state_name in enumerate(sorted(regions.keys())):
                state_item_id = f"scope-state-{state_idx}"
                self._scope_index[state_item_id] = ("state", state_name, "")
                items.append(ListItem(Label(f"State: {state_name}"), id=state_item_id))

                payload = regions.get(state_name, {})
                if not isinstance(payload, dict):
                    continue
                subregions = payload.get("subregions", {})
                if not isinstance(subregions, dict):
                    continue
                for sub_idx, sub_name in enumerate(sorted(subregions.keys())):
                    sub_item_id = f"scope-region-{state_idx}-{sub_idx}"
                    self._scope_index[sub_item_id] = ("region", sub_name, state_name)
                    items.append(ListItem(Label(f"  Region: {sub_name}"), id=sub_item_id))
        return items

    def _build_scoped_state(self) -> dict[str, Any]:
        base = dict(self.engine.store.state)
        base["scope_type"] = self._scope_type
        base["scope_key"] = self._scope_key
        base["scope_parent"] = self._scope_parent

        if self._scope_type == "nation":
            return base

        region_state = base.get("region_state", {})
        regions = region_state.get("regions", {}) if isinstance(region_state, dict) else {}
        if not isinstance(regions, dict):
            return base

        selected_payload: dict[str, Any] | None = None
        population = 0.0
        if self._scope_type == "state":
            payload = regions.get(self._scope_key)
            if isinstance(payload, dict):
                selected_payload = payload
                population = float(payload.get("population", 0.0))
        elif self._scope_type == "region":
            parent = regions.get(self._scope_parent)
            if isinstance(parent, dict):
                subregions = parent.get("subregions", {})
                if isinstance(subregions, dict):
                    payload = subregions.get(self._scope_key)
                    if isinstance(payload, dict):
                        selected_payload = payload
                        parent_pop = float(parent.get("population", 0.0))
                        pop_share  = float(payload.get("population_share", 0.0))
                        population = max(0.0, parent_pop * pop_share)

        if not selected_payload:
            return base

        support      = float(selected_payload.get("support_score", base.get("trust", 0.5)))
        unrest       = float(selected_payload.get("unrest_score", base.get("unrest", 0.3)))
        unemployment = float(selected_payload.get("unemployment", base.get("unemployment", 0.08)))
        output       = float(selected_payload.get("output", base.get("nominal_gdp_monthly", 0.0)))
        base.update({
            "trust":               support,
            "legitimacy":          max(0.0, min(1.0, 0.6 * support + 0.4 * (1.0 - unrest))),
            "unrest":              unrest,
            "unemployment":        unemployment,
            "nominal_gdp_monthly": output,
        })
        if population > 0:
            base["population"] = population
        return base

    def _views_for_scope(self) -> list[str]:
        preferred = SCOPE_VIEWS.get(self._scope_type, SCOPE_VIEWS["nation"])
        _custom_views = {
            "Executive Overview", "State Explorer",
            "Policy Dashboard", "Ideology Traditions", "Policy Graveyard", "Consequence Queue",
            "Regional Map (ASCII)", "Building Inventory", "Construction Pipeline",
        }
        return [name for name in preferred if name in SHEET_FIELDS or name in _custom_views]

    def _rebuild_view_list(self) -> None:
        view_list = self.query_one("#view-list", ListView)
        for child in list(view_list.children):
            child.remove()

        self._view_index = {}
        self._view_list_nonce += 1
        view_names = self._views_for_scope()
        for idx, name in enumerate(view_names):
            item_id = f"sheet-{self._view_list_nonce}-{idx}"
            self._view_index[item_id] = name
            view_list.append(ListItem(Label(name), id=item_id))

        if view_names and self._current_sheet not in view_names:
            self._current_sheet = view_names[0]

    def _history_value_for_scope(self, snap: dict[str, Any], metric: str) -> Any:
        if self._scope_type == "nation":
            return snap.get(metric)

        region_state = snap.get("region_state", {})
        regions = region_state.get("regions", {}) if isinstance(region_state, dict) else {}
        if not isinstance(regions, dict):
            return snap.get(metric)

        payload: dict[str, Any] | None = None
        population = 0.0
        if self._scope_type == "state":
            candidate = regions.get(self._scope_key)
            if isinstance(candidate, dict):
                payload = candidate
                population = float(candidate.get("population", 0.0))
        elif self._scope_type == "region":
            parent = regions.get(self._scope_parent)
            if isinstance(parent, dict):
                subregions = parent.get("subregions", {})
                if isinstance(subregions, dict):
                    candidate = subregions.get(self._scope_key)
                    if isinstance(candidate, dict):
                        payload = candidate
                        parent_pop = float(parent.get("population", 0.0))
                        pop_share  = float(candidate.get("population_share", 0.0))
                        population = max(0.0, parent_pop * pop_share)

        if not payload:
            return snap.get(metric)

        if metric == "unemployment":
            return float(payload.get("unemployment", snap.get(metric, 0.0)))
        if metric == "unrest":
            return float(payload.get("unrest_score", snap.get(metric, 0.0)))
        if metric in {"trust", "legitimacy"}:
            support = float(payload.get("support_score", snap.get("trust", 0.0)))
            unrest  = float(payload.get("unrest_score", snap.get("unrest", 0.0)))
            if metric == "trust":
                return support
            return max(0.0, min(1.0, 0.6 * support + 0.4 * (1.0 - unrest)))
        if metric == "nominal_gdp_monthly":
            return float(payload.get("output", snap.get(metric, 0.0)))
        if metric == "population" and population > 0:
            return population
        return snap.get(metric)

    def _show_history_for_current_view(self) -> None:
        _no_history = {
            "Regional Map (ASCII)", "Executive Overview", "State Explorer",
            "Building Inventory", "Construction Pipeline",
        }
        if self._current_sheet in _no_history or self._current_sheet not in SHEET_FIELDS:
            self.query_one("#history-title", Label).update("[bold]History: n/a for this view[/bold]")
            self.query_one("#history-table", DataTable).clear()
            return
        metric = SHEET_FIELDS[self._current_sheet][0]
        if self._scope_type == "nation":
            self.query_one(HistoryPanel).show_history(metric, self.engine.store.state_history)
            return
        history_rows: list[dict[str, Any]] = []
        for snap in self.engine.store.state_history:
            history_rows.append({metric: self._history_value_for_scope(snap, metric)})
        self.query_one(HistoryPanel).show_history(metric, history_rows)

    # ── Layout ───────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        scope_items = self._build_scope_items()
        self._view_index = {}
        self._view_list_nonce += 1
        view_items: list[ListItem] = []
        for idx, name in enumerate(self._views_for_scope()):
            item_id = f"sheet-{self._view_list_nonce}-{idx}"
            self._view_index[item_id] = name
            view_items.append(ListItem(Label(name), id=item_id))

        yield Header(show_clock=True)
        with Horizontal(id="main-area"):
            # ── Left: summary + scope/view navigation ────────────────────
            with Vertical(id="left-col"):
                yield SummaryPanel(id="summary")
                with ScrollableContainer(id="sheet-list-container"):
                    yield Label("[bold]Layers[/bold]")
                    yield ListView(*scope_items, id="scope-list")
                    yield Label("[bold]Views[/bold]")
                    yield ListView(*view_items, id="view-list")

            # ── Centre: tabbed Data / Policy workspace ───────────────────
            with Vertical(id="center-col"):
                with TabbedContent(id="center-tabs"):
                    with TabPane("Data", id="tab-data"):
                        yield SheetPanel(id="sheet-panel")
                        yield HistoryPanel(id="history")
                    with TabPane("Policy", id="tab-policy"):
                        yield PolicyWorkspacePanel(id="policy-workspace")

            # ── Right: policy category picker (yellow) + time controls ───
            with Vertical(id="right-col"):
                yield PolicyCategoryPanel(id="policy-cat-panel")
                with Vertical(id="step-controls"):
                    yield Label("[bold]Advance Time[/bold]")
                    yield Button("▶  Step 1 month",    id="btn-step-1",  variant="primary")
                    yield Button("▶▶ Step 12 months",  id="btn-step-12", variant="primary")
                    yield Button("▶▶▶ Step 60 months", id="btn-step-60")
                    yield Button("↺  Reset",            id="btn-reset",   variant="error")

        yield Label("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_all()
        # Seed workspace with first category so it isn't blank
        cat_name, cat_keys = self._active_category
        self.query_one(PolicyWorkspacePanel).show_category(
            cat_name, cat_keys, self.engine.store.state
        )

    # ── Refresh helpers ──────────────────────────────────────────────────

    def _refresh_all(self) -> None:
        scoped_state = self._build_scoped_state()
        self.query_one(SummaryPanel).refresh_data(scoped_state)
        self.query_one(SheetPanel).show_sheet(self._current_sheet, scoped_state)

        tick  = int(scoped_state.get("last_tick", 0))
        year  = 1990 + tick // 12
        month = (tick % 12) + 1
        self.sub_title = f"Republic of Aster  |  {year}-{month:02d}  |  Tick {tick}"

        scope_label = "Nation"
        if self._scope_type == "state":
            scope_label = f"State: {self._scope_key}"
        elif self._scope_type == "region":
            scope_label = f"Region: {self._scope_key} ({self._scope_parent})"

        self.query_one("#status-bar", Label).update(
            f"  Scope: {scope_label}   "
            f"Legitimacy: {_fmt(scoped_state.get('legitimacy'))}   "
            f"Unrest: {_fmt(scoped_state.get('unrest'))}   "
            f"Reserves: {_fmt(scoped_state.get('reserves'))}   "
            f"Debt/GDP: {_fmt(scoped_state.get('debt', 0) / max(scoped_state.get('nominal_gdp_monthly', 1) * 12, 1) * 100)}%"
        )

        # Keep workspace status line in sync
        workspace = self.query_one(PolicyWorkspacePanel)
        workspace.load_all_from_state(self.engine.store.state)
        self._show_history_for_current_view()

    def _advance_ticks(self, count: int) -> None:
        current_tick = int(self.engine.store.state.get("last_tick", 0))
        for _ in range(count):
            current_tick += 1
            self.engine.run_tick(current_tick)
        self.engine.store.state["last_tick"] = current_tick
        self._refresh_all()

    def _reset_engine(self) -> None:
        self.engine = build_engine_from_scenario(seed=self.seed, scenario_path=self.scenario_path)
        self.engine.store.state["last_tick"] = 0
        self._scope_type = "nation"
        self._scope_key = "nation"
        self._scope_parent = ""
        self._active_category = POLICY_CATEGORIES[0]
        self._rebuild_view_list()
        self._refresh_all()

        cat_list = self.query_one("#cat-list", ListView)
        if cat_list.children:
            cat_list.index = 0

        cat_name, cat_keys = self._active_category
        self.query_one(PolicyWorkspacePanel).show_category(
            cat_name, cat_keys, self.engine.store.state
        )

    @on(ListView.Selected, "#scope-list")
    def _on_scope_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        if not item_id or item_id not in self._scope_index:
            return
        self._scope_type, self._scope_key, self._scope_parent = self._scope_index[item_id]
        self._rebuild_view_list()
        self._refresh_all()

    @on(ListView.Selected, "#view-list")
    def _on_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        if not item_id or item_id not in self._view_index:
            return
        self._current_sheet = self._view_index[item_id]
        self.query_one(TabbedContent).active = "tab-data"
        self._refresh_all()

    @on(ListView.Selected, "#cat-list")
    def _on_category_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id
        if not item_id or item_id not in self._category_index:
            return
        self._active_category = self._category_index[item_id]
        cat_name, cat_keys = self._active_category
        self.query_one(TabbedContent).active = "tab-policy"
        self.query_one(PolicyWorkspacePanel).show_category(
            cat_name, cat_keys, self.engine.store.state
        )

    @on(Button.Pressed, "#btn-apply")
    def _on_apply_pressed(self) -> None:
        cat_name, cat_keys = self._active_category
        workspace = self.query_one(PolicyWorkspacePanel)
        patches = workspace.collect_patches(cat_keys)
        if not patches:
            self.query_one("#pw-feedback", Label).update("[dim]No changes to apply.[/dim]")
            return

        self.engine.store.state.update(patches)
        workspace.show_category(cat_name, cat_keys, self.engine.store.state)
        self._refresh_all()
        self.query_one("#pw-feedback", Label).update(
            f"[green]Applied {len(patches)} change{'s' if len(patches) != 1 else ''}.[/green]"
        )

    @on(Button.Pressed, "#btn-step-1")
    def _on_step_one_pressed(self) -> None:
        self._advance_ticks(1)

    @on(Button.Pressed, "#btn-step-12")
    def _on_step_twelve_pressed(self) -> None:
        self._advance_ticks(12)

    @on(Button.Pressed, "#btn-step-60")
    def _on_step_sixty_pressed(self) -> None:
        self._advance_ticks(60)

    @on(Button.Pressed, "#btn-reset")
    def _on_reset_pressed(self) -> None:
        self._reset_engine()

    def action_step_one(self) -> None:
        self._advance_ticks(1)

    def action_step_twelve(self) -> None:
        self._advance_ticks(12)

    def action_refresh_view(self) -> None:
        self._refresh_all()

    def action_open_policy(self) -> None:
        self.query_one(TabbedContent).active = "tab-policy"

    def action_open_data(self) -> None:
        self.query_one(TabbedContent).active = "tab-data"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Country Simulation Textual dashboard.")
    parser.add_argument("--scenario-path", default=DEFAULT_SCENARIO_PATH)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    CountrySimulationApp(scenario_path=args.scenario_path, seed=args.seed).run()


if __name__ == "__main__":
    main()
