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

## Project evaluator *(after marts)*

Before running, confirm `dbt_project.yml` routes `dbt_project_evaluator` to `<layer_schema_prefix>_evaluator`.

```powershell
& $dbt build --select package:dbt_project_evaluator
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

If validation fails, fix before commit unless user explicitly documents a failing checkpoint.

## If Validation Gets Stuck

Read [stuck-recovery.md](stuck-recovery.md).

Do not keep retrying the same command. Summarize the current phase, last successful command, stuck/failed command, error output, changed files, and `git status`, then try one safe recovery or ask the user for a decision.
