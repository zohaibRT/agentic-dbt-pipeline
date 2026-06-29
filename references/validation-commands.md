# dbt Validation Commands

Run from `{project.root}`. Prefer the active environment's `dbt` command.
If `dbt` is not available, try `python -m dbt`.
On Windows only, fall back to `dbt.executable_windows_fallback` from `project.config.yml`.

```powershell
$dbt = "dbt"
if (-not (Get-Command $dbt -ErrorAction SilentlyContinue)) {
  $dbt = "python -m dbt"
}
if ($IsWindows -and -not (Get-Command "dbt" -ErrorAction SilentlyContinue)) {
  $fallback = "$env:APPDATA\Python\Python312\Scripts\dbt.exe"
  if (Test-Path $fallback) { $dbt = $fallback }
}
```

## Connection check *(init or profile changes)*

```powershell
& $dbt debug
```

## Parse project *(after any YAML/SQL change)*

```powershell
& $dbt parse --no-partial-parse
```

## Install packages *(after packages.yml change)*

```powershell
& $dbt deps
```

## Build models + tests *(preferred over run + test separately)*

```powershell
# Full layer (with upstream)
& $dbt build --select +path:models/{layer_1_name}/{domain}
& $dbt build --select +path:models/{layer_2_name}/{domain}
& $dbt build --select +path:models/{layer_3_name}/{domain}
```

## Layer data validation *(required after every layer build)*

After each bronze/staging, silver/intermediate, and gold/marts build, read [layer-data-validation.md](layer-data-validation.md) and run warehouse aggregate queries for the models in that layer. When the layer creates or feeds key performance indicator logic, also read [metric-verification.md](metric-verification.md) and reconcile expected versus actual numerator, denominator, filters, and final result.

Required validation evidence:

- Row count for every built model
- Expected-empty check for any zero-row model
- Grain or primary-key duplicate check
- Relationship or orphan check where keys connect models
- Row-count comparison to source or upstream models where the grain makes comparison meaningful
- Date coverage for important date fields
- Status/category distribution for important fields
- Measure sanity checks for important numeric fields
- Privacy check before any gold/marts handoff

Write the results into `reports/agent/<layer>_report.md` under `Data Verification Results`, share the important findings in chat, and stop before the next layer if a model expected to contain data is empty or any validation issue is unexplained.

## Project evaluator *(after marts)*

Before running, confirm `dbt_project.yml`:

- Routes `dbt_project_evaluator` to `<layer_schema_prefix>_evaluator`
- Sets `vars: dbt_project_evaluator:` for the active medallion folders
- Includes `mart_` in `marts_prefixes` when the gold layer contains `mart_*` reporting models

```powershell
& $dbt build --select package:dbt_project_evaluator
```

Before querying evaluator result tables, inspect available columns because package versions can differ:

```powershell
& $dbt show --inline "select column_name from information_schema.columns where table_schema = '<layer_schema_prefix>_evaluator' and table_name = '<evaluator_table_name>' order by ordinal_position" --limit 100
& $dbt show --inline "select * from <layer_schema_prefix>_evaluator.<evaluator_table_name>" --limit 20
```

Do not assume columns such as `issue` exist. If the diagnostic query fails because a column is missing, inspect the table shape first and do not apply structural fixes until the actual evaluator finding is understood.

If using an exceptions seed:

```powershell
& $dbt build --select package:dbt_project_evaluator dbt_project_evaluator_exceptions
```

## Schema isolation *(after builds)*

Confirm no dbt-created artifacts landed in `<source_schema>`. See [schema-isolation.md](schema-isolation.md).

## Semantic layer *(after marts)*

```powershell
& $dbt parse --no-partial-parse
```

See [semantic-layer-spec.md](semantic-layer-spec.md).

## Tests only *(when debugging)*

```powershell
& $dbt test --select path:models/{layer_3_name}/{domain}
```

## Documentation

```powershell
& $dbt docs generate
```

Confirm after generate:

- `target/manifest.json` exists
- `target/catalog.json` exists

## View docs locally *(optional)*

After docs generate succeeds:

```powershell
& $dbt docs serve --host 127.0.0.1 --port 8080
```

Use a non-blocking/background process when the agent starts the server. Report the final URL.

## Pre-commit minimum

Before every layer commit:

1. `dbt parse --no-partial-parse`
2. `dbt build --select +path:<layer_folder>`
3. Warehouse layer data validation from [layer-data-validation.md](layer-data-validation.md)
4. Metric verification from [metric-verification.md](metric-verification.md) for implemented key performance indicators

If validation fails, fix before commit unless user explicitly documents a failing checkpoint.

## If Validation Gets Stuck

Read [stuck-recovery.md](stuck-recovery.md).

Do not keep retrying the same command. Summarize the current phase, last successful command, stuck/failed command, error output, changed files, and `git status`, then try one safe recovery or ask the user for a decision.
