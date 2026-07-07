# Bronze / Staging Report

## Template Use

Use this file as the fixed structure for `reports/agent/03_bronze/bronze_report.md`.
Replace placeholders with bronze/staging model and validation evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Layer schema: <schema>
- Models built: <count>
- Source tables staged: <count>

## What Was Built Or Changed

| Model | Source table | Materialization | Row count | Status | Notes |
|---|---|---|---:|---|---|
| <model> | <source table> | <view/table/incremental> | <row_count> | <PASS/WARN/FAIL/BLOCKED> | <notes> |

## Transformation Rules Applied

- Source-shaped staging only
- Basic casts and standard names: <yes/no/details>
- Ambiguous fields kept raw: <yes/no/details>
- Sensitive fields handling: <pass through/exclude/mask/defer>

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Source-to-bronze row count | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Primary/candidate key check | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Status/category distribution | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Date coverage | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Privacy exposure check | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
