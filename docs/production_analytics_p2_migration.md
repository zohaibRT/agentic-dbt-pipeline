# Production Analytics P2 Migration

This document summarizes behavior changes introduced by the P2 production gate correctness fixes.

## Fact coverage (`check_fact_analytical_coverage.py`)

| Old behavior | New behavior |
|---|---|
| Generic `status` column alias satisfied `status_family` | Only `status_distribution`, `status_mix`, `workflow_state_analysis` count |
| Any nonempty analytical cell counted as evaluated | Each family requires explicit `SUPPORTED`, `NOT_APPLICABLE`, `BLOCKED`, or `DEFERRED` |
| `SUPPORTED` treated as any nonempty value | `SUPPORTED`/`PASS` normalized; invalid tokens fail |
| Overall row status could collide with analytical Status column | Overall status read only via `named_status` on final Status column |
| Legacy duplicate Status columns lost middle value | Positional parse maps first Status → `status_distribution`, last → overall Status |
| Seven analytical families | Sixteen families: grain, counting_key, primary_date, volume, amount_or_quantity, duration_or_balance, status_distribution, lifecycle, dimensions, time_trends, period_comparison, data_quality, exceptions, aging, reconciliation, business_questions |

**Migration:** Rename middle `Status` column to `Status Distribution`. Add missing columns from `templates/reports/09_analytics_insights/fact_coverage_contracts.md`. Populate applicability tokens explicitly.

## KPI contracts (`check_metric_contract_completeness.py`)

| Old behavior | New behavior |
|---|---|
| `formula` and `business_definition` were aliases | Separate required columns when expanded schema present |
| Missing business_definition silently passed if formula present | One-time WARN during migration; FAIL when Business Definition column exists |
| BLOCKED/DEFERRED missing fields were warnings for next_action | Hard errors for reason, missing_evidence, owner, next_action |
| No conditional field rules | Ratio metrics require numerator/denominator; currency format requires currency |

**Migration:** Add **Business Definition** column separate from **Formula**. Fill deferred section with Owner and Next Action.

## Metric reconciliation (`verify_metric_reconciliation.py`)

| Old behavior | New behavior |
|---|---|
| `set_match` and `acceptance_rule` trusted recorded PASS | Independently calculated; PASS contradictions fail |
| Free-text expected counted as acceptance rule | Requires `acceptance_rule_id` or `rule_id` plus proof |
| Nonnumeric without validation_type warned only | `set_match` computes missing/unexpected sets |

**Migration:** Set `validation_type` explicitly. For set checks, document expected/actual as delimited token lists. For acceptance rules, add `acceptance_rule_id`.

## Data observability (`check_data_observability_coverage.py`)

| Old behavior | New behavior |
|---|---|
| Pipeline reliability NOT_APPLICABLE waived DQ catalog | DQ catalog always required when analytics in scope |
| Minimal column set | Expanded columns documented in template; legacy tables warn |
| NOT_APPLICABLE only needed notes | Requires notes and owner; reassessment_condition recommended |

## Time intelligence (`check_time_intelligence_coverage.py`)

| Old behavior | New behavior |
|---|---|
| Display names counted as published metric obligations | Only `metric_id` / `kpi_id` from contracts and catalogs |
| Display names could satisfy coverage rows | Coverage rows must include `metric_id`; display names are attributes |

## Exposure coverage (`check_exposure_coverage.py`)

| Old behavior | New behavior |
|---|---|
| Only `exposures*.yml` scanned | All `models/**/*.yml|yaml` with `exposures:` keys |
| Presentation without dbt exposure warned | FAIL when `dbt_project.yml` exists unless BLOCKED with owner + next_action |

## Report page contracts (`check_report_page_contracts.py`)

| Old behavior | New behavior |
|---|---|
| Dimensions inferred from fact list (`list_gold_fact_names`) | Dimensions from classification (`class=dimension`) or `dim_*` prefix |

## Independent verification

New script: `scripts/run_independent_verifier.py`

- Runs core validators in fresh subprocesses
- Writes `reports/agent/INDEPENDENT_VERIFICATION_REPORT.md` and `.json`
- Wired into `run_acceptance_gate.py` FINAL phase

## Shared helpers (`lib_gate_common.py`)

New helpers: `parse_set`, `reconcile_set_match`, `reconcile_acceptance_rule`, `list_gold_dimension_names`.

## Fixture rebuild

Regenerate fixtures after pulling these changes:

```bash
python scripts/build_analytics_fixtures.py
python scripts/build_dbt_duckdb_fixtures.py
```

## Tests

New regression coverage in `tests/test_p2_gate_fixes.py`.

`tests/test_interactive_reporting.py::DuckDbFixtureGateTests` rebuilds `domain_a_transactional` when control-plane files are missing, then runs `run_acceptance_gate.py --phase final --strict --skip-dbt`.

## Interactive charting and presentation (P2+)

### Chart registry and hover contracts

- `chart_registry.json` defines chart metadata, metric bindings, and expected tooltip text.
- `validate_chart_registry.py` enforces unique `chart_id` values and manifest cross-links.
- `chart_interactivity_contracts.md` documents hover/click expectations per chart.
- Tooltip text must match registry `tooltip_text` values (see `tooltip_matches_registry` in `validate_live_report_dom.py`).

### Live DOM validation

- `validate_live_report_dom.py` loads `report.html` in headless Chromium via Playwright.
- Verifies KPI cards, chart canvases, tab navigation, and tooltip content against `chart_registry.json`.
- Writes `LIVE_REPORT_DOM_REPORT.md` and `.json` under `reports/agent/`.
- Optional screenshots and traces land under `reports/agent/10_presentation/matplotlib/` when enabled.

### Warning policy at final gate

- `--phase final --strict` converts unaccepted `WARN` checks to `FAIL`.
- Accept warnings explicitly in `CONTEXT_TREE.md`, `PIPELINE_STATUS.md`, or `HUMAN_ATTENTION_BOARD.md` using tokens parsed by `load_accepted_warnings()`:
  - `accepted warning: <id>`
  - `warning id: <id>`
  - Bullet lines like `- [ACCEPTED] source_freshness`
- Fixture projects prefer adding evidence (source `freshness:`, CI workflow stubs) so checks `PASS` instead of documenting accepted warnings.

### CI detection

- `run_acceptance_gate.py` passes `--allow-skip` to `validate_live_report_dom.py` only when `CI` is unset.
- GitHub Actions sets `CI=true` in `analytics_gates.yml`; Playwright must be installed (`requirements-ci.txt` + `playwright install chromium`).
- Fixture roots include `.github/workflows/fixture_ci.yml` so operational CI checks detect orchestration evidence inside fixture projects.
- On failure, CI uploads `LIVE_REPORT_DOM_REPORT*`, `INDEPENDENT_VERIFICATION*`, `ACCEPTANCE_GATE*`, screenshots, traces, `chart_registry.json`, and `rendered_metric_manifest.json`.
