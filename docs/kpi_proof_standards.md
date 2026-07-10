# Key Performance Indicator Proof Standards

Use this during analytics insight reporting, semantic layer design, presentation planning, and final delivery.

Also read:

- [references/universal-analytics-framework.md](../references/universal-analytics-framework.md)
- [references/kpi-discovery-framework.md](../references/kpi-discovery-framework.md)
- [references/kpi-definition-contract.md](../references/kpi-definition-contract.md)
- [references/metric-verification-checklist.md](../references/metric-verification-checklist.md)
- [references/kpi-reconciliation.md](../references/kpi-reconciliation.md)
- [references/metric-verification.md](../references/metric-verification.md)

## Core rule

Use the hierarchy:

```text
measures -> metrics -> key performance indicators
```

Maximize **useful validated coverage**, not chart count or catalog row count for its own sake.

Every number that appears in:

- `KPI_DEFINITION_CONTRACTS.md`
- `METRIC_VERIFICATION_MATRIX.md`
- `measure_catalog.md`
- `metric_catalog.md`
- `kpi_catalog.md`
- executive summary text
- `dashboard_spec.md`
- Matplotlib or Power BI presentation outputs

must have a matching SQL proof under:

```text
reports/agent/09_analytics_insights/kpis/sql_proofs/
```

unless the row is explicitly marked `BLOCKED` or `DEFERRED` with evidence in `insight_backlog.md`.

## Do not use

- `5 key performance indicators from each table` on every table
- Key performance indicators inferred from column names alone
- Report numbers without `sql_proofs/*.sql`
- Raw warehouse codes on business-facing chart labels without `label_dictionary.md`
- Promoting every metric to `kpi_catalog.md`

## Do use — table classification first

Classify each included source or gold table, then apply minimum coverage by table type.

| Table type | Examples (illustrative only) | Minimum measures | Minimum metrics | Key performance indicator candidates |
|---|---|---:|---:|---:|
| Fact / event | subscriptions, orders, payments, order items | 5–10 per fact | 3–6 per fact | 2–4 per fact when `HIGH` or approved `MEDIUM` |
| Dimension | customer, partner, program | 2–4 | 1–3 | 0–1 only if strategic |
| Bridge | subscription-payment link | 2–3 | 1–2 | 0–1 |
| Reference / catalog | SKU, country, pricing | 1–2 | 0–1 | 0 unless business asks |
| Audit / system | audit, job queue, oauth | 0 business measures | 0 | exclude |

The phrase `5 per table` applies only to **fact/event** tables, not dimensions, bridges, reference tables, or audit tables.

## Business-process minimums

Before analytics insight reporting can be marked `PASS`, fill catalogs for each supported business process discovered in `business_process_catalog.md`.

Use this template:

| Business process | Minimum metrics | Minimum strategic key performance indicators (`HIGH` / approved `MEDIUM` + proof) |
|---|---:|---:|
| Primary lifecycle or core revenue process | 8+ | 4+ |
| Secondary transaction or fulfillment process | 4+ | 2+ |
| Partner, program, or segmentation process | 4+ | 2+ |
| Data quality / reconciliation process | 4+ | 0 key performance indicators (metrics only) |

Do not hardcode one client's process names into the skill. Record project-specific process names and minimums in `business_process_catalog.md`.

### Example scale for medium projects

When roughly 25–30 validated tables are in scope, a realistic target profile is:

| Catalog | Example target | Rule if short |
|---|---:|---|
| `measure_catalog.md` | 60+ measures | Document each shortfall in `insight_backlog.md` |
| `metric_catalog.md` | 35+ metrics | Document each shortfall with evidence |
| `kpi_catalog.md` | 15+ approved key performance indicators with SQL proofs | Not `5`; use bounded maximum useful coverage |
| `insight_backlog.md` | all `LOW` / `BLOCKED` candidates with reason | Required |

For a medium project with about five major facts, a realistic key performance indicator total is often **15–25**, not five.

## Required discovery artifacts

Before analytics insight reporting = `PASS`:

| Artifact | Purpose |
|---|---|
| `kpi_discovery_matrix.md` | Every fact table × measure families: volume, value, status, time, ratio, quality with confidence |
| `business_process_catalog.md` | Business areas, processes, and minimum coverage targets |
| `fact_catalog.md` | Fact grain, dates, amounts, statuses, relationships |
| `dimension_catalog.md` | Safe dimensions, labels, slicers, privacy |
| `measure_catalog.md` | All supported counts, sums, averages from gold facts |
| `metric_catalog.md` | Time, dimension, ratio, funnel, quality metrics from measures |
| `kpi_catalog.md` | Decision-relevant reconciled subset only |
| `reports/agent/KPI_DEFINITION_CONTRACTS.md` | Business contract, source mapping, expected result, actual result, approval, and verification status for every key performance indicator claim |
| `reports/agent/METRIC_VERIFICATION_MATRIX.md` | Source proof, mart proof, semantic proof, presentation proof, difference or tolerance, and status for important measures, metrics, and key performance indicators |
| `insight_backlog.md` | Deferred and blocked candidates with reasons |
| `sql_proofs/` | One proof file per published measure, metric, or key performance indicator |

## Per fact table checklist

For each gold fact, the agent must verify:

- [ ] Row count and distinct grain key
- [ ] Status distribution (counts per status with business labels)
- [ ] Amount sums (gross/net where columns exist)
- [ ] Date coverage (minimum, maximum, trend by month)
- [ ] At least one rate or ratio (failure %, conversion %, eligible %, etc.)
- [ ] At least one dimensional split (partner, program, type, channel, etc.)
- [ ] Source → gold reconciliation for top three measures

Record pass/fail evidence in `fact_catalog.md` or the phase report.

## SQL proof file standard

Location:

```text
reports/agent/09_analytics_insights/kpis/sql_proofs/
```

Filename pattern:

```text
010_measure_<measure_slug>.sql
110_metric_<metric_slug>.sql
210_kpi_<kpi_slug>.sql
```

Each proof file must include:

1. Business meaning
2. Source model and grain
3. Formula
4. Filters
5. Runnable SQL
6. Expected result or acceptance rule
7. Captured result at run time
8. `PASS`, `WARN`, `FAIL`, or `BLOCKED` status

Catalog rows must link to the proof file path. Do not paste SQL only in Markdown tables without a proof file.

## Key performance indicator promotion rules

Promote to `kpi_catalog.md` only when all are true:

- Confidence is `HIGH`, or `MEDIUM` with explicit user approval
- Grain and cardinality are proven
- Source-to-gold reconciliation is recorded
- SQL proof file exists and passed or is documented as blocked with reason

Keep useful non-strategic items in `measure_catalog.md` or `metric_catalog.md`. They are valuable and not “missing.”

## Presentation rule

The refreshable web report or presentation artifact must map **every key performance indicator in `kpi_catalog.md`** to:

- a chart or summary visual, or
- an explicit `BLOCKED` / `DEFERRED` row in `kpi_figure_coverage.md`

Measures and metrics from the broader catalogs should appear in supporting tabs when marked recommended or trusted.

## Completion gate

Analytics insight reporting cannot be marked `PASS` unless:

```bash
python scripts/validate_kpi_proofs.py --root .
python <installed-skill-path>/scripts/verify_metric_reconciliation.py --root <project.root>
```

pass, or the phase report documents each failed check with evidence and `insight_backlog.md` explains every catalog shortfall.

## Validation command

```bash
python scripts/validate_kpi_proofs.py --root .
python <installed-skill-path>/scripts/verify_metric_reconciliation.py --root <project.root>
```

Optional project-scale targets:

```bash
python scripts/validate_kpi_proofs.py --root . --min-measures 60 --min-metrics 35 --min-kpis 15
```

If targets are not met, `insight_backlog.md` must explain each gap with evidence. Do not mark the phase `PASS` silently.
