# Cardinality Report

## Template Use

Use this file as the fixed structure for `reports/agent/00_discovery/cardinality_report.md`.
Replace placeholder text with source-specific relationship and join-safety evidence.

## Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Main join path reviewed: <path or "Not enough evidence">
- Many-to-many risks found: <yes/no>
- Bridge tables suspected: <tables or "None observed">

## Relationship Cardinality Matrix

| Parent table | Child table | Join columns | Parent grain | Child grain | Match rate | Orphan count | Row multiplication risk | Status | Proof file |
|---|---|---|---|---|---:|---:|---|---|---|
| <parent> | <child> | <parent_key = child_key> | <grain> | <grain> | <percent> | <count> | <low/medium/high/blocker> | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |

## Bridge Or Link Table Candidates

| Table | Why it looks like a bridge | Grain evidence | Safe modeling direction | Status |
|---|---|---|---|---|
| <table> | <evidence> | <proof file/result> | <aggregate first / build bridge / defer> | <PASS/WARN/FAIL/BLOCKED> |

## Unsafe Join Warnings

- <warning or "None observed">

## Recommended Modeling Impact

- Sources: <impact>
- Bronze / staging: <impact>
- Silver / intermediate: <impact>
- Gold / marts: <impact>

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |
