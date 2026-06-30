# Project Evaluator Alignment

Use this after marts are built and before final docs/summary.

Before changing evaluator config, seeds, or exceptions, follow [phase-plan-approval.md](phase-plan-approval.md).

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Approved evaluator phase plan, built marts, evaluator package installed, evaluator schema routing, and medallion folder vars |
| Allowed changes | Evaluator configuration, reviewed exceptions seed, evaluator report, and pipeline status updates |
| Not allowed | Moving source YAML into layer folders to satisfy warnings, hiding failed tests, building evaluator objects in source schema, or structural fixes based on failed diagnostic queries |
| Commands to run | `dbt build --select package:dbt_project_evaluator`, evaluator table shape inspection, and targeted evaluator findings queries |
| Completion criteria | Errors are fixed or blocked, warnings are fixed or documented as accepted, and evaluator outputs are isolated outside source schema |
| Report required | `reports/agent/evaluator_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Recommended path

Keep the skill's medallion structure: `bronze`, `silver`, `gold`.

Do not rename folders to `staging`, `intermediate`, and `marts` only to satisfy `dbt_project_evaluator`. Instead, configure the package to understand the project conventions.

Do not create additional `staging`, `intermediate`, or `marts` folders when the active layer folders are `bronze`, `silver`, and `gold`. Evaluator folder names must be configured to the active layer names.

Do not move generated or curated source YAML from `models/sources/` into the bronze/staging folder only to clear `fct_source_directories` warnings. Source YAML belongs in `models/sources/` for this skill. Fix evaluator alignment through package vars, reviewed exceptions, or documentation; do not change the architecture silently.

## Required `dbt_project.yml` config

Add evaluator routing and medallion naming vars before running the evaluator:

```yaml
dispatch:
  - macro_namespace: dbt
    search_order: ['dbt_project_evaluator', 'dbt']

models:
  dbt_project_evaluator:
    +schema: <layer_schema_prefix>_evaluator
    +materialized: table

vars:
  dbt_project_evaluator:
    staging_folder_name: <layer_1_name>        # bronze by default
    intermediate_folder_name: <layer_2_name>   # silver by default
    marts_folder_name: <layer_3_name>          # gold by default
    marts_prefixes: ['fct_', 'dim_', 'mart_']
    other_prefixes: ['rpt_']
```

Use `marts_prefixes` for `mart_` models because the skill places reporting marts in the gold/marts layer. Do not put `mart_` in `other_prefixes` unless the project also defines an `other_folder_name`.

## Folder convention

For new projects, make the staging subfolder source-specific when possible:

```text
models/<layer_1_name>/<source_folder>/stg_<source_name>__table.sql
```

Derive `source_folder` from `source_name` or `source_schema`. If an existing project already uses a domain folder such as `models/bronze/hospital/`, keep it unless the user approves a move. Document any remaining evaluator directory warnings.

Intermediate and gold folders may stay domain-oriented:

```text
models/<layer_2_name>/<project_slug>/
models/<layer_3_name>/<project_slug>/
```

## Run

```powershell
& $dbt build --select package:dbt_project_evaluator
```

## Inspect evaluator findings safely

Evaluator table columns can differ by package version. Before querying a specific column such as `issue`, inspect the table shape:

```powershell
& $dbt show --inline "select column_name from information_schema.columns where table_schema = '<layer_schema_prefix>_evaluator' and table_name = 'fct_source_directories' order by ordinal_position" --limit 100
```

Then query only columns that exist:

```powershell
& $dbt show --inline "select * from <layer_schema_prefix>_evaluator.fct_source_directories" --limit 20
```

If a diagnostic query fails because a column does not exist, do not apply structural fixes. Inspect the evaluator table columns first, then summarize the actual findings.

If an exceptions seed exists, run it with the package:

```powershell
& $dbt build --select package:dbt_project_evaluator dbt_project_evaluator_exceptions
```

## Exceptions

Only add exceptions for intentional, reviewed design choices. Do not use exceptions to hide broken tests, missing docs, or accidental source-schema writes.

Create `seeds/dbt_project_evaluator_exceptions.csv`:

```csv
fct_name,column_name,id_to_exclude,comment
fct_rejoining_of_upstream_concepts,parent_and_child,<id_to_exclude>,accepted medallion/star-schema pattern
```

For existing projects that intentionally keep generated source YAML in `models/sources/` or staging models in a domain folder, prefer documented exceptions over moving many completed files:

```csv
fct_name,column_name,id_to_exclude,comment
fct_source_directories,current_file_path,%sources%,Accepted centralized generated source YAML path.
fct_model_directories,current_file_path,%bronze%<domain>%,Accepted existing domain-based staging folder.
```

Only add these exceptions after reviewing the evaluator table columns and the actual finding identifiers used by the installed package version.

When adding a custom exceptions seed, disable the package's blank seed:

```yaml
seeds:
  dbt_project_evaluator:
    dbt_project_evaluator_exceptions:
      +enabled: false
```

## Review rules

- Treat `ERROR` or failed evaluator tests as blockers.
- Treat `WARN` as acceptable only after summarizing the finding and either fixing it or documenting why it is accepted.
- Keep evaluator outputs in `<layer_schema_prefix>_evaluator`, never in `source_schema`.
