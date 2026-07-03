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

Add domain-specific families only when source evidence supports them, such as healthcare visits and claims, travel bookings and refunds, real estate leads and purchase orders, or software subscriptions and payments.

## Universal dimensions

Consider these as slicers, grouping fields, drill-downs, or report page filters when validated and safe:

```text
Date, time, customer, patient, account, product, service, employee,
provider, department, location, city, country, branch, supplier,
category, status, stage, channel, payment method, currency, salesperson,
region, source system
```

Do not expose direct identifiers, protected health information, personally identifiable information, or sensitive business fields without approval.

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
| Entity Performance | Customer, patient, provider, employee, product, supplier, department, location, or account performance |
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
