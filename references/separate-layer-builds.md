# Separate Layer Builds - Order, Schemas, and Examples

> **Skill default:** always create **all** layers. Use `bronze`/`silver`/`gold` unless the user or existing project provides different layer names. Names become `dbt_project.yml` keys, folders, and `+schema` values. See [dbt-project-layers.md](dbt-project-layers.md).

## Correct layer order (always - all layers)

```
1. Sources     ->  models/sources/
2. Layer 1     ->  models/{layer_1_name}/{domain}/  ->  Postgres: {target}_{layer_1_name}
3. Layer 2     ->  models/{layer_2_name}/{domain}/  ->  Postgres: {target}_{layer_2_name}
4. Layer 3     ->  models/{layer_3_name}/{domain}/  ->  Postgres: {target}_{layer_3_name}
```

Default names: `bronze`, `silver`, `gold`.

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

Set `workflow_phase:` in the prompt to run **only** that phase.

For every phase: **discover -> write `AGENT_PLAN.md` -> ask approval -> implement -> parse/build -> summarize -> ask commit**.

### Sources only

```text
workflow_phase: sources
```

Ensure `packages.yml` has **codegen only** - see [packages-and-sources.md](packages-and-sources.md).

```powershell
dbt deps
dbt run-operation generate_source --args '{"schema_name": "<source.schema>", "generate_columns": true}'
dbt parse --no-partial-parse
# No dbt build for sources alone - sources are YAML definitions
```

Explain the source YAML plan and get approval before running codegen or writing source files.
Ask commit for `models/sources/` only.

---

### Layer 1 - Bronze / staging only

```text
workflow_phase: staging
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

Explain planned staging models, source tables, casts, tests, and schema target before creating files.
Ask commit -> push `models/{layer_1_name}/{domain}/` only.

---

### Layer 2 - Silver / intermediate only

```text
workflow_phase: intermediate
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

Explain planned intermediate models, joins, grains, mappings, flags, and tests before creating files.
Ask commit -> push `models/{layer_2_name}/{domain}/` only.

---

### Layer 3 - Gold / marts only

```text
workflow_phase: marts
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

Explain planned facts, dimensions, reporting marts, metrics, privacy handling, grains, and materializations before creating files.
Ask commit -> push `models/{layer_3_name}/{domain}/` (+ `dbt_project.yml` if changed).

---

## Full pipeline (all layers, still separate commits)

```text
Run the default prompt without `workflow_phase`.
```

Run in order, **stop for phase plan approval before each build and ask commit after each**:

1. Sources (if needed) -> plan approval -> source files -> ask commit
2. Staging -> plan approval -> build `+path:models/{layer_1_name}/{domain}` -> ask commit
3. Intermediate -> plan approval -> build `+path:models/{layer_2_name}/{domain}` -> ask commit
4. Marts -> plan approval -> build `+path:models/{layer_3_name}/{domain}` -> ask commit

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
