# agentic-dbt-pipeline

Cursor Agent Skill for **end-to-end agentic dbt automation**: bootstrap, layered models, dbt packages, semantic layer, docs, per-layer git commits, and GitHub push via `gh` CLI.

**One install command.** On first use, the agent bootstraps everything else (dbt Agent Skills, dbt packages, codegen, CI workflows).

## Install (one command)

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

That is the **only** skill you install manually. When you run the pipeline, bootstrap automatically:

1. Installs [dbt Agent Skills](https://github.com/dbt-labs/dbt-agent-skills) (`npx skills add dbt-labs/dbt-agent-skills/skills/dbt`) if missing
2. Runs `dbt deps` for codegen, dbt_utils, dbt_project_evaluator, audit_helper
3. Verifies `dbt debug`, codegen sources, and GitHub repo setup

Default flags (`auto_bootstrap: true`, `auto_install_dbt_skills: true`) handle this — you do not run separate install commands.

## Use

In Cursor chat:

```text
Use the agentic-dbt-pipeline skill.

auto_bootstrap: true
auto_install_dbt_skills: true
push_to_github: true
commit: ask
materialization_profile: prod

github_repo_name: your-repo-name

layer_names:
  layer_1: staging
  layer_2: intermediate
  layer_3: marts
```

Full copy-paste prompt: [prompt.md](prompt.md)

## Verify (after first agent run)

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md          ← you installed this
.agents/skills/using-dbt-for-analytics-engineering/    ← agent installed this
```

## Configure

Edit `project.config.yml` (under `.agents/skills/agentic-dbt-pipeline/` after install) for warehouse metadata, project paths, and layer defaults.

**GitHub:** agent asks for `github_repo_name`; owner comes from `gh api user`.

## What the agent automates

| Phase | Action |
|---|---|
| Bootstrap | **Auto-install** dbt Agent Skills + all dbt packages, `dbt debug`, codegen |
| Sources | `packages.yml`, `dbt deps`, `generate_source` |
| Layers | staging → intermediate → marts (build + tests) |
| Semantic layer | MetricFlow YAML on marts |
| Quality | `dbt_project_evaluator`, `audit_helper` |
| Docs | `dbt docs generate` |
| Git | Per-layer commits + push to GitHub on approval |
| CI | GitHub Actions + Agents Schema workflows |

## dbt packages (installed by agent via `dbt deps`)

- `dbt-labs/codegen`
- `dbt-labs/dbt_utils`
- `dbt-labs/dbt_project_evaluator`
- `dbt-labs/audit_helper`

## Prerequisites

- Python 3.12 + `dbt-core` + adapter (e.g. `dbt-postgres`)
- `~/.dbt/profiles.yml` with warehouse credentials
- [GitHub CLI](https://cli.github.com/) (`gh auth login`) for push
- Node.js (for `npx skills` on first install)

## More docs

| File | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Main skill orchestrator |
| [references/install-skill.md](references/install-skill.md) | Install details |
| [references/bootstrap.md](references/bootstrap.md) | What auto-runs on first use |
| [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | Full stack |
