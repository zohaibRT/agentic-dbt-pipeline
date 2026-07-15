# Universal Analytics Framework

Use this during discovery, analytics insight reporting, semantic design, and presentation-layer planning.

## Core rule

Maximize useful report results from validated data, but do not maximize noise.

The agent should discover the broadest safe analytics surface, then organize it into business-friendly catalogs and report pages. Do not turn every column into a chart, and do not promote every metric into a key performance indicator.

## Analytics hierarchy

Use this hierarchy before writing report SQL, semantic metrics, or presentation visuals:

```text
Business
  -> Department or business area
  -> Business process
  -> Key performance indicators
  -> Metrics
  -> Measures
  -> Dimensions
  -> Facts
```

The hierarchy is discovery guidance, not a hardcoded domain template. If departments or business areas are not obvious from source data, infer only safe candidates and mark them as `Needs business confirmation`.

## Universal discovery questions

Ask these through source evidence first, then through targeted user questions only when the answer affects modeling or reporting:

| Question | Purpose |
|---|---|
| What business domain is represented? | Frame the language and likely processes |
| Which departments or business areas appear? | Organize analytics into useful report sections |
| Which business processes generate events? | Identify facts and workflow metrics |
| Which entities are being managed? | Identify dimensions and slicers |
| Which financial or value fields exist? | Identify revenue, cost, payment, balance, and margin measures |
| Which date fields matter? | Build trends, freshness, cycle time, and period comparisons |
| Which statuses or stages exist? | Build funnels, backlog, completion, failure, and quality metrics |
| Which calculations are clear from evidence? | Create trusted measures and metrics |
| Which calculations need business rules? | Defer or ask targeted questions |
| Which comparisons are useful? | Month-over-month, year-over-year, year to date, last 12 months, target variance |
| Which data quality rules apply? | Protect trust before presentation |

## Universal measure families

Create broad raw measures where grain and SQL proof are clear:

| Family | Examples |
|---|---|
| Volume | total records, total events, total transactions, total entities, completed count, failed count, open count |
| Financial or value | revenue, cost, profit, margin, discount, tax, refund, balance, outstanding, receivable, payable |
| Time | created date, updated date, completed date, cancelled date, duration, waiting time, processing time |
| Growth | current period, previous period, month-over-month change, year-over-year change, year to date |
| Customer or entity | new, returning, active, inactive, retained, churned, repeat activity |
| Product or service | sold quantity, inventory, stock, returns, defects, utilization |
| Quality | errors, failed records, rejected records, cancelled records, duplicate records, missing values |
| Operational | completed jobs, pending jobs, open tickets, closed tickets, backlog, workload, productivity |
| Service | tickets, calls, complaints, resolutions, first response time, resolution time, satisfaction |
| Marketing or funnel | impressions, clicks, leads, conversions, campaign cost, conversion rate |

Add process-specific families only when source evidence supports them for **this** warehouse. Do not import another industry’s KPI family when the tables are absent.

## Universal dimensions

Consider slicers, grouping fields, drill-downs, or report page filters **only when validated and present in evidence**. There is no mandatory dimension checklist. Illustrative labels (for example customer, product, employee, supplier, or salesperson) are examples of common patterns—never required entities for every project.

Build dimensions from discovered keys, join paths, and business questions for **this** warehouse. Skip classes that have no supporting tables.

Do not expose direct identifiers or sensitive business fields without approval (or under a recorded privacy opt-out for reporting attributes — see [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md)).

## Report result maximization

For each validated fact or event model:

1. Create volume measures.
2. Create amount, quantity, duration, and quality measures when fields exist.
3. Create status and stage distributions when categorical workflow fields exist.
4. Create date coverage and time-trend metrics when usable date fields exist.
5. Create rankings by safe dimensions when the dimension key and label are validated.
6. Create ratios only when numerator and denominator are both clear and reconciled.
7. Create backlog or aging metrics only when open/pending state and date logic are clear.
8. Create growth metrics only when date range supports comparison.
9. Put blocked or ambiguous ideas into `insight_backlog.md` with the missing proof.

For each safe dimension:

1. List its business meaning and source model.
2. Record row count, distinct key count, duplicate key count, and null key count.
3. Identify which facts it can slice without ambiguous relationships.
4. Use its human-readable label in dashboards; avoid raw codes or keys.

## Dashboard page maximization

Build the richest useful dashboard design the validated data can support. Recommended page set:

| Page | Purpose |
|---|---|
| Executive Overview | Strategic key performance indicators, short narrative, top risks, and next actions |
| Trends and Variance | Time showcase, period movement, year to date, last 12 months, month-over-month, year-over-year when supported |
| Financial or Value | Revenue, cost, payment, balance, outstanding, margin, average value, or equivalent value metrics |
| Operations and Activity | Volumes, statuses, workflow movement, backlog, completions, failures |
| Entity Performance | Customer, employee, product, supplier, department, location, account, or other entity performance when dimensions exist |
| Segmentation and Drivers | Safe dimensions that explain variance, outliers, or concentration |
| Quality and Exceptions | Missing values, duplicates, orphan records, invalid statuses, failed events, outliers |
| Detail and Drill-Down | Operational matrix or table for safe investigation |
| Report Information | Purpose, audience, data sources, metric definitions, filters, caveats, privacy, validation evidence |

Omit a page only when the data cannot support it, and document the reason.

## Promotion rules

- Measures are raw counts, sums, averages, minimums, maximums, and date coverage.
- Metrics add context through time, dimension, ratio, ranking, aging, funnel, or quality logic.
- Key performance indicators are the strategic subset tied to decisions, targets, thresholds, risk, management review, revenue, cost, service, quality, or explicit user approval.

Use many measures and metrics. Use fewer, better key performance indicators.

## Trust rules

No result is trusted unless it has:

- Clear source model and grain.
- Clear formula and filters.
- Safe dimensions.
- SQL proof file with captured result.
- Cardinality and relationship evidence when joins are involved.
- Privacy review when presentation-facing.

If a useful result cannot satisfy these requirements, keep it visible as deferred or blocked rather than deleting it silently.

## Do not use

- `5 key performance indicators from each table` on every table
- Key performance indicators from column names alone
- Numbers in catalogs or reports without `sql_proofs/*.sql`
- Equal key performance indicator quotas on dimensions, bridges, reference tables, or audit tables
- Promoting every useful metric into `kpi_catalog.md`

Read [../docs/kpi_proof_standards.md](../docs/kpi_proof_standards.md) for the full proof standard and completion gate.

## Table classification guidance (advisory only)

Classify each included source or gold table before writing catalogs. Coverage is driven by **process and fact completeness**, not by fixed row quotas. Counts below are **optional planning heuristics** — they are **not** acceptance-gate failures unless the project explicitly sets `analytics_policy.advisory_*_target` and enables advisory checks.

| Table type | Illustrative examples | Typical measures (advisory) | Typical metrics (advisory) | Key performance indicator candidates |
|---|---|---:|---:|---:|
| Fact / event | primary facts evidenced in the project | enough for grain/volume/value/status/time/quality | enough for process questions | only strategic / approved items |
| Dimension | entity and descriptive dimensions evidenced in the project | light row/freshness counts | optional quality mixes | 0–1 only if strategic |
| Bridge | evidenced bridge between facts | relationship health measures | optional | usually none |
| Reference / catalog | reference/catalog dims when present | light | usually none | 0 unless business asks |
| Audit / system | audit, job queue, oauth tables | 0 business measures | 0 | exclude (pipeline/DQ catalogs instead) |

Do **not** treat 5–10 / 3–6 / 2–4 (or any fixed per-fact quota) as a hard completion gate.

## Business-process coverage (required shape, not fixed counts)

Record project-specific process names in `business_process_catalog.md`. Before analytics insight reporting can be `PASS`, each **material** process must have evidence-backed coverage for applicable families (volume, value when amounts exist, status, time, quality, reconciliation, segmentation). Fixed “8+ metrics / 4+ KPIs” style quotas are **advisory examples only** — enable only via `analytics_policy` advisory targets when a team wants them.

| Process class (illustrative) | Coverage expectation |
|---|---|
| Primary lifecycle / core value process | Full applicable families + approved strategic KPIs |
| Secondary transaction or supporting process | Applicable families; fewer strategic KPIs |
| Segmentation / entity processes | Segmentation + quality; KPIs only when strategic |
| Data quality / reconciliation process | Metrics in DQ catalogs — not executive KPI boards |

### Advisory scale examples (never default gates)

When roughly 25–30 validated tables are in scope, some teams optionally track planning targets such as “about 60 measures / 35 metrics / 15 KPIs.” Those numbers must **not** drive `PASS`/`FAIL` unless configured in `project.config.yml` under `analytics_policy.advisory_*_target`. Primary gates remain process/fact/KPI-contract/reconciliation coverage.

Validate with process-coverage scripts (defaults):

```bash
python scripts/check_analytics_coverage.py --root .
python scripts/validate_kpi_proofs.py --root .
```

Optional advisory count check (only when explicitly requested):

```bash
python scripts/validate_kpi_proofs.py --root . --min-measures 60 --min-metrics 35 --min-kpis 15
```

## Per fact table checklist

For each gold fact in `fact_catalog.md`, verify:

- Row count and distinct grain key
- Status distribution with business labels, not raw codes
- Amount sums where amount columns exist
- Date coverage and monthly trend
- At least one rate or ratio
- At least one dimensional split
- Source → gold reconciliation for the top three measures

## Required discovery artifacts

Before analytics insight reporting = `PASS`, create or update:

- `kpi_discovery_matrix.md` — every fact table × measure families with confidence
- `business_process_catalog.md`
- `fact_catalog.md`
- `dimension_catalog.md`
- `measure_catalog.md`
- `metric_catalog.md`
- `kpi_catalog.md`
- `insight_backlog.md`
- `sql_proofs/` — one proof file per published measure, metric, or key performance indicator

## Presentation mapping rule

Map every key performance indicator in `kpi_catalog.md` to a chart, summary visual, or explicit `BLOCKED` / `DEFERRED` note in `kpi_figure_coverage.md`. Supporting measures and metrics should appear in classified report tabs when marked recommended or trusted.
