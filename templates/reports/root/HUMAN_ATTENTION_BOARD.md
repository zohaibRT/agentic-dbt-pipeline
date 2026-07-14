# Human Attention Board

## Purpose

This is the **only** file a human should need for “what do you need from me?”  
Technical detail stays in phase reports and `sql_proofs/`. Do not duplicate full matrices here.

Read [references/human-attention-reporting.md](../../../references/human-attention-reporting.md) in the skill repo.

## Current Checkpoint

| Field | Value |
|---|---|
| Checkpoint | <phase name> |
| Overall status | <PASS / WARN / FAIL / BLOCKED / AWAITING USER INPUT> |
| Last updated | <timestamp> |
| Active evidence folder | `reports/agent/<phase>/` |

## Need From Human Now

Only decisions that are `OPEN` and require a human answer or approval.

| ID | Need from human | Why it matters (plain language) | Recommendation | Evidence link | Blocks | Status |
|---|---|---|---|---|---|---|
| <D-01> | <one clear question> | <what goes wrong if unanswered> | <safe default or ask> | `<path>` | <phase/output> | OPEN |

If none: write one row `None | No human input required for this checkpoint | n/a | Continue | n/a | n/a | NONE`.

## Carry-Forward Conditions

Accepted WARN/BLOCKED items that still constrain later phases. Do not re-ask unless the human wants to change them.

| ID | Condition | Why it still matters | Evidence link | Status |
|---|---|---|---|---|
| <C-01> | <condition> | <later impact> | `<path>` | CARRY_FORWARD |

## Not On This Board

Keep these out of the attention board (link only if needed):

- Full table inventories
- Full relationship/cardinality matrices
- PASS-only proof dumps
- Software version lists unless they block work
- Repeated copies of the same WARN text

## Recommended Next Action

- Next approval: <what Yes means>
- Does not approve: <excluded work>
- Exact prompt: see `reports/agent/NEXT_PHASE_PROMPT.md`

## Quick Links

| Need | File |
|---|---|
| Pipeline status | `PIPELINE_STATUS.md` |
| Report map | `REPORT_INDEX.md` |
| Context / decisions memory | `CONTEXT_TREE.md` |
| Current phase detail | `<phase report path>` |
| Proofs | `<phase>/sql_proofs/_proof_index.md` |
