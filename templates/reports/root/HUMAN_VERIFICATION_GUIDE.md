# Human Verification Guide

## Purpose

Use this guide to verify the generated dbt project without relying on chat history.

**Start here first:** `reports/agent/HUMAN_ATTENTION_BOARD.md`  
That board lists only what needs human input now. Do not begin in deep phase reports unless you are auditing evidence.

When any evidence file shows `WARN`, `FAIL`, `BLOCKED`, or `SKIPPED`, open the Attention Board row first, then follow its evidence link.

## What To Check

| Area | Evidence File | Why current status (if not PASS) | Human Action | Status |
|---|---|---|---|---|
| Human decisions now | `reports/agent/HUMAN_ATTENTION_BOARD.md` | <OPEN row count / "NONE"> | Answer OPEN questions; approve or change next prompt | TODO |
| Source lock | `reports/agent/00_discovery/core_profile.json` | <reason or "PASS"> | Confirm profile, adapter, database, and source schema | TODO |
| Discovery evidence | `reports/agent/00_discovery/sql_proofs/` | <Attention Board IDs or "PASS"> | Re-run only proofs linked from OPEN/CARRY_FORWARD rows | TODO |
| Layer validation | `reports/agent/LAYER_VERIFICATION_LEDGER.md` | <reason or "N/A until layers built"> | Confirm grain/joins only for built layers | TODO |
| KPI definitions | `reports/agent/KPI_DEFINITION_CONTRACTS.md` | <reason or "N/A until analytics"> | Confirm numerator/denominator only for proposed KPIs | TODO |
| Metric reconciliation | `reports/agent/METRIC_VERIFICATION_MATRIX.md` | <reason or "N/A until analytics"> | Confirm expected vs actual for promoted metrics | TODO |
| Presentation | `reports/agent/10_presentation/presentation_report.md` | <reason or "N/A until presentation"> | Confirm visuals use validated measures only | TODO |

## Open Decisions

Maintain OPEN decisions only on `HUMAN_ATTENTION_BOARD.md`. This section should point there, not duplicate the full list.

| Decision | Why It Matters | Recommendation | Owner | Status |
|---|---|---|---|---|
| See Attention Board | Single human surface | Answer OPEN rows there | Data engineer | OPEN / NONE |

## Final Sign-Off

Do not sign off when any Attention Board OPEN row remains unanswered, any hard gate is `FAIL`, any critical business definition is still ambiguous, or any `WARN` lacks a written reason and evidence link.
