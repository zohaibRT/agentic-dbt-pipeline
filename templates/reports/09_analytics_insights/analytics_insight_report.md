# Analytics Insight Report

## Template Use

Use this file as the fixed structure for `reports/agent/09_analytics_insights/analytics_insight_report.md`.
Replace placeholders with validated business insights, catalogs, and reporting recommendations.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Business processes covered: <count>
- Measures cataloged: <count>
- Metrics cataloged: <count>
- Key performance indicators proposed: <count>
- Key performance indicators verified: <count>

## Business Process Coverage

| Business process | Source facts/models | Reporting value | Confidence | Status |
|---|---|---|---|---|
| <process> | <models> | <value> | <high/medium/low/blocker> | <trusted/deferred/blocked> |

## Insight Themes

| Theme | Evidence | Recommended report page | Status |
|---|---|---|---|
| <theme> | `<proof/catalog>` | <page> | <trusted/deferred/blocked> |

## Measures, Metrics, And Key Performance Indicators

| Artifact | Count | Path | Status |
|---|---:|---|---|
| Measure catalog | <count> | `reports/agent/09_analytics_insights/kpis/measure_catalog.md` | <status> |
| Metric catalog | <count> | `reports/agent/09_analytics_insights/kpis/metric_catalog.md` | <status> |
| Key performance indicator catalog | <count> | `reports/agent/09_analytics_insights/kpis/kpi_catalog.md` | <status> |

## Reporting Recommendation

- Recommended pages: <pages>
- Default presentation recommendation: <Matplotlib refreshable web report / Power BI handoff / blocked>
- Important blockers or caveats: <items or "None">

## Validation

| Check | Result | Evidence |
|---|---|---|
| KPI reconciliation | <PASS/WARN/FAIL/BLOCKED> | <path> |
| SQL proof coverage | <PASS/WARN/FAIL/BLOCKED> | <path> |
| Cardinality/grain support | <PASS/WARN/FAIL/BLOCKED> | <path> |

## Open Decisions

- <decision or "None">

## Next Action

- <presentation decision or final delivery checkpoint>
