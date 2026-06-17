# agentic-dbt-pipeline

Cursor Agent Skill for **end-to-end agentic dbt automation**: bootstrap, layered models, dbt packages, semantic layer, docs, per-layer git commits, and GitHub push via `gh` CLI.

Works with [dbt Agent Skills](https://github.com/dbt-labs/dbt-agent-skills) the same way you install `using-dbt-for-analytics-engineering`.

## Install

### 1. dbt Agent Skills (required companion)

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

### 2. This skill

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Skills install to `.agents/skills/` in your project (or global agent skills path, depending on your Cursor setup).

### 3. Verify

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md
.agents/skills/using-dbt-for-analytics-engineering/SKILL.md
```

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

Full copy-paste prompt: [ONE_SHOT_PROMPT.md](ONE_SHOT_PROMPT.md)

## Configure

Edit `project.config.yml` in this skill folder (or after install, under `.agents/skills/agentic-dbt-pipeline/`) for:

- dbt project name and root path
- Warehouse connection metadata (no passwords)
- Layer folder names and materialization defaults

**GitHub:** do not hardcode accounts. The agent asks for `github_repo_name` and resolves the owner from `gh api user`.

## What the agent automates

| Phase | Action |
|---|---|
| Bootstrap | Install dbt skills, all packages, `dbt debug`, codegen |
| Sources | `packages.yml`, `dbt deps`, `generate_source` |
| Layers | staging → intermediate → marts (build + tests) |
| Semantic layer | MetricFlow YAML on marts |
| Quality | `dbt_project_evaluator`, `audit_helper` |
| Docs | `dbt docs generate` |
| Git | Per-layer commits + push to GitHub on approval |
| CI | GitHub Actions + Agents Schema workflows |

## dbt packages included

- `dbt-labs/codegen`
- `dbt-labs/dbt_utils`
- `dbt-labs/dbt_project_evaluator`
- `dbt-labs/audit_helper`

## Prerequisites

- Python 3.12 + `dbt-core` + `dbt-postgres`
- `~/.dbt/profiles.yml` with warehouse credentials
- [GitHub CLI](https://cli.github.com/) (`gh auth login`)
- Postgres (or adapt `project.config.yml` for your adapter)

## More docs

| File | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Main skill orchestrator |
| [references/install-skill.md](references/install-skill.md) | Install options |
| [references/github-repo-resolution.md](references/github-repo-resolution.md) | GitHub owner + repo name |
| [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | Full package stack |

## License

Apache-2.0 (same spirit as dbt Labs agent skills — adjust if you add a LICENSE file).
