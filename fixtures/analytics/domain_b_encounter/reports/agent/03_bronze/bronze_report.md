# Bronze / Staging Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Models built: 1

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Source-to-bronze row count | PASS | `sql_proofs/010_row_count.sql` |
| Primary key check | PASS | `sql_proofs/010_row_count.sql` |
| Date coverage | PASS | `sql_proofs/010_row_count.sql` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/010_row_count.sql` | Row presence | PASS | 5 rows |

## What Was Built Or Changed

| Model | Source table | Materialization | Row count | Status | Notes |
|---|---|---|---:|---|---|
| stg_encounters | seed | view | 5 | PASS | Fixture |
