# Model Classification (TEST FIXTURE — unique_id stamped after dbt parse)

| Unique ID | Model | Package | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Human Approval Status | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model.domain_b_encounter.activity_events | activity_events | domain_b_encounter | event_fact | primary measurable event | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.dim_locations | dim_locations | domain_b_encounter | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.dim_providers | dim_providers | domain_b_encounter | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.dim_statuses | dim_statuses | domain_b_encounter | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.fct_encounters | fct_encounters | domain_b_encounter | event_fact | primary measurable event | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.int_activities_enriched | int_activities_enriched | domain_b_encounter | intermediate | enriched business logic layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.int_encounters_enriched | int_encounters_enriched | domain_b_encounter | intermediate | enriched business logic layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.stg_activities | stg_activities | domain_b_encounter | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.stg_encounters | stg_encounters | domain_b_encounter | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.stg_locations | stg_locations | domain_b_encounter | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.stg_providers | stg_providers | domain_b_encounter | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_b_encounter.stg_statuses | stg_statuses | domain_b_encounter | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| source.domain_b_encounter.raw.raw_activities | raw_activities | domain_b_encounter | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_b_encounter.raw.raw_encounters | raw_encounters | domain_b_encounter | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_b_encounter.raw.raw_locations | raw_locations | domain_b_encounter | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_b_encounter.raw.raw_providers | raw_providers | domain_b_encounter | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_b_encounter.raw.raw_statuses | raw_statuses | domain_b_encounter | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_b_encounter.raw_activities | raw_activities | domain_b_encounter | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_b_encounter.raw_encounters | raw_encounters | domain_b_encounter | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_b_encounter.raw_locations | raw_locations | domain_b_encounter | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_b_encounter.raw_providers | raw_providers | domain_b_encounter | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_b_encounter.raw_statuses | raw_statuses | domain_b_encounter | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| snapshot.domain_b_encounter.activity_events_scd | activity_events_scd | domain_b_encounter | snapshot | SCD snapshot resource | entity | id | updated_at | n/a | n/a | n/a | n/a | table | HIGH | APPROVED | PASS |
| exposure.domain_b_encounter.browser_report | browser_report | domain_b_encounter | exposure | production presentation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
