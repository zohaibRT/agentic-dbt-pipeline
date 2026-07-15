# Analytics Product Completeness

Use this before analytics insight reporting or presentation can pass.

Also read [reporting-coverage-requirements.md](reporting-coverage-requirements.md), [time-intelligence-standard.md](time-intelligence-standard.md), [report-page-contract.md](report-page-contract.md), [kpi-definition-contract.md](kpi-definition-contract.md), and [universal-analytics-framework.md](universal-analytics-framework.md).

## Core rule

Analytics completeness is based on **supported business and engineering coverage**, not a fixed number of catalog rows.

Do **not** optimize for 50+, 100+, or any other arbitrary measure or metric count. Generate as many validated measures and metrics as needed to cover the material business processes, and no more.

A project with three good facts may need ~25 meaningful metrics. Another may legitimately need 100. The number is a **result** of the model, not the objective.

## Distinguish four kinds of completeness

| Kind | Meaning |
|---|---|
| Technical completeness | Models parse, build, test, and reconcile with SQL proofs |
| Analytical completeness | Every material fact and process has volume, value, status, time, quality, and segmentation coverage |
| Business usefulness | Published numbers answer documented questions and support decisions |
| Presentation quality | Business pages use readable labels, formats, periods, insights, and actions |

Do not treat technical success or catalog volume as proof of business usefulness.

## Required model classes (not fixed names)

Require **classes**, not fixed model names such as `dim_customer` or `fct_orders`. Build only when evidence exists:

| Required model class | Build when |
|---|---|
| Date dimension | Facts contain usable business dates |
| Entity dimension | A stable customer, patient, account, asset, employee, or equivalent entity exists |
| Product/service dimension | A product, service, device, plan, or equivalent catalog exists |
| Status dimension | Workflow/status codes require reusable business labels |
| Transaction fact | Financial or quantity transactions exist |
| Event fact | Operational events or interactions exist |
| Periodic snapshot fact | Point-in-time balances or statuses must be analyzed |
| Accumulating snapshot | A lifecycle has multiple milestones |
| Bridge | A validated many-to-many relationship exists |
| Exposure | A dashboard, application, notebook, or API consumes the models |
| Snapshot/SCD model | Attribute history matters and source history is insufficient |

`core/` is a **conceptual** layer. It may be implemented inside `intermediate/` or `gold/` depending on the project. It is not a mandatory physical folder.

## Mandatory analytics product modules

Before analytics reporting or presentation can pass, evaluate:

| Module | Required output |
|---|---|
| Architecture | Source, staging, intermediate, facts, dimensions, bridges, marts, snapshots, and exposures decision |
| Business processes | Process catalog with event, grain, owner, start/end states, and measurable outcomes |
| Model completeness | Every reporting fact has suitable dimensions and date roles |
| Business measures | Counts, amounts, quantities, durations, and balances supported by facts |
| Contextual metrics | Rates, averages, trends, shares, rankings, aging, funnel, and variance |
| Strategic KPIs | Small decision-focused subset with owner, target or management purpose |
| Time intelligence | Current period, prior period, trend, and rolling comparisons where supported |
| Segmentation | Approved dimensions capable of explaining performance |
| Data quality | Completeness, uniqueness, validity, integrity, consistency, freshness, and reconciliation |
| Pipeline health | Run success, model failures, test failures, duration, freshness, and SLA status |
| Verification | Row-level, transformation, aggregate, and business-owner verification |
| Presentation | Business pages, readable formatting, filters, insights, exceptions, and actions |
| Governance | Metric dictionary, lineage, owners, definitions, caveats, and approval status |

## Canonical coverage matrix

Create:

```text
reports/agent/09_analytics_insights/analytics_coverage_matrix.md
```

Suggested columns:

| Business Process | Facts | Dimensions | Measures | Metrics | KPIs | Time Analysis | Quality | Reconciliation | Report Page | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| <process> | <fct_*> | <dim_*> | <count> | <count> | <names> | <current/prior/trend> | <checks> | <proof> | <page> | PASS/WARN/BLOCKED |

This matrix is the **primary coverage gate**, not the raw count of catalog rows.

## Separate metric families (hard)

Do not mix technical row counts with business KPIs on the same executive pages.

Maintain separate catalogs under `reports/agent/09_analytics_insights/kpis/`:

| Catalog | Contents |
|---|---|
| `business_measure_catalog.md` | Business volumes, amounts, quantities, durations, balances |
| `business_metric_catalog.md` | Rates, averages, shares, growth, rankings built from business measures |
| `kpi_catalog.md` | Small decision-focused subset with owner and management purpose |
| `data_quality_metric_catalog.md` | Missing rates, orphan rates, null rates, duplicates, invalid statuses, reconciliation variance |
| `pipeline_health_metric_catalog.md` | Build success, failed models/tests, freshness, duration, SLA, documentation/test coverage |

Legacy `measure_catalog.md` / `metric_catalog.md` may remain as combined views, but presentation business pages must consume the **business** catalogs. Technical values such as model row counts belong in **Data Model Health / Data Quality**, not in **All Business Measures**.

### Illustrative families (examples only — use this project’s evidence)

**Business measures:** orders, active entities, paid amount, units sold, invoice amount, quantity, duration, outstanding balance.

**Business metrics:** paid rate, average order value, activation rate, failure rate, active share, contribution by channel/entity, month-over-month growth.

**Strategic KPIs:** recurring revenue, growth, churn, renewal, margin, conversion, collection rate, channel contribution — only when the business process exists.

**Data-quality metrics:** account-match rate, orphan rate, null-rate, duplicate rate, invalid-status rate, reconciliation variance.

**Pipeline-health metrics:** dbt build success, failed model/test count, source freshness failures, pipeline duration, SLA compliance, documentation coverage, tested-model coverage.

## Fact coverage contract

For every `fct_`, transaction mart, event mart, or snapshot mart, evaluate:

| Coverage area | Required evaluation |
|---|---|
| Grain | One row represents exactly what? |
| Counting key | Which key is used for distinct counts? |
| Date roles | Created, entered, completed, paid, delivered, cancelled, or equivalent |
| Volume | Total and relevant status counts |
| Value | Amount, quantity, balance, cost, or duration |
| Status | Distribution and state transitions |
| Lifecycle | Start, intermediate, and completion stages |
| Time | Trend and period comparison |
| Dimensions | Which validated dimensions can slice it? |
| Quality | Nulls, duplicates, invalid values, and orphans |
| Reconciliation | Source total versus fact total |
| Exceptions | Failed, overdue, missing, unmatched, or abnormal records |
| Business questions | What decisions can this fact support? |

A fact is not analytically complete merely because five measures were generated from it.

Write per-fact coverage into:

```text
reports/agent/09_analytics_insights/fact_coverage_contracts.md
```

## Suggested acceptance targets

| Gate | Target |
|---|---|
| Critical fact coverage | 100% of in-scope facts evaluated against the contract |
| Critical KPI contract coverage | 100% of published KPIs |
| Critical reconciliation | 100% of published KPIs |
| Business process coverage | >= 90% of material processes |
| Time-intelligence coverage | >= 80% where dates support it |
| Business label coverage | 100% on business pages |
| Technical-name leakage | 0 on business pages |

## Related references

- [time-intelligence-standard.md](time-intelligence-standard.md)
- [report-page-contract.md](report-page-contract.md)
- [kpi-definition-contract.md](kpi-definition-contract.md)
- [reporting-coverage-requirements.md](reporting-coverage-requirements.md)
- [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md)
