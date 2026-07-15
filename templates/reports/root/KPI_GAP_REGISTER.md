# KPI Gap Register

## Purpose

List KPIs this project **can** deliver once blockers, missing data, or unclear definitions are fixed.  
Update after every checkpoint. Re-warn the human in chat every time OPEN gaps remain.

Read skill reference: `references/kpi-gap-and-stakeholder-warnings.md`.

## How To Use

1. Human answers OPEN rows on `HUMAN_ATTENTION_BOARD.md`.
2. Agent unlocks matching KPIs with proofs and contracts.
3. Move unlocked rows to `UNLOCKED` and stop presenting them as blocked.
4. Keep `IMPOSSIBLE` rows when source data does not exist.

## Current Checkpoint

| Field | Value |
|---|---|
| Checkpoint | <phase name> |
| Last updated | <timestamp> |
| OPEN gap count | <n> |
| Trusted live KPIs | <names or None> |

## Makeable KPIs Still Blocked

| ID | KPI candidate | Why it matters | Evidence it is makeable | Blocker type | What is missing or confusing | Attention Board ID | Needed human action | Cannot ship until | Status |
|---|---|---|---|---|---|---|---|---|---|
| KG-001 | <Active Subscription Count> | <portfolio health> | <fct_subscriptions + status column; proof path> | MISSING_DEFINITION | <Active vs not_deleted unclear> | HA-002 | <Approve Active rule> | <definition approved + reconciled> | OPEN |

If none: write one row `None | No blocked makeable KPIs | n/a | n/a | n/a | n/a | n/a | Continue | n/a | NONE`.

## Impossible Or Out-Of-Scope KPIs

KPIs the human may expect from the domain story, but this warehouse cannot support yet.

| KPI candidate | Why expected | Why impossible / out of scope | Needed data or system | Status |
|---|---|---|---|---|
| <NPS> | <customer experience> | <no survey/ticket satisfaction tables in source> | <CSAT/NPS feed> | IMPOSSIBLE |

If none: write `None`.

## Unlocked Since Last Update

| ID | KPI | Unlocked by decision | Proof / contract | Status |
|---|---|---|---|---|
| <KG-00x> | <name> | <HA-00x answer> | <contract + proof path> | UNLOCKED |

## Chat Reminder Text (copy into every checkpoint summary)

```text
## Still blocked — fix these or these KPIs stay missing

Until OPEN blockers below are fixed, these KPIs will not be delivered.

| Attention ID | Blocker / missing / confusing | KPIs blocked | Status |
|---|---|---|---|
| <HA-00x> | <gap> | <KPI names> | OPEN |

Trusted now: <list>
Still blocked: <list>
```
