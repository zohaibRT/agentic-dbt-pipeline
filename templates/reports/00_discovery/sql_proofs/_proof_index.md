# SQL Proof Index

Folder: `reports/agent/00_discovery/sql_proofs/`

Purpose: Source discovery proofs for table inventory, row counts, candidate keys, business-state counts, date coverage, numeric summaries, relationship checks, cardinality checks, and data quality checks.

## Status Vocabulary

| Status | Meaning |
|---|---|
| PASS | Evidence supports the claim |
| WARN | Usable with a documented limitation |
| FAIL | Claim is wrong or unsafe |
| BLOCKED | Waiting on user input or approval |
| SKIPPED | Intentionally not run |

## Large Schema Rule

If the schema has hundreds or thousands of tables:

1. Use `001_source_table_inventory.sql` for all table names and row counts.
2. Put every table in `discovery_raw.json` with at least `table_name` and `row_count`.
3. Create `010+` row-count proofs only for included or priority tables.
4. Mark other tables `deferred` or `excluded` with reasons in `discovery_report.md`.

## How To Use

Each proof file is a runnable SQL query with captured aggregate results in the comment header.
Use these files to verify that the discovery report is based on source evidence, not guesses.

## Proof Naming Standard

| Sequence | Proof type | Filename pattern |
|---:|---|---|
| 001 | Source table inventory | `001_source_table_inventory.sql` |
| 010 | Per-table row count | `010_<source_table>_row_count.sql` |
| 020 | Candidate key check | `020_<source_table>_<key>_key_check.sql` |
| 030 | Status/category distribution | `030_<source_table>_<column>_distribution.sql` |
| 035 | Active/open/closed count | `035_<source_table>_<business_state>_count.sql` |
| 040 | Date coverage | `040_<source_table>_<date_column>_date_coverage.sql` |
| 050 | Amount/quantity summary | `050_<source_table>_<measure>_summary.sql` |
| 060 | Relationship check | `060_<child_table>_<parent_table>_relationship_check.sql` |
| 070 | Bridge/cardinality check | `070_<table>_bridge_or_cardinality_check.sql` |
| 080 | Data quality check | `080_<source_table>_data_quality_check.sql` |

## Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<file>.sql` | <what it proves> | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <captured result summary> |
