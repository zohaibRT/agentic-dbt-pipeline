# KPI Gap Register And Stakeholder Warnings

Use this after **every** completed or blocked checkpoint, including discovery, bronze, silver, gold, semantic, analytics insights, presentation, and final delivery.

Also read [human-attention-reporting.md](human-attention-reporting.md), [stakeholder-layer-and-presentation-guide.md](stakeholder-layer-and-presentation-guide.md), [kpi-discovery-framework.md](kpi-discovery-framework.md), and [reporting-standards.md](reporting-standards.md).

## Core rule

Blockers and missing/confusing definitions hide valuable KPIs. The agent must:

1. Keep a live **KPI Gap Register** that lists KPIs the project **can** support once gaps are fixed.
2. Tie every blocked KPI to a concrete blocker, missing data, or open human decision.
3. **Re-warn the human in chat after every checkpoint**, even when the same blocker was shown before.
4. Tell the human plainly: **you must fix or answer these items, or these KPIs stay missing.**

Do not treat repeated chat warnings as duplication noise. File reports stay thin (Attention Board + Gap Register). Chat must re-state OPEN gaps every turn so the human cannot miss the cost of leaving blockers open.

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
| Attention Board ID | Matching `HA-###` / decision ID when human-owned |
| Needed human action | What the human must answer or approve |
| Cannot ship until | Plain “blocked until …” |
| Status | `OPEN` / `ANSWERED` / `UNLOCKED` / `DEFERRED` / `IMPOSSIBLE` |

`IMPOSSIBLE` means the warehouse has no supporting data (for example NPS with no survey tables). Keep those visible so the human does not expect magic.

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
Until you answer or fix them, the pipeline will not deliver the KPIs below.

| Attention ID | Blocker / missing / confusing | KPIs we can make after you fix this | Status |
|---|---|---|---|
| HA-002 | Active subscription definition unclear | Active Subscription Count | OPEN |
| HA-003 | CRM vs payments-service amount units unconfirmed | Cross-System Revenue, Net Revenue mix | OPEN |
| HA-004 | Delivered order definition unclear | Delivered Order Count | OPEN |

What you must do now:
1. Answer each OPEN row on `HUMAN_ATTENTION_BOARD.md`.
2. Supply missing business definitions, units, privacy policy, or mappings.
3. Confirm when source data simply does not exist (`IMPOSSIBLE` rows).

Trusted now (may present): <list APPROVED KPIs or "none yet">
Still blocked (do not present as live KPIs): <list OPEN gap KPI names>
```

Rules:

- If there are no KPI gaps, write exactly: `No open KPI gaps at this checkpoint.`
- If technical work continues (bronze → silver → gold facts) while gaps remain, say: **Build can continue, but these KPIs remain unavailable until you fix the gaps.**
- Never bury the warning only inside a report file.
- Never drop the section because the human approved a technical next phase.
- Mirror the same OPEN IDs as `HUMAN_ATTENTION_BOARD.md` and `KPI_GAP_REGISTER.md`.

## Layer speech template (stakeholder)

After every layer, the chat (and phase summary) should also include:

```text
Layer: <name>   Status: PASS / WARN / BLOCKED
Built: <what>
Trusted now: <what business users may rely on>
Still missing because of blockers: <KPI names>
Attention Board: <OPEN IDs>
Evidence: <phase report + gap register>
Next Yes allows: <scope>
Next Yes does NOT unlock: <blocked KPIs unless IDs are answered>
```

## Anti-duplication vs re-warning

| Allowed | Forbidden |
|---|---|
| Full KPI gap matrix once in `KPI_GAP_REGISTER.md` | Pasting the same long WARN essay into discovery, silver, gold, pipeline status, and context tree |
| Short Attention Board KPI impact table | Inventing KPIs with no evidence they are makeable |
| Re-stating OPEN gaps in **every chat summary** | Claiming “pipeline complete” while OPEN KPI gaps remain unmentioned |
| Linking proofs | Treating WARN as “ignore and approve” without KPI impact |

## Completion check

Checkpoint reporting is incomplete when:

- `KPI_GAP_REGISTER.md` is missing after discovery or any later phase that found candidate metrics
- Chat summary omits the **Still blocked — fix these or these KPIs stay missing** section
- OPEN Attention Board decisions have no linked blocked KPI names
- Presentation shows blocked KPIs as live cards
- Final delivery claims success without listing remaining OPEN KPI gaps
