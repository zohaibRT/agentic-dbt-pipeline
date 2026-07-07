# Project Evaluator Report

## Template Use

Use this file as the fixed structure for `reports/agent/07_evaluator/evaluator_report.md`.
Replace placeholders with dbt_project_evaluator results and accepted-warning evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Evaluator schema: <schema>
- Tests passed: <count>
- Warnings accepted: <count>
- Failures: <count>

## Evaluator Results

| Finding area | Result | Count | Action |
|---|---|---:|---|
| Model directories | <PASS/WARN/FAIL> | <count> | <fix/accept/defer> |
| Naming conventions | <PASS/WARN/FAIL> | <count> | <fix/accept/defer> |
| Documentation coverage | <PASS/WARN/FAIL> | <count> | <fix/accept/defer> |
| Test coverage | <PASS/WARN/FAIL> | <count> | <fix/accept/defer> |
| DAG quality | <PASS/WARN/FAIL> | <count> | <fix/accept/defer> |

## Accepted Warnings

| Warning | Reason accepted | Evidence | Future action |
|---|---|---|---|
| <warning> | <reason> | `<proof/report>` | <action> |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
