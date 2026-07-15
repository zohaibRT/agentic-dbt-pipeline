# Context Tree (TEST FIXTURE ONLY)

## Active Run

| Field | Value |
|---|---|
| Current checkpoint | Final |
| Current status | PASS |
| Last updated | fixture build |
| Source lock status | locked |

## Input Context

| Input | Value | Source | Notes |
|---|---|---|---|
| Domain | domain_a_transactional | fixture | TEST FIXTURE ONLY |
| Business description | Transactional lifecycle | fixture | illustrative |
| dbt profile name | fixture_duckdb | profiles.yml | no secrets |
| Adapter | duckdb | profiles.yml | local duckdb |
| Database or catalog | fixture | profiles.yml | file-backed |
| Source schema | main | seeds | synthetic |

## Decisions And Rules

| Decision / Rule | Status | Source | Applies To | Notes |
|---|---|---|---|---|
| Use synthetic seeds | approved | fixture | all layers | Gate regression only |

## Open Questions

| Question | Why it matters | Blocking phase | Current status |
|---|---|---|---|
| None | n/a | n/a | answered |
