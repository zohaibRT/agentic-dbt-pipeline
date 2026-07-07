# Sources Report

## Template Use

Use this file as the fixed structure for `reports/agent/02_sources/sources_report.md`.
Replace placeholders with source YAML, codegen, source test, and freshness evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Source schema: <source schema>
- dbt source name: <source name>
- Tables included: <count>
- Tables excluded or deferred: <count>

## What Was Built Or Changed

| Item | Detail | Status |
|---|---|---|
| Source YAML | <path> | <PASS/WARN/FAIL/BLOCKED> |
| Package dependencies | <packages> | <PASS/WARN/FAIL/BLOCKED> |
| Source tests | <unique/not_null/relationships/accepted_values/freshness> | <PASS/WARN/FAIL/BLOCKED> |
| Codegen output | <path or skipped reason> | <PASS/WARN/FAIL/BLOCKED/SKIPPED> |

## Included Source Tables

| Table | Row count | Grain | Candidate key | Included reason | Proof file |
|---|---:|---|---|---|---|
| <table> | <row_count> | <grain> | <key> | <reason> | `<proof file>` |

## Excluded Or Deferred Source Tables

| Table | Reason | Required action |
|---|---|---|
| <table> | <reason> | <action> |

## Validation

| Check | Result | Evidence |
|---|---|---|
| dbt deps | <PASS/WARN/FAIL/SKIPPED> | <command/result> |
| dbt parse | <PASS/WARN/FAIL/SKIPPED> | <command/result> |
| Source row-count proof | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |
| Source tests/freshness | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <command/result> |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
