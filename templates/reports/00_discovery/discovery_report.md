# Discovery Report

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

## Source Inventory

| Table | Row count | Likely role | Included in first pass | Notes |
|---|---:|---|---|---|
| <table> | <row_count> | <entity/fact/link/reference/unknown> | <yes/no/defer> | <notes> |

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
