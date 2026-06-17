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

```powershell
& $dbt build --select package:dbt_project_evaluator
```

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

## Pre-commit minimum

Before every layer commit:

1. `dbt parse --no-partial-parse`
2. `dbt build --select +path:<layer_folder>`

If validation fails, fix before commit unless user explicitly documents a failing checkpoint.
