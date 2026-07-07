# Metric Verification Checklist

Use this with [metric-verification.md](metric-verification.md), [kpi-reconciliation.md](kpi-reconciliation.md), and [kpi-definition-contract.md](kpi-definition-contract.md).

## Core rule

Every measure, metric, and key performance indicator must be reproducible from source or upstream models and reconciled to the final model, semantic layer, and presentation layer when those layers exist.

## Canonical generated file

Write the cross-project matrix to:

```text
reports/agent/METRIC_VERIFICATION_MATRIX.md
```

## Required matrix

```markdown
# Metric Verification Matrix

| Metric ID | Metric / Measure / KPI | Type | Definition Approved | Built In | Source Proof | Mart Proof | Semantic Proof | Presentation Proof | Expected Result | Actual Result | Difference / Tolerance | Status | Notes |
|---|---|---|---|---|---|---|---|---|---:|---:|---|---|---|
| MET-001 | <name> | measure / metric / key performance indicator | YES / NO / N/A | <path> | <sql_proof> | <sql_proof> | <sql_proof or N/A> | <proof or N/A> | <value> | <value> | <difference> | PASS / WARN / FAIL / BLOCKED | <reason> |
```

## Five required checks

| Check | Required proof | Why it matters |
|---|---|---|
| Definition approval | Contract row with approved or documented status | Correct SQL cannot fix wrong business meaning |
| Direct source SQL proof | Independent aggregate from source or earliest safe upstream layer | Proves the transformation did not change the value incorrectly |
| Reconciliation by dimensions | Compare totals by time, status, and safe dimensions | Grand totals can match accidentally |
| Golden test cases when feasible | Small known examples for edge cases | Proves business logic for refunds, cancellations, failures, and status handling |
| Join multiplication check | Before/after row counts, distinct keys, duplicate keys, and amount movement | Most wrong analytics numbers come from grain or join mistakes |

## Required proof patterns

For every important metric, create one or more SQL proof files that show:

```text
source result
upstream or silver result when applicable
gold or mart result
semantic result when applicable
presentation result when applicable
difference
status
```

For rates, ratios, averages, percentages, and success/failure metrics, prove numerator and denominator separately.

For amount metrics, prove amount type, status filters, negative/refund handling, and currency or unit.

For count metrics, prove the counting key and duplicate behavior.

## Fail examples

Mark verification `FAIL` when:

- A denominator equals the numerator but should include failed, cancelled, denied, inactive, or other companion states.
- A join multiplies measure values.
- A Power BI, Matplotlib, or other presentation measure uses different filters from the dbt metric.
- A semantic metric counts raw rows when the approved definition requires a reportable flag.
- The source proof and mart proof differ beyond the documented tolerance.
- The metric relies on an unapproved guess.
