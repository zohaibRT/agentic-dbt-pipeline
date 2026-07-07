# Semantic Layer Report

## Template Use

Use this file as the fixed structure for `reports/agent/06_semantic/semantic_report.md`.
Replace placeholders with semantic model, metric, and reconciliation evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Semantic models created: <count>
- Metrics created: <count>
- Time spine status: <status>

## Semantic Artifacts

| Artifact | Source model | Grain | Purpose | Status |
|---|---|---|---|---|
| <semantic model/metric> | <model> | <grain> | <purpose> | <PASS/WARN/FAIL/BLOCKED> |

## Metric Definitions

| Metric | Business meaning | Formula | Date basis | Filters | Approval status | Verification status |
|---|---|---|---|---|---|---|
| <metric> | <meaning> | <formula> | <date field> | <filters> | <approved/proposed> | <PASS/WARN/FAIL/BLOCKED> |

## Validation

| Check | Result | Evidence |
|---|---|---|
| dbt parse | <PASS/WARN/FAIL/SKIPPED> | <command/result> |
| Semantic metric SQL reconciliation | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Numerator/denominator proof | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Time spine coverage | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
