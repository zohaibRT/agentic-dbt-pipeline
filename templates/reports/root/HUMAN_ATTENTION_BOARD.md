# Human Attention Board

## Purpose

This is the **only** file a human should need for “what do you need from me?”  
Technical detail stays in phase reports and `sql_proofs/`. Do not duplicate full matrices here.

For KPIs that exist but cannot ship yet, also maintain `KPI_GAP_REGISTER.md` and re-warn in chat after every checkpoint.

Read skill references:

- `references/human-attention-reporting.md`
- `references/kpi-gap-and-stakeholder-warnings.md`
- `references/stakeholder-layer-and-presentation-guide.md`

## Current Checkpoint

| Field | Value |
|---|---|
| Checkpoint | <phase name> |
| Overall status | <PASS / WARN / FAIL / BLOCKED / AWAITING USER INPUT> |
| Last updated | <timestamp> |
| Active evidence folder | `reports/agent/<phase>/` |
| OPEN KPI gaps | <count — see KPI_GAP_REGISTER.md> |

## Need From Human Now

Only decisions that are `OPEN` and require a human answer or approval.

| ID | Need from human | Why it matters (plain language) | Recommendation | Evidence link | Blocks (including KPIs) | Status |
|---|---|---|---|---|---|---|
| <D-01> | <one clear question> | <what goes wrong if unanswered> | <safe default or ask> | `<path>` | <phase/output + KPI names> | OPEN |

If none: write one row `None | No human input required for this checkpoint | n/a | Continue | n/a | n/a | NONE`.

## KPI Impact Of OPEN Decisions

Re-state every checkpoint. Leaving these unanswered means these KPIs stay missing.

| Attention ID | Missing / confusing / blocked | KPIs we can make after you fix this | Gap Register ID | Status |
|---|---|---|---|---|
| <HA-002> | <Active definition unclear> | <Active Subscription Count> | <KG-001> | OPEN |

If none: write `No open KPI gaps.`

Full matrix: `reports/agent/KPI_GAP_REGISTER.md`.

## Carry-Forward Conditions

Accepted WARN/BLOCKED items that still constrain later phases. Do not re-ask unless the human wants to change them.

| ID | Condition | Why it still matters | Evidence link | Status |
|---|---|---|---|---|
| <C-01> | <condition> | <later impact including blocked KPIs> | `<path>` | CARRY_FORWARD |

## Not On This Board

Keep these out of the attention board (link only if needed):

- Full table inventories
- Full relationship/cardinality matrices
- PASS-only proof dumps
- Software version lists unless they block work
- Repeated copies of the same WARN essay across many phase files

Chat must still re-warn OPEN KPI gaps every checkpoint even when this board barely changed.

## Recommended Next Action

- Next approval: <what Yes means>
- Does not approve: <excluded work>
- Does **not** unlock blocked KPIs unless matching OPEN IDs above are answered
- Exact prompt: see `reports/agent/NEXT_PHASE_PROMPT.md`

## Quick Links

| Need | File |
|---|---|
| KPI gaps / blocked makeable KPIs | `KPI_GAP_REGISTER.md` |
| Pipeline status | `PIPELINE_STATUS.md` |
| Report map | `REPORT_INDEX.md` |
| Context / decisions memory | `CONTEXT_TREE.md` |
| Verification checklist | `HUMAN_VERIFICATION_GUIDE.md` |
| Current phase detail | `<phase report path>` |
| Proofs | `<phase>/sql_proofs/_proof_index.md` |
