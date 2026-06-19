# Warehouse Schema Setup

By default, dbt resolves custom schemas as `{profile_target_schema}_{+schema}` when using `+schema` in `dbt_project.yml`.

If the user requests source-prefixed schemas, prefer:

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
| Agents Schema | `AGENTS` | `AGENTS` *(separate - Agents Schema workflow)* |

## Verify source schema exists

```sql
select schema_name from information_schema.schemata where schema_name = '<source_schema>';
```

## Optional explicit schema creation

dbt usually creates schemas on first model build. To pre-create:

```sql
create schema if not exists <source_schema>;
-- dbt will create source-prefixed layer schemas on build
create schema if not exists agents;  -- only if not using default AGENTS uppercase
```

## Permissions

Confirm the dbt user can:

- `SELECT` on source tables in `<source_schema>`
- `CREATE` views/tables in `{layer_schema_prefix}_bronze`, `{layer_schema_prefix}_silver`, `{layer_schema_prefix}_gold`

## Agents Schema permissions

The Agents Schema writer needs `CREATE` on the `AGENTS` schema. See [agents-schema-setup.md](agents-schema-setup.md).
