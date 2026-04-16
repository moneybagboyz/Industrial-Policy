# UI Spec (Phase 8 Starter)

## Objective
Provide a spreadsheet-first interface with explainable metric drilldowns.

## Current Implementation
- Sheet registry in `src/ui/sheets.py`.
- Causality payload helpers in `src/ui/causality_explorer.py`.
- Table-driven CLI summary in `src/ui/dashboard_cli.py`.
- Scenario-driven tick stepping and per-sheet detail commands in `src/ui/dashboard_cli.py`.
- Per-sheet filtering and metric history commands in `src/ui/dashboard_cli.py`.
- In-dashboard command help and side-by-side scenario comparison tables in `src/ui/dashboard_cli.py`.
- Scenario comparison artifacts generated in `reports/scenario_comparison.md` and `reports/scenario_comparison.json`.

## Planned Expansion
1. Replace terminal CLI with panel-based interactive table UI.
2. Add per-sheet query, sorting, and richer history views.
3. Add metric driver tree explorer.
4. Add editable policy controls and persistent comparison sessions.
