# Time Intelligence Standard

Use this whenever strategic measures, metrics, KPIs, or report pages are defined.

Also read [analytics-product-completeness.md](analytics-product-completeness.md), [kpi-definition-contract.md](kpi-definition-contract.md), and [report-page-contract.md](report-page-contract.md).

## Core rule

Every strategic measure must be evaluated for time intelligence. Implement **only** comparisons supported by sufficient date coverage.

All-time totals are allowed only when the page explicitly labels them **All time**. Default executive reporting should state the current reporting period.

## Comparisons to evaluate

For each important metric, evaluate whether evidence supports:

- Current day / week / month / quarter / year
- Previous equivalent period
- Month-to-date (MTD)
- Quarter-to-date (QTD)
- Year-to-date (YTD)
- Month-over-month change
- Year-over-year change
- Rolling 7, 30, 90, or 365 days
- Trailing 12 months
- Target versus actual
- Baseline versus actual
- Period share or contribution
- Seasonality where enough history exists

Document unsupported comparisons as `DEFERRED` with the date-coverage reason. Do not invent prior-period or YoY figures when history is insufficient.

## KPI card minimum display

Every strategic KPI card should display at least:

```text
Current value
Reporting period
Change from previous period (or “Prior period not available”)
Target or “Target not defined”
Status (for example on track / below target / above target)
Last refresh
```

Preferred pattern when data and targets support it:

```text
Orders — July 2026
1,284
↑ 8.2% versus June
Target: 1,350 — 95.1% achieved
```

Avoid:

```text
Order Count
16043
Order grain
```

## Period labeling (hard failures if missing)

Treat these as presentation failures:

- KPI values without a reporting period
- All-time totals presented without an explicit **All time** label
- Period comparisons without naming both periods
- Mixing incompatible grains or calendars without a caveat

## Date role documentation

For each fact used in time intelligence, document date roles such as:

- created / entered
- completed / closed
- paid / collected
- delivered / activated
- cancelled / churned

Use the date role that matches the business definition. Do not silently switch date roles between trend, KPI, and reconciliation queries.

## Coverage artifact

Record time-intelligence coverage in:

```text
reports/agent/09_analytics_insights/time_intelligence_coverage.md
```

Suggested columns:

| Metric / KPI | Date field | Date role | Current period | Prior period | MoM/YoY | MTD/QTD/YTD | Rolling | Target/baseline | Status |
|---|---|---|---|---|---|---|---|---|---|
| <name> | <column> | <role> | <yes/no> | <yes/no> | <yes/no> | <yes/no> | <yes/no> | <yes/not defined> | PASS/WARN/DEFERRED |

Suggested acceptance: time-intelligence coverage >= 80% where dates support it.
