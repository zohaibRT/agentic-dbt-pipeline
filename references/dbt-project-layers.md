# dbt_project.yml — User-Defined Layer Names

**Always create all three model layers** (plus sources).  
**Ask the user for the layer names** before writing `dbt_project.yml` or any models.

## What to ask (required unless names are in the prompt)

Before any file creation, ask the user for **three layer names** used in `dbt_project.yml`:

> I will create **all layers** (sources → layer 1 → layer 2 → layer 3).  
> What names should I use in `dbt_project.yml`?
>
> 1. **Layer 1** (closest to source, `stg_*` models) — default: `staging`  
> 2. **Layer 2** (business logic, `int_*` models) — default: `intermediate`  
> 3. **Layer 3** (star schema, `dim_*` / `fct_*` / `mart_*`) — default: `marts`  

Examples the user might choose:
- `staging`, `intermediate`, `marts` (project default)
- `bronze`, `silver`, `gold`
- `raw_clean`, `enriched`, `analytics`

Use **AskQuestion** or chat. Wait for answers before proceeding.

If the user gives one name only, ask for all three.  
If the prompt already includes `layer_names:` (see [prompt.md](../prompt.md)), use those and skip the ask.

---

## How user names map to the project

Each name becomes the `dbt_project.yml` key and folder under `models/`.

For physical warehouse schemas, prefer source-prefixed names when `layer_schema_prefix` is provided:

```text
{layer_schema_prefix}_{layer_name}
```

Example:

```text
doctor_hospital_src_bronze
doctor_hospital_src_silver
doctor_hospital_src_gold
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
```

Folders: `models/bronze/{domain}/`, `models/silver/{domain}/`, `models/gold/{domain}/`  
Schemas: `{layer_schema_prefix}_bronze`, `{layer_schema_prefix}_silver`, `{layer_schema_prefix}_gold`

Important: dbt's default `generate_schema_name` macro prefixes custom schemas with the profile target schema. With profile schema `analytics` and `+schema: doctor_hospital_src_bronze`, dbt may create `analytics_doctor_hospital_src_bronze`.

If the user wants the exact physical schema `doctor_hospital_src_bronze`, add or confirm a project-level `macros/generate_schema_name.sql` override:

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
```

Ask before adding this macro in an existing project because it changes schema naming globally.

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

1. **Sources** → `models/sources/` → `dbt parse`
2. **Layer 1** (`{name_1}`) → create models → `build --select +path:models/{name_1}/{domain}` → ask commit
3. **Layer 2** (`{name_2}`) → create models → `build --select +path:models/{name_2}/{domain}` → ask commit
4. **Layer 3** (`{name_3}`) → create models → `build --select +path:models/{name_3}/{domain}` → ask commit

Write all three layer blocks to `dbt_project.yml` up front (when starting a new project) or ensure missing blocks are added before building that layer.

---

## Build commands (use user names)

```powershell
dbt build --select +path:models/{layer_1_name}/{domain}
dbt build --select +path:models/{layer_2_name}/{domain}
dbt build --select +path:models/{layer_3_name}/{domain}
```
