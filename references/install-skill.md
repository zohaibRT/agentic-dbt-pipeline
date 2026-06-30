# Install dbt Analytics Engineer Skill

## One command (all you install manually)

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Repository: https://github.com/zohaibRT/agentic-dbt-pipeline

**You do not install dbt Agent Skills separately.** On first pipeline run, project setup and configuration installs them automatically when `auto_install_dbt_skills: true` (default):

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

The agent runs that command - not you.

## Then invoke

```text
Use the dbt Analytics Engineer skill (`agentic-dbt-pipeline`).
```

See [prompt.md](../prompt.md) for the full prompt.

## What gets installed when

| What | Who installs | When |
|---|---|---|
| `agentic-dbt-pipeline` | **You** (`npx skills add ...`) | Once, before first use |
| dbt Agent Skills (9 skills) | **Agent** (project setup and configuration) | First run if missing |
| dbt packages (codegen, utils, etc.) | **Agent** (`dbt deps`) | Sources / full pipeline |
| dbt project + layers | **Agent** | Full pipeline |

## Verify

Some versions of `npx skills add` install only `SKILL.md` first. On first use, the skill must hydrate its local resources from the repository into the installed skill folder. After first agent run, verify:

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md
.agents/skills/agentic-dbt-pipeline/references/
.agents/skills/agentic-dbt-pipeline/scripts/
.agents/skills/agentic-dbt-pipeline/agents/
.agents/skills/agentic-dbt-pipeline/project.config.yml
.agents/skills/agentic-dbt-pipeline/prompt.md
.agents/skills/agentic-dbt-pipeline/.env.example
.agents/skills/using-dbt-for-analytics-engineering/SKILL.md
```

## Configure

Edit `.agents/skills/agentic-dbt-pipeline/project.config.yml` after hydration for warehouse, project name, and layer paths.
