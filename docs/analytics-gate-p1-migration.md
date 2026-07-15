# Analytics Gate P1 Migration

This note maps legacy acceptance/analytics gate behavior to the P1 (process-coverage) model.

## Acceptance gate CLI

| Old behavior | New behavior |
|---|---|
| Single full gate run | `--phase discovery\|bronze\|silver\|gold\|semantic\|analytics\|presentation\|final` scopes checks cumulatively |
| Implicit default = full project | Default phase = `analytics` when `reports/agent/09_analytics_insights/` exists, else `final` |
| WARN exits 0 unconditionally | WARN exits 0 only when accepted; unaccepted WARN fails under final/strict policy |
| No warning registry | `--accepted-warning-file PATH` plus control-plane accepted-warning lines |
| No rendered HTML scan in gate | `validate_rendered_report_content.py` runs with `--report-dir .../matplotlib` (SKIPPED when no `report.html`) |

New flags:

```bash
python scripts/run_acceptance_gate.py --root . --phase final --strict
python scripts/run_acceptance_gate.py --root . --fail-on-warning --accepted-warning-file reports/agent/accepted_warnings.txt
```

`acceptance_policy.final_fail_on_warning` (default `true`) participates in the same warning-enforcement OR-chain as `--phase final`, `--strict`, and `--fail-on-warning`.

## KPI proof validator

| Legacy format | P1 format | Compatibility |
|---|---|---|
| `measure_catalog.md` only | `business_measure_catalog.md` preferred | Legacy still accepted when separated catalog absent |
| `metric_catalog.md` only | `business_metric_catalog.md` preferred | Legacy still accepted when separated catalog absent |
| Combined QA rows in metric catalog | `data_quality_metric_catalog.md`, `pipeline_health_metric_catalog.md` | Additive; specialized catalogs count toward metric totals |
| Hard-required `dimension_catalog.md`, `kpi_discovery_matrix.md`, `insight_backlog.md` | Optional recommended artifacts | Missing optional files no longer fail proof validation |
| Path-regex proof checks only | `validate_sql_proof_file()` for catalog proof refs | Proof must include SQL, expected/acceptance rule, captured result, status |

Default `--min-measures`, `--min-metrics`, and `--min-kpis` remain `0`.

## Fact-table checklist vocabulary

| Legacy wording | P1 wording |
|---|---|
| “At least one rate or ratio” (mandatory) | Rate/ratio row marked **SUPPORTED** or **NOT_APPLICABLE** with evidence |
| “At least one dimensional split” (mandatory) | Dimensional split row marked **SUPPORTED** or **NOT_APPLICABLE** |
| Implicit pass/fail only | Explicit **SUPPORTED**, **NOT_APPLICABLE**, **BLOCKED**, **DEFERRED** per check |

## Validation Type column

Contracts, proof files, and verification matrices may use:

`numeric_exact`, `numeric_tolerance`, `ratio_tolerance`, `row_count_match`, `set_match`, `acceptance_rule`, `blocked`, `deferred`.

## Domain neutrality expansion

Executable skill code is now also scanned for:

- Hardcoded KPI formulas such as `required ... count(*) from orders`
- Hardcoded revenue/page mandates such as `must use revenue =` or `mandatory page ... Sales Dashboard`
- Hardcoded `required_sources = [` lists in scripts

Fixtures, tests, and illustrative examples remain excluded.

## Recommended migration steps

1. Add separated catalogs (`business_measure_catalog.md`, `business_metric_catalog.md`, optional QA/pipeline catalogs).
2. Mark fact checklist rows with applicability status instead of assuming every family applies.
3. Re-run `python scripts/validate_kpi_proofs.py --root .` then `python scripts/run_acceptance_gate.py --root . --phase analytics --skip-dbt`.
4. Record accepted warnings in `CONTEXT_TREE.md`, `PIPELINE_STATUS.md`, `HUMAN_ATTENTION_BOARD.md`, or `--accepted-warning-file` before `--phase final`.

See also [analytics-product-completeness-migration.md](analytics-product-completeness-migration.md).
