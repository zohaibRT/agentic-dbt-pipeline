# Project Context Tree

Maintain a compact project memory so later phases can reuse prior user input, decisions, and outputs without relying on the full chat history.

## Core rule

Create and update:

```text
reports/agent/CONTEXT_TREE.md
```

If the dbt project root does not exist yet, create it under the current workspace/run root:

```text
<workspace.root>/reports/agent/CONTEXT_TREE.md
```

Use it as a curated context tree, not a raw chat transcript. Record only project-relevant information that helps future dbt work.

## When to update

Update `CONTEXT_TREE.md` after:

- Required inputs are confirmed
- Discovery completes
- User adds requirements, mappings, metrics, exclusions, privacy rules, or special instructions
- A phase plan is approved
- A phase completes and a phase report is written
- A user decision changes prior assumptions
- A validation failure, blocker, or accepted warning appears
- Final delivery completes

For discovery, update `CONTEXT_TREE.md` before sending the chat summary. The chat summary should point to the context tree, not replace it.

## What to capture

Capture:

- User-provided inputs
- User-approved requirements and rules
- Discovery conclusions
- Agent recommendations and whether they were approved, changed, or deferred
- Confidence notes: what is proven, what is uncertain, and what needs business confirmation
- Important data-engineering decisions
- Assumptions and their approval status
- Open decisions
- Phase outputs and report links
- Mermaid diagrams and their verification status
- Validation status
- Commit status
- Next recommended action

Do not capture:

- Passwords, tokens, private keys, or full `profiles.yml`
- Sensitive row samples or direct personal records
- Noisy chat text that does not affect project work
- Guessed values not confirmed by the user
- Internal reasoning

## File shape

Use this structure:

```markdown
# Project Context Tree

## Current State
- Current phase: <phase>
- Overall status: <PASS/WARN/BLOCKED/etc.>
- Next action: <next user/agent action>

## Inputs Confirmed By User
| Input | Value | Source |
|---|---|---|
| Domain | <domain> | user/.env |
| dbt profile | <profile> | user/.env |
| Source schema | <schema> | user/.env |

## Project Rules
| Area | Rule | Status |
|---|---|---|
| Metrics | <rule> | approved/open |

## Discovery Context
- <source-data conclusion>

## Modeling Decisions
| Decision | Choice | Evidence | Status |
|---|---|---|---|
| Grain | <choice> | <evidence> | approved/open |

## Recommendations
| Phase | Recommendation | Evidence | Outcome |
|---|---|---|---|
| <phase> | <recommended path> | <evidence> | approved/changed/deferred/open |

## Confidence
| Phase | Confident About | Less Confident About |
|---|---|---|
| <phase> | <validated facts> | <uncertain business or data assumptions> |

## Diagrams
| Phase | Diagram | Mermaid Type | Verification |
|---|---|---|---|
| <phase> | <file or section> | <erDiagram/flowchart/etc.> | <PASS/WARN/FAIL/SKIPPED> |

## Phase Tree
- Discovery
  - Input: <what was used>
  - Output: <main conclusion>
  - Report: reports/agent/discovery_report.md
  - Requirements: reports/agent/requirements.md
  - Status: <status>
- Project setup and configuration
  - Plan: <approved/not approved>
  - Report: reports/agent/setup_report.md
  - Status: <status>

## Open Decisions
- <decision needed>

## Report Index
| Phase | Report | Status |
|---|---|---|
| Discovery | reports/agent/discovery_report.md | <status> |
```

## Update style

Keep entries concise. Prefer links to phase reports for detail. If a user changes a prior decision, do not erase history; mark the old decision as superseded and add the new decision.

## Commit behavior

Commit `reports/agent/CONTEXT_TREE.md` with the same phase commit as the updated phase report, when commit approval is granted.
