# Warehouse Schema Setup

By default, dbt resolves custom schemas as `{profile_target_schema}_{+schema}` when using `+schema` in `dbt_project.yml`.

If the user requests source-prefixed schemas, prefer:

```text
{layer_schema_prefix}_{layer_name}
```

Example for source `doctor_hospital_src`:

```text
doctor_hospital_src_bronze
doctor_hospital_src_silver
doctor_hospital_src_gold
```

To get those exact names instead of `analytics_doctor_hospital_src_bronze`, the project needs a `generate_schema_name` macro override. See [dbt-project-layers.md](dbt-project-layers.md).

With source prefix `doctor_hospital_src` and layer config:

| Layer | `+schema` | Postgres schema created |
|---|---|---|
| Raw source | *(source tables)* | `<source_schema>` |
| Bronze | `doctor_hospital_src_bronze` | `doctor_hospital_src_bronze` |
| Silver | `doctor_hospital_src_silver` | `doctor_hospital_src_silver` |
| Gold | `doctor_hospital_src_gold` | `doctor_hospital_src_gold` |
| Agents Schema | `AGENTS` | `AGENTS` *(separate — Agents Schema workflow)* |

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
