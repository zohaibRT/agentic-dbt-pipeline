# Project Requirements From Discovery

## Template Use

Use this file as the fixed structure for `reports/agent/00_discovery/requirements.md`.
Replace placeholder text with source-specific findings from read-only discovery.
Do not remove sections; write `None`, `Not observed`, or `Blocked` when a section has no evidence yet.

## Inputs Used

- Domain: <domain or domain label provided by user>
- Business description: <optional business description or "Not provided">
- dbt profile name: <profile name without secrets>
- Adapter: <adapter>
- Database or catalog: <database/catalog/project>
- Source schema: <source schema>
- Source tables inspected: <tables>

## Source-Derived Requirements

| Area | Requirement inferred | Evidence | Confidence | Build impact |
|---|---|---|---|---|
| Source inclusion | <include/exclude direction> | <tables, row counts, relationships> | <high/medium/low/blocker> | <source YAML, staging, tests> |
| Business process | <process supported by data> | <entity flow evidence> | <high/medium/low/blocker> | <facts/intermediate direction> |
| Data quality | <tests or checks needed> | <keys, statuses, dates, nulls> | <high/medium/low/blocker> | <dbt tests and validation queries> |
| Privacy | <safe default> | <sensitive fields found> | <high/medium/low/blocker> | <gold/marts exposure rules> |
| Metrics | <candidate metric area> | <amount/status/date columns> | <high/medium/low/blocker> | <semantic layer/gold marts> |
| Reporting | <likely reporting need> | <final consumers implied by source> | <high/medium/low/blocker> | <presentation layer options> |

## Recommended Defaults

- <safe professional default derived from evidence>

## Open Questions For The Data Engineer

- <question that affects business meaning, privacy, metrics, grain, mappings, joins, or reporting>

## Deferred Or Blocked Scope

- <scope that should not be built until requirements are confirmed>

## User Requirements Captured

- <requirements already provided by the user, or "None yet">

## Approval Impact

- Discovery approval permits: source confirmation and automatic project setup/configuration only.
- Discovery approval does not permit: source YAML generation, bronze/staging, silver/intermediate, gold/marts, semantic layer, presentation layer, commits, pushes, source switching, or warehouse model builds.
