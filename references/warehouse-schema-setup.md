# Warehouse Schema Setup

Postgres resolves dbt schemas as `{profile_target_schema}_{+schema}` when using `+schema` in `dbt_project.yml`.

With profile target `ecommerce` and layer config:

| Layer | `+schema` | Postgres schema created |
|---|---|---|
| Raw source | *(source tables)* | `ecommerce` |
| Staging | `staging` | `ecommerce_staging` |
| Intermediate | `intermediate` | `ecommerce_intermediate` |
| Marts | `marts` | `ecommerce_marts` |
| Agents Schema | `AGENTS` | `AGENTS` *(separate — Agents Schema workflow)* |

## Verify source schema exists

```sql
select schema_name from information_schema.schemata where schema_name = 'ecommerce';
```

## Optional explicit schema creation

dbt usually creates schemas on first model build. To pre-create:

```sql
create schema if not exists ecommerce;
-- dbt will create ecommerce_staging, ecommerce_intermediate, ecommerce_marts on build
create schema if not exists agents;  -- only if not using default AGENTS uppercase
```

## Permissions

Confirm the dbt user can:

- `SELECT` on source tables in `ecommerce`
- `CREATE` views/tables in `ecommerce_staging`, `ecommerce_intermediate`, `ecommerce_marts`

## Agents Schema permissions

The Agents Schema writer needs `CREATE` on the `AGENTS` schema. See [agents-schema-setup.md](agents-schema-setup.md).
