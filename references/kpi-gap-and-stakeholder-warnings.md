# KPI Gap Register And Stakeholder Warnings

Use this after **every** completed or blocked checkpoint, including discovery, bronze, silver, gold, semantic, analytics insights, presentation, and final delivery.

Also read [human-attention-reporting.md](human-attention-reporting.md), [stakeholder-layer-and-presentation-guide.md](stakeholder-layer-and-presentation-guide.md), [kpi-discovery-framework.md](kpi-discovery-framework.md), and [reporting-standards.md](reporting-standards.md).

## Core rule

Blockers and missing/confusing definitions hide valuable KPIs. The agent must:

1. Keep a live **KPI Gap Register** that lists KPIs the project **can** support once gaps are fixed.
2. Tie every blocked KPI to a concrete blocker, missing data, or open human decision.
3. For every OPEN gap, write a concrete **agent recommendation** (rule + why + alternative rejected), not only “needs human input.”
4. **Re-warn the human in chat after every checkpoint**, even when the same blocker was shown before.
5. Tell the human plainly: **accept the recommendation, override it, or these KPIs stay missing.**

Do not treat repeated chat warnings as duplication noise. File reports stay thin (Attention Board + Gap Register). Chat must re-state OPEN gaps **and agent recommendations** every turn so the human cannot miss the cost of leaving blockers open.

## Required artifact

Create and update:

```text
reports/agent/KPI_GAP_REGISTER.md
```

Use `templates/reports/root/KPI_GAP_REGISTER.md`.

Also keep a short **KPI impact** section on `reports/agent/HUMAN_ATTENTION_BOARD.md` that links to the register and lists only OPEN gap rows.

## Gap register columns

| Column | Meaning |
|---|---|
| KPI candidate | Business name of the KPI we could deliver |
| Why it matters | Plain-language value |
| Evidence that it is makeable | Tables/models/columns or proofs that exist today |
| Blocker type | `MISSING_DATA` / `MISSING_DEFINITION` / `PRIVACY` / `UNITS` / `GRAIN` / `MAPPING` / `RELATIONSHIP` / `DIMENSION` / `APPROVAL` |
| What is missing or confusing | Exact gap |
| Agent recommendation | Concrete preferred rule (not “pick one”) |
| Why this recommendation | Proof counts, uniqueness, privacy, or reconciliation evidence |
| Alternative rejected | Weaker option and why |
| Attention Board ID | Matching `HA-###` / decision ID when human-owned |
| Ask from human | `Accept recommendation` / `Override: <rule>` / `Defer` |
| Cannot ship until | Plain “blocked until …” |
| Status | `OPEN` / `ANSWERED` / `UNLOCKED` / `DEFERRED` / `IMPOSSIBLE` |

`IMPOSSIBLE` means the warehouse has no supporting data (for example NPS with no survey tables). Keep those visible so the human does not expect magic.

## Privacy opt-out and PRIVACY blockers

When `requirements.md` or `CONTEXT_TREE.md` records a privacy minimization opt-out (`Do NOT apply privacy minimization unless I explicitly request it`, etc.):

| Required | Forbidden |
|---|---|
| Close OPEN `PRIVACY` rows for phone, IMEI, serial, fingerprint, email, address, and other tier-2 operational identifiers | OPEN row: `Direct identifiers \| Exclude phone/IMEI/serial/IBAN/fingerprint from gold \| Privacy default` |
| Record opt-out once as `CARRY_FORWARD` on the Attention Board | Re-asking privacy approval every checkpoint |
| Exclude tier-1 fields (secrets, OTP, full IBAN dumps, national IDs, PHI) from **presentation** with a one-line caveat | Blocking partner/program/product/status dims for privacy |

Use blocker type `PRIVACY` only when the user has **not** opted out, or when tier-1 secrets would reach presentation without explicit approval. Under opt-out, product-key, payment-reconciliation, and mapping gaps stay OPEN; privacy on commercial identifiers does not.

Run `python <skill>/scripts/check_privacy_opt_out.py --root <project.root>` before final delivery when opt-out is recorded.

## When to update

Update the Gap Register whenever:

- Discovery finds candidate metrics that need definitions or reconciliation
- A layer proves a measure exists but cannot promote it to a KPI
- A dimension, privacy, date, currency, status, or join decision blocks reporting
- Analytics insights defer or block KPI contracts
- Presentation marks a visual `BLOCKED` / `DEFERRED`
- The human answers a decision (move to `ANSWERED` / `UNLOCKED`)

## Mandatory chat re-warning (every checkpoint)

Every visible Markdown chat control-panel summary **must** include this section, even if the human has seen it before and even if the next phase can still proceed technically:

```text
## Still blocked — fix these or these KPIs stay missing

You still have open blockers / missing data / unclear definitions.
Until you accept or override the agent recommendations below, the pipeline will not deliver these KPIs.

## Agent recommends (accept or override)

| Attention ID | Agent recommendation | Why | KPIs unlocked if accepted | Status |
|---|---|---|---|---|
| HA-002 | Active = status Active AND not deleted | Status separates states; not_deleted alone inflates 826 vs 271 | Active Subscription Count | OPEN |
| HA-003 | Keep CRM and payments-service money separate until units confirmed | Amount scales differ (~4k vs ~487k peaks) | Cross-System Revenue | OPEN |
| HA-004 | Delivered = order status delivered | delivered_on alone can count scheduled/future dates | Delivered Order Count | OPEN |

What you must do now:
1. For each OPEN row: reply Accept recommendation, Override with your exact rule, or Defer with reason.
2. Update answers on `HUMAN_ATTENTION_BOARD.md` / confirm in chat.
3. Confirm when source data simply does not exist (`IMPOSSIBLE` rows).

Trusted now (may present): <list APPROVED KPIs or "none yet">
Still blocked (do not present as live KPIs): <list OPEN gap KPI names>
```

Forbidden chat patterns for OPEN gaps:

- “What should we do?” with no recommendation
- “Please decide between A and B” with no preferred option
- Only listing blockers without how the agent would unblock them

Rules:

- If there are no KPI gaps, write exactly: `No open KPI gaps at this checkpoint.`
- If technical work continues (bronze → silver → gold facts) while gaps remain, say: **Build can continue, but these KPIs remain unavailable until you accept or override the recommendations.**
- Never bury the warning only inside a report file.
- Never drop the section because the human approved a technical next phase.
- Mirror the same OPEN IDs, recommendations, and KPI names as `HUMAN_ATTENTION_BOARD.md` and `KPI_GAP_REGISTER.md`.
- Every OPEN gap row in chat and files must include agent recommendation + why.
## Layer speech template (stakeholder)

After every layer, the chat (and phase summary) should also include:

```text
Layer: <name>   Status: PASS / WARN / BLOCKED
Built: <what>
Trusted now: <what business users may rely on>
Still missing because of blockers: <KPI names>
Agent recommends: <one-line preferred rule per OPEN ID>
Attention Board: <OPEN IDs>
Evidence: <phase report + gap register>
Next Yes allows: <scope>
Next Yes does NOT unlock: <blocked KPIs unless recommendations accepted/overridden>
```

## Anti-duplication vs re-warning

| Allowed | Forbidden |
|---|---|
| Full KPI gap matrix once in `KPI_GAP_REGISTER.md` | Pasting the same long WARN essay into discovery, silver, gold, pipeline status, and context tree |
| Short Attention Board KPI impact table | Inventing KPIs with no evidence they are makeable |
| Re-stating OPEN gaps + recommendations in **every chat summary** | Claiming “pipeline complete” while OPEN KPI gaps remain unmentioned |
| Linking proofs | Treating WARN as “ignore and approve” without KPI impact |
| Concrete agent recommendation on every OPEN row | Ask-only “what should we do?” / “pick one” |

## Completion check

Checkpoint reporting is incomplete when:

- `KPI_GAP_REGISTER.md` is missing after discovery or any later phase that found candidate metrics
- Chat summary omits the **Still blocked** or **Agent recommends** sections while OPEN gaps exist
- OPEN Attention Board decisions have no concrete Recommendation / Why / Ask
- OPEN Attention Board decisions have no linked blocked KPI names
- Presentation shows blocked KPIs as live cards
- Final delivery claims success without listing remaining OPEN KPI gaps
