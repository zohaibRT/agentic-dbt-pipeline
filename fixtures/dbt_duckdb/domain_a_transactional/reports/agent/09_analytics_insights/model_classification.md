# Model Classification (TEST FIXTURE — unique_id stamped after dbt parse)

| Unique ID | Model | Package | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Human Approval Status | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model.domain_a_transactional.dim_catalog_items | dim_catalog_items | domain_a_transactional | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.dim_entities | dim_entities | domain_a_transactional | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.dim_statuses | dim_statuses | domain_a_transactional | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.fct_events | fct_events | domain_a_transactional | event_fact | primary measurable event | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.int_events_enriched | int_events_enriched | domain_a_transactional | intermediate | enriched business logic layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.stg_catalog_items | stg_catalog_items | domain_a_transactional | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.stg_entities | stg_entities | domain_a_transactional | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.stg_events | stg_events | domain_a_transactional | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_a_transactional.stg_statuses | stg_statuses | domain_a_transactional | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| source.domain_a_transactional.raw.raw_catalog_items | raw_catalog_items | domain_a_transactional | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_a_transactional.raw.raw_entities | raw_entities | domain_a_transactional | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_a_transactional.raw.raw_events | raw_events | domain_a_transactional | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_a_transactional.raw.raw_statuses | raw_statuses | domain_a_transactional | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_a_transactional.raw_catalog_items | raw_catalog_items | domain_a_transactional | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_a_transactional.raw_entities | raw_entities | domain_a_transactional | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_a_transactional.raw_events | raw_events | domain_a_transactional | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_a_transactional.raw_statuses | raw_statuses | domain_a_transactional | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| exposure.domain_a_transactional.browser_report | browser_report | domain_a_transactional | exposure | production presentation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
