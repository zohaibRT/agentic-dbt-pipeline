# Staging Layer Spec

## Goal

Create or update **only** the staging layer from the current source YAML.

## Folder and naming

- Folder: `models/staging/{domain}/`
- SQL: `stg_{source}__<table_name>.sql`
- YAML: `_stg_{source}.yml`

## Rules

- `{{ config(materialized='view') }}` on every model
- `source('{source_name}', '<table_name>')` only — no `ref()` in staging
- Keep staging close to source; no heavy business logic
- Do not calculate final revenue, CLV, refund allocation, or KPI logic
- Use **actual** column names from source YAML — do not guess
- If source YAML is incomplete or inconsistent, **stop and explain**
- If a staging column no longer exists in source, **do not delete silently** — summarize and ask

## Safe standardization

- Lowercase: `email`, status fields, `customer_segment`
- Uppercase: `currency_code` (only if column exists in source)
- Cast `date` / `timestamp` fields explicitly
- If `first_name` and `last_name` exist → add `customer_full_name` via `trim(concat_ws(' ', first_name, last_name))`
- Preserve amount columns; do not create final revenue metrics

## If folder or models missing

Create from scratch. If models exist, compare to source YAML and update only what is needed.

## YAML per model

Document: purpose, grain, primary key, important columns, tests.

## Tests

- `not_null` + `unique` on primary keys
- `accepted_values` on known status/segment fields (query DB if needed)
- `relationships` only when clear and safe
- Use dbt 1.11+ syntax: nest test args under `arguments:`

## Validate (required after every staging change)

Run from dbt project root. **Build is mandatory** — a layer is not complete until build passes.

```powershell
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" parse --no-partial-parse
& "$env:APPDATA\Python\Python312\Scripts\dbt.exe" build --select +path:models/staging/{domain}
```

`+path` builds staging models, their tests, and required upstream dependencies.

## Do not create

intermediate, marts, semantic models, reports, dashboards, final documentation
