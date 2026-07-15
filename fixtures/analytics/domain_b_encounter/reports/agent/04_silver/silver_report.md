# Silver / Intermediate Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Models built: 1

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Row loss check | PASS | `sql_proofs/010_join_check.sql` |
| Relationship integrity | PASS | `sql_proofs/010_join_check.sql` |
| Mapping coverage | PASS | `sql_proofs/010_join_check.sql` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/010_join_check.sql` | Join safety | PASS | 5 rows |

## What Was Built Or Changed

| Model | Purpose | Grain | Materialization | Row count | Status |
|---|---|---|---|---:|---|
| int_encounters_enriched | enrichment | event | view | 5 | PASS |
