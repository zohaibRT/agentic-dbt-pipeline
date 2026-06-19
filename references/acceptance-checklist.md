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

- [ ] Python venv and dbt adapter installed
- [ ] `dbt debug` passes
- [ ] `.gitignore` excludes credentials and generated files
- [ ] `.env` loaded for non-secret inputs when present; `.env.example` contains no secrets when committed

## dbt Agent Skills & packages

- [ ] dbt Agent Skills installed ([install-dbt-agent-skills.md](install-dbt-agent-skills.md))
- [ ] `packages.yml`: codegen, dbt_utils, dbt_project_evaluator, audit_helper
- [ ] `dbt deps` succeeds
- [ ] `dispatch` block for dbt_project_evaluator in `dbt_project.yml`
- [ ] `dbt build --select package:dbt_project_evaluator` run (review results)

## Warehouse

- [ ] Source schema accessible
- [ ] Layer schemas build using configured layer schema suffixes

## Source profiling

- [ ] Row counts reviewed for each source table
- [ ] Candidate primary keys and important relationships reviewed
- [ ] Important date, amount/measure, status, type, and code columns identified
- [ ] Empty tables, duplicate keys, null keys, and major data quality concerns summarized

## dbt project

- [ ] Source YAML UTF-8 with `schema:` set
- [ ] `dbt_project.yml` layer blocks match user layer names
- [ ] Materialization matches `materialization_profile`

## Layers

- [ ] Staging: all source tables, tests pass
- [ ] Intermediate: 5 models, tests pass
- [ ] Marts: 5 dims + 2 facts + 2 reporting marts, tests pass
- [ ] Semantic layer: metrics on marts ([semantic-layer-spec.md](semantic-layer-spec.md))
- [ ] Each layer: `dbt parse` + `dbt build --select +path:...` PASS

## Mappings and business rules

- [ ] `project_rules` applied or explicitly marked not provided
- [ ] Manual mappings implemented as seeds or reference-table joins where appropriate
- [ ] Mapping coverage checked; unmapped values summarized or approved
- [ ] Business grain and key assumptions documented in model YAML or handoff notes

## Git

- [ ] `github_repo_name` collected; owner from `gh api user`
- [ ] Staged commits per layer ([github-setup.md](github-setup.md))
- [ ] Pushed when `push_to_github: true` and user approved
- [ ] No secrets in commits

## Documentation

- [ ] Model/column descriptions in YAML
- [ ] `dbt docs generate` → manifest + catalog exist

## Human review

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
- [ ] Phase commits created or intentionally skipped
- [ ] Final response summarizes build status, docs status, evaluator status, Agents Schema status, git status, limitations, and open decisions
