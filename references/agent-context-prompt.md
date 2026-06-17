# Agent Context Prompt

Copy into Cursor when starting dbt pipeline work. Edit overrides as needed.

```text
You are working in the dbt project.

Use the agentic-dbt-pipeline skill and these dbt-labs skills:
- using-dbt-for-analytics-engineering
- running-dbt-commands
- troubleshooting-dbt-job-errors

Read project.config.yml and references/skill-inputs.md first.

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
- Do not hardcode passwords
- Do not commit profiles.yml or .env

## GitHub *(ask repo name; owner from gh CLI)*

```text
github_repo_name: analytics
push_to_github: true
commit: ask
```

- Agent runs `gh api user` for owner — do not hardcode accounts
- Ask user for repo slug if not in prompt
- Commit per layer; push on approval

## dbt packages & skills *(full pipeline)*

See [dbt-packages-and-skills.md](dbt-packages-and-skills.md): codegen, dbt_utils, dbt_project_evaluator, audit_helper, semantic layer, dbt Agent Skills.

## dbt rules

- sources: models/sources/
- staging: models/staging/{domain}/ — stg_{source}__*
- intermediate: models/intermediate/{domain}/ — int_{source}__*
- marts: models/marts/{domain}/ — dim_*, fct_*, mart_*
- materialization_profile: prod (staging/intermediate=view; marts=table; fct_*=incremental)
- ref() only in intermediate/marts; source() only in staging
- Run dbt debug (init), dbt parse, dbt build after changes
- Commit each layer separately; ask before commit/push
- Push to `github_repo` after commits when `push_to_github: true`
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
