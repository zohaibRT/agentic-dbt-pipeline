# Human Verification Guide

## Purpose

Use this guide to verify the generated dbt project without relying on chat history.

## What To Check

| Area | Evidence File | Human Action | Status |
|---|---|---|---|
| Source lock | `reports/agent/00_discovery/core_profile.json` | Confirm the approved profile, adapter, database, and source schema are correct | TODO |
| Discovery evidence | `reports/agent/00_discovery/discovery_raw.json` and `sql_proofs/` | Re-run priority source proof queries if needed | TODO |
| Layer validation | `reports/agent/LAYER_VERIFICATION_LEDGER.md` | Confirm row counts, grain, joins, and expected-empty notes | TODO |
| KPI definitions | `reports/agent/KPI_DEFINITION_CONTRACTS.md` | Confirm numerator, denominator, filters, time field, and caveats | TODO |
| Metric reconciliation | `reports/agent/METRIC_VERIFICATION_MATRIX.md` | Confirm expected and actual results match | TODO |
| Presentation | `reports/agent/10_presentation/presentation_report.md` | Confirm visuals use only validated measures and data | TODO |

## Open Decisions

| Decision | Why It Matters | Recommendation | Owner | Status |
|---|---|---|---|---|
| TODO | TODO | TODO | Data engineer | OPEN |

## Final Sign-Off

Do not sign off when any required evidence file is missing, any hard gate is `FAIL`, or any critical business definition is still ambiguous.
