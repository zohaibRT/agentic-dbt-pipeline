# Key Performance Indicator Definition Contracts

## Purpose

Define every trusted key performance indicator before it is promoted to semantic metrics, presentation measures, or executive reporting.

Technical verification and business approval are **separate**. A technical PASS never implies business APPROVED. The agent must never approve its own business definitions.

Use the expanded production schema below. Do not invent owners, targets, or business definitions.

Legacy shorter tables are still readable during migration (see `docs/kpi-contract-human-approval-migration.md`), but new projects must use this schema.

## Canonical fields

Identity, business context, definition, data definition, formatting, operational expectations, performance management, validation, and human governance fields must be present for APPROVED / PROPOSED KPIs. Conditionally inapplicable fields require `NOT_APPLICABLE: <specific reason>` (bare `N/A` is rejected).

Do not treat these as aliases of each other:

- business_definition vs formula
- unit vs currency
- technical_verification_status vs business_approval_status
- business_owner vs approver
- target vs target_source
- expected_result vs actual_result

| KPI ID | Contract Version | Contract Fingerprint | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Business Owner | Approver | Business Definition | Formula | Grain | Counting Key | Source Models | Source Columns | Date Field | Date Role | Timezone | Included Records | Excluded Records | Status Logic | Dimensions | Numerator | Denominator | Unit | Currency | Format | Precision | Aggregation Behavior | Null Behavior | Zero Denominator Behavior | Refresh Frequency | Freshness SLA | Target | Target Source | Warning Threshold | Critical Threshold | Desired Direction | Validation Source | Validation Type | Reconciliation Tolerance | SQL Proof | Expected Result | Actual Result | Calculated Difference | Calculated Status | Technical Verification Status | Business Approval Status | Approval Evidence | Approval Date | Approval Conditions | Approval Expiry Or Review Condition | Confidence | Caveats | Missing Evidence | Recommended Next Action | Review Or Resolution Condition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | 1.0 | <fingerprint> | <Human title> | kpi | <process> | <question> | <decision> | <action> | <owner> | <approver> | <plain-language definition> | <formula> | <grain> | <key> | <models> | <columns> | <date> | <role> | NOT_APPLICABLE: date-only | <include> | <exclude> | <status logic> | <dims> | <num or NOT_APPLICABLE: reason> | <den or NOT_APPLICABLE: reason> | <unit> | <code or NOT_APPLICABLE: reason> | percent/currency/integer | <precision> | additive/semi_additive/non_additive/ratio | <null rule> | <zero-den or NOT_APPLICABLE: reason> | <freq> | <sla> | <target or Target not defined> | <source or NOT_APPLICABLE: reason> | <warn or NOT_APPLICABLE: reason> | <crit or NOT_APPLICABLE: reason> | increase/decrease/range | <proof path> | numeric_tolerance | <tol> | `<sql_proof>` | <expected> | <actual> | <diff> | PASS/FAIL | PASS/WARN/FAIL/BLOCKED/DEFERRED | APPROVED/PENDING_REVIEW/BLOCKED/DEFERRED | `<evidence path>` | YYYY-MM-DD | <conditions or NOT_APPLICABLE: reason> | <expiry or NOT_APPLICABLE: reason> | HIGH/MEDIUM/LOW | <caveats> | <missing or none> | <next or none> | <review or none> |

## Deferred Or Blocked KPIs

Blocked/deferred rows still require: kpi_id, contract_version, display_name, metric_class, business_process, business_question, reason, missing_evidence, business_owner, recommended_next_action, review_or_resolution_condition, business_approval_status, technical_verification_status.

Generic blockers (`TODO`, `TBD`, `pending`, `later`, `unknown`, `needs review`) without specifics are rejected.
