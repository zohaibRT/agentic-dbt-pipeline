# Separate Layer Builds - Order, Schemas, and Examples

> **Skill default:** always create **all** layers. **Ask user for three layer names** (e.g. `staging`/`intermediate`/`marts` or `bronze`/`silver`/`gold`). Names become `dbt_project.yml` keys, folders, and `+schema` values. See [dbt-project-layers.md](dbt-project-layers.md).

## Correct layer order (always - all layers)

```
1. Sources     ->  models/sources/
2. Layer 1     ->  models/{layer_1_name}/{domain}/  ->  Postgres: {target}_{layer_1_name}
3. Layer 2     ->  models/{layer_2_name}/{domain}/  ->  Postgres: {target}_{layer_2_name}
4. Layer 3     ->  models/{layer_3_name}/{domain}/  ->  Postgres: {target}_{layer_3_name}
```

Default names: `staging`, `intermediate`, `marts`.

**Do not** build intermediate before staging exists.
**Do not** build marts before intermediate exists.

Example for one entity through all layers:

| Step | Layer | Example model | Warehouse schema |
|---|---|---|---|
| 1 | Source | `source('<source_name>', 'customers')` | `<source_schema>` |
| 2 | Staging | `stg_<source_name>__customers` | `<layer_schema_prefix>_<layer_1_name>` |
| 3 | Intermediate | `int_<source_name>__customer_metrics` | `<layer_schema_prefix>_<layer_2_name>` |
| 4 | Marts | `dim_customers` | `<layer_schema_prefix>_<layer_3_name>` |

Staging comes **before** intermediate. Marts (star schema) come **last**.

---

## Build one layer at a time

Set `layers:` in the prompt to run **only** that layer. After each layer: **parse -> build -> summarize -> ask commit**.

### Layer 1 - Sources only

```text
layers: sources
```

Ensure `packages.yml` has **codegen only** - see [packages-and-sources.md](packages-and-sources.md).

```powershell
dbt deps
dbt run-operation generate_source --args '{"schema_name": "<source.schema>", "generate_columns": true}'
dbt parse --no-partial-parse
# No dbt build for sources alone - sources are YAML definitions
```

Ask commit for `models/sources/` only.

---

### Layer 2 - Staging only

```text
layers: staging
```

Creates models like:
- `stg_ecommerce__customers`
- `stg_<source>__events`
- `stg_<source>__entities`
- ... (one per source table)

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_1_name}/{domain}
```

**Builds:** staging models + tests + upstream source dependencies.
**Does NOT build:** intermediate or marts.

Warehouse models land in: **`<layer_schema_prefix>_<layer_1_name>`** (default materialization: `view`)

Ask commit -> push `models/{layer_1_name}/{domain}/` only.

---

### Layer 3 - Intermediate only

```text
layers: intermediate
```

Creates models like:
- `int_<source>__events_aggregated`
- `int_<source>__entities_enriched`
- `int_<source>__entity_metrics`

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_2_name}/{domain}
```

**Builds:** intermediate + staging (upstream) + tests.
**Does NOT build:** marts.

Warehouse models land in: **`<layer_schema_prefix>_<layer_2_name>`** (default materialization: `view`)

Ask commit -> push `models/{layer_2_name}/{domain}/` only.

---

### Layer 4 - Marts / star schema only

```text
layers: marts
```

Creates models like:
- **Dimensions:** `dim_<entity>`, `dim_dates`
- **Facts:** `fct_<business_event>`
- **Reporting:** `mart_<business_process>_performance`

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_3_name}/{domain}
```

**Builds:** marts + intermediate + staging (upstream) + tests.
**Does NOT build** downstream (there is none).

Warehouse models land in: **`<layer_schema_prefix>_<layer_3_name>`** (prod defaults: `dim_*`/`mart_*` = `table`, `fct_*` = `incremental`)

Ask commit -> push `models/{layer_3_name}/{domain}/` (+ `dbt_project.yml` if changed).

---

## Full pipeline (all layers, still separate commits)

```text
layers: all
```

Run in order, **stop and ask commit after each**:

1. Sources (if needed) -> ask commit
2. Staging -> build `+path:models/{layer_1_name}/{domain}` -> ask commit
3. Intermediate -> build `+path:models/{layer_2_name}/{domain}` -> ask commit
4. Marts -> build `+path:models/{layer_3_name}/{domain}` -> ask commit

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
