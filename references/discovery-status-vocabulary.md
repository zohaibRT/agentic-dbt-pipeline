# Discovery Status Vocabulary

Use these status values consistently in discovery reports, SQL proof headers, JSON artifacts, checklists, and `PIPELINE_STATUS.md`.

## Core statuses

| Status | Meaning | When to use | Can build continue? |
|---|---|---|---|
| **PASS** | Evidence supports the claim; no material issue found | Row count matches expectation, key is unique, relationship match rate is acceptable | Yes for this item |
| **WARN** | Evidence exists but a known limitation remains documented | Empty upstream table with approved reason, partial match rate that was accepted, low-confidence inference that is documented | Yes with documented review |
| **FAIL** | Evidence shows the claim is wrong or unsafe | Duplicate grain, broken relationship, wrong schema/profile, missing required proof | No until fixed |
| **BLOCKED** | Work cannot finish until user input, credential, source approval, or business decision arrives | Ambiguous business meaning, missing profile, unapproved source switch | No until resolved |
| **SKIPPED** | Check was intentionally not run | Adapter cannot support query, table excluded from v1 scope, proof not applicable | Only if reason is documented |

## Why WARN exists

`WARN` does **not** mean failure. It means:

- the check ran or was reviewed
- the result is usable with eyes open
- a limitation is written down
- a human or later phase should confirm or accept the risk

Examples:

- Source table is empty, so downstream models will also be empty until data lands.
- Relationship match rate is 94% and the team accepts orphan rows for guest checkout.
- Business meaning of a status code is inferred but not yet approved.

Do not use `WARN` to hide a `FAIL`. Do not use `PASS` when a real limitation was not documented.

## Other common labels

| Label | Meaning |
|---|---|
| **OPEN** | Requirement or matrix row exists but work has not started |
| **IN_PROGRESS** | Approved for active work |
| **DEFERRED** | Intentionally postponed with evidence |
| **N/A** | Not applicable to this project or checkpoint |
| **APPROVED** | Human or checklist approved moving forward |
| **APPROVED WITH CONDITIONS** | Approved, but listed conditions must be carried into `CONTEXT_TREE.md` and requirements |

## Required usage

Every discovery SQL proof header must include one core status.

Every discovery report summary, checklist row, JSON `status` field, and inventory inclusion decision must use the vocabulary above.

## Status reason requirement

Every `WARN`, `FAIL`, `BLOCKED`, or `SKIPPED` status must include:

| Required field | Why |
|---|---|
| Why this status was used | Prevents unexplained labels |
| Evidence path | Lets the human verify the claim |
| What to review | Tells the data engineer exactly where judgment is needed |
| Required action | Makes the next step clear |
| Whether it blocks the next phase | Prevents accidental continuation |

Write these details in:

1. `reports/agent/PIPELINE_STATUS.md` under `Status Review Queue`
2. The phase report under `Status Review`
3. `reports/agent/REPORT_INDEX.md` in the **Why this status was used** column for every non-`PASS` row

Do not leave a non-`PASS` status only in a table row or prose paragraph with no reason.

### REPORT_INDEX.md rule

`REPORT_INDEX.md` is the first place many humans look. For every discovery or phase row:

| Column | Required |
|---|---|
| Status | `PASS` / `WARN` / `FAIL` / `BLOCKED` / `SKIPPED` / `PENDING` / `NOT APPROVED` |
| Why this status was used | One concrete sentence answering “why this status?” |
| What the data engineer should check | What to verify next |

Bad:

> Status = WARN, check column = “review privacy”

Good:

> Status = WARN, Why = “108 potential sensitive fields remain; clear-text gold exposure is not approved yet”, Check = “Approve exclude/mask/hash default before gold”

If discovery overall is `WARN` because open conditions exist, each discovery file row may also be `WARN`, but each row must state **its own** reason (do not copy a blank check list with no why).


### Mandatory Status Review Queue columns

When creating or updating `reports/agent/PIPELINE_STATUS.md`, copy the Status Review Queue table from `templates/reports/root/PIPELINE_STATUS.md` exactly. Required header text:

```text
| Status | Phase / Area | Why this status was used | Evidence | What to review | Required action | Owner | Blocks next checkpoint? |
```

Rules:

- Keep the **Why this status was used** column on every run, including first discovery and every later phase update.
- Do not shorten the table to only `Status | Area | Evidence | Required action`.
- Do not rename `Why this status was used` to a shorter label that drops the word `why`.
- If there are no non-`PASS` statuses, keep the section and write one row: `None | N/A | No non-PASS statuses | N/A | N/A | None | Agent | No`.
- `scripts/check_discovery_artifacts.py` fails when non-`PASS` statuses exist without these columns/terms.
