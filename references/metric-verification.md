# Metric Verification

Use this before gold/marts, semantic layer, analytics insight reporting, presentation layer, Power BI artifacts, or final delivery complete.

## Core rule

Every implemented key performance indicator must be reconciled from its business definition to the actual built data. A dbt build, semantic parse, or Power BI file validation is not enough.

For each key performance indicator, verify:

1. Business definition: numerator, denominator, filters, time field, grain, and caveats are documented.
2. Discovery evidence: the candidate appears in `reports/agent/kpi_discovery_matrix.md` with source model, grain, archetype, confidence, caveats, and approval status.
3. Source evidence: the source or upstream layer contains the records/flags/amounts required by the definition.
4. Transformation lineage: silver/intermediate logic creates the required flags/measures correctly.
5. Gold/marts logic: final facts or marts combine numerator, denominator, filters, and flags exactly as defined.
6. Semantic logic: semantic metrics or measures reference the approved gold/mart columns and use safe denominators.
7. Presentation logic: Power BI/DAX/report measures match the semantic or gold definition.
8. Reconciliation: SQL expected values equal semantic/presentation actual values, or differences are explained.

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

## Stop conditions

Stop before semantic layer, analytics insight reporting, presentation layer, final delivery, or commit when:

- Expected and actual numerator differ without an approved reason.
- Expected and actual denominator differ without an approved reason.
- A denominator is equal to the numerator but the business definition expects additional states.
- A rate, ratio, percentage, or average cannot be recalculated from the documented components.
- The Power BI/DAX result differs from the gold/semantic SQL result.
- The metric depends on an unapproved assumption, ambiguous flag, or missing business definition.
- The metric is `LOW` or `BLOCKED` in `kpi_discovery_matrix.md` and the user has not explicitly approved further work.

When stopped, write the root cause, expected versus actual values, affected layer, safest fix, and retest command into the phase report and `reports/agent/PIPELINE_STATUS.md`.
