# Requirements Traceability Matrix (TEST FIXTURE ONLY)

Dimensions in scope: dim_providers, dim_locations, dim_statuses

| Requirement ID | Requirement / Rule | Source | Business Area | Layer Impact | Implementation Artifact | Verification Artifact | Presentation / Output Artifact | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| DISC-001 | Model Encounter lifecycle from seeds | reports/agent/00_discovery/requirements.md | Encounter lifecycle | bronze | models/staging/stg_encounters.sql | reports/agent/03_bronze/sql_proofs/010_row_count.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |
| DISC-002 | Enrich events with status | reports/agent/00_discovery/requirements.md | Encounter lifecycle | silver | models/intermediate/int_encounters_enriched.sql | reports/agent/04_silver/sql_proofs/010_join_check.sql | n/a | PASS | Fixture |
| DISC-003 | Publish gold star schema | reports/agent/00_discovery/requirements.md | Encounter lifecycle | gold | models/gold/fct_encounters.sql | reports/agent/05_gold/sql_proofs/010_grain_check.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |
| DISC-004 | Volume KPI with SQL proof | reports/agent/KPI_DEFINITION_CONTRACTS.md | analytics | presentation | reports/agent/KPI_DEFINITION_CONTRACTS.md | reports/agent/sql_proofs/010_volume.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |
| DISC-005 | Completion rate KPI | reports/agent/KPI_DEFINITION_CONTRACTS.md | analytics | presentation | reports/agent/KPI_DEFINITION_CONTRACTS.md | reports/agent/sql_proofs/020_rate.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |
