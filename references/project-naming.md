# Project Naming

Use this before `dbt init` or before creating a new project folder.

## Core rule

Do not use `dbt_profile_name` as the dbt project name or folder name unless the user explicitly provides the same value as `dbt_project_name`.

The dbt profile is the warehouse connection key from `~/.dbt/profiles.yml`. It is not the project identity.

## Resolve order

Resolve `dbt_project_name` and `dbt_project_root` in this order:

1. Prompt: `dbt_project_name` and `dbt_project_root`
2. Advanced `.env`: `DBT_PROJECT_NAME` and `DBT_PROJECT_ROOT`
3. `github_repo_name` when it is not local-only (`local-only`, `local`, `none`, `no`, `false`, `na`, or `n/a`)
4. `source_schema` when descriptive
5. `source_name` when descriptive
6. `domain`
7. Ask the user

Use the same value for `dbt_project_name` and `dbt_project_root` unless the user explicitly provides a different root folder. If the user provides only one of them, derive the other from the provided value.

Treat these config values as placeholders, not real names:

- `auto`
- `my_dbt_project`
- `default`
- `example`
- values wrapped in `<...>`

## Descriptive source names

Prefer `source_schema` over `source_name` when `source_name` is short, abbreviated, or ends with punctuation.

Examples:

| Input | Use? | Reason |
|---|---|---|
| `doctors_hospital_src` | Yes | descriptive source schema |
| `dh_` | No | abbreviated and produces awkward model names |
| `raw` | No | too generic |
| `source` | No | too generic |
| `hospital` | Yes | descriptive enough |

## Normalize names

Convert the chosen candidate into a valid dbt project name:

1. Lowercase it.
2. Replace spaces, hyphens, and punctuation with underscores.
3. Collapse repeated underscores.
4. Trim leading/trailing underscores.
5. Remove generic suffixes: `_src`, `_source`, `_raw`, `_schema`, `_db`, `_database`.
6. Append `_analytics` unless the name already ends with `_analytics`, `_dbt`, `_project`, `_pipeline`, `_mart`, or `_marts`.
7. Ensure it starts with a letter. If not, prefix `dbt_`.

Examples:

| Inputs | Result |
|---|---|
| `github_repo_name: hospital-analytics` | `hospital_analytics` |
| `source_schema: doctors_hospital_src` | `doctors_hospital_analytics` |
| `source_name: doctors_hospital_src` | `doctors_hospital_analytics` |
| `domain: hospital` | `hospital_analytics` |
| `source_schema: raw`, `domain: finance` | `finance_analytics` |

## dbt init behavior

When initializing:

```powershell
dbt init <dbt_project_name>
cd <dbt_project_root>
```

Then make sure `dbt_project.yml` contains:

```yaml
name: <dbt_project_name>
profile: <dbt_profile_name>
```

If the generated folder already exists, reuse it only after confirming it is the intended dbt project.
