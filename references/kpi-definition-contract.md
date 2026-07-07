# Key Performance Indicator Definition Contract

Use this before implementing a key performance indicator in gold/marts, semantic layer, analytics insight reporting, Power BI, Matplotlib, or any other presentation layer.

## Core rule

A key performance indicator is not verified until its business definition, data source, grain, filters, time basis, expected result, actual result, and proof file are documented.

Do not promote a measure or metric into a key performance indicator when the business meaning is guessed.

## Canonical generated file

Write approved, proposed, deferred, and blocked key performance indicator contracts to:

```text
reports/agent/KPI_DEFINITION_CONTRACTS.md
```

Analytics-specific catalogs may also reference the same items from:

```text
reports/agent/09_analytics_insights/kpis/kpi_catalog.md
reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md
```

## Required contract table

```markdown
# Key Performance Indicator Definition Contracts

| KPI ID | Key Performance Indicator | Business Meaning | Formula | Grain | Date Basis | Included Rows | Excluded Rows | Source Tables / Models | Built In | Verified By SQL Proof | Expected Result | Actual Result | Difference / Tolerance | Approval Status | Verification Status | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|
| KPI-001 | <name> | <meaning> | <formula> | <grain> | <date column> | <statuses/filters> | <statuses/filters> | <sources/models> | <model/metric/report path> | <sql_proof path> | <value> | <value> | <difference> | APPROVED / PROPOSED / DEFERRED / BLOCKED | PASS / WARN / FAIL / BLOCKED | <reason> |
```

## Required approval questions

Before implementation, resolve or document:

1. What exactly does this key performance indicator mean?
2. Which rows are included?
3. Which rows are excluded?
4. Which date or timestamp controls the metric?
5. What is the calculation grain?
6. How are cancelled, failed, denied, inactive, pending, refunded, deleted, or draft records handled?
7. Which amount type is used: gross, net, paid, billed, collected, cost, margin, or proxy?
8. Which dimensions are safe for breakdown?
9. What tolerance is acceptable for reconciliation?
10. Is the definition approved, proposed, deferred, or blocked?

Ask the user only for unresolved business decisions. Do not ask for items the data can prove directly.

## Stop conditions

Stop before semantic layer, analytics insight reporting, presentation layer, or final delivery when:

- Formula, date basis, grain, numerator, denominator, or filters are ambiguous.
- The business definition contradicts the source data.
- The expected and actual result do not reconcile.
- The key performance indicator depends on unsafe joins or unproven cardinality.
- The key performance indicator exposes sensitive fields without approval.
