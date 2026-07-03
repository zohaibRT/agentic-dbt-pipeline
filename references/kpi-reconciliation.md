# Key Performance Indicator Reconciliation

Use this whenever a key performance indicator is discovered, implemented, promoted to semantic metrics, used in Power BI, or reported in final delivery.

## Core Rule

No key performance indicator is trusted until its value is reconciled from source to final consumption.

Reconcile each approved or high-confidence key performance indicator across every available layer:

```text
Source -> Bronze / staging -> Silver / intermediate -> Gold / marts -> Semantic layer -> Power BI / DAX
```

If a value changes, identify the first layer where the unexpected variance appears. Do not guess whether the issue is source data, a join, a filter, a semantic metric, or DAX.

## Required Output Files

Create or update these files when key performance indicators are implemented or handed off:

```text
reports/agent/09_analytics_insights/kpis/kpi_reconciliation_report.md
reports/agent/09_analytics_insights/kpis/kpi_lineage_proofs.md
reports/agent/09_analytics_insights/kpis/kpi_variance_report.md
reports/agent/09_analytics_insights/kpis/sql_proofs/
```

Inside `reports/agent/09_analytics_insights/kpis/sql_proofs/`, write one proof file per key performance indicator and layer where applicable:

```text
<safe_kpi_name>_source.sql
<safe_kpi_name>_bronze.sql
<safe_kpi_name>_silver.sql
<safe_kpi_name>_gold.sql
<safe_kpi_name>_semantic.sql
<safe_kpi_name>_powerbi_dax.md
```

Use adapter-appropriate SQL and do not include sensitive row-level samples.

## Required Reconciliation Fields

For every key performance indicator, record:

- Key performance indicator name
- Business definition
- Formula
- Source model or table
- Grain
- Counting key or amount field
- Filters
- Time field
- Allowed dimensions
- Source SQL proof and result
- Bronze SQL proof and result
- Silver SQL proof and result
- Gold SQL proof and result
- Semantic query or metric proof and result
- Power BI DAX proof and result, when applicable
- Expected result per layer
- Variance and variance percentage
- Cardinality/grain assumption
- PASS, WARN, FAIL, or BLOCKED status
- First failing layer
- Explanation of where the value changed
- Recommended debugging action

## Report Tables

`kpi_reconciliation_report.md` must include:

| Key Performance Indicator | Layer | Model/Table | SQL/DAX Proof File | Result | Expected Result | Variance | Variance Percentage | Status | Notes |
|---|---|---|---|---:|---:|---:|---:|---|---|

`kpi_lineage_proofs.md` must include:

| Key Performance Indicator | Source Definition | Source To Bronze | Bronze To Silver | Silver To Gold | Gold To Semantic | Semantic To Power BI | First Failing Layer | Root Cause Hypothesis |
|---|---|---|---|---|---|---|---|---|

`kpi_variance_report.md` must include:

| Key Performance Indicator | First Layer Result | Final Layer Result | Difference | Difference Percentage | First Failing Layer | Likely Cause | Required Fix |
|---|---:|---:|---:|---:|---|---|---|

## Phase Integration

| Phase | Required proof |
|---|---|
| Discovery | Candidate definition, expected grain, likely proof SQL, and open business questions |
| Bronze / staging | Source versus bronze row and metric preservation |
| Silver / intermediate | Bronze versus silver value, row loss, row multiplication, and component logic |
| Gold / marts | Silver versus gold value, filters, aggregation, and final fact/dimension grain |
| Semantic layer | Gold SQL versus semantic metric result |
| Presentation layer | Semantic or gold result versus Power BI DAX and visual result |
| Final delivery | Full source-to-final reconciliation status |

The agent must not say a key performance indicator is validated unless the proof exists and the result is recorded.

## Variance Rules

- Exact count metrics usually require zero variance unless a documented business filter applies.
- Financial metrics may allow small rounding variance only when documented.
- Ratio, rate, percentage, and average metrics must compare numerator, denominator, and final result.
- Trend metrics must compare results by period, not only grand total.
- Filtered metrics must show equivalent filter logic at every layer.
- If rows are intentionally filtered, document the business reason.
- If rows are lost unintentionally, block final delivery until reviewed.

## Stop Conditions

Stop before semantic layer, presentation layer, final delivery, or commit when:

- Approved key performance indicators do not have lineage proof.
- Source-to-final results are not reconciled.
- Variance is unexplained.
- The first failing layer is not identified.
- Semantic metric result differs from gold SQL.
- Power BI DAX differs from the semantic metric or gold SQL.
- Gold differs unexpectedly from silver.
- Sensitive filters or row exclusions are undocumented.

When stopped, write the root cause, first failing layer, proof file paths, safest fix, and retest command in the active phase report and `reports/agent/PIPELINE_STATUS.md`.
