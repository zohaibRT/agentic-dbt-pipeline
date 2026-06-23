# Acceptance Checklist

Verify before marking the dbt pipeline workflow complete.

## Skill structure

- [ ] `SKILL.md` has `name` and `description` only in frontmatter
- [ ] Workflow instructions in body; details in `references/`
- [ ] `agents/openai.yaml` exists and matches the skill
- [ ] `python scripts/validate_config.py --root .` passes
- [ ] No secrets or hardcoded GitHub accounts in skill files
- [ ] `project.config.yml` has non-secret defaults

## Environment

- [ ] New/full pipeline started with read-only Discovery & Requirements before Bootstrap & Init
- [ ] Python venv and dbt adapter installed
- [ ] `dbt debug` passes
- [ ] `.gitignore` excludes credentials and generated files
- [ ] `.env` loaded for non-secret inputs when present; `.env.example` contains no secrets when committed
- [ ] Fresh clone without `.env` creates a safe local `.env` template and stops for required user inputs before dbt commands
- [ ] Missing required first-run values were requested directly from the user, not inferred or suggested from other workspaces or previous runs
- [ ] Any subagent delegation was read-only/draft work; main agent kept dbt commands, edits, commits, and final decisions
- [ ] `AGENT_PLAN.md` created or updated with the approved plan for each implemented phase
- [ ] `reports/agent/<phase>_report.md` created or updated for each implemented phase
- [ ] `reports/agent/PIPELINE_STATUS.md` updated after each phase

## dbt Agent Skills & packages

- [ ] dbt Agent Skills installed ([install-dbt-agent-skills.md](install-dbt-agent-skills.md))
- [ ] `packages.yml`: codegen, dbt_utils, dbt_project_evaluator, audit_helper
- [ ] `dbt deps` succeeds
- [ ] `dispatch` block for dbt_project_evaluator in `dbt_project.yml`
- [ ] Evaluator vars align package checks with active layer names (`bronze/silver/gold` by default)
- [ ] `mart_` reporting models are accepted through `marts_prefixes`
- [ ] `dbt build --select package:dbt_project_evaluator` run (review results)
- [ ] Evaluator warnings fixed or documented as accepted exceptions

## Warehouse

- [ ] Source schema accessible
- [ ] Source schema remains read-only input; no dbt-created models, evaluator tables, seeds, snapshots, or audit outputs were materialized there
- [ ] Layer schemas build using configured layer schema suffixes
- [ ] dbt_project_evaluator outputs build in `<layer_schema_prefix>_evaluator`, not `source_schema`

## Source profiling

- [ ] Row counts reviewed for each source table
- [ ] Candidate primary keys and important relationships reviewed
- [ ] Important date, amount/measure, status, type, and code columns identified
- [ ] Empty tables, duplicate keys, null keys, and major data quality concerns summarized

## dbt project

- [ ] Project name/root were derived from source/domain or explicitly provided; not accidentally copied from `dbt_profile_name`
- [ ] Source YAML UTF-8 with `schema:` set
- [ ] `dbt_project.yml` layer blocks match user layer names
- [ ] Materialization matches `materialization_profile`

## Layers

- [ ] Each phase had Markdown plan approval before implementation
- [ ] Each phase report documents what passed, warned, failed, or needs review
- [ ] Staging: all source tables, tests pass
- [ ] Intermediate: domain-appropriate reusable business logic models build successfully
- [ ] Marts: domain-appropriate facts, dimensions, and reporting marts build successfully
- [ ] Semantic layer: metrics on marts ([semantic-layer-spec.md](semantic-layer-spec.md))
- [ ] Each layer: `dbt parse` + `dbt build --select +path:...` PASS

## Mappings and business rules

- [ ] `project_rules` applied or explicitly marked not provided
- [ ] Manual mappings implemented as seeds or reference-table joins where appropriate
- [ ] Mapping coverage checked; unmapped values summarized or approved
- [ ] Business grain and key assumptions documented in model YAML or handoff notes

## Data engineering guardrails

- [ ] Each model has one documented grain
- [ ] Each phase plan includes a data-engineering decision check with evidence
- [ ] Any business-impacting decision that could not be proven from source data was approved by the user
- [ ] Incremental models have a unique key and clear update/filter rule
- [ ] Snapshots considered for slowly changing dimensions or historical attributes
- [ ] Source freshness added only when a reliable loaded-at timestamp exists
- [ ] Exposures added or recommended for known dashboards and downstream consumers
- [ ] Sensitive fields reviewed before reaching marts

## Git

- [ ] Git mode is local-only by default; GitHub repo/owner resolved only when push was requested
- [ ] Staged commits per layer ([github-setup.md](github-setup.md))
- [ ] Pushed only when repo is not `local-only` and user approved
- [ ] No secrets in commits

## Documentation

- [ ] Model/column descriptions in YAML
- [ ] `dbt docs generate` -> manifest + catalog exist
- [ ] Docs serve command or local docs URL provided when user wants to view docs

## Human review

- [ ] Pre-build plan approval captured for sources/staging/intermediate/marts/semantic/evaluator/docs as applicable
- [ ] Staging review summary produced
- [ ] Intermediate review summary produced
- [ ] Marts and metric review summary produced
- [ ] Open business decisions, assumptions, privacy concerns, and data limitations listed

## Automation *(optional)*

- [ ] CI workflow: deps + parse (+ build when creds available)
- [ ] Agents Schema workflow present
- [ ] `target/manifest.json` generated and committed when Agents Schema workflow needs it
- [ ] `WAREHOUSE_CREDENTIALS` secret configured for Snowflake, Databricks, or BigQuery
- [ ] `AGENTS` schema verified in warehouse
- [ ] Agent can query `AGENTS.ROOT` and `AGENTS.DBT_MODEL`

## Agent readiness

- [ ] Full stack documented in [dbt-packages-and-skills.md](dbt-packages-and-skills.md)
- [ ] [agent-context-prompt.md](agent-context-prompt.md) available for sessions
- [ ] Stuck or blocked runs followed [stuck-recovery.md](stuck-recovery.md)

## Final delivery

- [ ] Final handoff notes or README include domain, profile name, schemas, final models, metrics, run commands, and known limitations
- [ ] Final response starts with a short summary, then includes results, validation, data notes, git/automation status, and open decisions
- [ ] Final response references `AGENT_PLAN.md`, `reports/agent/PIPELINE_STATUS.md`, and relevant phase reports
- [ ] Phase commits created or intentionally skipped
- [ ] Final response summarizes build status, docs status, evaluator status, Agents Schema status, git status, limitations, and open decisions
