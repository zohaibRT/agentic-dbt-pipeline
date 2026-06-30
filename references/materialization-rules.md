# Materialization Rules

Controlled by `materialization_profile` in `project.config.yml` (default: `prod`).

## Production (`materialization_profile: prod`)

| Role | `dbt_project.yml` | Model-level override |
|---|---|---|
| Layer 1 / staging role | `+materialized: view` | - |
| Layer 2 / intermediate role | `+materialized: view` | - |
| Layer 3 / marts role | `+materialized: table` | - |
| dbt project evaluator package | `+schema: <layer_schema_prefix>_evaluator`, `+materialized: table` | - |
| `dim_*` | inherits table | `{{ config(materialized='table') }}` optional |
| `fct_*` | inherits table | `{{ config(materialized='incremental', unique_key='<pk>') }}` |
| `mart_*` reporting | inherits table | `{{ config(materialized='table') }}` |
| Internal single-use logic | not configured globally | `{{ config(materialized='ephemeral') }}` only when independent testing/lineage is not needed |

### Incremental facts

`fct_<business_event>` -> `unique_key='<fact_primary_key>'`
`fct_<child_business_event>` -> `unique_key='<child_fact_primary_key>'`

Use `is_incremental()` filter on date or id when adding incremental logic.

For large-scale incremental models, include a stable `unique_key` and an adapter-appropriate incremental predicate, merge predicate, or partition overwrite strategy when supported. Document late-arriving data assumptions.

## Contracts and public model versioning

For public marts consumed by dashboards, semantic models, or downstream applications, consider dbt model contracts and model versioning. Use them when the adapter and project maturity support them safely.

Ask before enabling contracts or versioning on an existing project because they can intentionally fail builds when downstream-facing schemas change.

## Development (`materialization_profile: dev`)

All layers `view` - faster iteration:

```yaml
models:
  <project.name>:
    <layer_1_name>:
      +materialized: view
    <layer_2_name>:
      +materialized: view
    <layer_3_name>:
      +materialized: view
  dbt_project_evaluator:
    +schema: <layer_schema_prefix>_evaluator
    +materialized: table
vars:
  dbt_project_evaluator:
    staging_folder_name: <layer_1_name>
    intermediate_folder_name: <layer_2_name>
    marts_folder_name: <layer_3_name>
    marts_prefixes: ['fct_', 'dim_', 'mart_']
    other_prefixes: ['rpt_']
```

## Sync rule

When writing or updating `dbt_project.yml`, **match** `materialization_profile` from user prompt or config.
If project file disagrees with profile, **update `dbt_project.yml`** and rebuild affected layers.

## Why prod uses tables for marts

- Better BI query performance
- Predictable latency under concurrency
- Facts as incremental reduce full-refresh cost
