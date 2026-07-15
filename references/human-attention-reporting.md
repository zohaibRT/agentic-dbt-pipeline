# Human Attention Reporting

Use this to keep reports readable. Humans should not re-read the same WARN across eight files.

Also read [report-artifact-organization.md](report-artifact-organization.md), [human-review.md](human-review.md), [phase-completion-report.md](phase-completion-report.md), [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md), and [stakeholder-layer-and-presentation-guide.md](stakeholder-layer-and-presentation-guide.md).

Important: anti-duplication applies to **files**. Chat must still **re-warn every checkpoint** about OPEN blockers and the KPIs those blockers keep missing.

## Goal

Separate:

| Layer | Purpose | Audience |
|---|---|---|
| **Attention** | Only decisions the human must make now | Human driver |
| **Evidence** | Proofs, inventories, technical detail | Auditor / re-run |
| **Archive** | Full phase narrative when needed | Later reference |

If a human opens one file and can answer “what do you need from me?”, reporting is working.

## Single human surface

Keep one live attention file:

```text
reports/agent/HUMAN_ATTENTION_BOARD.md
```

Update it after every checkpoint. It must contain only:

1. Current checkpoint and overall status
2. Decisions waiting on the human (OPEN / NEEDED NOW)
3. KPI impact of OPEN decisions (which makeable KPIs stay missing)
4. Conditions already accepted that still constrain later work (CARRY FORWARD)
5. Recommended next action and exact approval scope
6. Links to proof/report evidence and `KPI_GAP_REGISTER.md` (do not paste full matrices again)

Do **not** put full source inventories, full relationship matrices, or full SQL results on this board.

Maintain the full makeable-but-blocked KPI matrix in:

```text
reports/agent/KPI_GAP_REGISTER.md
```

## Anti-repetition rules

| Rule | Required behavior |
|---|---|
| One owner for each decision | Write the decision once on the Attention Board |
| Evidence stays in proofs | Put numbers in `sql_proofs/` headers; link from the board |
| Phase report is the detailed narrative | `discovery_report.md`, `gold_report.md`, etc. hold detail |
| Control files point, they do not clone | `PIPELINE_STATUS`, `CONTEXT_TREE`, `REPORT_INDEX` summarize and link |
| Chat summary mirrors the board | Chat shows the same OPEN decisions and **re-warns KPI gaps every checkpoint** |

Forbidden:

- Copying the same WARN paragraph into discovery report, checklist, pipeline status, context tree, requirements, and report index
- Asking the human to “review privacy” in six places with no single decision row
- Expanding every proof result into every Markdown report

Allowed:

- Short status + link: `WARN — see Attention Board #D-03 and proof 060`
- One plain-language Why on the Attention Board
- Full matrix only in the specialized report (`cardinality_report.md`, etc.)

## What must get human attention

Only promote a row to the Attention Board when the human must choose, approve, or unblock something:

| Promote | Examples |
|---|---|
| Yes | Scope approval, privacy policy, currency units, lifecycle mappings, dim build vs defer, next-phase approval |
| No | Exact row counts already proven PASS, template boilerplate, repeated inventory lists, software versions unless blocked |

Technical PASS evidence stays in proofs and the phase report. Do not flood the human with PASS noise.

## Attention Board row shape

| ID | Need from human | Why it matters | Agent recommendation | Why recommended | Alternative rejected | Evidence link | Blocks | Status |
|---|---|---|---|---|---|---|---|---|
| D-01 | Approve 30-table first pass? | Locks build scope | Approve with documented conditions | Priority tables have keys/counts; deferred tables are enrichment-only | Expanding to all adjacent tables before relationships are proven | `00_discovery/first_pass_scope.json` | Setup | OPEN |
| G-02 | Privacy-safe account dim policy? | Enables customer slicing without clear-text PII | Hash keys; exclude names/phones from gold | Direct identifiers are present in source and unnecessary for first marts | Clear-text gold exposure | `05_gold` proof `015` | Complete star / KPIs | OPEN |

Status values: `OPEN`, `ANSWERED`, `CARRY_FORWARD`, `DEFERRED`.

Every OPEN row must include a concrete agent recommendation. Forbidden recommendation text: `TBD`, `needs discussion`, `pick one`, or an empty cell.

## Chat and approval behavior

After each checkpoint, the chat control-panel summary should be short but must **repeat** open KPI warnings:

1. What finished
2. What needs human input now (IDs from the Attention Board)
3. Mandatory section: **Still blocked — fix these or these KPIs stay missing**
4. Mandatory section: **Agent recommends (accept or override)** — concrete preferred rule + why + KPIs unlocked for each OPEN ID
5. Trusted now vs still blocked KPI lists
6. What the next Yes allows / does not allow (explicitly: next Yes does not unlock blocked KPIs unless OPEN recommendations are accepted or overridden)
7. Exact next-phase prompt

Do not paste full discovery inventories or full cardinality matrices into chat.

Do not skip the KPI-gap re-warning because the human already approved a technical phase or saw the same blocker earlier.

Do not ask “what should we do?” without a recommended default. Every OPEN row must have Accept / Override / Defer.

## Maintenance rule

When updating an open decision:

1. Change the Attention Board row
2. Update matching `KPI_GAP_REGISTER.md` rows and KPI impact section
3. Update `PIPELINE_STATUS` Current Approval Gate to point at those IDs
4. Keep specialized reports as evidence owners; do not rewrite every file with the same paragraph

## Completion check

Reporting is unhealthy when:

- The same long decision essay appears in 3+ root/phase files
- The human cannot find OPEN decisions in under one minute
- Chat and Attention Board disagree
- Evidence is only in chat, not in proofs/files
- Chat omits the repeated **Still blocked** / **Agent recommends** warning while OPEN gaps exist
- Makeable blocked KPIs are not listed in `KPI_GAP_REGISTER.md`
- OPEN Attention Board rows lack a concrete agent recommendation (ask-only / pick-one / TBD)
