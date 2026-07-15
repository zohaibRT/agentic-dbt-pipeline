# Report Page Contract

Use this before building or accepting any presentation report page.

Also read [reporting-coverage-requirements.md](reporting-coverage-requirements.md), [time-intelligence-standard.md](time-intelligence-standard.md), [analytics-product-completeness.md](analytics-product-completeness.md), and [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md).

## Core rule

A production page must declare why it exists, who it is for, which decisions it supports, and what action follows a bad result. A page of unformatted warehouse values is not a report page.

## Required page contract fields

Record every page in:

```text
reports/agent/10_presentation/report_page_contracts.md
```

Use this structure per page:

```yaml
page_name:
audience:
business_process:
decisions_supported:
primary_kpis:
driver_metrics:
guardrail_metrics:
dimensions:
filters:
time_period:
visuals:
exceptions:
insight_narrative:
recommended_actions:
```

## Production page minimums

A production page must include:

- One clear business purpose
- A defined audience
- 4–8 primary KPIs
- Driver and guardrail metrics
- Period filters or an explicit all-time label
- Appropriate dimension filters
- Comparison context when date coverage supports it
- At least one exception or diagnostic section
- A short evidence-based insight
- Recommended action or “Business input required”

## Preferred navigation shape

Do **not** make raw All Measures / All Metrics the primary business navigation.

Prefer process-based pages derived from **this project’s** evidence, for example:

1. Executive Overview
2. Growth and Retention (when that process exists)
3. Funnel / Lifecycle (when that process exists)
4. Revenue, Billing and Collections (when financial facts exist)
5. Channel / Partner / Entity Performance (when those dims exist)
6. Product / Plan / Program Performance (when those dims exist)
7. Operations and Service Levels
8. Exceptions and Data Quality
9. Pipeline Health
10. Metric Dictionary and Reconciliation

Place the full measure/metric dictionaries under **Metric Dictionary**, not as the first business tabs. Business users should not need to browse dozens of raw calculated values to find decisions.

Page names must come from evidenced processes. Do not hardcode industry-specific page titles into the skill.

## Hard presentation failures

Treat the following as presentation failures:

```text
- Raw internal model names shown to business users as primary labels
- Raw decimal percentages instead of formatted percentages
- Currency without consistent decimals and units
- KPI values without reporting period
- All-time totals presented without explicit “All time” label
- Alternate or deleted-record definitions on executive pages
- Technical row counts on executive or commercial pages
- Blank categorical axes
- Codes shown when a business label is available
- Single-category charts that provide no comparison
- Charts with excessive empty space and no useful signal
- Revenue or payment stacks added together when sources are not reconcilable
- KPI cards without prior-period, target, or baseline context when available
- Charts without a business question or insight caption
- “SQL verified” used as evidence of business approval
```

A SQL proof verifies calculation execution and reconciliation. It does **not** by itself prove that the chosen business definition is correct.

## Related references

- [time-intelligence-standard.md](time-intelligence-standard.md)
- [analytics-product-completeness.md](analytics-product-completeness.md)
- [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md)
- [kpi-definition-contract.md](kpi-definition-contract.md)
