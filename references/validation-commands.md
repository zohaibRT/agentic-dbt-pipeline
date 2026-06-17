# dbt Validation Commands

Run from `{project.root}`. Use executable from `project.config.yml`:

```powershell
$dbt = "$env:APPDATA\Python\Python312\Scripts\dbt.exe"
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
& $dbt build --select +path:models/staging/ecommerce
& $dbt build --select +path:models/intermediate/ecommerce
& $dbt build --select +path:models/marts/ecommerce
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
& $dbt test --select path:models/marts/ecommerce
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
