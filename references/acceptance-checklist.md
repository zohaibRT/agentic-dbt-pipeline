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

## dbt Agent Skills & packages

- [ ] dbt Agent Skills installed ([install-dbt-agent-skills.md](install-dbt-agent-skills.md))
- [ ] `packages.yml`: codegen, dbt_utils, dbt_project_evaluator, audit_helper
- [ ] `dbt deps` succeeds
- [ ] `dispatch` block for dbt_project_evaluator in `dbt_project.yml`
- [ ] `dbt build --select package:dbt_project_evaluator` run (review results)

## Warehouse

- [ ] Source schema accessible
- [ ] Layer schemas build using configured layer schema suffixes

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

## Git

- [ ] `github_repo_name` collected; owner from `gh api user`
- [ ] Staged commits per layer ([github-setup.md](github-setup.md))
- [ ] Pushed when `push_to_github: true` and user approved
- [ ] No secrets in commits

## Documentation

- [ ] Model/column descriptions in YAML
- [ ] `dbt docs generate` → manifest + catalog exist

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
