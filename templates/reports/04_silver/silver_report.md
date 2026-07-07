# Silver / Intermediate Report

## Template Use

Use this file as the fixed structure for `reports/agent/04_silver/silver_report.md`.
Replace placeholders with intermediate model, join, mapping, and validation evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Layer schema: <schema>
- Models built: <count>
- Main business processes modeled: <processes>

## What Was Built Or Changed

| Model | Purpose | Grain | Materialization | Row count | Status |
|---|---|---|---|---:|---|
| <model> | <purpose> | <grain> | <view/table/incremental> | <row_count> | <PASS/WARN/FAIL/BLOCKED> |

## Join And Mapping Decisions

| Decision | Evidence | Status | Approval source |
|---|---|---|---|
| <join/mapping/flag> | `<proof file or report>` | <PASS/WARN/FAIL/BLOCKED> | <user/discovery/default> |

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Row loss check | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Row multiplication check | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Relationship integrity | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Mapping coverage | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Derived flag logic | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
