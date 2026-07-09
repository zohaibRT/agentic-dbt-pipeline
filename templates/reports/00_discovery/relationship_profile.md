# Relationship Profile

## Read First

This file documents which tables connect to which tables and which joins are proven vs uncertain.

Status meanings: see `reports/agent/00_discovery/README.md`.

## Template Use

Use this file as the fixed structure for `reports/agent/00_discovery/relationship_profile.md`.
Replace placeholder text with source-specific relationship evidence.

## Relationship Summary

- Status: <PASS / WARN / FAIL / BLOCKED>
- Credible relationships found: <count>
- Relationships needing user confirmation: <count>
- Relationships blocked: <count>

## Proven Or Credible Relationships

| Relationship | Evidence type | Parent key | Child key | Cardinality | Match status | Proof file |
|---|---|---|---|---|---|---|
| <parent> to <child> | <constraint/name/profile/user-approved> | <parent column> | <child column> | <one-to-many/one-to-one/many-to-many/unknown> | <PASS/WARN/FAIL/BLOCKED> | `<proof file>` |

## Uncertain Relationship Candidates

| Candidate relationship | Why it is uncertain | Modeling risk | Recommended action |
|---|---|---|---|
| <table> to <table> | <missing key/no match/ambiguous business meaning> | <risk> | <ask/defer/profile later> |

## Mermaid Entity Relationship Diagram

Only draw relationships that are proven, credible, or user-approved.
Put uncertain relationships in the table above instead of drawing them as confirmed edges.

```mermaid
erDiagram
    %% Replace with evidence-backed relationships only.
```

Mermaid verification: <PASS/WARN/NOT RUN and reason>

## Join Path Recommendations

- <recommended safe join path>

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `<proof file>` | <purpose> | <status> | <result> |
