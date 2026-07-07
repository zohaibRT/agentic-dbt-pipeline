# Pipeline Status

## Template Use

Use this file as the fixed structure for `reports/agent/PIPELINE_STATUS.md`.
Replace placeholder text with the current pipeline state.
Keep this file current after every checkpoint.

## Current Status

| Field | Value |
|---|---|
| Current checkpoint | Discovery |
| Status | <PASS / WARN / FAIL / BLOCKED / AWAITING USER INPUT> |
| Active phase folder | `reports/agent/00_discovery/` |
| Last updated | <date/time/timezone> |
| Next checkpoint | <setup / requirements update / source confirmation / blocked> |

## Configuration Scope

| Setting | Value | Source | Status |
|---|---|---|---|
| Domain | <domain> | `.env` or user prompt | <confirmed / missing / placeholder> |
| Business description | <description or "Not provided"> | `.env` or user prompt | <confirmed / optional> |
| dbt profile name | <profile name without secrets> | `.env` or user prompt | <confirmed / missing> |
| Adapter | <adapter> | `profiles.yml` | <confirmed / blocked> |
| Database or catalog | <database/catalog/project> | `profiles.yml` | <confirmed / blocked> |
| Source schema | <source schema> | `.env` or user prompt | <confirmed / missing / blocked> |

## Phase Status

| Phase | Status | Report | Notes |
|---|---|---|---|
| Discovery | <PASS/WARN/FAIL/BLOCKED> | `reports/agent/00_discovery/discovery_report.md` | <notes> |
| Project setup and configuration | <PENDING/BLOCKED/SKIPPED> | `reports/agent/01_setup/setup_report.md` | <notes> |
| Sources | PENDING | `reports/agent/02_sources/sources_report.md` | Not approved by discovery |
| Bronze / staging | PENDING | `reports/agent/03_bronze/bronze_report.md` | Not approved by discovery |
| Silver / intermediate | PENDING | `reports/agent/04_silver/silver_report.md` | Not approved by discovery |
| Gold / marts | PENDING | `reports/agent/05_gold/gold_report.md` | Not approved by discovery |
| Semantic layer | PENDING | `reports/agent/06_semantic/semantic_report.md` | Not approved by discovery |
| Project evaluator | PENDING | `reports/agent/07_evaluator/evaluator_report.md` | Not approved by discovery |
| Documentation | PENDING | `reports/agent/08_documentation/docs_report.md` | Not approved by discovery |
| Analytics insight reporting | PENDING | `reports/agent/09_analytics_insights/analytics_insight_report.md` | Not approved by discovery |
| Presentation layer | PENDING | `reports/agent/10_presentation/presentation_report.md` | Not approved by discovery |

## Current Approval Gate

- Approval requested: <yes/no>
- Approval scope: <what approval permits>
- Approval does not permit: <what remains excluded>
- Required user response: <response or decision needed>

## Important Warnings Or Blockers

- <warning/blocker or "None">

## Latest Validation Evidence

| Check | Result | Evidence |
|---|---|---|
| Source inventory | <PASS/WARN/FAIL/BLOCKED> | <proof/report path> |
| Row counts | <PASS/WARN/FAIL/BLOCKED> | <proof/report path> |
| Keys and grain | <PASS/WARN/FAIL/BLOCKED> | <proof/report path> |
| Relationships | <PASS/WARN/FAIL/BLOCKED> | <proof/report path> |
| Privacy review | <PASS/WARN/FAIL/BLOCKED> | <report path> |
