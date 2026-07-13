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

## Software Prerequisites

Use `references/software-prerequisites.md` and `scripts/check_software_prerequisites.py`.

| Software | Required for | Detected | Installed / action | Status | Notes |
|---|---|---|---|---|---|
| Python | scripts + dbt env | <version or missing> | <action> | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| venv | isolated installs | <yes/no> | <action> | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| pip | package install | <version or missing> | <action> | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| dbt-core | build/test | <version or missing> | <action> | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| dbt adapter | warehouse | <adapter/version or missing> | <action> | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| Skill requirements.txt | YAML/scripts/presentation | <ok/missing> | <action> | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| git | commits | <version or missing> | <action> | <PASS/WARN/FAIL/BLOCKED> | <notes> |
| Node/npx | skill install | <version or missing> | <action> | <PASS/WARN/N/A> | <notes> |
| gh | GitHub automation | <version or missing/n/a> | <action> | <PASS/WARN/N/A> | <notes> |

Evidence report: `reports/agent/01_setup/SOFTWARE_PREREQUISITES.md`

## What Was Completed

| Item | Result | Evidence |
|---|---|---|
| Software prerequisites check | <PASS/WARN/FAIL/BLOCKED> | <notes> |
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
