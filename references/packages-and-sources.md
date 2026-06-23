# Packages & Source YAML (Phase 3)

See full stack: [dbt-packages-and-skills.md](dbt-packages-and-skills.md) and schema routing rules in [schema-isolation.md](schema-isolation.md).

Before writing `packages.yml`, running codegen, or creating source YAML, follow [phase-plan-approval.md](phase-plan-approval.md).

## `packages.yml` - standard packages

```yaml
packages:
  - package: dbt-labs/codegen
    version: 0.14.1
  - package: dbt-labs/dbt_utils
    version: 1.3.3
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

## Resolve dbt source name

The user does not need to provide a source name. Derive `source.name` before writing source YAML:

1. Use explicit `source_name` / `DBT_SOURCE_NAME` only when provided.
2. Otherwise normalize `source_schema`.
3. Remove generic suffixes such as `_src`, `_source`, `_raw`, `_schema`.
4. If the result is generic (`raw`, `source`, `src`) or unclear, use `domain`.
5. Ask only if both `source_schema` and `domain` are unclear.

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
    description: Source tables for <domain>
    schema: <source.schema>
    tables:
      - name: customers
        description: One row per customer
        columns:
          - name: customer_id
            description: Primary key for the customer
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
