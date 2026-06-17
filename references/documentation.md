# Documentation Requirements

Apply when completing a model layer or `workflow_phase: docs`.

Also use dbt-labs skill: `using-dbt-for-analytics-engineering` → `references/writing-documentation.md`.

## Per-model YAML

For each model in staging, intermediate, and marts:

- `description` — purpose and grain (not just restating the model name)
- Column `description` for primary keys, foreign keys, and business fields
- Document non-obvious logic (e.g. `channel_id = -1` for unattributed)

## Per-source YAML

After codegen, add if missing:

```yaml
sources:
  - name: ecommerce
    description: Ecommerce operational source tables
    schema: ecommerce
    tables:
      - name: customers
        description: One row per customer
```

## Source freshness *(optional)*

Add when the source has a reliable loaded-at column:

```yaml
    freshness:
      warn_after: {count: 24, period: hour}
      error_after: {count: 48, period: hour}
    loaded_at_field: updated_at
```

Only add if `updated_at` (or equivalent) exists in source YAML — **do not assume**.

## Generate docs

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" docs generate
```

Verify `target/manifest.json` and `target/catalog.json`.

## Commit

After docs YAML updates:

```powershell
git add models/
git commit -m "Add dbt tests and documentation"
```

Ask user before commit (default `commit: ask`).
