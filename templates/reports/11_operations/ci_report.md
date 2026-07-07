# Continuous Integration Report

## Template Use

Use this file as the fixed structure for `reports/agent/11_operations/ci_report.md`.
Replace placeholders with workflow, secret, and validation evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED / SKIPPED>
- Continuous integration provider: <GitHub Actions / other>
- Workflow path: <path>

## Workflows

| Workflow | Path | Purpose | Status |
|---|---|---|---|
| <workflow> | <path> | <purpose> | <PASS/WARN/FAIL/BLOCKED/SKIPPED> |

## Required Secrets Or Variables

| Secret / Variable | Purpose | Status |
|---|---|---|
| <name> | <purpose> | <configured/missing/not required> |

## Validation

| Check | Result | Evidence |
|---|---|---|
| YAML parse | <PASS/WARN/FAIL/SKIPPED> | <result> |
| dbt command dry run | <PASS/WARN/FAIL/SKIPPED> | <result> |

## Next Action

- <action or "None">
