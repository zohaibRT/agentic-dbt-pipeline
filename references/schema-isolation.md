# Schema Isolation

Use this before writing `dbt_project.yml`, running `dbt build`, seeds, snapshots, or `dbt_project_evaluator`.

## Core rule

The source schema is read-only and immutable input. Do not materialize dbt models, seeds, snapshots, package models, evaluator tables, docs artifacts, audit outputs, or temporary project tables into `source_schema`.

Never run warehouse data manipulation or source-object mutation against the configured source schema or source tables:

- No `UPDATE`
- No `INSERT`
- No `DELETE`
- No `TRUNCATE`
- No `MERGE`
- No `CREATE TABLE AS`
- No `CREATE`, `DROP`, or `ALTER` against source objects
- No "repair", "backfill", "mark complete", "fix status", or similar action that changes source rows

If the user asks for a data change such as "mark completed where status is X", translate that into dbt framework work only:

- A staging, intermediate, or mart model that derives a corrected status or business flag
- A seed or mapping file in a non-source schema when the user approves mapping rules
- A dbt test, audit query, or exception report that identifies rows needing source-system remediation
- A snapshot in a non-source snapshot schema when history tracking is approved

The user-facing response must say the source data was not changed and identify the dbt artifact where the derived logic lives.

One-line rule:

```text
Source schema = read-only and immutable. Profile schema = neutral dbt work/default. Medallion layers = explicit +schema with generate_schema_name override. Packages = own schemas, never source.
```

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

## Resolve `layer_schema_prefix`

`layer_schema_prefix` controls the physical warehouse schemas, not the dbt source name used in `source()`.

Resolve it in this order:

1. Explicit prompt value: `layer_schema_prefix`
2. Advanced `.env`: `DBT_LAYER_SCHEMA_PREFIX`
3. Existing complete medallion schema set, when detected and approved for reuse
4. Normalized `source_schema`, when descriptive
5. Normalized `project_slug` / `dbt_project_name`, when descriptive
6. Normalized `source_name`, only when descriptive
7. `domain` only as a last fallback when concise, descriptive, and approved for physical naming
8. Ask the user

Do not use short or abbreviated source names such as `dh`, `src`, `raw`, or names ending in punctuation as the physical schema prefix unless the user explicitly sets `layer_schema_prefix`.

Do not use the full `DBT_DOMAIN` value as a physical schema prefix by default. `DBT_DOMAIN` is business context for modeling and reporting; physical schemas need a short stable prefix. A value such as `real_estate_house_building` should normally inform analytics context while the prefix comes from a better project/source identifier such as `property_sales`, `real_estate`, or an approved existing medallion prefix.

Example:

| Input | Good physical prefix |
|---|---|
| `domain: ops`, `source_name: ao`, no better source/project identifier | `ops` |
| `source_schema: acme_ops_src`, no useful domain | `acme_ops` |
| `source_name: acme_ops_src`, no useful domain/schema | `acme_ops` |
| `DBT_DOMAIN: long_business_context_name`, `source_schema: property_sales_src` | `property_sales` |

The dbt source name may still be short, such as `ao`, for model names like `stg_ao__events`. That does not require physical schemas like `ao_bronze`.

If old schemas already exist from a previous prefix, do not create another medallion set silently. Reuse the intended prefix or ask before changing it.

When multiple medallion prefix sets exist, such as `ao_bronze/ao_silver/ao_gold` and `acme_bronze/acme_silver/acme_gold`, stop and ask which prefix is canonical before the next build. Do not drop the older schemas without explicit approval.

## Profile target schema

The dbt profile target schema is only a fallback/work schema. It must not be the source schema.

Profile target schema hygiene is a required setup check, not an optional hardening task. The setup report must show the active profile name, adapter, database or database-equivalent, target schema, source schema, whether they match, and the chosen mitigation.

If the active dbt target schema equals `source_schema`, stop before running builds and either:

1. Ask the user to change the profile target schema to a safe work schema such as `<layer_schema_prefix>_work`, or
2. Confirm that every project model, package, seed, snapshot, and evaluator output is explicitly routed to a non-source schema.

Prefer option 1 for new projects.

If the profile target schema is generic, such as `public`, `default`, `raw`, `source`, or `analytics`, it is not automatically unsafe, but the agent must document why explicit model, package, seed, snapshot, and evaluator routing prevents accidental writes. If that routing is incomplete, stop before builds.

Add this to `reports/agent/01_setup/setup_report.md` and `reports/agent/PIPELINE_STATUS.md`:

```markdown
## Profile Target Schema Hygiene

| Profile | Adapter | Database | Target Schema | Source Schema | Safe? | Evidence / Action |
|---|---|---|---|---|---|---|
| <profile> | <adapter> | <database> | <target_schema> | <source_schema> | <PASS/WARN/BLOCKED> | <routing or required change> |
```

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

vars:
  dbt_project_evaluator:
    staging_folder_name: <layer_1_name>
    intermediate_folder_name: <layer_2_name>
    marts_folder_name: <layer_3_name>
    marts_prefixes: ['fct_', 'dim_', 'mart_']
    other_prefixes: ['rpt_']
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

Also confirm no source mutation command was run. If a requested task sounded like a source data update, document how it was implemented as dbt model logic or an audit instead.

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
