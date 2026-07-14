# Human Attention Reporting

Use this to keep reports readable. Humans should not re-read the same WARN across eight files.

Also read [report-artifact-organization.md](report-artifact-organization.md), [human-review.md](human-review.md), and [phase-completion-report.md](phase-completion-report.md).

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
3. Conditions already accepted that still constrain later work (CARRY FORWARD)
4. Recommended next action and exact approval scope
5. Links to proof/report evidence (do not paste full tables again)

Do **not** put full source inventories, full relationship matrices, or full SQL results on this board.

## Anti-repetition rules

| Rule | Required behavior |
|---|---|
| One owner for each decision | Write the decision once on the Attention Board |
| Evidence stays in proofs | Put numbers in `sql_proofs/` headers; link from the board |
| Phase report is the detailed narrative | `discovery_report.md`, `gold_report.md`, etc. hold detail |
| Control files point, they do not clone | `PIPELINE_STATUS`, `CONTEXT_TREE`, `REPORT_INDEX` summarize and link |
| Chat summary mirrors the board | Chat shows the same OPEN decisions, not a second invented list |

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

| ID | Need from human | Why it matters | Recommendation | Evidence link | Blocks | Status |
|---|---|---|---|---|---|---|
| D-01 | Approve 30-table first pass? | Locks build scope | Approve with conditions | `00_discovery/first_pass_scope.json` | Setup | OPEN |
| G-02 | Privacy-safe account dim policy? | Enables customer slicing without clear-text PII | Hash keys; exclude names/phones | `05_gold` proof `015` | Complete star / KPIs | OPEN |

Status values: `OPEN`, `ANSWERED`, `CARRY_FORWARD`, `DEFERRED`.

## Chat and approval behavior

After each checkpoint, the chat control-panel summary should be short:

1. What finished
2. What needs human input now (IDs from the Attention Board)
3. What the next Yes allows / does not allow
4. Exact next-phase prompt

Do not paste full discovery inventories or full cardinality matrices into chat.

## Maintenance rule

When updating an open decision:

1. Change the Attention Board row
2. Update `PIPELINE_STATUS` Current Approval Gate to point at those IDs
3. Keep specialized reports as evidence owners; do not rewrite every file with the same paragraph

## Completion check

Reporting is unhealthy when:

- The same decision text appears in 3+ root/phase files
- The human cannot find OPEN decisions in under one minute
- Chat and Attention Board disagree
- Evidence is only in chat, not in proofs/files
