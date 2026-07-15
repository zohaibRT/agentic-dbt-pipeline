# Gold / Marts Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Dimensions built: 3
- Facts built: 1

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Fact grain uniqueness | PASS | `sql_proofs/010_grain_check.sql` |
| Dimension key uniqueness | PASS | `sql_proofs/010_grain_check.sql` |
| Relationship integrity | PASS | `sql_proofs/010_grain_check.sql` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/010_grain_check.sql` | Grain check | PASS | unique keys |

## Models Built Or Changed

| Model | Type | Grain | Materialization | Row count | Status |
|---|---|---|---|---:|---|
| fct_encounters | fact | event | table | 5 | PASS |
| dim_providers | dimension | entity | table | 5 | PASS |
| dim_locations | dimension | entity | table | 5 | PASS |
| dim_statuses | dimension | entity | table | 5 | PASS |
