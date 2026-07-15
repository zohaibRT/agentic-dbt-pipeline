# Model Classification (TEST FIXTURE)

| Model | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stg_statuses | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| stg_providers | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| stg_locations | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| stg_encounters | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| stg_activities | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| int_encounters_enriched | intermediate | enriched business logic layer | logic | logic_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| int_activities_enriched | intermediate | enriched business logic layer | logic | logic_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| fct_encounters | fact/event | primary measurable event | event | event_id | event_date | count, amount | dim_providers, dim_locations, dim_statuses | not_null | PASS | table | HIGH | PASS |
| activity_events | fact/event | primary measurable event | event | event_id | event_date | count, amount | dim_providers, dim_locations, dim_statuses | not_null | PASS | table | HIGH | PASS |
| dim_providers | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |
| dim_locations | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |
| dim_statuses | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |
