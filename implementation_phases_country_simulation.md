# Implementation Phases - Country Simulation

## 1. Goal and Delivery Strategy
Build the project in thin, testable vertical layers: first a deterministic simulation kernel with strict accounting and social-state integrity, then model coverage expansion, then UI and content. This sequence reduces rework because UI/content built on unstable mechanics is expensive to revise. The kernel must come first so every later feature is grounded in reproducible state transitions, validated equations, and traceable metric decomposition.

## 2. Phase Plan (Phase 0 to Phase 10)

### Phase 0 - Project Setup and Architecture Skeleton
- Objective: Establish repository structure, coding standards, CI checks, and simulation architecture boundaries.
- Scope in: Repo layout, module boundaries, state model conventions, logging/telemetry format, test harness scaffolding.
- Scope out: Full equations, content balancing, UI implementation.
- Concrete deliverables:
- `README.md` with architecture overview.
- `docs/architecture.md` with module map.
- `docs/tick_order_spec.md` initial skeleton.
- `src/core/` package scaffolding.
- `tests/` harness with deterministic seed test placeholder.
- Dependencies: none.
- Entry criteria: finalized design spec in `preliminary_answers.md`.
- Exit criteria: project boots, tests run in CI, architecture docs approved.
- Validation gates: lint and test pass, reproducibility seed test scaffold present.
- Risks and mitigation: overengineering risk mitigated by limiting to one-page docs and minimal code scaffold.
- Estimated effort: Medium (1 week).

### Phase 1 - Tick Engine and Deterministic State Pipeline
- Objective: Implement monthly state transition engine with stage isolation and deterministic replay.
- Scope in: Tick loop, immutable prior-state read, deterministic RNG stream, state commit semantics.
- Scope out: Full economic/social equations.
- Concrete deliverables:
- `src/core/tick_engine.py`.
- `src/core/state_store.py`.
- `src/core/rng.py` deterministic stream keyed by tick and event id.
- `tests/test_replay_determinism.py`.
- `docs/tick_order_spec.md` stage I/O contract draft.
- Dependencies: Phase 0 complete.
- Entry criteria: architecture skeleton merged.
- Exit criteria: identical inputs produce byte-identical outputs for 240 ticks.
- Validation gates: deterministic replay gate pass.
- Risks and mitigation: hidden non-determinism mitigated with seeded wrappers for all random calls.
- Estimated effort: Medium (1 to 2 weeks).

### Phase 2 - Economic Accounting Core (GDP Identities and Sector Balances)
- Objective: Implement national accounts and sector financial balance framework.
- Scope in: GDP expenditure/income identities, sector flow ledgers, stock-flow reconciliation.
- Scope out: Full supply constraints and social dynamics.
- Concrete deliverables:
- `src/econ/national_accounts.py`.
- `src/econ/sector_balances.py`.
- `docs/data_dictionary.md` first release (economic core tables).
- `tests/test_accounting_identities.py`.
- Dependencies: Phase 1.
- Entry criteria: deterministic pipeline passes.
- Exit criteria: accounting discrepancy below threshold each tick.
- Validation gates: GDP identity tolerance <0.1 percent, sector net balance tolerance pass.
- Risks and mitigation: sign-convention errors mitigated by strict flow naming and dual-entry checks.
- Estimated effort: Medium (1 to 2 weeks).

### Phase 3 - Production, Inventories, and Constrained Supply Chains
- Objective: Add input-output production with bottlenecks and inventory dynamics.
- Scope in: Sector capacity, input coefficients, constrained allocation, inventory carryover.
- Scope out: Labor wage dynamics and inflation decomposition.
- Concrete deliverables:
- `src/econ/production.py`.
- `src/econ/inventory.py`.
- `src/econ/supply_allocation.py`.
- `docs/data_dictionary.md` update (goods, sectors, coefficients).
- `tests/test_supply_constraints.py`.
- Dependencies: Phase 2.
- Entry criteria: accounting framework stable.
- Exit criteria: shortages and bottlenecks produce expected output suppression with no accounting breaks.
- Validation gates: stock-flow checks pass under constrained scenarios.
- Risks and mitigation: solver instability mitigated with bounded iterative solver and fallback diagnostics.
- Estimated effort: Large (2 weeks).

### Phase 4 - Price System, Inflation Decomposition, and Labor/Wage Block
- Objective: Implement price update, inflation channel decomposition, and labor market dynamics.
- Scope in: Cost/demand/FX pass-through, wage equations, unemployment transitions, household disposable income.
- Scope out: Public debt and FX reserves accounting.
- Concrete deliverables:
- `src/econ/pricing.py`.
- `src/econ/labor.py`.
- `src/econ/households.py`.
- `docs/parameter_registry.md` initial coefficient registry.
- `tests/test_inflation_decomposition.py`.
- Dependencies: Phase 3.
- Entry criteria: supply system stable.
- Exit criteria: inflation and labor metrics behave plausibly under shocks.
- Validation gates: decomposition completeness gate, labor transition consistency gate.
- Risks and mitigation: runaway inflation loops mitigated with parameter bounds and expectation dampeners.
- Estimated effort: Large (2 weeks).

### Phase 5 - Fiscal, Debt, Monetary, and FX/External Sector
- Objective: Add policy levers and sovereign/external constraints.
- Scope in: Budget identity, debt dynamics, policy rate transmission hooks, current account and reserves.
- Scope out: Full sociological layer and protest dynamics.
- Concrete deliverables:
- `src/econ/fiscal.py`.
- `src/econ/debt.py`.
- `src/econ/external_sector.py`.
- `src/econ/monetary.py`.
- `tests/test_debt_external_dynamics.py`.
- Dependencies: Phase 4.
- Entry criteria: prices and labor stable.
- Exit criteria: debt and FX crises emerge only under plausible stress conditions.
- Validation gates: debt reconciliation gate, reserve reconciliation gate, FX stress test pass.
- Risks and mitigation: unrealistic crisis frequency mitigated with calibration bands and scenario anchors.
- Estimated effort: Large (2 weeks).

### Phase 6 - Sociology Layer (Cohorts, Mobility, Trust, Legitimacy, Unrest)
- Objective: Implement social reproduction, trust/legitimacy, polarization, and mobilization systems.
- Scope in: Cohort transitions, mobility probabilities, trust/legitimacy updates, unrest/protest probability.
- Scope out: Final UI and content balancing.
- Concrete deliverables:
- `src/social/cohorts.py`.
- `src/social/mobility.py`.
- `src/social/trust_legitimacy.py`.
- `src/social/unrest.py`.
- `tests/test_social_state_consistency.py`.
- Dependencies: Phase 5.
- Entry criteria: macro-econ core passes stress tests.
- Exit criteria: social-state transitions conserve population and produce interpretable socio-political responses.
- Validation gates: social-state consistency and identity-share sum gates pass.
- Risks and mitigation: unstable feedback loops mitigated via bounded indices and lag terms.
- Estimated effort: Large (2 weeks).

### Phase 7 - Validation Framework (Identity, Soak, Sensitivity, Incidence)
- Objective: Build automated reliability and plausibility gates.
- Scope in: Test orchestration, scenario runner, sensitivity sweeps, distributional incidence analyzer.
- Scope out: New mechanics.
- Concrete deliverables:
- `docs/validation_suite.md`.
- `tools/run_validation.py`.
- `tests/stress/` scenarios for sanctions, energy, sudden stop, drought, banking panic, disinformation, polarization.
- `reports/validation_baseline.md`.
- Dependencies: Phases 2 to 6.
- Entry criteria: core systems feature complete for v0.1 model scope.
- Exit criteria: all mandatory gates pass on CI and local reproducible run.
- Validation gates: all required quality gates in Section 5 pass.
- Risks and mitigation: false confidence mitigated by mandatory adversarial scenario set.
- Estimated effort: Medium (1 week).

### Phase 8 - Spreadsheet UI Sheets and Causality Explorer
- Objective: Expose model state and driver decomposition through spreadsheet-first interface.
- Scope in: National Accounts, Supply Chains, Prices/Inflation, Labor/Distribution, Debt/FX, Demography/Mobility, Trust/Unrest sheets and causality pane.
- Scope out: Content expansion to multiple countries.
- Concrete deliverables:
- `src/ui/` sheet views.
- `src/ui/causality_explorer.py`.
- `tests/test_ui_metric_traceability.py`.
- `docs/ui_spec.md`.
- Dependencies: Phase 7.
- Entry criteria: validation framework stable.
- Exit criteria: every top-line metric has drilldown explanation path.
- Validation gates: traceability gate and no-hidden-modifier gate pass.
- Risks and mitigation: UI performance risk mitigated via cached aggregations and incremental rendering.
- Estimated effort: Large (2 weeks).

### Phase 9 - Content Pass (One-Country Baseline Scenario and Balancing Loop)
- Objective: Build one complete playable country dataset and run iterative balancing.
- Scope in: Scenario data, policy presets, baseline institutions, initial technology and supply tables.
- Scope out: Multi-country launch and large narrative event library.
- Concrete deliverables:
- `data/scenarios/baseline_1990_country_a.yaml`.
- `data/parameters/defaults.yaml`.
- `reports/calibration_log.md`.
- `reports/balance_iterations.md`.
- Dependencies: Phase 8.
- Entry criteria: UI and model traceability complete.
- Exit criteria: baseline campaign from 1990 to 2100 is stable and strategically interesting.
- Validation gates: long-run soak and distributional incidence gates pass under baseline and stress variants.
- Risks and mitigation: balance thrash mitigated by parameter freeze windows.
- Estimated effort: Large (2 to 3 weeks).

### Phase 10 - Vertical Slice Hardening and Release Readiness
- Objective: Finalize reliability, UX clarity, onboarding, and release checklist.
- Scope in: Bug fixing, performance profiling, tutorial flow, telemetry for post-release tuning.
- Scope out: major new mechanics.
- Concrete deliverables:
- `docs/release_checklist.md`.
- `docs/known_issues.md`.
- `reports/performance_profile.md`.
- `CHANGELOG.md` with v0.1 notes.
- Dependencies: Phase 9.
- Entry criteria: one-country campaign playable end-to-end.
- Exit criteria: release candidate passes all quality gates and acceptance scenarios.
- Validation gates: full gate suite pass and regression suite green.
- Risks and mitigation: late-breaking regressions mitigated by release branch freeze and triage SLA.
- Estimated effort: Medium (1 to 2 weeks).

## 3. Mandatory Phase Breakdown
- Phase 0: Project setup and architecture skeleton.
- Phase 1: Tick engine and deterministic state pipeline.
- Phase 2: Economic accounting core (GDP identities plus sector balances).
- Phase 3: Production, inventories, and constrained supply chains.
- Phase 4: Price system, inflation decomposition, and labor/wage block.
- Phase 5: Fiscal, debt, monetary, and FX/external sector.
- Phase 6: Sociology layer (cohorts, mobility, trust, legitimacy, unrest).
- Phase 7: Validation framework (identity checks, soak tests, sensitivity tests, incidence tests).
- Phase 8: Spreadsheet UI sheets plus causality explorer.
- Phase 9: Content pass (one-country baseline scenario plus balancing loop).
- Phase 10: Vertical slice hardening and release readiness.

## 4. Artifacts to Produce Per Phase

| Phase | Required artifacts |
|---|---|
| 0 | `docs/architecture.md`, `README.md`, initial `docs/tick_order_spec.md` |
| 1 | `src/core/tick_engine.py`, `src/core/state_store.py`, `tests/test_replay_determinism.py` |
| 2 | `src/econ/national_accounts.py`, `src/econ/sector_balances.py`, `docs/data_dictionary.md` (v1) |
| 3 | `src/econ/production.py`, `src/econ/inventory.py`, `tests/test_supply_constraints.py` |
| 4 | `src/econ/pricing.py`, `src/econ/labor.py`, `docs/parameter_registry.md` (v1) |
| 5 | `src/econ/fiscal.py`, `src/econ/debt.py`, `src/econ/external_sector.py` |
| 6 | `src/social/*.py`, `tests/test_social_state_consistency.py` |
| 7 | `docs/validation_suite.md`, `tools/run_validation.py`, `reports/validation_baseline.md` |
| 8 | `src/ui/*`, `docs/ui_spec.md`, traceability tests |
| 9 | scenario data packs in `data/scenarios/`, `reports/calibration_log.md`, `reports/balance_iterations.md` |
| 10 | `CHANGELOG.md`, `docs/release_checklist.md`, `reports/performance_profile.md` |

Always maintain and update across all phases:
- `docs/tick_order_spec.md`.
- `docs/data_dictionary.md`.
- `docs/parameter_registry.md`.
- `docs/validation_suite.md`.
- `CHANGELOG.md`.

## 5. Testing and Quality Gates (Pass/Fail)

A phase cannot close unless all applicable gates pass.

- Deterministic replay checks:
- Same seed plus inputs must reproduce identical outputs across runs.
- Hash of state snapshots at fixed ticks must match golden outputs.

- Stock-flow consistency:
- GDP and sector-balance identities within tolerance.
- Debt and reserves must reconcile against flow statements.

- Social-state consistency:
- Population conservation under births/deaths/migration.
- Cohort shares and ideology-share vectors sum to 1.0 within tolerance.

- Stress scenario stability:
- Sanctions, energy shock, sudden stop, drought, banking panic, disinformation, and polarization scenarios run without invalid states.

- Traceability and transparency:
- No hidden modifiers without trace logs.
- Each headline metric has contribution decomposition.

Recommended gate thresholds:
- Identity residual < 0.1 percent of nominal GDP per tick.
- Zero NaN or infinite values in core state arrays.
- 1000-tick soak pass for baseline and at least 3 stress variants.

## 6. Team Workflow

### Branch strategy
- `main`: always releasable.
- `develop`: integration branch.
- `feature/<area>-<short-name>` for new work.
- `hotfix/<issue-id>` for production blockers.

### PR checklist
- Tests added or updated.
- Determinism preserved.
- Data dictionary and parameter registry updated if fields or coefficients changed.
- Changelog entry added.
- Performance impact noted.
- Traceability output verified for changed metrics.

### Definition of done
- Code merged with green CI.
- Documentation updated.
- Validation gates for relevant phase passed.
- No unresolved blockers or hidden TODO in critical path modules.

### Issue labeling
- `phase-0` to `phase-10`.
- `system-econ`, `system-social`, `system-ui`, `system-validation`.
- `risk-high`, `risk-medium`, `risk-low`.
- `bug`, `design`, `data`, `performance`, `tooling`.

### Solo-dev variant
- Use one active feature branch at a time.
- Run full validation nightly and mini validation after each merge.
- Timebox balancing changes to prevent endless tuning loops.

### Small-team variant (2 to 5 people)
- Assign ownership by subsystem with one integration owner.
- Weekly integration freeze window.
- Shared parameter review board for coefficient changes.

## 7. First 14-Day Execution Sprint

### Day-by-day plan
- Day 1: Create repo structure, architecture doc, CI baseline.
- Day 2: Implement deterministic RNG and seed plumbing.
- Day 3: Implement state container and snapshot hashing.
- Day 4: Implement tick loop with stage stubs and stage contracts.
- Day 5: Add replay determinism tests for 24-tick and 240-tick runs.
- Day 6: Implement national accounts ledger and GDP identity checks.
- Day 7: Implement sector balances and reconciliation reports.
- Day 8: Add accounting tests and residual threshold assertions.
- Day 9: Implement minimal production with one-sector bottleneck prototype.
- Day 10: Implement inventory carryover and shortage logic.
- Day 11: Create `docs/data_dictionary.md` and `docs/parameter_registry.md` v1.
- Day 12: Add baseline scenario seed data for one country.
- Day 13: Run first 120-tick baseline and fix determinism or identity breaks.
- Day 14: Publish sprint report and lock Phase 1 to Phase 2 transition checklist.

Build first:
- Deterministic pipeline and accounting core.

Test first:
- Replay determinism and identity checks.

Postpone until later:
- Rich UI, advanced events, extra countries, and narrative content.

## 8. Open Risks (Top 10)

1. Non-deterministic behavior in runtime dependencies.
- Early warning: snapshot hashes diverge across identical runs.
- Response: isolate all randomness through seeded adapter and ban direct random calls.

2. Accounting sign errors in ledgers.
- Early warning: persistent identity residual spikes.
- Response: enforce dual-entry templates and automated ledger audits.

3. Supply-chain solver instability.
- Early warning: oscillating shortages or negative inventories.
- Response: bounded iterations, fallback allocator, and debug traces.

4. Inflation runaway from parameter interactions.
- Early warning: explosive CPI under moderate shocks.
- Response: clamp expectation channels and recalibrate pass-through coefficients.

5. Debt-crisis over-triggering.
- Early warning: frequent insolvency in normal scenarios.
- Response: revise refinancing assumptions and risk-premium sensitivity.

6. Sociological feedback loops too strong or too weak.
- Early warning: constant unrest or inert political layer.
- Response: add lag smoothing and rebalance trust-legitimacy weights.

7. Hidden modifiers breaking explainability.
- Early warning: metric deltas without trace attribution.
- Response: mandatory trace schema and CI gate blocking untraced changes.

8. Performance degradation from trace-heavy simulation.
- Early warning: tick time exceeds target budget.
- Response: switch to sampled trace depth and cached decomposition paths.

9. Balance drift during content pass.
- Early warning: repeated parameter churn with no convergence.
- Response: parameter freeze windows and controlled experiment logs.

10. UI built before model maturity.
- Early warning: frequent UI rewrites and broken metric semantics.
- Response: enforce phase gate that blocks major UI build before validation framework completion.
