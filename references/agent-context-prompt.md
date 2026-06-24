# Agent Context Prompt

Copy into an agent session when starting dbt pipeline work. Edit overrides as needed.

```text
You are working in the dbt project.

Use the dbt Pipeline skill (`agentic-dbt-pipeline`) and these dbt-labs skills:
- using-dbt-for-analytics-engineering
- running-dbt-commands
- troubleshooting-dbt-job-errors

Read project.config.yml, references/skill-inputs.md, references/profile-listing.md, references/project-naming.md, references/schema-isolation.md, references/env-configuration.md, references/warehouse-adapter-routing.md, references/writing-style.md, and references/data-engineering-best-practices.md first. If `.env` exists, load non-secret settings from it before asking for missing inputs. If `.env` is missing, create a safe local `.env` from `.env.example` with placeholder values only, ask which dbt profile the pipeline should use by listing available dbt profiles with profile name, adapter, database or database-equivalent, and profile schema, stop before discovery or dbt commands, and ask the user for `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA`. Do not create discovery reports while `.env` is missing or placeholder-only. Do not fill `.env` from a profile, profile target schema, warehouse schema, previous run, example, or guess. Do not say you will resolve the active profile or run adapter-specific discovery until the user chooses `DBT_PROFILE_NAME`. Do not search the repository, inspect terminal output, infer, suggest, or summarize values from other workspaces or previous runs. Do not choose a profile automatically.
After `.env` is loaded, resolve the active dbt profile adapter from `~/.dbt/profiles.yml`, announce the selected profile and adapter, and use only that adapter's discovery path. Do not call AWS, Redshift, PostgreSQL, Snowflake, BigQuery, Databricks, cloud identity checks, warehouse connectors, metadata queries, or Model Context Protocol discovery servers before `.env` and the selected dbt profile adapter are resolved. Do not call AWS, Redshift, or any unrelated warehouse connector unless the selected profile adapter requires it or the user explicitly changes profiles.
For a new/full pipeline, run lightweight read-only project discovery first, write reports/agent/discovery_report.md, update reports/agent/PIPELINE_STATUS.md and reports/agent/CONTEXT_TREE.md, create necessary Mermaid discovery diagrams including an entity relationship diagram when credible relationships exist, explain what you conclude from the source schemas/tables, include recommended medallion direction for sources, bronze/staging, silver/intermediate, and gold/marts, recommend the best next path with evidence, and ask whether the user wants to add or change requirements before automatic setup-only Bootstrap. If the dbt project root does not exist yet, create reports/agent/ under the current workspace/run root. Do not design every layer upfront; read references/phased-discovery.md and references/recommendation-and-review.md, then run focused discovery before sources, bronze, silver, gold, semantic, evaluator, and documentation phases.
After the user accepts discovery requirements, read references/bootstrap.md and run automatic setup-only Bootstrap when auto_bootstrap is true. Write/update AGENT_PLAN.md with Bootstrap marked automatic setup-only, run only scaffold/dependency/debug/parse setup actions, and write reports/agent/bootstrap_report.md, reports/agent/PIPELINE_STATUS.md, and reports/agent/CONTEXT_TREE.md. Stop and ask before Bootstrap only when a bootstrap safety gate is triggered.
When work can be safely delegated, read references/subagent-workflow.md and use subagents only for read-only analysis or draft review.
Before each non-bootstrap phase that changes files or builds warehouse objects, read references/phase-plan-approval.md, references/recommendation-and-review.md, and references/data-engineer-decision-gate.md, update AGENT_PLAN.md, explain the plan in Markdown with the agent recommendation, explicit data-engineering decisions, evidence, confidence, risks, and approval needs, and wait for approval. After each completed phase, read references/phase-completion-report.md and references/context-tree.md, write/update reports/agent/<phase>_report.md, reports/agent/PIPELINE_STATUS.md, and reports/agent/CONTEXT_TREE.md.
Use Mermaid for every diagram. Read references/mermaid-diagrams.md before creating or changing diagrams. Entity relationships must use Mermaid erDiagram, and every added or changed Mermaid diagram must be verified as visible/parseable with the result recorded in the phase report.
Use full wording in user-facing plans, reports, summaries, diagram notes, and final handoffs. Read references/writing-style.md before writing user-facing output, and avoid shorthand unless it is an official tool name, command, filename, environment variable, package name, or code identifier.

## Warehouse (non-secret, after profile selection)

- type: <adapter from selected dbt profile>
- host: <host from selected dbt profile, if applicable>
- port: <port from selected dbt profile, if applicable>
- database: <database/dbname/project from selected dbt profile, if applicable>
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
- Use only the adapter from the selected dbt profile for discovery
- Do not call any warehouse or cloud connector until `.env` and the selected dbt profile adapter are resolved and announced
- Derive dbt project name/root from source schema or domain. Use repository name only when the user provided one for push. Do not use the profile name as the folder unless explicitly requested.
- Do not hardcode passwords
- Do not commit profiles.yml or .env
- Commit `.env.example` only when it contains no secrets

## Git

- Commit locally by default
- Use GitHub only when the user requests push or provides a repository
- When pushing, run `gh api user` for owner - do not hardcode accounts
- Ask user for repository slug only when push is requested and no repository is configured
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
- Do not probe unrelated warehouses or cloud connectors before or during discovery
- Run setup-only Bootstrap automatically after discovery requirements are accepted, unless a bootstrap safety gate is triggered
- Run focused phase discovery before each non-bootstrap phase plan; recommend the best path with evidence, but do not replace the data engineer's business decisions
- Keep ambiguous, placeholder, abbreviated, generic, or poorly named fields unchanged unless the user provides definitions or explicitly asks for suggested names; suggestions require value-pattern evidence and separate approval before SQL or YAML changes
- Before each non-bootstrap phase build: write/update AGENT_PLAN.md, explain what will be built, include recommendation, confidence, and data-engineering decision check, and wait for approval
- Use Mermaid for all diagrams; verify Mermaid visibility/parse status before marking the phase complete
- Use full wording in user-facing output; avoid shorthand such as primary key abbreviations, foreign key abbreviations, entity relationship diagram abbreviations, documentation abbreviations, repository abbreviations, and continuous integration abbreviations
- After each completed phase: write/update reports/agent/<phase>_report.md, reports/agent/PIPELINE_STATUS.md, and reports/agent/CONTEXT_TREE.md
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
