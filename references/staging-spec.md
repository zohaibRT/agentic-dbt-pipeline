# Staging Layer Spec

## Goal

Create or update **only** the staging layer from the current source YAML.

Read [source-profiling.md](source-profiling.md) before creating or changing staging models.
Read [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md) when source columns look sensitive or unclear.
Read [layer-data-validation.md](layer-data-validation.md) before marking staging complete.
Before creating or changing staging files, follow [phase-plan-approval.md](phase-plan-approval.md).

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Approved staging phase plan, source YAML, source profiling findings, primary key candidates, important dates/statuses, and sensitive or unclear field decisions |
| Allowed changes | Staging SQL models, staging YAML, staging tests, and staging documentation |
| Not allowed | Intermediate models, marts models, semantic metrics, dashboards, final key performance indicators, or business-process joins |
| Commands to run | `dbt parse --no-partial-parse`, `dbt build --select +path:models/{layer_1_name}/{domain}`, and staging data validation queries |
| Completion criteria | Every included source table has a source-shaped staging model, expected row counts are verified, primary keys/statuses are tested where possible, and unclear fields are documented |
| Report required | `reports/agent/staging_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Folder and naming

- Folder: `models/{layer_1_name}/{domain}/` (default: `models/bronze/{domain}/`)
- SQL: `stg_{source}__<table_name>.sql`
- YAML: `_stg_{source}.yml`

Do not create `models/staging/` unless `{layer_1_name}` is explicitly configured as `staging`. With default layer names, staging models live in `models/bronze/{domain}/`.

## Rules

- `{{ config(materialized='view') }}` on every model
- `source('{source_name}', '<table_name>')` only - no `ref()` in staging
- Keep staging close to source; no heavy business logic
- Do not calculate final revenue, CLV, refund allocation, or KPI logic
- Use **actual** column names from source YAML - do not guess
- If source YAML is incomplete or inconsistent, **stop and explain**
- If a staging column no longer exists in source, **do not delete silently** - summarize and ask

## Safe standardization

Preserve raw mapping/code columns so later layers can apply business mappings safely.

For ambiguous, placeholder, abbreviated, generic, or poorly named fields, keep them as raw columns in staging, document them as raw unmapped codes or unclear source fields, and do not rename them to business-friendly fields unless the source metadata, a reliable reference table, or the user provides definitions.

If the user asks the agent to suggest names for unclear fields, run a read-only value-pattern review first and report candidate names with confidence. Do not apply those names in staging until the user approves the exact final column names. If the user approves staging but does not approve final names, keep the original source names.

For direct identifiers or sensitive fields, keep them only when needed for source traceability or validation, document the sensitivity, and do not include full sensitive sample values in model descriptions or reports.

- Lowercase: `email`, status fields, `customer_segment`
- Uppercase: `currency_code` (only if column exists in source)
- Cast `date` / `timestamp` fields explicitly
- If `first_name` and `last_name` exist -> add `customer_full_name` via `trim(concat_ws(' ', first_name, last_name))`
- Preserve amount columns; do not create final revenue metrics

## If folder or models missing

Create from scratch. If models exist, compare to source YAML and update only what is needed.

## YAML per model

Document: purpose, grain, primary key, important columns, tests.

## Tests

- `not_null` + `unique` on primary keys
- `accepted_values` on known status/segment fields (query DB if needed)
- `relationships` only when clear and safe
- Use modern generic test `arguments:` nesting when supported by the installed dbt version

## Validate (required after every staging change)

Run from dbt project root. **Build is mandatory** - a layer is not complete until build passes.

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_1_name}/{domain}
```

`+path` builds staging models, their tests, and required upstream dependencies.

After the build, run [layer-data-validation.md](layer-data-validation.md). For staging, the report must show row counts for every staging model, source-to-staging row-count comparison for one-to-one models, primary-key uniqueness and not-null checks where keys exist, important status/category distributions, and any expected-empty source evidence. Share the staging validation results with the user before asking for commit or moving to intermediate.

## Do not create

intermediate, marts, semantic models, reports, dashboards, final documentation
