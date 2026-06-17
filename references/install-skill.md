# Install agentic-dbt-pipeline Skill

## One command (all you install manually)

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Repository: https://github.com/zohaibRT/agentic-dbt-pipeline

**You do not install dbt Agent Skills separately.** On first pipeline run, bootstrap installs them automatically when `auto_install_dbt_skills: true` (default):

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

The agent runs that command — not you.

## Then invoke

```text
Use the agentic-dbt-pipeline skill.
```

See [ONE_SHOT_PROMPT.md](../ONE_SHOT_PROMPT.md) for the full prompt.

## What gets installed when

| What | Who installs | When |
|---|---|---|
| `agentic-dbt-pipeline` | **You** (`npx skills add ...`) | Once, before first use |
| dbt Agent Skills (9 skills) | **Agent** (bootstrap) | First run if missing |
| dbt packages (codegen, utils, etc.) | **Agent** (`dbt deps`) | Sources / full pipeline |
| dbt project + layers | **Agent** | Full pipeline |

## Verify

After first agent run:

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md
.agents/skills/using-dbt-for-analytics-engineering/SKILL.md
```

## Configure

Edit [project.config.yml](../project.config.yml) for warehouse, project name, and layer paths.
