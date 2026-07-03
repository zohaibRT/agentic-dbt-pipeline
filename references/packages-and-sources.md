# Packages & Source YAML (Phase 3)

See full stack: [dbt-packages-and-skills.md](dbt-packages-and-skills.md) and schema routing rules in [schema-isolation.md](schema-isolation.md).

Before writing `packages.yml`, running codegen, or creating source YAML, follow [phase-plan-approval.md](phase-plan-approval.md).

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Approved source phase plan, confirmed source schema, selected adapter, package stack, and source naming decision |
| Allowed changes | `packages.yml`, `package-lock.yml`, `models/sources/**`, source descriptions, source tests, and source freshness only when supported |
| Not allowed | Staging/intermediate/marts models, source YAML inside layer folders, source schema writes, alternate source profiling without approval, or invented columns |
| Commands to run | `dbt deps`, `dbt run-operation generate_source`, `dbt parse --no-partial-parse`, and source profiling queries |
| Completion criteria | Source YAML exists under `models/sources/`, schema is explicit, columns match the warehouse, parse passes, source profiling findings are documented, and source SQL proof files capture profiling evidence |
| Report required | `reports/agent/02_sources/sources_report.md`, `reports/agent/02_sources/sql_proofs/`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## `packages.yml` - standard packages

Package versions must be pinned. Do not use unbounded latest installs, floating branch references, or missing `version:` values for standard packages. If a project needs a newer version, update the pinned version intentionally, run `dbt deps`, commit `package-lock.yml`, and record the reason in the phase report.

```yaml
packages:
  - package: dbt-labs/codegen
    version: 0.14.1
  - package: dbt-labs/dbt_utils
    version: 1.3.3
  - package: calogica/dbt_expectations
    version: 0.10.4
  - package: dbt-labs/dbt_project_evaluator
    version: 1.3.0
  - package: dbt-labs/audit_helper
    version: 0.14.0
```

```powershell
git add packages.yml && git commit -m "Add dbt packages"
dbt deps
git add package-lock.yml && git commit -m "Install dbt packages"
```

`dbt_utils`, `dbt_project_evaluator`, and `audit_helper` install via `dbt deps`. Add `dispatch` and route evaluator outputs to `<layer_schema_prefix>_evaluator` - see [dbt-packages-and-skills.md](dbt-packages-and-skills.md).

Before accepting `packages.yml`, verify every standard package has an exact or range-bounded `version:` value. Treat a missing version as a source phase validation failure.

## Generate source YAML

From `{project.root}`:

```powershell
$dbt = "dbt"
& $dbt deps
& $dbt --quiet run-operation generate_source `
  --args '{"schema_name": "<source.schema>", "generate_columns": true}' `
  > models\sources\<source.name>_sources_generated.yml
& $dbt parse --no-partial-parse
```

This step reads `<source.schema>` only. It must not create models, package tables, or evaluator artifacts in the source schema.

## Source YAML location

Source definitions must live under:

```text
models/sources/
```

Do not place generated or curated source YAML in medallion layer folders such as:

```text
models/bronze/
models/silver/
models/gold/
```

Layer folders are for dbt models and layer-specific model YAML only. For example:

```text
models/sources/<source.name>_sources.yml
models/<layer_1_name>/<project_slug>/stg_<source.name>__<table>.sql
models/<layer_1_name>/<project_slug>/_stg_<source.name>.yml
```

If codegen output is accidentally written to a layer folder, move it to `models/sources/`, update references if needed, and run `dbt parse --no-partial-parse` before continuing.

Do not move source YAML from `models/sources/` into `models/<layer_1_name>/` to satisfy `dbt_project_evaluator` source-directory warnings. That mixes source metadata with model layers and makes the project harder for data engineers to review. Treat centralized source YAML under `models/sources/` as the skill default. If the evaluator warns about source directories, configure/document an accepted evaluator exception or ask the user before changing the project structure.

## Resolve dbt source name

The user does not need to provide a source name. Derive `source.name` before writing source YAML:

1. Use explicit `source_name` / `DBT_SOURCE_NAME` only when provided.
2. Otherwise normalize `source_schema`.
3. Remove generic suffixes such as `_src`, `_source`, `_raw`, `_schema`.
4. If the result is generic (`raw`, `source`, `src`) or unclear, use a concise domain-derived fallback only when no better source/project signal exists.
5. Ask only if both `source_schema` and business context are unclear.

Examples:

| Source schema | Domain | Derived source name |
|---|---|---|
| `doctors_hospital_src` | `hospital` | `doctors_hospital` |
| `hospital_raw` | `hospital` | `hospital` |
| `raw` | `finance` | `finance` |

## Source profiling

After codegen and before staging, read [source-profiling.md](source-profiling.md).

Inspect each source table for row counts, candidate keys, relationships, important date columns, numeric measure columns, status/code values, duplicate keys, null keys, and empty tables.

Use the findings to choose staging tests and to decide whether the agent needs clarification before building intermediate joins or marts.

## Post-codegen: add `schema` and descriptions

Codegen may omit `schema:`. Add explicitly:

```yaml
version: 2

sources:
  - name: <source.name>
    description: Source tables for <business_context>
    schema: <source.schema>
    tables:
      - name: <source_table>
        description: One row per <source_table_grain>
        columns:
          - name: <primary_key>
            description: Primary key for <source_table>
```

Rules:

- Use **only** columns from codegen output - do not invent columns
- Add table/column descriptions where purpose is clear
- Add `freshness` only if a loaded-at column exists in source YAML

## Source freshness *(optional)*

```yaml
    freshness:
      warn_after: {count: 24, period: hour}
      error_after: {count: 48, period: hour}
    loaded_at_field: updated_at
```

**Stop and ask** if no reliable timestamp column exists.

## Encoding

If parse fails, convert source YAML from UTF-16 to **UTF-8** (content unchanged).

## Validate

See [validation-commands.md](validation-commands.md).

## Commit

```powershell
git add models/sources/
git commit -m "Define dbt sources"
```

Ask user before commit.

## Do not commit

`dbt_packages/` (usually in `.gitignore`)
