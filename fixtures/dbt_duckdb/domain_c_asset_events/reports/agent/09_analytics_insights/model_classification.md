# Model Classification (TEST FIXTURE — unique_id stamped after dbt parse)

| Unique ID | Model | Package | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Human Approval Status | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| model.domain_c_asset_events.dim_assets | dim_assets | domain_c_asset_events | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_c_asset_events.dim_statuses | dim_statuses | domain_c_asset_events | dimension | descriptive entity | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_c_asset_events.fct_asset_events | fct_asset_events | domain_c_asset_events | event_fact | primary measurable event | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_c_asset_events.int_asset_events_enriched | int_asset_events_enriched | domain_c_asset_events | intermediate | enriched business logic layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_c_asset_events.stg_asset_events | stg_asset_events | domain_c_asset_events | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_c_asset_events.stg_assets | stg_assets | domain_c_asset_events | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| model.domain_c_asset_events.stg_statuses | stg_statuses | domain_c_asset_events | staging | cleaned source-aligned layer | event | event_id | event_date | count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |
| source.domain_c_asset_events.raw.raw_asset_events | raw_asset_events | domain_c_asset_events | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_c_asset_events.raw.raw_assets | raw_assets | domain_c_asset_events | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| source.domain_c_asset_events.raw.raw_statuses | raw_statuses | domain_c_asset_events | source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_c_asset_events.raw_asset_events | raw_asset_events | domain_c_asset_events | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_c_asset_events.raw_assets | raw_assets | domain_c_asset_events | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| seed.domain_c_asset_events.raw_statuses | raw_statuses | domain_c_asset_events | seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
| exposure.domain_c_asset_events.browser_report | browser_report | domain_c_asset_events | exposure | production presentation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |
