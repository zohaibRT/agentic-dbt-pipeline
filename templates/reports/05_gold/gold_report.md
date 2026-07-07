# Gold / Marts Report

## Template Use

Use this file as the fixed structure for `reports/agent/05_gold/gold_report.md`.
Replace placeholders with facts, dimensions, marts, metric components, and validation evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Layer schema: <schema>
- Dimensions built: <count>
- Facts built: <count>
- Marts built: <count>

## Models Built Or Changed

| Model | Type | Grain | Materialization | Row count | Status |
|---|---|---|---|---:|---|
| <model> | <dimension/fact/mart> | <grain> | <table/incremental/view> | <row_count> | <PASS/WARN/FAIL/BLOCKED> |

## Star Schema And Reporting Shape

| Area | Decision | Evidence | Status |
|---|---|---|---|
| Fact grain | <decision> | `<proof file>` | <PASS/WARN/FAIL/BLOCKED> |
| Dimension keys | <decision> | `<proof file>` | <PASS/WARN/FAIL/BLOCKED> |
| Relationship paths | <decision> | `<proof file>` | <PASS/WARN/FAIL/BLOCKED> |
| Bridge tables | <built/deferred/not needed> | `<proof file>` | <PASS/WARN/FAIL/BLOCKED> |
| Privacy exposure | <decision> | `<proof file>` | <PASS/WARN/FAIL/BLOCKED> |

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Fact row counts | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Dimension uniqueness | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Relationship integrity | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Measure component summaries | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Mart non-empty check | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
