# Model Classification (TEST FIXTURE — unique_id stamped after dbt parse)

| Unique ID | Model | Package | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Human Approval Status | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model.domain_d_case_activity.dim_organizations | dim_organizations | domain_d_case_activity | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.dim_people | dim_people | domain_d_case_activity | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.dim_statuses | dim_statuses | domain_d_case_activity | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.fct_case_activities | fct_case_activities | domain_d_case_activity | event_fact | primary measurable event | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.int_case_activities_enriched | int_case_activities_enriched | domain_d_case_activity | intermediate | enriched business logic layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.stg_case_activities | stg_case_activities | domain_d_case_activity | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.stg_organizations | stg_organizations | domain_d_case_activity | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.stg_people | stg_people | domain_d_case_activity | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_d_case_activity.stg_statuses | stg_statuses | domain_d_case_activity | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| source.domain_d_case_activity.raw.raw_case_activities | raw_case_activities | domain_d_case_activity | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_d_case_activity.raw.raw_organizations | raw_organizations | domain_d_case_activity | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_d_case_activity.raw.raw_people | raw_people | domain_d_case_activity | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_d_case_activity.raw.raw_statuses | raw_statuses | domain_d_case_activity | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_d_case_activity.raw_case_activities | raw_case_activities | domain_d_case_activity | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_d_case_activity.raw_organizations | raw_organizations | domain_d_case_activity | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_d_case_activity.raw_people | raw_people | domain_d_case_activity | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_d_case_activity.raw_statuses | raw_statuses | domain_d_case_activity | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| exposure.domain_d_case_activity.browser_report | browser_report | domain_d_case_activity | exposure | production presentation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
