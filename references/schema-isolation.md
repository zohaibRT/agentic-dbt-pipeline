# Schema Isolation

Use this before writing `dbt_project.yml`, running `dbt build`, seeds, snapshots, or `dbt_project_evaluator`.

## Core rule

The source schema is read-only input. Do not materialize dbt models, seeds, snapshots, package models, evaluator tables, docs artifacts, audit outputs, or temporary project tables into `source_schema`.

The warehouse should stay separated like this:

| Purpose | Schema |
|---|---|
| Raw/source tables | `<source_schema>` |
| Layer 1 / bronze | `<layer_schema_prefix>_<layer_1_name>` |
| Layer 2 / silver | `<layer_schema_prefix>_<layer_2_name>` |
| Layer 3 / gold | `<layer_schema_prefix>_<layer_3_name>` |
| Mapping seeds | `<layer_schema_prefix>_seeds` |
| Snapshots | `<layer_schema_prefix>_snapshots` |
| dbt project evaluator package | `<layer_schema_prefix>_evaluator` |
| Optional audit outputs | `<layer_schema_prefix>_audit` |
| Agents Schema metadata | `AGENTS` or configured agents schema |

## Profile target schema

The dbt profile target schema is only a fallback/work schema. It must not be the source schema.

If the active dbt target schema equals `source_schema`, stop before running builds and either:

1. Ask the user to change the profile target schema to a safe work schema such as `<layer_schema_prefix>_work`, or
2. Confirm that every project model, package, seed, snapshot, and evaluator output is explicitly routed to a non-source schema.

Prefer option 1 for new projects.

## Required `dbt_project.yml` routing

For new projects, configure all known outputs explicitly:

```yaml
models:
  <project.name>:
    <layer_1_name>:
      +schema: <layer_schema_prefix>_<layer_1_name>
      +materialized: view
    <layer_2_name>:
      +schema: <layer_schema_prefix>_<layer_2_name>
      +materialized: view
    <layer_3_name>:
      +schema: <layer_schema_prefix>_<layer_3_name>
      +materialized: table

  dbt_project_evaluator:
    +schema: <layer_schema_prefix>_evaluator
    +materialized: table

seeds:
  <project.name>:
    +schema: <layer_schema_prefix>_seeds

snapshots:
  <project.name>:
    +schema: <layer_schema_prefix>_snapshots
```

When `audit_helper` writes persistent outputs, route them to `<layer_schema_prefix>_audit`.

## Exact schema names

For new projects, add `macros/generate_schema_name.sql` so custom schemas resolve exactly:

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
```

Ask before adding this macro to an existing project because it changes schema naming globally.

## Validation

After each build, confirm no dbt-created objects landed in `source_schema`.

Use warehouse inspection when possible:

```sql
select table_schema, table_name
from information_schema.tables
where table_schema = '<source_schema>'
  and (
    table_name like 'stg_%'
    or table_name like 'int_%'
    or table_name like 'dim_%'
    or table_name like 'fct_%'
    or table_name like 'mart_%'
    or table_name like 'base_%'
    or table_name like 'dbt_project_evaluator%'
  );
```

Expected result: zero rows.

If source schema already contains dbt-created artifacts, do not drop them automatically. Summarize the objects and ask before cleanup.
