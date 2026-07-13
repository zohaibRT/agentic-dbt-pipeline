# Project Requirements From Discovery

## Read First

- Status meanings: see `reports/agent/00_discovery/README.md`.
- `WARN` means a documented limitation exists; it is not the same as `FAIL`.

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
| Source inclusion | <include/exclude/defer direction using table-inclusion-priority-filter> | <inventory proof, inclusion counts, process name> | <high/medium/low/blocker> | <source YAML, staging, tests> |
| First-pass process | <named business process for v1 scope> | <entity/relationship evidence> | <high/medium/low/blocker> | <facts/intermediate direction> |
| Business process | <process supported by data> | <entity flow evidence> | <high/medium/low/blocker> | <facts/intermediate direction> |
| Data quality | <tests or checks needed> | <keys, statuses, dates, nulls> | <high/medium/low/blocker> | <dbt tests and validation queries> |
| Privacy | <safe default> | <sensitive fields found> | <high/medium/low/blocker> | <gold/marts exposure rules> |
| Metrics | <candidate metric area> | <amount/status/date columns> | <high/medium/low/blocker> | <semantic layer/gold marts> |
| Reporting | <likely reporting need> | <final consumers implied by source> | <high/medium/low/blocker> | <presentation layer options> |

## Table Inclusion Scope

Mandatory checklist (from `references/table-inclusion-priority-filter.md`):

1. Keep fact/event tables on the main process: <yes/no + process name>
2. Keep related dimensions/lookups: <yes/no + key tables>
3. Exclude audit/log/platform/empty unless requested: <yes/no + excluded groups>
4. Every table has `inclusion_reason`: <yes/no>
5. Ask user if process scope is unclear: <asked/not needed + why>

- First-pass business process: <process name>
- Total tables: <count>
- Included: <count and key table names>
- Deferred: <count and examples>
- Excluded: <count and reason groups such as platform/audit/empty>
- Filter evidence: `discovery_raw.json`, `001_source_table_inventory.sql`, `discovery_report.md` Table Inclusion Filter section
- Deep proofs limited to included/priority tables: <yes/no>

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
