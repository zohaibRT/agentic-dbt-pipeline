# Reporting Standards

Use this before writing discovery reports, phase reports, presentation reports, final handoffs, dashboard designs, and Power BI report plans.

## Core rule

Every report must be actionable. Do not only list data, files, models, or charts. A good report tells the data engineer and business user what happened, why it matters, what changed, what is uncertain, and what should happen next.

When a section is not supported by validated data, include it as `Not available yet` or `Deferred` with the reason. Do not invent targets, benchmarks, root causes, or recommendations that are not supported by evidence.

## Five report pillars

Every report should include these pillars when relevant:

| Pillar | Purpose | Required content |
|---|---|---|
| Context and strategy | Explain why the work or numbers matter | Objective, business process, audience, scope, baseline, target, benchmark, or why the metric exists |
| Key performance indicators | Show the current state | Primary measures, leading indicators, lagging indicators, business definition, source model, grain, filters, time field, and caveats |
| Trend analysis and variance | Show direction and gap | Historical trend, period comparison, target variance, baseline variance, month-over-month, year-over-year, year to date, or last 12 months when supported |
| Insights and attribution | Explain why performance changed | Drivers, root-cause hypotheses, anomalies, outliers, segment changes, data quality explanations, and confidence level |
| Recommendations and next steps | Drive action | Actionable next steps, owner or decision needed when known, risk, resource need, blocked item, and next approval checkpoint |

## Report behavior

- Start with a short executive summary before details.
- Separate evidence from interpretation.
- Use validated metrics and source-backed findings first.
- State targets and benchmarks only when provided, discovered, or safely derived from approved baseline logic.
- When no target exists, recommend that the data engineer or business owner define one.
- Include both leading and lagging indicators when the data supports them.
- Include variance from target or baseline when a target or baseline exists.
- Include anomaly and outlier notes when distributions, trends, or data validation show unusual values.
- Include limitations and confidence notes so users can trust what is proven and see what is still uncertain.
- Use full wording in headings and summaries.

## Presentation report behavior

For business-facing presentation layers, the report design must show more than key performance indicator cards and trends. It should include:

- Context and strategy page or section.
- Executive Overview page.
- Key performance indicator scorecard with leading and lagging measures when supported.
- Trends and variance page.
- Driver, segmentation, attribution, or root-cause page when dimensions support it.
- Exceptions, anomalies, and data quality page when issues exist.
- Recommendations and next steps page or section.

If targets, benchmarks, attribution dimensions, or next-step owners are missing, include a visible `Needs business input` note instead of leaving the pillar out silently.

## Power BI canvas standard

Use this fixed layout standard for every generated Power BI report unless the user provides a stronger company template.

Every Power BI report must feel like an interactive dashboard canvas, not a static table dump. Each main report page should include these elements when supported:

| Layer | Required content | Purpose |
|---|---|---|
| Header and navigation | Report title, page title, company or project branding when available, last refreshed timestamp, reset filters button, and page navigation buttons | Keep the user oriented and make the report feel consistent |
| Key performance indicator summary | Three to five primary cards near the top, with conditional formatting or trend context when targets or prior periods exist | Show current state quickly |
| Interactive slicers | Date range plus important dimensions such as region, department, category, product, provider, customer, status, or channel when available | Let users filter without cluttering the page |
| Trends and comparisons | Line or area charts for time series, bar or column charts for category comparisons, and drill-down when a date hierarchy or hierarchy dimension exists | Show direction, variance, and drivers |
| Detail layer | Matrix or detail table at the bottom of the page or on a separate details page, with conditional formatting for outliers when useful | Support operational investigation |
| Tooltips and drill-throughs | Report page tooltips and drill-through pages for important entities or data points when the model supports safe row-level investigation | Keep pages clean while preserving depth |

Default top-to-bottom canvas order:

1. Header/navigation bar.
2. Key performance indicator card row.
3. Primary trends and comparison visuals.
4. Secondary driver, attribution, or segmentation visuals.
5. Matrix/detail table or drill-through entry point.

Power BI page rules:

- Use native page navigation buttons for multi-page reports.
- Include a reset filters button on main report pages when supported by the chosen PBIP/report format.
- Include a last refreshed timestamp measure or equivalent metadata visual when the model can support it.
- Keep primary slicers visible and put secondary filters in the filter pane or a dedicated filter area.
- Use line or area charts for time series, not pie-heavy trend pages.
- Use bar or column charts for ranked comparison across categories.
- Use matrix visuals for operational detail and apply conditional formatting when it helps users spot exceptions.
- Add report page tooltips for important charts when the PBIP/report format supports them.
- Add drill-through pages for important entities such as customer, patient, provider, product, location, department, account, or order when safe and useful.
- Hide technical fields from the report canvas and report view unless they are needed for investigation.
- Document any missing layout element in `reports/agent/presentation_report.md` with the reason, such as unsupported by current PBIP generation, missing dimension, or privacy risk.

## Required report sections

Use these headings, or equivalent full wording, in reports and handoffs:

```markdown
## Context and Strategy

## Key Performance Indicators

## Trend Analysis and Variance

## Insights and Attribution

## Recommendations and Next Steps
```

For technical phase reports, these sections may be brief, but they must still orient the user:

- Context and Strategy: why the phase exists and what business or data-engineering goal it supports.
- Key Performance Indicators: implemented or deferred metrics, or `Not applicable for this technical phase`.
- Trend Analysis and Variance: validation movement, row-count movement, or `Not applicable yet`.
- Insights and Attribution: what the checks suggest about data behavior, blockers, or quality.
- Recommendations and Next Steps: the next checkpoint and exact approval needed.
