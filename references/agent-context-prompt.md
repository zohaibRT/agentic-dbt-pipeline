# Agent Context Prompt

Copy into Cursor when starting dbt pipeline work. Edit overrides as needed.

```text
You are working in the dbt project.

Use the dbt Pipeline skill (`agentic-dbt-pipeline`) and these dbt-labs skills:
- using-dbt-for-analytics-engineering
- running-dbt-commands
- troubleshooting-dbt-job-errors

Read project.config.yml, references/skill-inputs.md, references/project-naming.md, references/env-configuration.md, and references/data-engineering-best-practices.md first. If `.env` exists, load non-secret settings from it before asking for missing inputs.
When work can be safely delegated, read references/subagent-workflow.md and use subagents only for read-only analysis or draft review.

## Warehouse (non-secret)

- type: postgres
- host: <database.host>
- port: 5432
- database: <database.dbname>
- source schema: <source.schema>
- staging schema: <target_schema>_<layer_1_name>
- intermediate schema: <target_schema>_<layer_2_name>
- marts schema: <target_schema>_<layer_3_name>
- agents schema: AGENTS

## Credentials

- Use existing dbt profile: <project.profile>
- Derive dbt project name/root from repo, source schema, source name, or domain. Do not use the profile name as the folder unless explicitly requested.
- Do not hardcode passwords
- Do not commit profiles.yml or .env
- Commit `.env.example` only when it contains no secrets

## GitHub *(ask repo name; owner from gh CLI)*

```text
github_repo_name: analytics
```

- Agent runs `gh api user` for owner - do not hardcode accounts
- Ask user for repo slug if not in prompt
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
- Run dbt debug (init), dbt parse, dbt build after changes
- Commit each layer separately; ask before commit/push
- Keep dbt commands, file edits, commits, pushes, and final decisions with the main agent
- Push to `github_repo` only after approval; do not push when repo intent is `local-only`
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
