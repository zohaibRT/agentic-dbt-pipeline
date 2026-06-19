# Warehouse Schema Setup

Read [schema-isolation.md](schema-isolation.md) first. The source schema is read-only input; dbt-created objects must land in separate schemas.

By default, dbt resolves custom schemas as `{profile_target_schema}_{+schema}` when using `+schema` in `dbt_project.yml`.

Resolve `layer_schema_prefix` with [schema-isolation.md](schema-isolation.md). If the user requests source-prefixed schemas, prefer a descriptive source/schema/domain prefix:

```text
{layer_schema_prefix}_{layer_name}
```

Example for layer schema prefix `<layer_schema_prefix>`:

```text
<layer_schema_prefix>_bronze
<layer_schema_prefix>_silver
<layer_schema_prefix>_gold
```

To get those exact names instead of `analytics_<layer_schema_prefix>_bronze`, the project needs a `generate_schema_name` macro override. See [dbt-project-layers.md](dbt-project-layers.md).

With `layer_schema_prefix` and layer config:

| Layer | `+schema` | Postgres schema created |
|---|---|---|
| Raw source | *(source tables)* | `<source_schema>` |
| Bronze | `<layer_schema_prefix>_bronze` | `<layer_schema_prefix>_bronze` |
| Silver | `<layer_schema_prefix>_silver` | `<layer_schema_prefix>_silver` |
| Gold | `<layer_schema_prefix>_gold` | `<layer_schema_prefix>_gold` |
| Seeds | `<layer_schema_prefix>_seeds` | `<layer_schema_prefix>_seeds` |
| Snapshots | `<layer_schema_prefix>_snapshots` | `<layer_schema_prefix>_snapshots` |
| Project evaluator | `<layer_schema_prefix>_evaluator` | `<layer_schema_prefix>_evaluator` |
| Audit outputs | `<layer_schema_prefix>_audit` | `<layer_schema_prefix>_audit` |
| Agents Schema | `AGENTS` | `AGENTS` *(separate - Agents Schema workflow)* |

## Verify source schema exists

```sql
select schema_name from information_schema.schemata where schema_name = '<source_schema>';
```

## Optional explicit schema creation

dbt usually creates output schemas on first model build. To pre-create output schemas:

```sql
-- dbt will create source-prefixed layer schemas on build
create schema if not exists <layer_schema_prefix>_evaluator;
create schema if not exists agents;  -- only if not using default AGENTS uppercase
```

Create `<source_schema>` only when the user explicitly asks to create a new raw/source schema. The dbt pipeline should treat existing source schemas as read-only inputs.

## Permissions

Confirm the dbt user can:

- `SELECT` on source tables in `<source_schema>`
- `CREATE` views/tables in `{layer_schema_prefix}_bronze`, `{layer_schema_prefix}_silver`, `{layer_schema_prefix}_gold`
- `CREATE` views/tables in `{layer_schema_prefix}_evaluator`, `{layer_schema_prefix}_seeds`, `{layer_schema_prefix}_snapshots`, and `{layer_schema_prefix}_audit` when those features are used

## Source schema protection

Before running `dbt build`, confirm the active profile target schema is not the same as `<source_schema>`. If it is the same, stop and follow [schema-isolation.md](schema-isolation.md).

After evaluator or full builds, inspect `<source_schema>` for accidental dbt artifacts. If any `stg_*`, `int_*`, `dim_*`, `fct_*`, `mart_*`, `base_*`, or evaluator package tables appear there, summarize them and ask before cleanup.

## Agents Schema permissions

The Agents Schema writer needs `CREATE` on the `AGENTS` schema. See [agents-schema-setup.md](agents-schema-setup.md).
