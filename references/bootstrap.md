# Project Setup And Connection Validation - Automatic Setup-Only Phase After Discovery

For a new project or full pipeline, run [discovery-requirements.md](discovery-requirements.md) first. The setup phase starts only after discovery is summarized and the user accepts the discovery recommendation by replying with requirements, `continue`, `no changes`, `go ahead`, or similar.

Run this setup phase before layer work. Do not skip unless user sets `auto_bootstrap: false`.

## Automatic setup rule

Project setup and connection validation is foundational, so it auto-runs by default when `auto_bootstrap: true`. Do not ask for a separate `approve bootstrap` response after the discovery requirements checkpoint is accepted.

Before running it, write or update `AGENT_PLAN.md` with:

- Phase: Project setup and connection validation
- Status: Automatic setup-only
- Discovery report used
- Exact setup actions to run
- Validation commands
- Safety gates checked
- Profile target schema hygiene check from [schema-isolation.md](schema-isolation.md)

Then run only the setup actions allowed in this file and write:

```text
reports/agent/bootstrap_report.md
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
```

## Setup boundary

Project setup and connection validation may:

- Create a local dbt project scaffold when the project root is missing
- Create baseline local files required to make dbt parse, such as `dbt_project.yml`, `packages.yml`, `.gitignore`, safe profile examples, and the schema naming macro
- Install missing dbt Agent Skills when `auto_install_dbt_skills: true`
- Install dbt package dependencies with `dbt deps`
- Run `dbt debug` and `dbt parse --no-partial-parse`
- Resolve local-only or user-requested GitHub mode without pushing
- Write or update setup reports

Project setup and connection validation must not:

- Run codegen or create source YAML unless the current approved workflow phase is Sources
- Create bronze/staging, silver/intermediate, gold/marts, semantic layer, documentation, continuous integration, or Agents Schema files
- Build, drop, replace, or full-refresh warehouse models
- Change `~/.dbt/profiles.yml` without explicit user approval
- Commit or push without the configured git approval flow

## Stop and ask before setup when

- Required `.env` values are missing
- The selected dbt profile is missing, ambiguous, or failing
- The selected profile target schema equals the source schema and needs a safer work schema
- The selected profile target schema is generic or risky and explicit routing is incomplete
- Existing project files would be overwritten or moved
- Setup would need to create or replace warehouse objects beyond setup validation
- Credentials, secrets, GitHub remote creation, or GitHub Secrets are needed
- `auto_bootstrap: false` is set
- The user explicitly asked to approve setup manually

## 1. dbt Agent Skills + dbt packages *(agent installs - user does not)*

**User installed only:** `npx skills add zohaibRT/agentic-dbt-pipeline`

**Agent skills (auto)** - see [install-dbt-agent-skills.md](install-dbt-agent-skills.md):

If `.agents/skills/using-dbt-for-analytics-engineering/SKILL.md` is missing, agent **must** run:

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

Do not ask the user to install dbt skills manually when `auto_install_dbt_skills: true`.

**dbt packages (auto)** - see [dbt-packages-and-skills.md](dbt-packages-and-skills.md):

1. Write full `packages.yml` (codegen, dbt_utils, dbt_expectations, dbt_project_evaluator, audit_helper)
2. Add `dispatch`, `<layer_schema_prefix>_evaluator` schema routing, and medallion folder vars to `dbt_project.yml` for evaluator
3. Run `dbt deps`

## 2. Git mode (local by default; GitHub only when pushing)

See [github-repo-resolution.md](github-repo-resolution.md):

Default to local commits only. Do not ask for `github_repo_name` and do not run `gh` unless the user requests a push, provides a repo override, or an existing remote must be verified.

When GitHub is needed, use `gh api user --jq ".login"` for owner and ask only for the repo slug if missing. Do not hardcode GitHub accounts in config.

## 3. Check dbt CLI

```powershell
dbt --version
```

If missing and `workflow_phase` includes `init` or full pipeline -> run [project-initialization.md](project-initialization.md).

## 4. Check dbt connection

```powershell
dbt debug
```

If profile missing -> guide user to `~/.dbt/profiles.yml` (never commit passwords).

After `dbt debug`, perform the profile target schema hygiene check from [schema-isolation.md](schema-isolation.md). The setup report must include the active profile, adapter, database or database-equivalent, target schema, source schema, safe status, and evidence/action. Do not treat this as an optional follow-up.

## 5. Sources readiness

Prepare the project so the Sources phase can run next, but do not generate source YAML during automatic Bootstrap.

When the **Sources** phase is approved later:

1. Ensure full `packages.yml` exists
2. Run `dbt deps`
3. Run `generate_source` -> source YAML
4. Add `schema:` to source YAML if missing
5. Run `dbt parse`

See [packages-and-sources.md](packages-and-sources.md).

## 6. Agents Schema readiness

Prepare the project so Agents Schema can be enabled later, but do not create Agents Schema workflow files during automatic Bootstrap unless the user explicitly approved the automation phase.

When `auto_agents_schema: true`, the warehouse destination is supported, and the automation phase is approved:

1. Run `dbt docs generate` (requires layers built)
2. Create `.github/workflows/agents-schema-dbt.yml` if missing
3. Create `.github/workflows/dbt-ci.yml` if missing
4. **Ask user once** if `WAREHOUSE_CREDENTIALS` GitHub secret is configured

If the adapter is unsupported, skip Agents Schema and summarize that it can be enabled later for Snowflake, Databricks, or BigQuery.

## 7. Skill self-check

Confirm `.agents/skills/agentic-dbt-pipeline/SKILL.md` and `project.config.yml` are readable.

## Project setup and connection validation complete when

| Check | Status |
|---|---|
| dbt Agent Skills installed | PASS |
| All 5 dbt packages in `packages.yml` + `dbt deps` | PASS |
| `dbt debug` passes | PASS |
| Profile target schema hygiene documented and safe, or blocked for user action | PASS |
| Git mode resolved: local-only or GitHub remote prepared when requested | PASS |
| `dbt parse --no-partial-parse` passes or skipped with documented reason | PASS |
| Workflow files not created unless automation was explicitly approved | PASS |

Use this full wording in user-facing summaries. Do not write `Bootstrap complete` as the only completion message; write `Project setup and connection validation complete`.

Then proceed to layer phases.

## Advanced prompt flags

```text
auto_bootstrap: true
auto_agents_schema: false
auto_install_dbt_skills: true
github_repo_name: analytics    # optional; only when pushing to GitHub
```

Set `auto_bootstrap: false` only for layer-only edits on a fully set up project.
