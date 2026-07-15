# Key Performance Indicator Discovery Framework

Use this during analytics insight reporting before finalizing `kpi_catalog.md`, semantic metrics, Power BI measures, or dashboard specifications. Also read [universal-analytics-framework.md](universal-analytics-framework.md) for business-area, process, measure, metric, dimension, and report-page coverage.

## Core Rule

Discover key performance indicators from evidence. Do not hardcode domain-specific metrics.

Use this order for every schema:

```text
Data structure first
Business process second
Measure candidate third
Contextual metric fourth
Key performance indicator promotion fifth
Confidence score sixth
User approval seventh
Semantic metrics and Power BI measures last
```

## Discovery Sequence

1. Classify source and gold tables.
2. Infer safe business areas, departments, processes, events, entities, and reporting opportunities.
3. Detect grain for every possible fact.
4. Detect candidate measures.
5. Create a broad `measure_catalog.md`.
6. Promote supported measures into contextual metrics in `metric_catalog.md`.
7. Map metrics to generic archetypes.
8. Promote only strategic, decision-relevant metrics into `kpi_catalog.md`.
9. Score confidence.
10. Ask targeted business questions only where needed.
11. Send approved metrics to semantic layer and presentation tooling.

## Table Classification

Classify each relevant table before deciding facts, dimensions, reports, or measures:

| Table Type | Meaning | Key Performance Indicator Potential |
|---|---|---|
| Entity or master table | Customers, products, suppliers, employees, accounts, counterparties, or other masters present in evidence | Dimensions and entity counts |
| Transaction or event table | Orders, appointments, invoices, settlements, payments, visits, bookings | Facts and primary metrics |
| Status or history table | Status changes, workflow movement, logs, lifecycle events | Funnel, aging, conversion, and backlog metrics |
| Bridge or link table | Many-to-many relationships | Segmentation and relationship analysis |
| Reference or code table | Status codes, categories, lookup values | Slicers, filters, and mapping seeds |
| Finance or amount table | Amounts, payments, balances, revenue, cost, fees, tax, discounts | Value, revenue, margin, paid, pending, and outstanding metrics |
| Date or activity table | Created, booked, settled, cancelled, closed, updated, completed dates | Trend, cycle-time, aging, and period comparison metrics |
| Audit or system table | Sync metadata, logs, loader tables, technical audit records | Usually excluded from business metrics |

## Grain Detection

Every key performance indicator candidate must state what one row represents.

Examples:

- One row per customer.
- One row per order.
- One row per payment.
- One row per appointment.
- One row per status change.
- One row per relationship/link.

Unknown or unvalidated grain lowers confidence or blocks the metric. Do not use `count(*)` as a business metric until the counting key and grain are understood.

## Candidate Measure Detection

Look for generic evidence, not hardcoded domain names:

| Candidate Type | Column Evidence | Examples |
|---|---|---|
| Count | Stable primary key, unique business key, event identifier | Total records, total transactions, total customers |
| Amount | Amount, price, balance, cost, fee, tax, discount, revenue, sale, deposit, paid, outstanding | Total amount, paid amount, outstanding amount, average value |
| Quantity | Quantity, days, hours, duration, units, area, capacity, visits | Total quantity, average duration, utilization |
| Status or funnel | Status, stage, type, category, active flag, cancelled flag, deleted flag, closed flag, approved flag | Status mix, completed count, conversion rate, backlog |
| Date or time | Created, updated, booked, settled, payment, appointment, closed, cancelled, completed dates | Daily trend, monthly trend, year to date, cycle time |
| Ranking | Fact measure plus safe dimensions | Top customers, top products, top locations, top providers |

Create `measure_catalog.md` before deciding key performance indicators. Include broad raw measures even when they are not strategic key performance indicators yet. The goal is maximum useful metric coverage from validated data, not a tiny executive-only list.

Recommended measure categories:

- Counts: row counts, distinct entity counts, event counts, completed counts, failed counts, open counts.
- Amounts: gross, net, paid, collected, billed, cost, fee, discount, tax, balance, outstanding.
- Quantities: units, area, capacity, duration, days, hours, visits, items.
- Dates: first event date, latest event date, completion date, settlement date, freshness date.
- Status distributions: counts or amounts by status, stage, category, type, channel, source system.
- Quality measures: null counts, duplicate counts, orphan counts, invalid code counts, stale record counts.

## Metric Promotion

Promote validated measures into contextual metrics when the context is clear:

| Metric Type | Pattern |
|---|---|
| Time-context metric | Measure by day, week, month, quarter, year, year to date, last 12 months, or period-over-period |
| Dimensional metric | Measure by safe dimension such as customer segment, product, provider, department, location, vendor, region, or status |
| Ratio or rate | Numerator divided by denominator, with inclusion/exclusion rules and safe division |
| Average metric | Sum or count divided by entity/event count |
| Ranking metric | Top or bottom entities by value, count, rate, or exception volume |
| Aging metric | Open or pending records grouped by age buckets |
| Quality metric | Error, missing, duplicate, orphan, stale, or invalid rates |

Only promote a metric to a key performance indicator when it is tied to a decision, target, threshold, operating review, risk, cost, revenue, service level, quality goal, or explicit user-approved business objective.

## Coverage Expectation

The analytics insight phase must analyze and construct as many **supported** measures, metrics, and key performance indicator candidates as the validated data can safely justify.

Do not stop after three to five executive key performance indicators. Instead:

1. Inventory every fact-like, event-like, entity-like, finance-like, status-like, date-like, and bridge-like model available in gold/marts and validated upstream layers.
2. Generate broad raw measures for every safe count, distinct count, amount, quantity, date coverage, status distribution, and data quality signal.
3. Promote those measures into contextual metrics wherever a time field, dimension, ratio denominator, status grouping, ranking dimension, aging field, or quality rule is clear.
4. Promote only the decision-relevant, strategic subset into `kpi_catalog.md`.
5. Keep non-strategic but useful measures and metrics in `measure_catalog.md` and `metric_catalog.md` so presentation and human review can still use them.
6. Put unclear, unreconciled, sensitive, or unsupported candidates into `insight_backlog.md` with the exact missing proof or business rule.

Use this broad-but-safe rule:

```text
Create many candidate measures and metrics.
Trust only the candidates that have grain, formula, allowed dimensions, time field when needed, and SQL proof.
Promote only strategic candidates to key performance indicators.
```

Coverage targets when validated gold has multiple facts and dimensions (see [reporting-coverage-requirements.md](reporting-coverage-requirements.md)):

| Catalog | Target |
|---|---|
| `measure_catalog.md` | **50+** supported measures when evidence allows |
| `metric_catalog.md` | **50+** supported metrics when evidence allows |
| `kpi_catalog.md` | Strategic subset (rich, not capped at 3–5) |

Do **not** stop after three to five executive KPIs and leave catalogs empty. Presentation must still cover measures and metrics, not only the executive KPI cards.

Hard gate: `scripts/check_analytics_coverage.py` **FAIL**s when gold has 3+ facts/marts and `measure_catalog` / `metric_catalog` are below 50 / 30. Thin executive lists are not analytics-complete.

This lets the project expose a rich analysis surface without pretending every metric is a management key performance indicator.

## Generic Archetypes

Map candidates to one of these reusable archetypes:

| Archetype | Meaning |
|---|---|
| Volume | Count of records, transactions, cases, events, or entities |
| Value | Sum of amounts, revenue, cost, balance, or value |
| Average value | Average amount or value per entity/event |
| Ratio | A numerator divided by a denominator |
| Funnel | Movement through statuses or stages |
| Conversion rate | Completed or successful events divided by eligible events |
| Status mix | Count or value by status/stage/category |
| Time trend | Count or value by date period |
| Cycle time | Duration between start and end dates |
| Aging or backlog | Open or pending items older than a threshold |
| Ranking or top-N | Highest or lowest entities by count/value/performance |
| Utilization or capacity | Used amount divided by available amount |
| Quality or error | Missing, invalid, failed, duplicate, stale, or exception records |
| Retention or cohort | Repeat, returning, renewed, or recurring behavior |
| Exception reporting | Negative balances, missing dates, invalid statuses, or outlier values |

## Confidence Scoring

Score every candidate:

| Confidence | Meaning |
|---|---|
| `HIGH` | Source model, grain, formula, time field, filters, and validation are clear |
| `MEDIUM` | Mostly clear, but one business rule needs confirmation |
| `LOW` | Possible metric, but column or business meaning is uncertain |
| `BLOCKED` | Cannot safely create due to missing data, missing relationships, missing mapping, privacy, unvalidated grain, or unclear formula |

Only promote `HIGH` and user-approved `MEDIUM` metrics into semantic metrics or Power BI DAX. Put `LOW` and `BLOCKED` metrics into `insight_backlog.md` unless the user explicitly approves further exploration.

## Required Matrix

Create or update `reports/agent/09_analytics_insights/kpis/measure_catalog.md`, `reports/agent/09_analytics_insights/kpis/metric_catalog.md`, and `reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md` during analytics insight reporting. For older flat-layout projects, use the legacy `reports/agent/<file>` path only when canonical folders are absent.

Required columns:

`measure_catalog.md`:

| Measure | Measure Type | Source Model | Grain | Formula | Time Field | Allowed Dimensions | SQL Proof File | Captured Result | Status | Caveats |
|---|---|---|---|---|---|---|---|---|---|---|

`metric_catalog.md`:

| Metric | Metric Type | Business Question | Source Measures | Source Model | Grain | Formula | Time Field | Allowed Dimensions | Filters | SQL Proof File | Captured Result | Confidence | Caveats | Promotion Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`kpi_discovery_matrix.md`:

| Key Performance Indicator | Business Question | Metric Type | Source Metric | Source Model | Grain | Formula | Numerator | Denominator | Time Field | Allowed Dimensions | Filters | SQL Proof File | Captured Result | Confidence | Caveats | Approval Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Generate `reports/agent/09_analytics_insights/kpis/kpi_catalog.md` from the discovery matrix. The catalog should contain trusted, approved, deferred, and blocked key performance indicators with the reason for each status.

## SQL proof requirements

For every `HIGH` confidence measure, metric, and key performance indicator candidate, write a runnable proof query under:

```text
reports/agent/09_analytics_insights/kpis/sql_proofs/
```

Use proof filenames that map back to the catalog row:

```text
010_measure_<measure_slug>.sql
110_metric_<metric_slug>.sql
210_kpi_<kpi_slug>.sql
```

Each proof file must include:

- Business meaning
- Source model and grain
- Formula
- Expected result or acceptance rule
- Captured result at run time
- Pass/warn/fail status
- Runnable SQL

For `MEDIUM`, `LOW`, or `BLOCKED` candidates, create proof files when a query was actually run or when the proof explains why the candidate is blocked. Do not fabricate a proof query for a metric whose business meaning or source field is unknown.

The catalogs must link to the proof file path, not only paste SQL text into a table cell.

Read [../docs/kpi_proof_standards.md](../docs/kpi_proof_standards.md) for proof file content, naming, and validation rules.

Before marking analytics insight reporting `PASS`, run:

```bash
python scripts/validate_kpi_proofs.py --root .
```

Use project-scale targets when the business scope is large enough to justify them:

```bash
python scripts/validate_kpi_proofs.py --root . --min-measures 60 --min-metrics 35 --min-kpis 15 --require-sql-proofs
```

If minimum counts are not met, document each shortfall in `insight_backlog.md` with evidence. Do not mark the phase `PASS` silently.

## Targeted Questions

Ask only questions that affect business meaning or safety, such as:

- Which status values count as completed, failed, cancelled, active, inactive, or reportable?
- Which date field controls this metric?
- Should deleted, cancelled, test, draft, denied, refunded, or pending records be excluded?
- Which amount field is gross, net, paid, billed, collected, refunded, or outstanding?
- May this sensitive field be shown, masked, hashed, or aggregated?
- Is this mapping table or code definition available?

Do not ask the user to invent the whole dashboard. Recommend the safe default with evidence, then ask only for uncertain decisions.

## Hard Stops

Do not create:

- Key performance indicators from column names alone.
- A flat `5 key performance indicators per table` rule across dimensions, bridges, reference tables, or audit tables.
- Key performance indicators without confirmed or validated grain.
- Ratio metrics without a clear numerator and denominator.
- Trend metrics without a clear time field.
- Funnel metrics without status or stage mapping.
- Financial metrics without clear amount columns and inclusion/exclusion rules.
- Presentation or DAX measures for `LOW`, `BLOCKED`, unvalidated, or sensitive metrics.

If a key performance indicator needs a missing key, mapping, relationship, source data, privacy decision, or business rule, defer it to `reports/agent/09_analytics_insights/insight_backlog.md`.
