# Writing Style

Use full, clear wording in all user-facing output.

## Core rule

Do not use shortened wording when writing prompts, plans, reports, summaries, recommendations, diagram notes, or final handoffs. Write for a data engineer who may be reviewing the project quickly and should not have to decode shorthand.

## Use full wording

Prefer:

- `entity relationship diagram` instead of `ERD`
- `primary key` instead of `PK`
- `foreign key` instead of `FK`
- `data quality` instead of `DQ`
- `continuous integration` instead of `CI`
- `documentation` instead of `docs`
- `repository` instead of `repo`
- `configuration` instead of `config`
- `source` instead of `src`
- `destination` instead of `dest`
- `production` instead of `prod` in prose
- `development` instead of `dev` in prose

## Allowed exact terms

Keep official names, commands, filenames, model prefixes, environment variables, package names, and code identifiers exactly as required:

- `dbt`
- `SQL`
- `YAML`
- `CLI`
- `API`
- `GitHub`
- `Mermaid`
- `AGENT_PLAN.md`
- `.env`
- `.env.example`
- `dbt_project.yml`
- `profiles.yml`
- `stg_`, `int_`, `dim_`, `fct_`, `mart_`
- `dbt docs generate`
- `dbt docs serve`
- `materialization_profile: prod`
- `target: dev`
- package names such as `dbt_utils`, `dbt_project_evaluator`, and `audit_helper`

## Tables and headings

- Use clear column headings such as `Primary key`, `Foreign key`, `Documentation`, and `Continuous integration`.
- Avoid short headings like `PK`, `FK`, `Docs`, or `CI` unless quoting a tool output exactly.
- In Mermaid diagrams, keep node identifiers valid for Mermaid, but use full wording in nearby labels and notes.

## Validation

Before marking a phase complete, scan user-facing files that were added or changed. Replace shorthand unless it is an allowed exact term or a quoted command/output.
