# Human Verification Guide

## Purpose

Use this guide to verify the generated dbt project without relying on chat history.

When any evidence file shows `WARN`, `FAIL`, `BLOCKED`, or `SKIPPED`, open that file and read **Why this status was used** before asking the agent. The reason must already be written in the report, `PIPELINE_STATUS.md` Status Review Queue, or `REPORT_INDEX.md`.

## What To Check

| Area | Evidence File | Why current status (if not PASS) | Human Action | Status |
|---|---|---|---|---|
| Source lock | `reports/agent/00_discovery/core_profile.json` | <reason or "PASS"> | Confirm the approved profile, adapter, database, and source schema are correct | TODO |
| Discovery evidence | `reports/agent/00_discovery/discovery_raw.json` and `sql_proofs/` | <reason or "PASS"> | Re-run priority source proof queries if needed | TODO |
| Discovery conditions | `reports/agent/00_discovery/discovery_report.md` Status Review | <copy top WARN reasons> | Accept, defer, or change scope before next phase | TODO |
| Layer validation | `reports/agent/LAYER_VERIFICATION_LEDGER.md` | <reason or "N/A until layers built"> | Confirm row counts, grain, joins, and expected-empty notes | TODO |
| KPI definitions | `reports/agent/KPI_DEFINITION_CONTRACTS.md` | <reason or "N/A until analytics"> | Confirm numerator, denominator, filters, time field, and caveats | TODO |
| Metric reconciliation | `reports/agent/METRIC_VERIFICATION_MATRIX.md` | <reason or "N/A until analytics"> | Confirm expected and actual results match | TODO |
| Presentation | `reports/agent/10_presentation/presentation_report.md` | <reason or "N/A until presentation"> | Confirm visuals use only validated measures and data | TODO |

## Open Decisions

| Decision | Why It Matters | Recommendation | Owner | Status |
|---|---|---|---|---|
| TODO | TODO | TODO | Data engineer | OPEN |

## Final Sign-Off

Do not sign off when any required evidence file is missing, any hard gate is `FAIL`, any critical business definition is still ambiguous, or any `WARN` lacks a written reason.
