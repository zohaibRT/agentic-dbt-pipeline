# Assumption Tests

Use this after discovery and before marking bronze, silver, gold, semantic, analytics, or final delivery complete. Also read [evidence-driven-dbt-process.md](evidence-driven-dbt-process.md), [layer-data-validation.md](layer-data-validation.md), and [cardinality-validation.md](cardinality-validation.md).

## Core distinction

| Type | Question | Examples |
|---|---|---|
| **Structural test** | Does the column obey schema rules? | `unique`, `not_null`, `relationships`, `accepted_values` |
| **Assumption test** | Is our belief about business reality still true? | one row per order after join; ship date never before order date; cancelled orders have a reason |

`dbt build` auto-runs structural tests. Assumption tests must be written deliberately.

## Required process: state, prove, lock in

1. **State** the assumption in plain language in `AGENT_PLAN.md`, the phase report, and `reports/agent/CONTEXT_TREE.md`.
2. **Prove** it against real data during discovery or layer validation and save a SQL proof under the phase `sql_proofs/` folder.
3. **Lock in** the assumption as a dbt singular test or generic test so every future `dbt build` fails when the belief breaks.

Do not leave approved assumptions only in chat or only in one-time SQL proofs.

## Where assumptions come from

Promote assumptions to tests when they appear in:

- `reports/agent/00_discovery/cardinality_report.md`
- `reports/agent/00_discovery/relationship_profile.md`
- `reports/agent/CONTEXT_TREE.md` under confident or approved items
- `reports/agent/00_discovery/requirements.md` or user `project_rules`
- layer `sql_proofs/` with `PASS` status

If discovery showed a threshold assumption, such as a 97% match rate, encode the threshold you proved — not naive zero tolerance.

## Assumption categories

### 1. Grain — one row per business key

Use after joins that should preserve grain.

Singular test pattern:

```sql
-- tests/assert_<model>_grain_one_row_per_<grain_key>.sql
select {{ grain_key }}, count(*) as row_count
from {{ ref('<model>') }}
group by {{ grain_key }}
having count(*) > 1
```

Generic alternative:

```yaml
- dbt_utils.unique_combination_of_columns:
    arguments:
      combination_of_columns: [<grain_key>]
```

This catches join fan-out that a `unique` test on upstream staging would miss.

### 2. Join cardinality — join must not multiply or drop rows

Use when a model should stay 1:1 with its upstream grain.

```sql
-- tests/assert_<model>_join_preserves_row_count.sql
with base as (
    select count(*) as row_count from {{ ref('<upstream_model>') }}
),
joined as (
    select count(*) as row_count from {{ ref('<model>') }}
)
select base.row_count as before_join, joined.row_count as after_join
from base, joined
where base.row_count != joined.row_count
```

Pair this with warehouse proof `020_<model>_upstream_row_count_compare.sql`.

### 3. Temporal and logical sequence

Use for dates, statuses, and sequences that must hold even when columns are populated and valid.

```sql
-- tests/assert_<model>_ship_date_not_before_order_date.sql
select <grain_key>, order_date, ship_date
from {{ ref('<model>') }}
where ship_date < order_date
```

```sql
-- tests/assert_<model>_no_future_dated_orders.sql
select <grain_key>, order_date
from {{ ref('<model>') }}
where order_date > current_date
```

### 4. Completeness — parts sum to the whole

Use when header totals must equal detail sums.

```sql
-- tests/assert_<header_model>_total_matches_line_items.sql
select
    h.<grain_key>,
    h.<header_total_column>,
    sum(d.<detail_amount_column>) as detail_total
from {{ ref('<header_model>') }} h
join {{ ref('<detail_model>') }} d on h.<grain_key> = d.<grain_key>
group by h.<grain_key>, h.<header_total_column>
having abs(h.<header_total_column> - sum(d.<detail_amount_column>)) > 0.01
```

### 5. Business rule — status implies required field

Use when a status value implies another field must be present.

```sql
-- tests/assert_<model>_cancelled_orders_have_reason.sql
select <grain_key>, status, cancellation_reason
from {{ ref('<model>') }}
where status = 'cancelled'
  and cancellation_reason is null
```

These protect KPI numerators and denominators from silently dropping rows.

### 6. Threshold match rate — not always 100%

Use when discovery proved a normal orphan or unmatched rate.

```yaml
- dbt_utils.relationships_where:
    arguments:
      to: ref('<dimension_model>')
      field: <foreign_key>
    config:
      severity: warn
      error_if: ">100"
```

Or use `dbt_expectations` range/row-count tests with thresholds derived from discovery proof results.

Document the approved threshold in `CONTEXT_TREE.md` and the model YAML description.

### 7. Cross-check — same fact computed two ways

Use for the strongest verification of facts and dimensions.

```sql
-- tests/assert_<dimension>_lifetime_value_matches_order_sum.sql
select d.<dimension_key>, d.<stored_measure>, o.computed_total
from {{ ref('<dimension_model>') }} d
join (
    select <dimension_key>, sum(<amount_column>) as computed_total
    from {{ ref('<fact_model>') }}
    group by <dimension_key>
) o on d.<dimension_key> = o.<dimension_key>
where abs(d.<stored_measure> - o.computed_total) > 0.01
```

Pair with `audit_helper.compare_relations` when comparing source to staging or old model to new model.

## Template files

Copy and adapt from:

```text
templates/dbt/tests/
  README.md
  assert_grain_one_row_per_key.sql
  assert_join_does_not_multiply_rows.sql
  assert_date_sequence_valid.sql
  assert_status_implies_required_field.sql
  assert_detail_sums_to_header.sql
  assert_cross_check_two_methods.sql
```

Replace placeholders such as `<model>`, `<grain_key>`, `<upstream_model>`, and `<status_value>` with project-specific names.

## Required agent behavior

After each bronze, silver, and gold build:

1. Run warehouse proofs and save them under the phase `sql_proofs/` folder.
2. Promote every approved assumption from discovery or the phase report into at least one dbt test when the assumption is meant to stay true over time.
3. Record promoted tests in the phase report, `LAYER_VERIFICATION_LEDGER.md`, and model YAML `tests:` sections.
4. Do not add assumption tests for unapproved business rules.

## Required report evidence

Phase reports must include an **Assumption Tests** section with:

| Assumption | Source evidence | SQL proof file | dbt test file | Status |
|---|---|---|---|---|
| <plain-language assumption> | discovery / context tree / user rule | `reports/agent/.../sql_proofs/...` | `tests/assert_...sql` or YAML test | PASS/WARN/FAIL/BLOCKED |

## Relationship to KPI verification

Assumption tests protect the inputs KPIs depend on. KPI reconciliation still requires:

- `KPI_DEFINITION_CONTRACTS.md`
- `METRIC_VERIFICATION_MATRIX.md`
- `kpi_reconciliation_report.md`
- `kpi_variance_report.md`
- proofs under `reports/agent/09_analytics_insights/kpis/sql_proofs/`

A KPI can pass structural tests and still be wrong if the underlying assumption was never locked in.

## Completion rule

Do not mark a layer or final delivery complete when:

- An approved assumption has proof but no dbt test.
- An assumption test fails on `dbt build`.
- A threshold test uses zero tolerance despite discovery proving a lower match rate.
- A KPI depends on an assumption that is only documented in chat.
