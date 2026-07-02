# Agent Instructions

This repository contains a dbt analytics engineering agent workflow. Use `SKILL.md` as the main workflow controller and load the relevant reference files before changing dbt project files.

## Default Workflow

1. Discovery and requirements
2. Project setup and configuration
3. Sources
4. Staging
5. Intermediate
6. Marts
7. Validation
8. Documentation
9. Analytics insight reporting
10. Presentation layer (optional after approval)

Semantic layer, project evaluator, analytics insight reporting, presentation layer, continuous integration, Agents Schema, commits, and pushes require the approval rules in `SKILL.md`.

## Before Editing

- Read `project.config.yml`.
- Identify the current workflow phase.
- Read the matching reference file in `references/`.
- Explain the plan before non-setup build changes.
- Keep changes limited to the approved phase.

Creating or updating workspace `.env` from user-provided values on first run is allowed per `references/env-configuration.md`. Do not commit `.env`.

## Safety Rules

Do not:

- Edit `target/`, `dbt_packages/`, `logs/`, `.venv/`, or `profiles.yml`.
- Commit workspace `.env`, secrets, passwords, tokens, or warehouse credentials.
- Tell users to create workspace `.env` manually before the first prompt when the skill can create it on first run per `references/env-configuration.md`.
- Run discovery or dbt commands while workspace `.env` is missing or placeholder-only.
- Hardcode credentials in SQL, YAML, Markdown, workflows, or scripts.
- Update, insert, delete, truncate, merge into, create, drop, alter, or repair rows or objects in the configured source schema or source tables.
- Write dbt outputs into the configured source schema.
- Create marts before staging and intermediate models are built and validated.
- Guess business metrics, mappings, relationships, reporting needs, or sensitive-field handling.
- Mark work complete when dbt tests or warehouse validation failed without documenting the blocker.

## Validation

After dbt model or YAML changes, run the smallest useful validation first, then broaden only as needed:

- `dbt parse --no-partial-parse`
- `dbt build --select <model_name>+`
- `dbt build --select +path:<layer_path>`
- `dbt test --select <model_name>`

Document validation commands, failures, fixes, skips, and remaining risks in the phase report.
