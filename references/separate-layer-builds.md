# Separate Layer Builds — Order, Schemas, and Examples

> **Skill default:** always create **all** layers. **Ask user for three layer names** (e.g. `staging`/`intermediate`/`marts` or `bronze`/`silver`/`gold`). Names become `dbt_project.yml` keys, folders, and `+schema` values. See [dbt-project-layers.md](dbt-project-layers.md).

## Correct layer order (always — all layers)

```
1. Sources     →  models/sources/
2. Layer 1     →  models/{layer_1_name}/{domain}/  →  Postgres: {target}_{layer_1_name}
3. Layer 2     →  models/{layer_2_name}/{domain}/  →  Postgres: {target}_{layer_2_name}
4. Layer 3     →  models/{layer_3_name}/{domain}/  →  Postgres: {target}_{layer_3_name}
```

Default names: `staging`, `intermediate`, `marts`.

**Do not** build intermediate before staging exists.  
**Do not** build marts before intermediate exists.

Example for **customers** (one entity through all layers):

| Step | Layer | Example model | Postgres schema (ecommerce profile) |
|---|---|---|---|
| 1 | Source | `source('ecommerce', 'customers')` | `ecommerce` (raw) |
| 2 | Staging | `stg_ecommerce__customers` | `ecommerce_staging` |
| 3 | Intermediate | `int_ecommerce__customer_order_metrics` | `ecommerce_intermediate` |
| 4 | Marts | `dim_customers` | `ecommerce_marts` |

Staging comes **before** intermediate. Marts (star schema) come **last**.

---

## Build one layer at a time

Set `layers:` in the prompt to run **only** that layer. After each layer: **parse → build → summarize → ask commit**.

### Layer 1 — Sources only

```text
layers: sources
```

Ensure `packages.yml` has **codegen only** — see [packages-and-sources.md](packages-and-sources.md).

```powershell
dbt deps
dbt run-operation generate_source --args '{"schema_name": "<source.schema>", "generate_columns": true}'
dbt parse --no-partial-parse
# No dbt build for sources alone — sources are YAML definitions
```

Ask commit for `models/sources/` only.

---

### Layer 2 — Staging only

```text
layers: staging
```

Creates models like:
- `stg_ecommerce__customers`
- `stg_ecommerce__orders`
- `stg_ecommerce__products`
- … (one per source table)

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_1_name}/{domain}
```

**Builds:** staging models + tests + upstream source dependencies.  
**Does NOT build:** intermediate or marts.

Postgres models land in: **`ecommerce_staging`** (default materialization: `view`)

Ask commit → push `models/{layer_1_name}/{domain}/` only.

---

### Layer 3 — Intermediate only

```text
layers: intermediate
```

Creates models like:
- `int_ecommerce__payments_aggregated`
- `int_ecommerce__refunds_aggregated`
- `int_ecommerce__orders_enriched`
- `int_ecommerce__order_items_enriched`
- `int_ecommerce__customer_order_metrics`

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_2_name}/{domain}
```

**Builds:** intermediate + staging (upstream) + tests.  
**Does NOT build:** marts.

Postgres models land in: **`ecommerce_intermediate`** (default materialization: `view`)

Ask commit → push `models/{layer_2_name}/{domain}/` only.

---

### Layer 4 — Marts / star schema only

```text
layers: marts
```

Creates models like:
- **Dimensions:** `dim_customers`, `dim_products`, `dim_categories`, `dim_marketing_channels`, `dim_dates`
- **Facts:** `fct_orders`, `fct_order_items`
- **Reporting:** `mart_channel_performance`, `mart_product_performance`

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_3_name}/{domain}
```

**Builds:** marts + intermediate + staging (upstream) + tests.  
**Does NOT build** downstream (there is none).

Postgres models land in: **`ecommerce_marts`** (prod defaults: `dim_*`/`mart_*` = `table`, `fct_*` = `incremental`)

Ask commit → push `models/{layer_3_name}/{domain}/` (+ `dbt_project.yml` if changed).

---

## Full pipeline (all layers, still separate commits)

```text
layers: all
```

Run in order, **stop and ask commit after each**:

1. Sources (if needed) → ask commit  
2. Staging → build `+path:models/{layer_1_name}/{domain}` → ask commit
3. Intermediate → build `+path:models/{layer_2_name}/{domain}` → ask commit
4. Marts → build `+path:models/{layer_3_name}/{domain}` → ask commit

Each layer is a separate build and optional separate git push.

---

## Optional: build a single model (advanced)

After creating one model in a layer:

```powershell
dbt build --select +stg_<source>__customers
dbt build --select +int_<source>__customer_order_metrics
dbt build --select +dim_customers
```

`+model_name` builds that model and required upstream only.  
Use for incremental work inside a layer; default skill flow still builds the **whole layer path** after all layer files are ready.

---

## What `+path` means

| Selector | Meaning |
|---|---|
| `path:models/{layer_1_name}/{domain}` | Only models in that folder |
| `+path:models/{layer_1_name}/{domain}` | That folder **+ all upstream** dependencies |

Prefer **`+path`** so upstream layers are built automatically when you build intermediate or marts alone.
