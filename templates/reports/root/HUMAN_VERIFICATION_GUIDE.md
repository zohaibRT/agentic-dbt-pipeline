# Human Verification Guide

## Purpose

Use this guide to verify the generated dbt project without relying on chat history.

**Start here first:** `reports/agent/HUMAN_ATTENTION_BOARD.md`  
Then open: `reports/agent/KPI_GAP_REGISTER.md`  

The Attention Board lists decisions you must answer now.  
The Gap Register lists KPIs the project can make once those gaps are fixed, plus impossible/out-of-scope KPIs.

When any evidence file shows `WARN`, `FAIL`, `BLOCKED`, or `SKIPPED`, open the Attention Board row first, then follow its evidence link and Gap Register impact.

## What To Check

| Area | Evidence File | Why current status (if not PASS) | Human Action | Status |
|---|---|---|---|---|
| Human decisions now | `reports/agent/HUMAN_ATTENTION_BOARD.md` | <OPEN row count / "NONE"> | Answer OPEN questions; approve or change next prompt | TODO |
| KPI gaps / blocked makeable KPIs | `reports/agent/KPI_GAP_REGISTER.md` | <OPEN gap count / "NONE"> | Fix definitions/data/privacy/units listed; do not expect blocked KPIs live | TODO |
| Source lock | `reports/agent/00_discovery/core_profile.json` | <reason or "PASS"> | Confirm profile, adapter, database, and source schema | TODO |
| Discovery evidence | `reports/agent/00_discovery/sql_proofs/` | <Attention Board IDs or "PASS"> | Re-run only proofs linked from OPEN/CARRY_FORWARD rows | TODO |
| Layer validation | `reports/agent/LAYER_VERIFICATION_LEDGER.md` | <reason or "N/A until layers built"> | Confirm grain/joins only for built layers | TODO |
| KPI definitions | `reports/agent/KPI_DEFINITION_CONTRACTS.md` | <reason or "N/A until analytics"> | Confirm numerator/denominator only for proposed KPIs | TODO |
| Metric reconciliation | `reports/agent/METRIC_VERIFICATION_MATRIX.md` | <reason or "N/A until analytics"> | Confirm expected vs actual for promoted metrics | TODO |
| Presentation | `reports/agent/10_presentation/presentation_report.md` | <reason or "N/A until presentation"> | Confirm visuals use validated measures only; blocked KPIs stay on Blocked tab | TODO |

## Open Decisions

Maintain OPEN decisions only on `HUMAN_ATTENTION_BOARD.md`. Maintain blocked makeable KPIs only on `KPI_GAP_REGISTER.md`. This section should point there, not duplicate the full lists.

| Decision | Why It Matters | Recommendation | Owner | Status |
|---|---|---|---|---|
| See Attention Board | Single human decision surface | Answer OPEN rows there | Data engineer | OPEN / NONE |
| See KPI Gap Register | Shows KPI cost of unanswered blockers | Fix gaps before expecting live KPIs | Data engineer / business owner | OPEN / NONE |

## Pass Criteria Reminder

- Trusted / APPROVED KPIs reconcile expected = actual
- OPEN Gap Register KPIs are **not** presented as live cards
- Chat checkpoint summaries repeatedly warned about remaining OPEN gaps
- No sign-off while OPEN Attention Board rows that block critical KPIs remain unanswered without explicit deferral

## Final Sign-Off

Do not sign off when any Attention Board OPEN row remains unanswered without documented deferral, any hard gate is `FAIL`, any critical business definition is still ambiguous, any OPEN Gap Register KPI is treated as delivered, or any `WARN` lacks a written reason and evidence link.
