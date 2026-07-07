# Project Setup And Configuration Report

## Template Use

Use this file as the fixed structure for `reports/agent/01_setup/setup_report.md`.
Replace placeholders with setup-specific evidence. Do not remove sections.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Project root: <path>
- dbt profile: <profile name without secrets>
- Adapter: <adapter>
- Setup mode: Automatic setup-only

## What Was Completed

| Item | Result | Evidence |
|---|---|---|
| Workspace `.env` check | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| dbt project scaffold | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <path> |
| Dependency installation | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <command/result> |
| dbt debug | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <command/result> |
| dbt deps | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <command/result> |
| dbt parse | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <command/result> |

## Schema Hygiene

| Check | Result | Notes |
|---|---|---|
| Source schema is read-only | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| Profile target schema is safe | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| Layer schemas are isolated | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| Package/evaluator schemas avoid source | <PASS/WARN/FAIL/BLOCKED> | <notes> |

## Files Created Or Changed

- `<path>`

## Not Included In Setup

- Source YAML generation
- Bronze/staging models
- Silver/intermediate models
- Gold/marts models
- Semantic layer
- Presentation layer
- Commits or pushes unless explicitly approved

## Open Decisions

- <decision or "None">

## Next Action

- <recommended next checkpoint and approval needed>
