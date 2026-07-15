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

Every published KPI (APPROVED / PROPOSED) must document the canonical fields in
`templates/reports/root/KPI_DEFINITION_CONTRACTS.md`, including:

```yaml
kpi_id:
contract_version:
contract_fingerprint:
display_name:
metric_class:

business_process:
business_question:
decision_supported:
action_when_bad:
business_owner:
approver:

business_definition:   # plain language — not an alias of formula
formula:
numerator:
denominator:
included_records:
excluded_records:
status_logic:

grain:
counting_key:
source_models:
source_columns:
date_field:
date_role:
timezone:
dimensions:

unit:
currency:
format:
precision:
aggregation_behavior:
null_behavior:
zero_denominator_behavior:

refresh_frequency:
freshness_sla:

target:
target_source:
warning_threshold:
critical_threshold:
desired_direction:

validation_source:
validation_type:
reconciliation_tolerance:
sql_proof:
expected_result:
actual_result:
calculated_difference:
calculated_status:
technical_verification_status:  # never confuse with business approval

business_approval_status:
approval_evidence:
approval_date:
approval_conditions:
approval_expiry_or_review_condition:
confidence:
caveats:
```

Conditionally inapplicable fields require `NOT_APPLICABLE: <specific reason>`.

Technical PASS never implies business APPROVED. See `docs/kpi-contract-human-approval-migration.md`.

Most important fields:

- `business_question`
- `decision_supported`
- `action_when_bad`
- `aggregation_behavior`
- `desired_direction`
- `target_source`
- `business_approval_status` + `approval_evidence`

Without these, the system can calculate a number but cannot justify showing it as a trusted business KPI.

## Validation Type values

When documenting proof or reconciliation expectations, use explicit validation types:

- `numeric_exact` — expected and actual must match exactly
- `numeric_tolerance` — absolute or relative numeric tolerance applies
- `ratio_tolerance` — ratio/percent comparison with tolerance
- `row_count_match` — row-count reconciliation between source and mart
- `set_match` — categorical/set equality check
- `acceptance_rule` — human-approved rule documented in the proof
- `blocked` — cannot verify yet; documented blocker required
- `deferred` — intentionally postponed with owner and reason

## Required contract table

```markdown
# Key Performance Indicator Definition Contracts

| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Business Definition | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Numerator | Denominator | Unit/Currency | Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | Validation Type | Precision | Null Behavior | Zero Denominator Behavior | Confidence | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Missing Evidence | Next Action | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | <display> | kpi | <process> | <question> | <decision> | <action> | <owner> | <plain-language definition> | <formula> | <grain> | <key> | <date> | <role> | <include> | <exclude> | <dims> | <num> | <den> | <unit> | <code> | <format> | additive/semi/non/ratio | <target or not defined> | increase/decrease/range | <models> | <path> | numeric_tolerance | <precision> | <null rule> | <zero-den rule> | HIGH | <proof> | <value> | <value> | <diff> | APPROVED/PROPOSED/DEFERRED/BLOCKED | PASS/WARN/FAIL/BLOCKED | <missing> | <next> | <reason> |
```

**Business Definition** and **Formula** are separate required columns. Business Definition is plain-language meaning; Formula is the executable calculation.

Ratio metrics (`metric_class=ratio`, `validation_type=ratio_*`, or `format=percent`) require **Numerator** and **Denominator**.
Currency format requires **Currency**.

BLOCKED/DEFERRED rows require **Reason**, **Missing Evidence**, **Owner**, and **Next Action** (hard errors).

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
