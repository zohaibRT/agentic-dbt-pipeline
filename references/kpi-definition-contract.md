# Key Performance Indicator Definition Contract

Use this before implementing a key performance indicator in gold/marts, semantic layer, analytics insight reporting, Power BI, Matplotlib, or any other presentation layer.

## Core rule

A key performance indicator is not verified until its business definition, data source, grain, filters, time basis, expected result, actual result, and proof file are documented.

Do not promote a measure or metric into a key performance indicator when the business meaning is guessed.

The system must know **why** a number is shown, not only how it is calculated.

## Canonical generated file

Write approved, proposed, deferred, and blocked key performance indicator contracts to:

```text
reports/agent/KPI_DEFINITION_CONTRACTS.md
```

Analytics-specific catalogs may also reference the same items from:

```text
reports/agent/09_analytics_insights/kpis/kpi_catalog.md
reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md
reports/agent/09_analytics_insights/kpis/business_measure_catalog.md
reports/agent/09_analytics_insights/kpis/business_metric_catalog.md
reports/agent/09_analytics_insights/kpis/data_quality_metric_catalog.md
reports/agent/09_analytics_insights/kpis/pipeline_health_metric_catalog.md
```

## Required contract fields

Every published KPI (and preferably every published business metric) should document:

```yaml
metric_name:
display_name:
metric_class: measure | metric | kpi | quality | pipeline_health

business_process:
business_question:
decision_supported:
action_when_bad:
owner:

business_definition:
formula:
numerator:
denominator:

grain:
counting_key:
source_models:
source_columns:

included_records:
excluded_records:
status_logic:
date_field:
date_role:

dimensions:
unit:
currency:
format:
aggregation_behavior: additive | semi_additive | non_additive
null_behavior:
zero_denominator_behavior:

refresh_frequency:
freshness_sla:

target:
target_source:
warning_threshold:
critical_threshold:
desired_direction: increase | decrease | range

validation_source:
reconciliation_tolerance:
sql_proof:
approval_status:
confidence:
```

Most important fields:

- `business_question`
- `decision_supported`
- `action_when_bad`
- `aggregation_behavior`
- `desired_direction`
- `target_source`

Without these, the system can calculate a number but cannot justify showing it.

## Required contract table

```markdown
# Key Performance Indicator Definition Contracts

| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Unit/Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | <display> | kpi | <process> | <question> | <decision> | <action> | <owner> | <formula> | <grain> | <key> | <date> | <role> | <include> | <exclude> | <dims> | <unit> | <format> | additive/semi/non | <target or not defined> | increase/decrease/range | <models> | <path> | <proof> | <value> | <value> | <diff> | APPROVED/PROPOSED/DEFERRED/BLOCKED | PASS/WARN/FAIL/BLOCKED | <reason> |
```

## Required approval questions

Before implementation, resolve or document:

1. What business question does this answer?
2. What decision does a change in this number support?
3. What action should be taken when performance is bad?
4. Who owns the definition?
5. Which rows are included and excluded?
6. Which date or timestamp controls the metric, and what is its role?
7. What is the calculation grain and counting key?
8. Is the metric additive, semi-additive, or non-additive?
9. What unit, currency, and display format apply?
10. What target, baseline, or “target not defined” status applies?
11. What reconciliation tolerance is acceptable?
12. Is the definition approved, proposed, deferred, or blocked?

Ask the user only for unresolved business decisions. Do not ask for items the data can prove directly.

## Stop conditions

Stop before semantic layer, analytics insight reporting, presentation layer, or final delivery when:

- Formula, date basis, grain, numerator, denominator, or filters are ambiguous.
- Business question, decision supported, or action-when-bad is missing for a published KPI.
- The business definition contradicts the source data.
- The expected and actual result do not reconcile.
- The key performance indicator depends on unsafe joins or unproven cardinality.
- The key performance indicator exposes sensitive fields without approval.
- Aggregation behavior would produce unsupported additive totals across irreconcilable sources.
