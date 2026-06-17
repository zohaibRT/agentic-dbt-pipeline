# Materialization Rules

Controlled by `materialization_profile` in `project.config.yml` (default: `prod`).

## Production (`materialization_profile: prod`)

| Layer | `dbt_project.yml` | Model-level override |
|---|---|---|
| Staging | `+materialized: view` | — |
| Intermediate | `+materialized: view` | — |
| Marts folder default | `+materialized: table` | — |
| `dim_*` | inherits table | `{{ config(materialized='table') }}` optional |
| `fct_*` | inherits table | `{{ config(materialized='incremental', unique_key='<pk>') }}` |
| `mart_*` reporting | inherits table | `{{ config(materialized='table') }}` |

### Incremental facts

`fct_orders` → `unique_key='order_id'`  
`fct_order_items` → `unique_key='order_item_id'`

Use `is_incremental()` filter on date or id when adding incremental logic.

## Development (`materialization_profile: dev`)

All layers `view` — faster iteration:

```yaml
models:
  shopsphere_analytics:
    staging:
      +materialized: view
    intermediate:
      +materialized: view
    marts:
      +materialized: view
```

## Sync rule

When writing or updating `dbt_project.yml`, **match** `materialization_profile` from user prompt or config.  
If project file disagrees with profile, **update `dbt_project.yml`** and rebuild affected layers.

## Why prod uses tables for marts

- Better BI query performance
- Predictable latency under concurrency
- Facts as incremental reduce full-refresh cost
