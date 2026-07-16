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
| Domain | domain_c_asset_events | fixture | TEST FIXTURE ONLY |
| Business description | Asset event monitoring | fixture | illustrative |
| dbt profile name | fixture_analytics | profiles.yml | no secrets |
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

## Accepted Warnings

- Accepted warning: validate_kpi_proofs:w0:ee46cc6d76e7
- Accepted warning: check_report_business_readability:w0:a8029ff012c7
