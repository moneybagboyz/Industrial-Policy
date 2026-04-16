# Country Simulation

Simulation-first country strategy game starting in 1990.

## Current Status
- Phase 0 scaffold created.
- Deterministic simulation core started.
- Replay determinism tests added.

## Project Layout
- `docs/`: design and implementation contracts.
- `src/core/`: deterministic engine and state handling.
- `tests/`: verification for deterministic behavior.

## Quick Start
1. Create a Python virtual environment.
2. Install dependencies: `pip install -e . pytest`.
3. Run the terminal dashboard: `python -m src.ui.dashboard_cli`.
4. Optional: choose a scenario and seed: `python -m src.ui.dashboard_cli --scenario data/scenarios/baseline_1990_country_a.yaml --seed 42`.
5. Run tests: `pytest -q`.

## Playing The Current Build

### Full-screen TUI (recommended)

Press **F5** in VS Code, or run from the project root:

```powershell
.\.venv\Scripts\python.exe -m src.ui.tui_app
```

The game opens in a separate terminal window with three columns:

| Column | Contents |
|--------|----------|
| Left   | Key-indicator summary + 9 spreadsheet-view list |
| Centre | Active sheet detail + metric history (last 20 ticks) |
| Right  | **Policy Decisions panel** + time-advance controls |

#### Making decisions

The right column contains editable fields for every policy lever.  
Change a value and press **Apply Policies** — changes take effect on the
*next* simulated tick.

| Lever | What it does |
|-------|-------------|
| Tax Rate % | Share of GDP collected as tax. Higher taxes raise revenue but can dampen growth. |
| Spending % | Non-interest spending as % of GDP. Affects demand, unrest, and deficits. |
| Policy Rate % | Central bank annual rate. Rises in risk premium. Feeds into debt service cost. |
| Export Boost % | Trade multiplier on structural exports (100 = baseline). |
| Import Tariff % | Trade multiplier on structural imports (100 = baseline). |
| Repression | State repression level 0–100. Reduces unrest short-term at cost of trust. |
| Corruption | Perceived corruption 0–1. Weighs on trust and legitimacy each tick. |
| Info Quality | State information quality 0–1. Affects expectation anchoring and trust. |

#### Keyboard shortcuts

| Key | Action |
|-----|--------|
| `s` | Advance 1 month |
| `S` | Advance 12 months (1 year) |
| `r` | Refresh display |
| `q` | Quit |

#### CLI dashboard (fallback)

```powershell
.\.venv\Scripts\python.exe -m src.ui.dashboard_cli
```

Useful commands: `show`, `sheets`, `sheet 5`, `step 12`, `history debt 10`, `compare 24`, `q`.

## Immediate Next Steps
1. Implement Phase 2 accounting core.
2. Extend tick stage contracts with read/write lists.
3. Add validation gate runner.
