# Gold / Marts Report

## Template Use

Use this file as the fixed structure for `reports/agent/05_gold/gold_report.md`.
Replace placeholders with facts, dimensions, marts, metric components, and validation evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Layer schema: <schema>
- Dimensions built: <count>
- Facts built: <count>
- Bridges built: <count>
- Marts built: <count>
- Star-schema completeness: <COMPLETE / INCOMPLETE — see Dimension Inventory>

## Dimension Inventory

Every candidate dimension from included discovery/silver entities must appear here. Zero built dimensions is allowed only when every row is `DEFERRED`, `BLOCKED`, or `NOT_NEEDED` with proof. See `references/gold-dimension-completeness.md`.

| Candidate dimension | Evidence model/table | Decision | Privacy handling | Proof | Blocks complete star? |
|---|---|---|---|---|---|
| <entity or date dim> | <silver/bronze model> | <BUILD / BUILD_PRIVACY_SAFE / DEFERRED / BLOCKED / NOT_NEEDED> | <hash/exclude attrs/n/a> | `<proof file>` | <yes/no> |

## Models Built Or Changed

| Model | Type | Grain | Materialization | Row count | Status |
|---|---|---|---|---:|---|
| <model> | <dimension/fact/bridge/mart> | <grain> | <table/incremental/view> | <row_count> | <PASS/WARN/FAIL/BLOCKED> |

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
