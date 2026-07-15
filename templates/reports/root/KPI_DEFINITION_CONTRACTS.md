# Key Performance Indicator Definition Contracts

## Purpose

Define every trusted key performance indicator before it is promoted to semantic metrics, presentation measures, or executive reporting.

Use the expanded production schema below. Do not invent owners, targets, or business definitions.

Legacy shorter tables are still readable by `verify_metric_reconciliation.py` during migration, but new projects must use this schema.

| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Unit/Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | Validation Type | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | <Human title> | kpi | <process> | <question> | <decision> | <action> | <owner or unknown> | <formula> | <grain> | <key> | <date> | <role> | <include> | <exclude> | <dims> | <unit> | percent/currency/integer | additive/semi_additive/non_additive/ratio | Target not defined | increase/decrease/range | <models> | <path> | numeric_tolerance | `<sql_proof>` | <expected> | <actual> | <diff> | APPROVED/PROPOSED/DEFERRED/BLOCKED | PASS/WARN/FAIL/BLOCKED | <reason> |

## Deferred Or Blocked KPIs

| KPI | Reason | Missing Evidence | Recommended Next Action |
|---|---|---|---|
| None | Not applicable | Not applicable | Not applicable |
