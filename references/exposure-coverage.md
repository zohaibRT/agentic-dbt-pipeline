# Exposure And Downstream Consumer Coverage

Use during analytics product completeness and final delivery.

## Core rule

Evaluate how models will be consumed. Prefer declaring dbt exposures for production reports when practical. Do not hardcode consumer types beyond the generic classes below.

## Consumer classes

- dashboards
- browser reports
- Power BI reports
- notebooks
- applications
- APIs
- reverse ETL
- AI agents
- extracts
- scheduled reports

## Required fields

Write to:

```text
reports/agent/09_analytics_insights/exposure_coverage.md
```

| Field | Required |
|---|---|
| exposure name | yes |
| type | yes |
| owner | when known |
| dependent models | yes |
| dependent metrics | when applicable |
| refresh expectation | when known |
| business purpose | yes |
| criticality | yes |
| validation status | PASS/WARN/BLOCKED/DEFERRED |

## Acceptance

Critical downstream consumers should be documented before final PASS. Missing exposures for an approved live presentation layer is at least WARN, FAIL when the project marks the presentation as production-critical.
