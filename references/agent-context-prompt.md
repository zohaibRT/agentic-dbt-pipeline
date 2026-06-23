# Agent Context Prompt

Copy into an agent session when starting dbt pipeline work. Edit overrides as needed.

```text
You are working in the dbt project.

Use the dbt Pipeline skill (`agentic-dbt-pipeline`) and these dbt-labs skills:
- using-dbt-for-analytics-engineering
- running-dbt-commands
- troubleshooting-dbt-job-errors

Read project.config.yml, references/skill-inputs.md, references/project-naming.md, references/schema-isolation.md, references/env-configuration.md, and references/data-engineering-best-practices.md first. If `.env` exists, load non-secret settings from it before asking for missing inputs.
For a new/full pipeline, run read-only discovery first, explain what you conclude from the source schemas/tables, and ask whether the user wants to add requirements before planning Bootstrap & Init.
When work can be safely delegated, read references/subagent-workflow.md and use subagents only for read-only analysis or draft review.
Before each phase that changes files or builds warehouse objects, read references/phase-plan-approval.md and references/data-engineer-decision-gate.md, update AGENT_PLAN.md, explain the plan in Markdown with explicit data-engineering decisions and evidence, and wait for approval. After each completed phase, read references/phase-completion-report.md, write/update reports/agent/<phase>_report.md, and update reports/agent/PIPELINE_STATUS.md.

## Warehouse (non-secret)

- type: postgres
- host: <database.host>
- port: 5432
- database: <database.dbname>
- source schema: <source.schema> (read-only)
- work/target schema: <database.target_schema> (must not equal source schema)
- layer 1 schema: <layer_schema_prefix>_<layer_1_name>
- layer 2 schema: <layer_schema_prefix>_<layer_2_name>
- layer 3 schema: <layer_schema_prefix>_<layer_3_name>
- evaluator schema: <layer_schema_prefix>_evaluator
- seeds schema: <layer_schema_prefix>_seeds
- agents schema: AGENTS

## Credentials

- Use existing dbt profile: <project.profile>
- Derive dbt project name/root from source schema or domain. Use repo name only when the user provided one for push. Do not use the profile name as the folder unless explicitly requested.
- Do not hardcode passwords
- Do not commit profiles.yml or .env
- Commit `.env.example` only when it contains no secrets

## Git

- Commit locally by default
- Use GitHub only when the user requests push or provides a repo
- When pushing, run `gh api user` for owner - do not hardcode accounts
- Ask user for repo slug only when push is requested and no repo is configured
- Commit per layer; push on approval

## dbt packages & skills *(full pipeline)*

See [dbt-packages-and-skills.md](dbt-packages-and-skills.md): codegen, dbt_utils, dbt_project_evaluator, audit_helper, semantic layer, dbt Agent Skills.

## dbt rules

- sources: models/sources/
- layer 1: models/{layer_1_name}/{domain}/ - stg_{source}__* (default layer name: bronze)
- layer 2: models/{layer_2_name}/{domain}/ - int_{source}__* (default layer name: silver)
- layer 3: models/{layer_3_name}/{domain}/ - dim_*, fct_*, mart_* (default layer name: gold)
- materialization_profile: prod (layer 1/2=view; layer 3=table; fct_*=incremental)
- ref() only in intermediate/marts; source() only in staging
- Never materialize dbt models, package models, evaluator tables, seeds, snapshots, or audit outputs in source schema
- Run dbt debug (init), dbt parse, dbt build after changes
- Before each phase build: write/update AGENT_PLAN.md, explain what will be built, include the data-engineering decision check, and wait for approval
- After each completed phase: write/update reports/agent/<phase>_report.md and reports/agent/PIPELINE_STATUS.md
- Commit each layer separately; ask before commit/push
- Keep dbt commands, file edits, commits, pushes, and final decisions with the main agent
- Push to `github_repo` only after approval; do not push in local-only mode
- Never stage: .venv, target, logs, dbt_packages, .env, profiles.yml

## Task

<describe workflow_phase or layer to build>
```

## workflow_phase values

| Phase | Reference |
|---|---|
| `init` | [project-initialization.md](project-initialization.md) |
| `sources` | [packages-and-sources.md](packages-and-sources.md) |
| `staging` | [staging-spec.md](staging-spec.md) |
| `intermediate` | [intermediate-spec.md](intermediate-spec.md) |
| `marts` | [marts-spec.md](marts-spec.md) |
| `docs` | [documentation.md](documentation.md) |
| `ci` | [cicd-setup.md](cicd-setup.md) |
| `agents_schema` | [agents-schema-setup.md](agents-schema-setup.md) |
| `semantic_layer` | [semantic-layer-spec.md](semantic-layer-spec.md) |
| `project_evaluator` | [dbt-packages-and-skills.md](dbt-packages-and-skills.md) |
