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

### Incremental facts

`fct_orders` -> `unique_key='order_id'`
`fct_order_items` -> `unique_key='order_item_id'`

Use `is_incremental()` filter on date or id when adding incremental logic.

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
```

## Sync rule

When writing or updating `dbt_project.yml`, **match** `materialization_profile` from user prompt or config.
If project file disagrees with profile, **update `dbt_project.yml`** and rebuild affected layers.

## Why prod uses tables for marts

- Better BI query performance
- Predictable latency under concurrency
- Facts as incremental reduce full-refresh cost
