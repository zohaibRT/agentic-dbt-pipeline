# Packages & Source YAML (Phase 3)

See full stack: [dbt-packages-and-skills.md](dbt-packages-and-skills.md).

## `packages.yml` — standard packages

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

`dbt_utils`, `dbt_project_evaluator`, and `audit_helper` install via `dbt deps`. Add `dispatch` for evaluator — see [dbt-packages-and-skills.md](dbt-packages-and-skills.md).

## Generate source YAML

From `{project.root}`:

```powershell
$dbt = "$env:APPDATA\Python\Python312\Scripts\dbt.exe"
& $dbt deps
& $dbt --quiet run-operation generate_source `
  --args '{"schema_name": "<source.schema>", "generate_columns": true}' `
  > models\sources\ecommerce_sources_generated.yml
& $dbt parse --no-partial-parse
```

## Post-codegen: add `schema` and descriptions

Codegen may omit `schema:`. Add explicitly:

```yaml
version: 2

sources:
  - name: ecommerce
    description: Ecommerce operational source tables in PostgreSQL
    schema: ecommerce
    tables:
      - name: customers
        description: One row per customer
        columns:
          - name: customer_id
            description: Primary key for the customer
```

Rules:

- Use **only** columns from codegen output — do not invent columns
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
