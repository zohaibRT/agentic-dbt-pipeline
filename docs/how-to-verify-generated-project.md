# How To Verify a Generated dbt Project

Use this guide after the builder agent runs on a real project. It answers one question:

**How do I know the generated code, layers, and KPIs are going in the right direction?**

## Short answer

You are on track when all four correctness levels are green:

| Level | Proves | Main evidence |
|---|---|---|
| Technical | SQL runs and dbt tests pass | `dbt build`, `target/run_results.json` |
| Data | Row counts, grain, joins, amounts make sense | `reports/agent/**/sql_proofs/` |
| Business | Definitions match approved requirements | traceability matrix, KPI contracts |
| Independent | A fresh auditor agrees | acceptance gate + verifier report |

`dbt build` passing is necessary. It is not sufficient.

## Five-minute status check

Read in this order:

1. `reports/agent/PIPELINE_STATUS.md`
2. `reports/agent/REPORT_INDEX.md`
3. `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md`
4. `reports/agent/LAYER_VERIFICATION_LEDGER.md`
5. One phase folder per built layer, especially `sql_proofs/`

Red flags:

- `FAIL` or `BLOCKED` in `PIPELINE_STATUS.md`
- missing proof files for important claims
- KPI in catalog with no linked SQL proof
- agent says complete but acceptance gate failed

## Verification stack

```text
Human sign-off
Independent verifier agent
Acceptance scripts
KPI reconciliation
Assumption dbt tests
Warehouse sql_proofs
Structural dbt tests
```

Work from bottom to top.

## After each layer

### Bronze / staging

Check:

- source row count vs staging row count when 1:1 is expected
- primary keys: no nulls, no duplicates
- proofs in `reports/agent/03_bronze/sql_proofs/`

### Silver / intermediate

Check:

- row count before join vs after join
- grain still one row per business key
- proofs in `reports/agent/04_silver/sql_proofs/`

### Gold / marts

Check:

- facts have rows when upstream has rows
- dimension keys are unique
- measure summaries are sane
- proofs in `reports/agent/05_gold/sql_proofs/`

Red flags:

- empty gold while source has data
- `after_join > before_join` with no explanation
- assumption only in chat, not in `tests/`

## Two kinds of dbt tests

| Kind | Examples | Catches |
|---|---|---|
| Structural | `unique`, `not_null`, `relationships`, `accepted_values` | schema and orphan issues |
| Assumption | grain after join, date order, status implies field, cross-check totals | business beliefs that break later |

See [references/assumption-tests.md](../references/assumption-tests.md).

Process:

```text
State assumption -> prove in sql_proofs -> lock in dbt test
```

## KPI and metric verification

Start with:

- `reports/agent/09_analytics_insights/kpis/kpi_variance_report.md`
- `reports/agent/KPI_DEFINITION_CONTRACTS.md`
- `reports/agent/METRIC_VERIFICATION_MATRIX.md`

For every rate or ratio KPI, verify independently:

- numerator count or sum
- denominator count or sum
- excluded rows and why
- same number at source, silver, gold, semantic, and presentation

Classic trap: denominator excludes failure states, so the rate looks artificially high.

Re-run proof files such as:

```text
reports/agent/09_analytics_insights/kpis/sql_proofs/<kpi>_gold.sql
reports/agent/09_analytics_insights/kpis/sql_proofs/<kpi>_semantic.sql
```

Confirm the captured result in the file header still matches a live warehouse run.

## SQL proof file numbering

The first three digits are proof categories, not a simple counter.

| Band | Meaning |
|---|---|
| 001 | source inventory |
| 010-019 | row counts |
| 020-029 | key / grain checks |
| 030-039 | status or category distributions |
| 040-049 | date coverage |
| 050-059 | amount or quantity summaries |
| 060-069 | relationship checks |
| 070-079 | bridge or cardinality checks |
| 080-089 | compare or data-quality checks |

Example:

- `010_crm_tos_subscriptions_row_count.sql` = row-count proof for subscriptions
- `011_crm_tos_devices_row_count.sql` = another row-count proof in the same band

## Automated commands

Run from the generated dbt project root:

```bash
dbt build
python scripts/run_acceptance_gate.py --root .
python scripts/check_requirement_traceability.py --root .
python scripts/check_layer_proof_coverage.py --root .
python scripts/validate_kpi_proofs.py --root . --require-sql-proofs
python scripts/verify_metric_reconciliation.py --root .
```

Then run a fresh verifier session with [agents/dbt-verifier-agent.md](../agents/dbt-verifier-agent.md) and read:

```text
reports/agent/INDEPENDENT_VERIFICATION_REPORT.md
reports/agent/ACCEPTANCE_GATE_REPORT.md
```

Do not accept final delivery on `FAIL`.

## Manual spot checks worth doing

Even when scripts pass:

1. Re-run 2-3 `sql_proofs/*.sql` files per layer at random.
2. Compare captured result in the file header to your live query result.
3. Re-derive numerator and denominator for your top 2-3 business KPIs from the business definition, not only from agent SQL.
4. Check one join and one measure using the layer validation patterns in [references/layer-data-validation.md](../references/layer-data-validation.md).

## Green vs red signals

### Green

- discovery approved before build
- each built layer has report + proofs with `PASS`
- requirements trace to real models
- KPI variance report is clean or explained
- assumption tests exist for approved beliefs
- acceptance gate and verifier are `PASS` or documented `WARN`

### Red

- proofs missing or never re-run
- captured results do not match live SQL
- join multiplied rows silently
- KPI is 0% or 100% with no business explanation
- only chat memory, no files or tests
- acceptance gate or verifier returns `FAIL`

## Who verifies what

| Role | Responsibility |
|---|---|
| Builder agent | build, proofs, reports, tests |
| You | approve assumptions, spot-check proofs, approve KPI meaning |
| Scripts | deterministic pass/fail |
| Verifier agent | independent audit from repo only |
| CI | block bad merges when enabled |

## One-line summary

> Trust files you can re-run, tests that guard approved assumptions, and reconciliation that traces KPIs from source to presentation — not chat summaries alone.

## Related docs

- [how-the-skill-works-marp.md](how-the-skill-works-marp.md) — presentation deck
- [references/evidence-driven-dbt-process.md](../references/evidence-driven-dbt-process.md) — evidence-first rules
- [references/assumption-tests.md](../references/assumption-tests.md) — structural vs assumption tests
- [references/independent-verification-governance.md](../references/independent-verification-governance.md) — verifier and CI model
