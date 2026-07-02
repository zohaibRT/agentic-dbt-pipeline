# Key Performance Indicator Discovery Framework

Use this during analytics insight reporting before finalizing `kpi_catalog.md`, semantic metrics, Power BI measures, or dashboard specifications.

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
2. Detect grain for every possible fact.
3. Detect candidate measures.
4. Create a broad `measure_catalog.md`.
5. Promote supported measures into contextual metrics in `metric_catalog.md`.
6. Map metrics to generic archetypes.
7. Promote only strategic, decision-relevant metrics into `kpi_catalog.md`.
8. Score confidence.
9. Ask targeted business questions only where needed.
10. Send approved metrics to semantic layer and presentation tooling.

## Table Classification

Classify each relevant table before deciding facts, dimensions, reports, or measures:

| Table Type | Meaning | Key Performance Indicator Potential |
|---|---|---|
| Entity or master table | Customers, patients, products, houses, suppliers, doctors, employees, accounts | Dimensions and entity counts |
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

Create `measure_catalog.md` before deciding key performance indicators. Include broad raw measures even when they are not strategic key performance indicators yet.

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

| Measure | Measure Type | Source Model | Grain | Formula | Time Field | Allowed Dimensions | Validation Query | Status | Caveats |
|---|---|---|---|---|---|---|---|---|---|

`metric_catalog.md`:

| Metric | Metric Type | Business Question | Source Measures | Source Model | Grain | Formula | Time Field | Allowed Dimensions | Filters | Validation Query | Confidence | Caveats | Promotion Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

`kpi_discovery_matrix.md`:

| Key Performance Indicator | Business Question | Metric Type | Source Metric | Source Model | Grain | Formula | Numerator | Denominator | Time Field | Allowed Dimensions | Filters | Validation Query | Confidence | Caveats | Approval Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Generate `reports/agent/09_analytics_insights/kpis/kpi_catalog.md` from the discovery matrix. The catalog should contain trusted, approved, deferred, and blocked key performance indicators with the reason for each status.

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
- Key performance indicators without confirmed or validated grain.
- Ratio metrics without a clear numerator and denominator.
- Trend metrics without a clear time field.
- Funnel metrics without status or stage mapping.
- Financial metrics without clear amount columns and inclusion/exclusion rules.
- Presentation or DAX measures for `LOW`, `BLOCKED`, unvalidated, or sensitive metrics.

If a key performance indicator needs a missing key, mapping, relationship, source data, privacy decision, or business rule, defer it to `reports/agent/insight_backlog.md`.
