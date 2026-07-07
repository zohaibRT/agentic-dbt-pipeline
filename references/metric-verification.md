# Metric Verification

Use this before gold/marts, semantic layer, analytics insight reporting, presentation layer, Power BI artifacts, or final delivery complete. Also read [kpi-definition-contract.md](kpi-definition-contract.md), [metric-verification-checklist.md](metric-verification-checklist.md), [kpi-reconciliation.md](kpi-reconciliation.md), and [cardinality-validation.md](cardinality-validation.md).

## Core rule

Every implemented key performance indicator must be reconciled from its business definition to the actual built data. A dbt build, semantic parse, or Power BI file validation is not enough.

No key performance indicator is trusted until its value, grain, and cardinality are proven from source to final consumption.

For each key performance indicator, verify:

1. Business definition: numerator, denominator, filters, time field, grain, and caveats are documented.
2. Discovery evidence: the candidate appears in `reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md` with source model, grain, archetype, confidence, caveats, and approval status.
3. Cardinality evidence: row counts, distinct business keys, duplicate keys, null keys, row loss, and row multiplication are understood for the metric grain.
4. Source evidence: the source or upstream layer contains the records/flags/amounts required by the definition.
5. Transformation lineage: silver/intermediate logic creates the required flags/measures correctly.
6. Gold/marts logic: final facts or marts combine numerator, denominator, filters, and flags exactly as defined.
7. Semantic logic: semantic metrics or measures reference the approved gold/mart columns and use safe denominators.
8. Presentation logic: Power BI/DAX/report measures match the semantic or gold definition.
9. Reconciliation: SQL expected values equal semantic/presentation actual values, or differences are explained.

Do not continue to analytics insight reporting or presentation delivery when a metric denominator, numerator, filter, time field, or status inclusion is wrong, incomplete, or not reconciled.

## Required checks

For every rate, ratio, percentage, average, and status-based metric, run explicit checks for:

| Check | Required evidence |
|---|---|
| Numerator membership | Count or sum of rows included in the numerator |
| Denominator membership | Count or sum of rows included in the denominator |
| Excluded rows | Count of rows excluded and why |
| Component reconciliation | Numerator plus known companion states equals denominator when the business definition requires it |
| Gold column lineage | Gold numerator/denominator columns match upstream silver/intermediate flags or measures |
| Semantic reconciliation | Semantic metric result matches gold SQL result |
| Presentation reconciliation | Power BI/DAX visual result matches gold or semantic SQL result |
| Cardinality reconciliation | Row count, distinct business key count, duplicate key count, null key count, row multiplier, and row loss support the metric grain |

Example patterns to adapt to the current project:

```sql
select
    sum(case when <numerator_condition> then 1 else 0 end) as expected_numerator,
    sum(case when <denominator_condition> then 1 else 0 end) as expected_denominator,
    cast(sum(case when <numerator_condition> then 1 else 0 end) as decimal)
        / nullif(sum(case when <denominator_condition> then 1 else 0 end), 0) as expected_rate
from <gold_schema>.<fact_model>;
```

```sql
select
    sum(case when <gold_numerator_flag> then 1 else 0 end) as actual_numerator,
    sum(case when <gold_denominator_flag> then 1 else 0 end) as actual_denominator
from <gold_schema>.<fact_model>;
```

```sql
select
    sum(case when <upstream_numerator_flag> then 1 else 0 end) as upstream_numerator,
    sum(case when <upstream_denominator_condition> then 1 else 0 end) as upstream_denominator
from <silver_schema>.<upstream_model>;
```

Use equivalent sums for amount-based metrics.

## Common failures to catch

- Denominator is accidentally the same as the numerator.
- A denominator misses failed, cancelled, denied, inactive, refunded, or otherwise required companion states.
- A success rate, completion rate, collection rate, or conversion rate returns 100% because excluded failure rows never entered the denominator.
- A presentation measure uses a different filter than the dbt semantic metric.
- A semantic metric uses a raw row count where the approved definition requires a reportable flag.
- A gold fact aliases one flag as another instead of combining the approved flags.
- A Power BI measure divides by a filtered visual total that does not match the approved denominator.
- Empty or missing upstream facts make a metric appear valid but actually untestable.

## Required report section

Gold, semantic, analytics insight, presentation, and final reports must include:

```markdown
## Metric Verification Results

| Key Performance Indicator | Layer Checked | Expected Numerator | Actual Numerator | Expected Denominator | Actual Denominator | Expected Result | Actual Result | Status | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| <metric> | <gold/semantic/presentation> | <value> | <value> | <value or not applicable> | <value or not applicable> | <value> | <value> | <PASS/WARN/FAIL/BLOCKED> | <query, command, or report reference> |
```

For metrics without denominators, use `Not applicable` for denominator columns and reconcile the aggregate value.

Also update the cross-phase `reports/agent/METRIC_VERIFICATION_MATRIX.md` for every important measure, metric, and key performance indicator. The matrix is an acceptance-gate input and must link source proof, mart proof, semantic proof when applicable, presentation proof when applicable, expected result, actual result, difference or tolerance, and status.

## Stop conditions

Stop before semantic layer, analytics insight reporting, presentation layer, final delivery, or commit when:

- Expected and actual numerator differ without an approved reason.
- Expected and actual denominator differ without an approved reason.
- A denominator is equal to the numerator but the business definition expects additional states.
- A rate, ratio, percentage, or average cannot be recalculated from the documented components.
- The Power BI/DAX result differs from the gold/semantic SQL result.
- The metric depends on an unapproved assumption, ambiguous flag, or missing business definition.
- The metric is `LOW` or `BLOCKED` in `kpi_discovery_matrix.md` and the user has not explicitly approved further work.
- The metric lacks source-to-final proof files from [kpi-reconciliation.md](kpi-reconciliation.md).
- The metric grain or relationship cardinality is unproven or shows unexplained row multiplication/loss.

When stopped, write the root cause, expected versus actual values, affected layer, safest fix, and retest command into the phase report and `reports/agent/PIPELINE_STATUS.md`.
