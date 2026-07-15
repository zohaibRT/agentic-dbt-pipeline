# Data Observability Standard

Use before final analytics / presentation acceptance.

Also read [analytics-product-completeness.md](analytics-product-completeness.md), [layer-data-validation.md](layer-data-validation.md), and [independent-verification-governance.md](independent-verification-governance.md).

## Core rule

Every project must evaluate data observability as a **separate metric family** from business KPIs. Do not invent industry-specific alert rules. Infer checks from this project's models, tests, freshness config, proofs, and pipeline evidence.

## Required evaluation areas

| Area | Examples of evidence |
|---|---|
| Completeness | null rates, required field fill, empty unexpected models |
| Uniqueness | grain tests, duplicate proofs |
| Validity | accepted-value tests, status dictionaries |
| Consistency | cross-system comparison notes |
| Referential integrity | relationship proofs, orphan rates |
| Reconciliation accuracy | source-to-mart variance within tolerance |
| Freshness | dbt source freshness or documented SLA |
| Timeliness | pipeline duration vs expectation |
| Row-count stability | unusual volume change notes |
| Distribution stability | status mix drift notes |
| Pipeline reliability | build success / failed model count |
| Test reliability | failed test count |
| Documentation coverage | model/column docs |
| Model ownership | owners in contracts/exposures |
| Lineage coverage | documented upstream/downstream |
| Incident history | when available |

## Generated artifacts

```text
reports/agent/09_analytics_insights/kpis/data_quality_metric_catalog.md
reports/agent/09_analytics_insights/kpis/pipeline_health_metric_catalog.md
reports/agent/09_analytics_insights/data_observability_report.md
```

## Observability report page

Presentation must include an **Exceptions and Data Quality** surface and, when pipeline evidence exists, a **Pipeline Health** surface. Separate:

- source issues
- transformation issues
- relationship issues
- reconciliation issues
- freshness issues
- presentation limitations
- business-definition gaps

Technical row counts belong here — not on executive business pages.

## Acceptance targets (configurable)

Default guidance:

- Material facts have quality evaluation documented
- Critical reconciliations complete
- Freshness/SLA either configured or explicitly DEFERRED with reason
- Business pages do not mix unexplained DQ metrics with strategic KPIs
