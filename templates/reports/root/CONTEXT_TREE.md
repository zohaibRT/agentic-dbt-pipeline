# Context Tree

## Template Use

Use this file as the fixed structure for `reports/agent/CONTEXT_TREE.md`.
Update it after each checkpoint so later phases can reload decisions without depending on chat history.

## Active Run

| Field | Value |
|---|---|
| Current checkpoint | Discovery |
| Current status | <PASS / WARN / FAIL / BLOCKED / AWAITING USER INPUT> |
| Last updated | <date/time/timezone> |
| Source lock status | <locked / pending / blocked> |

## Input Context

| Input | Value | Source | Notes |
|---|---|---|---|
| Domain | <domain> | `.env` or prompt | <notes> |
| Business description | <description or "Not provided"> | `.env` or prompt | <notes> |
| dbt profile name | <profile> | `.env` or prompt | <notes> |
| Adapter | <adapter> | `profiles.yml` | <notes> |
| Database or catalog | <database/catalog/project> | `profiles.yml` | <notes> |
| Source schema | <source schema> | `.env` or prompt | <notes> |

## Source Evidence Summary

| Area | Evidence | Confidence | Report / Proof |
|---|---|---|---|
| Tables | <summary> | <high/medium/low/blocker> | <path> |
| Keys and grain | <summary> | <high/medium/low/blocker> | <path> |
| Relationships | <summary> | <high/medium/low/blocker> | <path> |
| Business process | <summary> | <high/medium/low/blocker> | <path> |
| Data quality | <summary> | <high/medium/low/blocker> | <path> |
| Privacy | <summary> | <high/medium/low/blocker> | <path> |
| Candidate metrics | <summary> | <high/medium/low/blocker> | <path> |

## Decisions And Rules

| Decision / Rule | Status | Source | Applies To | Notes |
|---|---|---|---|---|
| <decision> | <approved/proposed/blocked/deferred> | <user/discovery/default> | <phase/layer> | <notes> |

## Open Questions

| Question | Why it matters | Blocking phase | Current status |
|---|---|---|---|
| <question> | <impact> | <phase> | <open/deferred/answered> |

## Deferred Or Blocked Scope

| Scope | Reason | Required action | Owner |
|---|---|---|---|
| <scope> | <reason> | <action> | <user/agent> |

## Next Action

- Recommended next checkpoint: <checkpoint>
- What approval permits: <scope>
- What approval does not permit: <scope>
