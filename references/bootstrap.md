# Bootstrap - Agent Runs This First (Mandatory)

On **every** dbt Pipeline skill invocation (full pipeline or single phase), the agent **must** run this bootstrap before layer work. Do not skip unless user sets `auto_bootstrap: false`.

## 1. dbt Agent Skills + dbt packages *(agent installs - user does not)*

**User installed only:** `npx skills add zohaibRT/agentic-dbt-pipeline`

**Agent skills (auto)** - see [install-dbt-agent-skills.md](install-dbt-agent-skills.md):

If `.agents/skills/using-dbt-for-analytics-engineering/SKILL.md` is missing, agent **must** run:

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

Do not ask the user to install dbt skills manually when `auto_install_dbt_skills: true`.

**dbt packages (auto)** - see [dbt-packages-and-skills.md](dbt-packages-and-skills.md):

1. Write full `packages.yml` (codegen, dbt_utils, dbt_project_evaluator, audit_helper)
2. Add `dispatch` block to `dbt_project.yml` for evaluator
3. Run `dbt deps`

## 2. GitHub repo (ask name, use gh account)

See [github-repo-resolution.md](github-repo-resolution.md):

```powershell
gh auth status
$owner = gh api user --jq ".login"
```

**Ask user** for `github_repo_name` (repo slug only). Do not hardcode GitHub accounts in config.

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

## 5. Sources bootstrap (codegen)

When running **sources** phase or full pipeline:

1. Ensure full `packages.yml` exists
2. Run `dbt deps`
3. Run `generate_source` -> source YAML
4. Add `schema:` to source YAML if missing
5. Run `dbt parse`

See [packages-and-sources.md](packages-and-sources.md).

## 6. Agents Schema (automation bootstrap)

When `auto_agents_schema: true` and the warehouse destination is supported:

1. Run `dbt docs generate` (requires layers built)
2. Create `.github/workflows/agents-schema-dbt.yml` if missing
3. Create `.github/workflows/dbt-ci.yml` if missing
4. **Ask user once** if `WAREHOUSE_CREDENTIALS` GitHub secret is configured

If the adapter is unsupported, skip Agents Schema and summarize that it can be enabled later for Snowflake, Databricks, or BigQuery.

## 7. Skill self-check

Confirm `.agents/skills/agentic-dbt-pipeline/SKILL.md` and `project.config.yml` are readable.

## Bootstrap complete when

| Check | Status |
|---|---|
| dbt Agent Skills installed | PASS |
| All 4 dbt packages in `packages.yml` + `dbt deps` | PASS |
| `dbt debug` passes | PASS |
| `github_repo_name` collected (or in prompt) | PASS |
| Workflow files created (if automation requested) | PASS |

Then proceed to layer phases.

## Advanced prompt flags

```text
auto_bootstrap: true
auto_agents_schema: false
auto_install_dbt_skills: true
github_repo_name: analytics    # repo slug - owner from gh CLI
```

Set `auto_bootstrap: false` only for layer-only edits on a fully set up project.
