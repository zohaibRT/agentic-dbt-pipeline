# Layer Data Validation

Use this after each layer build and before marking the layer phase complete. Also read [cardinality-validation.md](cardinality-validation.md) for grain, relationship, and join safety checks. Also read [metric-verification.md](metric-verification.md) and [kpi-reconciliation.md](kpi-reconciliation.md) when the layer creates, changes, or feeds key performance indicator logic.

## Core rule

`dbt build` passing is required, but it is not enough. After every bronze/staging, silver/intermediate, and gold/marts build, run warehouse validation queries that prove the built data exists, keeps the expected grain, preserves expected cardinality, and still matches the upstream evidence.

Do not defer layer data validation to the final handoff. If a layer has an unexpected empty model, row-count mismatch, broken relationship, duplicate grain, or suspicious metric result, stop before the next layer and report the issue.

## What to validate

For every model created or changed in the current layer:

| Validation area | Required evidence |
|---|---|
| Row presence | Row count for each built model |
| Expected emptiness | If a model has zero rows, show whether upstream data was also empty |
| Grain | Duplicate check on the model grain or primary key |
| Required keys | Null checks for primary business keys and relationship keys |
| Relationships | Orphan checks against referenced upstream models or dimensions |
| Cardinality and join safety | Row multiplier, row loss, distinct grain movement, many-to-many risks, and expected versus observed cardinality |
| Bridge tables | Composite key uniqueness and relationships to both dimensions when bridge tables exist |
| Row-count movement | Compare source to bronze, bronze to silver, or silver to gold where the grain makes comparison meaningful |
| Date coverage | Minimum date, maximum date, and populated date count for important date fields |
| Status and category values | Distribution of important status, type, or code fields after transformation |
| Measures | Count, sum, minimum, maximum, and null counts for important numeric measures |
| Metric components | Expected versus actual numerator, denominator, filter, flag, and rate/ratio checks for key performance indicators supported by the layer |
| Key performance indicator lineage | Source-to-current-layer proof files and first unexpected variance when key performance indicators are supported by the layer |
| Mapping coverage | Unmapped value counts when mapping seeds or reference tables are used |
| Privacy | Confirm sensitive or direct identifier fields did not reach gold unless approved |

Use lightweight aggregate queries. Avoid full samples and never include sensitive record-level values in reports.

## Layer expectations

### Bronze / staging

- Compare each one-to-one staging model row count to its source table row count.
- Prove source-to-bronze grain preservation with row count, distinct key count, duplicate key count, and null key count.
- Verify staging primary keys remain unique and not null when the source has a candidate key.
- Verify accepted status values and relationship tests that were added in YAML.
- If a source table is empty, mark the staging model as `WARN` with source evidence, not `FAIL`.

### Silver / intermediate

- Verify each intermediate model has rows when its required upstream models have rows.
- Check the declared grain for duplicates after joins.
- Check row loss and row multiplication against upstream models.
- Update `join_safety_report.md` for joins, especially when joining one-to-many children to parent-grain models.
- For joins, verify orphan or unmatched counts and explain intentional left joins.
- Validate derived flags, mapped fields, and important measures with aggregate checks.
- For flags or measures that feed key performance indicators, verify each component separately and check that denominator logic includes all required states.

### Gold / marts

- Verify every fact, dimension, and reporting mart has rows when supporting upstream data has rows.
- Treat an unexpectedly empty gold model as `FAIL` or `BLOCKED`; do not continue to semantic layer, documentation, presentation layer, or final delivery until fixed or explicitly accepted.
- Verify dimensions have unique keys and facts have valid relationships to dimensions or parent facts.
- Verify bridge tables have unique composite keys and valid relationships to both sides when bridge tables exist.
- Verify key performance indicator measures have non-null, reasonable aggregate values when source data exists.
- Run [metric-verification.md](metric-verification.md) checks for every implemented key performance indicator before semantic layer or presentation work. Expected numerator, expected denominator, actual numerator, actual denominator, and final result must reconcile.
- Run [kpi-reconciliation.md](kpi-reconciliation.md) checks for every implemented key performance indicator before semantic layer or presentation work. Source, bronze, silver, and gold proof results must be recorded where applicable.
- Confirm direct identifiers, sensitive fields, protected health information, and personally identifiable information are excluded, masked, hashed, or explicitly approved.

If upstream data is genuinely empty, the gold model may be structurally correct with zero rows. Mark it `WARN`, document the empty upstream source, and explain which metrics will be empty until data lands.

## Example query patterns

Adapt identifiers and quoting to the selected dbt profile adapter.

```sql
select count(*) as row_count
from <schema>.<model>;
```

```sql
select count(*) as duplicate_grain_rows
from (
    select <grain_key>, count(*) as row_count
    from <schema>.<model>
    group by <grain_key>
    having count(*) > 1
) duplicates;
```

```sql
select
    count(*) as row_count,
    min(<date_column>) as minimum_date,
    max(<date_column>) as maximum_date,
    count(<date_column>) as populated_date_count
from <schema>.<model>;
```

```sql
select
    count(*) as row_count,
    sum(<amount_column>) as total_amount,
    min(<amount_column>) as minimum_amount,
    max(<amount_column>) as maximum_amount,
    sum(case when <amount_column> is null then 1 else 0 end) as null_amount_count
from <schema>.<model>;
```

```sql
select <status_column>, count(*) as row_count
from <schema>.<model>
group by <status_column>
order by row_count desc;
```

## Required report section

Each bronze, silver, and gold phase report must include a section named `Data Verification Results`.

```markdown
## Data Verification Results

| Layer | Model | Row Count | Expected Evidence | Grain Check | Relationship Check | Measure Check | Result | Notes |
|---|---:|---:|---|---|---|---|---|---|
| <layer> | <model> | <row_count> | <source/upstream comparison> | <PASS/WARN/FAIL/SKIPPED> | <PASS/WARN/FAIL/SKIPPED> | <PASS/WARN/FAIL/SKIPPED> | <PASS/WARN/FAIL/BLOCKED> | <important finding> |
```

When key performance indicators are present, also include the `Metric Verification Results` section from [metric-verification.md](metric-verification.md).

When joins, facts, dimensions, bridge tables, or key performance indicators are present, also update the cardinality files from [cardinality-validation.md](cardinality-validation.md).

After writing the report, share the important validation results in the chat summary before asking for commit or the next phase.

## Stop conditions

Stop before the next layer when any of these occur:

- A model expected to have data has zero rows.
- A row-count mismatch is not explained by approved grain changes or filters.
- A join multiplies rows beyond the planned grain.
- Cardinality changes unexpectedly between layers.
- Primary keys or declared grain keys are duplicated.
- Required relationship keys are orphaned.
- Important measures are all null, negative when impossible, or clearly unreasonable.
- Key performance indicator numerator, denominator, filter, flag, or result does not reconcile to upstream logic or approved definition.
- Important date coverage is missing or outside the expected source range.
- Sensitive fields reach gold without approval.

When stopped, write the issue into the phase report, update `PIPELINE_STATUS.md` as `FAIL` or `BLOCKED`, summarize the evidence to the user, and recommend the safest fix.
