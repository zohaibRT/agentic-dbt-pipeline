# Layer Verification Ledger (TEST FIXTURE ONLY)

| Phase | Layer | Model / Artifact | Expected Grain | Row Count | Upstream Comparison | Key / Grain Proof | Relationship Proof | Measure / KPI Proof | Privacy Check | Proof Files | dbt Command Result | Overall Status | Notes |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| 03_bronze | bronze/staging | stg_asset_events | source row | 5 | match | PASS | PASS | PASS | PASS | reports/agent/03_bronze/sql_proofs/010_row_count.sql | PASS | PASS | Fixture |
| 04_silver | silver/intermediate | int_asset_events_enriched | event | 5 | match | PASS | PASS | PASS | PASS | reports/agent/04_silver/sql_proofs/010_join_check.sql | PASS | PASS | Fixture |
| 05_gold | gold/marts | fct_asset_events | event | 5 | match | PASS | PASS | PASS | PASS | reports/agent/05_gold/sql_proofs/010_grain_check.sql | PASS | PASS | Fixture |
| 05_gold | gold/marts | dim_assets | entity | 5 | match | PASS | PASS | n/a | PASS | reports/agent/05_gold/sql_proofs/010_grain_check.sql | PASS | PASS | Fixture |
| 05_gold | gold/marts | dim_statuses | entity | 5 | match | PASS | PASS | n/a | PASS | reports/agent/05_gold/sql_proofs/010_grain_check.sql | PASS | PASS | Fixture |
