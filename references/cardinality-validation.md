# Cardinality And Relationship Grain Validation

Use this during discovery, source profiling, layer validation, key performance indicator reconciliation, semantic layer validation, Power BI readiness, and final delivery.

## Core Rule

No key performance indicator is trusted until its grain and cardinality are proven.

Incorrect cardinality can cause row loss, row multiplication, duplicate dimension keys, invalid many-to-many relationships, and wrong Power BI totals.

## Required Output Files

Create or update these files when relationships, joins, final models, key performance indicators, or Power BI relationships are designed or validated:

```text
reports/agent/00_discovery/cardinality_report.md
reports/agent/00_discovery/relationship_profile.md
reports/agent/05_gold/join_safety_report.md
reports/agent/05_gold/grain_validation_report.md
```

Include relevant cardinality results in:

```text
reports/agent/09_analytics_insights/kpis/kpi_reconciliation_report.md
reports/agent/09_analytics_insights/kpis/kpi_lineage_proofs.md
reports/agent/09_analytics_insights/reporting_readiness_scorecard.md
reports/agent/10_presentation/powerbi_model_plan.md
```

## Discovery Checks

For every relevant table, detect and document:

- Candidate primary keys
- Candidate foreign keys
- Unique columns
- Duplicate key counts
- Null key counts
- Likely grain
- Likely parent-child relationships
- Likely bridge/link tables
- Likely history/status tables
- One-to-one relationships
- One-to-many relationships
- Many-to-one relationships
- Many-to-many risks
- Tables that should not be joined directly without aggregation

## Required Report Tables

`cardinality_report.md` must include:

| Relationship | Left Model | Right Model | Left Key | Right Key | Expected Cardinality | Observed Cardinality | Left Rows | Right Rows | Left Distinct Keys | Right Distinct Keys | Null Keys | Duplicate Keys | Status | Notes |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|

`relationship_profile.md` must include:

| Parent Candidate | Child Candidate | Parent Key | Child Key | Parent Unique | Child Nulls | Child Unmatched | Match Rate | Cardinality | Confidence | Recommended Action |
|---|---|---|---|---|---:|---:|---:|---|---|---|

`join_safety_report.md` must include:

| Join | Base Grain | Join Type | Expected Result | Actual Result | Row Multiplier | Row Loss | Safe | Reason | Fix |
|---|---|---|---|---|---:|---:|---|---|---|

`grain_validation_report.md` must include:

| Model | Expected Grain | Grain Key | Row Count | Distinct Grain Key Count | Duplicate Grain Keys | Null Grain Keys | Status | Notes |
|---|---|---|---:|---:|---:|---:|---|---|

## Join Validation

For every join in silver/intermediate and gold/marts:

1. Record base model row count before join.
2. Record joined model row count after join.
3. Record base grain distinct count before join.
4. Record base grain distinct count after join.
5. Calculate row multiplier: joined rows divided by base rows.
6. Calculate row loss: base distinct keys minus joined distinct keys.
7. If the model should remain one row per base entity, row multiplier must be `1.0`.
8. If row multiplication is intentional, document why and define the new grain.
9. If row loss is intentional, document the business filter.
10. If row multiplication or row loss is unexplained, mark validation as `FAIL`.

## Key Performance Indicator Integration

For every key performance indicator proof, include:

- Row count
- Distinct business key count
- Duplicate key count
- Null key count
- Row multiplier compared to previous layer
- Row loss compared to previous layer
- Relationship/cardinality assumption
- Whether the metric uses row count, distinct count, sum, average, ratio, or DAX
- Whether the measure is safe at the current grain

If key performance indicator variance exists, check cardinality before blaming DAX.

## Power BI Readiness

Before creating Power BI relationships:

- Every one-side relationship key must be unique.
- Every one-side relationship key must be not null.
- Many-to-many relationships must not be created by default.
- If many-to-many is required, require a tested bridge table.
- Composite business keys must use tested dbt surrogate keys.
- Do not create relationship keys in Power BI M by default.
- If a relationship key is missing, block Power BI delivery and add the issue to `reports/agent/09_analytics_insights/insight_backlog.md`.

## DAX Safety

Before generating DAX:

- Count metrics must state whether they use row count or distinct business key count.
- If a fact table can contain multiple rows per business entity, do not use `COUNTROWS` for entity counts.
- Use `DISTINCTCOUNT` only when the business key is validated and stable.
- Ratio metrics must validate numerator and denominator cardinality separately.
- Measures must not hide row multiplication issues.
- DAX must map back to the approved key performance indicator definition and cardinality proof.

## Hard Rules

- Do not trust joins without cardinality proof.
- Do not trust key performance indicators without grain proof.
- Do not trust Power BI relationships unless the one-side key is unique and not null.
- Do not create many-to-many relationships unless explicitly approved and backed by a tested bridge table.
- Do not use `COUNTROWS` for entity counts when the table grain is not one row per entity.
- Do not allow unexplained row multiplication or row loss to pass validation.
- If cardinality changes between layers, identify the first layer where it changed.
