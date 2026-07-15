# Model Classification (TEST FIXTURE)

| Model | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| stg_statuses | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| stg_people | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| stg_organizations | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| stg_case_activities | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| int_case_activities_enriched | intermediate | enriched business logic layer | logic | logic_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |
| fct_case_activities | fact/event | primary measurable event | event | event_id | event_date | count, amount | dim_people, dim_organizations, dim_statuses | not_null | PASS | table | HIGH | PASS |
| dim_people | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |
| dim_organizations | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |
| dim_statuses | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |
