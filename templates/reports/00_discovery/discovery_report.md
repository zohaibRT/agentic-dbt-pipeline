# Discovery Report

## Read First

- Status meanings: `PASS`, `WARN`, `FAIL`, `BLOCKED`, `SKIPPED` — see `reports/agent/00_discovery/README.md` and skill reference `references/discovery-status-vocabulary.md`.
- Machine-readable context: `core_profile.json` and `discovery_raw.json` in this folder are required on every discovery run.
- `WARN` means a documented limitation exists; it is not the same as `FAIL`.

## Template Use

Use this file as the fixed structure for `reports/agent/00_discovery/discovery_report.md`.
Replace placeholder text with source-specific evidence.
Do not remove sections; write `None`, `Not observed`, `Not supported by evidence`, or `Blocked` when needed.

## Executive Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Source reviewed: <database/catalog>.<source schema>
- Tables inspected: <count>
- Non-empty tables: <count>
- Recommended next step: <automatic setup / stop for requirements / stop for source confirmation>

## Status Review

Every non-`PASS` status in this report must be explained here so a normal human can understand it without asking the agent.

**Writing rule for this table:** use plain language first, technical detail second.

Each **Why this status was used** cell must answer all of these in 2–4 short sentences:

1. What we found (in everyday words)
2. Why that matters / what could go wrong
3. What is still OK to do now
4. What must wait

Do **not** write only jargon such as “21 of 38 candidate joins contain orphans” with no explanation of orphan.

| Status | Area | Why this status was used | Evidence | What the data engineer should review | Recommended action | Owner | Blocks next phase? |
|---|---|---|---|---|---|---|---|
| WARN | Relationships | We checked 38 possible table links. 21 of them have child rows that point to a parent id that is missing or blank (orphan rows). If we use hard inner joins later, those rows can disappear and totals will look wrong. Setup can continue. Careful join design is required before silver/gold. | `<proof file>` | Confirm what those keys mean in the source before building joined models. | Keep the warning; use left joins and report orphans; do not assume every child has a valid parent. | Data engineer | No for setup; yes for dependent joined models |
| WARN | Monetary units | One payment system shows amounts like normal money (example max about 4,241). Another shows much larger numbers (example max about 487,800). That may mean major vs minor currency units (for example riyal vs halala), but it is not proven. Setup can continue. Do not publish revenue metrics until units are confirmed. | `<proof file>` | Confirm currency and whether payment-service amounts are minor units. | Defer money KPIs until reconciled. | Data engineer | No for setup; yes for financial metrics |
| <WARN/FAIL/BLOCKED/SKIPPED> | <area> | <plain-language why: found + risk + what can continue + what must wait> | <proof/report path> | <human review question in plain words> | <approve/fix/defer/change scope> | <agent/data engineer> | <yes/no and for which phase> |

## Table Inclusion Filter

Use the skill rule in `references/table-inclusion-priority-filter.md`.

### Mandatory checklist

| # | Checklist item | Done? | Evidence |
|---|---|---|---|
| 1 | Keep fact/event tables on the main process | <yes/no> | <process name + fact tables> |
| 2 | Keep related dimensions/lookups for included facts | <yes/no> | <entity/lookup tables> |
| 3 | Exclude audit/log/platform/empty (unless user requested) | <yes/no> | <excluded groups + counts> |
| 4 | Every table has `inclusion_reason` in `discovery_raw.json` | <yes/no> | `discovery_raw.json.tables[]` |
| 5 | Ask user if process scope is unclear | <yes/no/n/a> | <question asked or why scope is clear> |

- First-pass business process: <process name>
- Total tables in schema: <count>
- Included (v1 / priority): <count>
- Deferred: <count>
- Excluded: <count>
- Filter rationale: <why these tables were kept or dropped>
- Inventory proof: `sql_proofs/001_source_table_inventory.sql`
- Priority / deep proof set: <paths such as `sql_proofs/010_priority_table_row_counts.sql`>
- User approval needed for scope? <yes/no and why>

| Inclusion status | Meaning |
|---|---|
| `included` / yes | First-pass process path; deep proofs required |
| `deferred` / defer | Relevant later; inventory only for now |
| `excluded` / no | Outside first-pass scope; inventory only |

## Source Inventory

| Table | Row count | Likely role | Included in first pass | Inclusion reason | Notes |
|---|---:|---|---|---|---|
| <table> | <row_count> | <entity/fact/link/reference/unknown> | <yes/no/defer> | <reason matching discovery_raw.json> | <notes> |

For large schemas, summarize excluded groups in one or more rows and keep the full per-table list in `discovery_raw.json`.

## Important Entities And Business Processes

- <entity or process with evidence>

## Key, Grain, And Relationship Findings

| Table | Likely grain | Candidate key | Key status | Relationship notes |
|---|---|---|---|---|
| <table> | <one row per ...> | <column(s)> | <PASS/WARN/FAIL/BLOCKED> | <notes> |

## Data Quality Signals

| Area | Finding | Evidence | Status | Build impact |
|---|---|---|---|---|
| Row counts | <finding> | <proof file> | <PASS/WARN/FAIL/BLOCKED> | <impact> |
| Keys | <finding> | <proof file> | <PASS/WARN/FAIL/BLOCKED> | <impact> |
| Relationships | <finding> | <proof file> | <PASS/WARN/FAIL/BLOCKED> | <impact> |
| Dates | <finding> | <proof file> | <PASS/WARN/FAIL/BLOCKED> | <impact> |
| Measures | <finding> | <proof file> | <PASS/WARN/FAIL/BLOCKED> | <impact> |
| Statuses/Categories | <finding> | <proof file> | <PASS/WARN/FAIL/BLOCKED> | <impact> |

## Privacy And Sensitive Data

- Sensitive fields observed: <fields or "None observed">
- Recommended default: <mask/exclude/hash/pass through bronze only/defer>
- Approval needed: <yes/no and why>

## Ambiguous Or Poorly Named Fields

| Table | Column | Observed values or pattern | Safe default | Approval needed |
|---|---|---|---|---|
| <table> | <column> | <pattern> | <keep raw in bronze; exclude from gold until defined> | <yes/no> |

## Candidate Metrics And Reporting Needs

| Candidate area | Evidence | Confidence | Status | Next action |
|---|---|---|---|---|
| <metric/reporting area> | <columns/statuses/measures/dates> | <high/medium/low/blocker> | <draft/defer/block> | <next action> |

## Diagrams

### Entity Relationship Diagram

```mermaid
erDiagram
    %% Replace with evidence-backed relationships only.
```

Mermaid verification: <PASS/WARN/NOT RUN and reason>

### Source Or Business Process Flow

```mermaid
flowchart LR
    %% Replace with evidence-backed flow only.
```

Mermaid verification: <PASS/WARN/NOT RUN and reason>

## Recommended Medallion Direction

| Layer area | Recommendation | Evidence | Not ready yet | Approval needed |
|---|---|---|---|---|
| Sources | <source YAML and source table direction> | <tables, columns, profile evidence> | <missing/unclear source items> | <source exclusions or naming approvals> |
| Bronze / staging | <staging direction> | <grain, columns, data quality evidence> | <ambiguous columns or sensitive fields> | <privacy/pass-through approvals> |
| Silver / intermediate | <intermediate direction> | <relationship/cardinality evidence> | <joins, mappings, or empty tables needing more profiling> | <business rule approvals> |
| Gold / marts | <facts, dimensions, marts, and metrics direction> | <business processes and measures found> | <metric definitions or privacy decisions not proven> | <metric, grain, and exposure approvals> |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `reports/agent/00_discovery/sql_proofs/<file>.sql` | <what it proves> | <PASS/WARN/FAIL/BLOCKED> | <captured result summary> |

## What Looks Right

- <validated or safe direction>

## What Is Not Ready Yet

- <risk, missing data, ambiguity, or required approval>

## Confidence

- Confident about: <validated source/project facts>
- Less confident about: <business meaning, privacy choices, metric dates, ambiguous fields, or anything not proven>

## Required User Decisions

- <decision before setup or later build phases>

## Inputs Used

- Domain: <domain>
- dbt profile name: <profile name without secrets>
- Adapter: <adapter>
- Database or catalog: <database/catalog/project>
- Source schema: <source schema>
- Source tables inspected: <tables>
