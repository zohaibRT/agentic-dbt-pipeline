# dbt_project.yml - Layer Names

**Always create all three model layers** (plus sources).
Default to `bronze`, `silver`, and `gold` unless the prompt, advanced `.env` keys, or an existing project clearly uses different names.

Ask the user only when:

- They explicitly request custom layer names.
- Existing folders or `dbt_project.yml` conflict with the defaults.
- They provide only one or two custom layer names.

Examples of valid custom names:

- `staging`, `intermediate`, `marts`
- `raw_clean`, `enriched`, `analytics`

---

## How user names map to the project

Each name becomes the `dbt_project.yml` key and folder under `models/`.

For physical warehouse schemas, resolve `layer_schema_prefix` with [schema-isolation.md](schema-isolation.md). Do not default to a short source name such as `dh` unless explicitly requested:

```text
{layer_schema_prefix}_{layer_name}
```

Example:

```text
<layer_schema_prefix>_bronze
<layer_schema_prefix>_silver
<layer_schema_prefix>_gold
```

| Role | User name (example) | `dbt_project.yml` | Folder | Postgres schema |
|---|---|---|---|---|
| Layer 1 | `bronze` | `bronze:` | `models/bronze/{domain}/` | `{layer_schema_prefix}_bronze` |
| Layer 2 | `silver` | `silver:` | `models/silver/{domain}/` | `{layer_schema_prefix}_silver` |
| Layer 3 | `gold` | `gold:` | `models/gold/{domain}/` | `{layer_schema_prefix}_gold` |

If user chooses `bronze`, `silver`, `gold` (production defaults):

```yaml
models:
  {project.name}:
    bronze:
      +schema: {layer_schema_prefix}_bronze
      +materialized: view
    silver:
      +schema: {layer_schema_prefix}_silver
      +materialized: view
    gold:
      +schema: {layer_schema_prefix}_gold
      +materialized: table
  dbt_project_evaluator:
    +schema: {layer_schema_prefix}_evaluator
    +materialized: table
seeds:
  {project.name}:
    +schema: {layer_schema_prefix}_seeds
snapshots:
  {project.name}:
    +schema: {layer_schema_prefix}_snapshots
vars:
  dbt_project_evaluator:
    staging_folder_name: {layer_1_name}
    intermediate_folder_name: {layer_2_name}
    marts_folder_name: {layer_3_name}
    marts_prefixes: ['fct_', 'dim_', 'mart_']
    other_prefixes: ['rpt_']
```

Folders: `models/bronze/{domain}/`, `models/silver/{domain}/`, `models/gold/{domain}/`
Schemas: `{layer_schema_prefix}_bronze`, `{layer_schema_prefix}_silver`, `{layer_schema_prefix}_gold`
Package/evaluator schema: `{layer_schema_prefix}_evaluator`

Important: dbt's default `generate_schema_name` macro prefixes custom schemas with the profile target schema. With profile schema `analytics` and `+schema: <layer_schema_prefix>_bronze`, dbt may create `analytics_<layer_schema_prefix>_bronze`.

If the user wants the exact physical schema `<layer_schema_prefix>_bronze`, add or confirm a project-level `macros/generate_schema_name.sql` override:

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
```

For new projects, add this macro automatically so medallion, evaluator, seed, and snapshot schemas are exact and separate. Ask before adding this macro in an existing project because it changes schema naming globally.

For layer 3 (marts), set model-level configs in SQL:
- `dim_*` / `mart_*`: `materialized='table'`
- `fct_*`: `materialized='incremental'` (with `unique_key` and incremental predicate)

---

## Fixed layer roles (names change, logic does not)

| Role | Model prefix | Spec file |
|---|---|---|
| Layer 1 | `stg_{source}__` | [staging-spec.md](staging-spec.md) |
| Layer 2 | `int_{source}__` | [intermediate-spec.md](intermediate-spec.md) |
| Layer 3 | `dim_`, `fct_`, `mart_` | [marts-spec.md](marts-spec.md) |

Model **prefixes** stay the same; only folder / `dbt_project.yml` / schema **names** come from the user.

---

## Full pipeline (always all layers)

After names are confirmed, run in order:

1. **Sources** -> `models/sources/` -> `dbt parse`
2. **Layer 1** (`{name_1}`) -> create models -> `build --select +path:models/{name_1}/{domain}` -> ask commit
3. **Layer 2** (`{name_2}`) -> create models -> `build --select +path:models/{name_2}/{domain}` -> ask commit
4. **Layer 3** (`{name_3}`) -> create models -> `build --select +path:models/{name_3}/{domain}` -> ask commit

Write all three layer blocks to `dbt_project.yml` up front (when starting a new project) or ensure missing blocks are added before building that layer.

---

## Build commands (use user names)

```powershell
dbt build --select +path:models/{layer_1_name}/{domain}
dbt build --select +path:models/{layer_2_name}/{domain}
dbt build --select +path:models/{layer_3_name}/{domain}
```
