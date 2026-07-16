# Install dbt Analytics Engineer Skill

## One command (all you install manually)

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

### Windows / Cursor-only install (recommended when multi-agent copy fails)

Copying this large skill into many agent folders at once can fail on Windows with:

`ENOENT: no such file or directory, mkdir '...templates\\reports\\10_presentation'`

Install into Cursor (and the shared `.agents/skills` folder) only:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline --agent cursor -y
```

If a previous install was partial, remove the broken skill folder and reinstall, or hydrate from git per `SKILL.md` (Local resource hydration). After install, confirm these exist:

```text
.agents/skills/agentic-dbt-pipeline/templates/reports/09_analytics_insights/
.agents/skills/agentic-dbt-pipeline/templates/reports/10_presentation/
.agents/skills/agentic-dbt-pipeline/scripts/run_acceptance_gate.py
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

Skill install does **not** create workspace `.env`. That file is created on the **first agent run** in your workspace or dbt project root.

### Expected files after install

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md
.agents/skills/agentic-dbt-pipeline/references/
.agents/skills/agentic-dbt-pipeline/scripts/
.agents/skills/agentic-dbt-pipeline/agents/
.agents/skills/agentic-dbt-pipeline/project.config.yml
.agents/skills/agentic-dbt-pipeline/prompt.md
.agents/skills/agentic-dbt-pipeline/.env.example
```

You should **not** expect `.env` in the workspace immediately after install.

### First run

1. Open the dbt project workspace in the agent.
2. Run the prompt from `prompt.md`.
3. If `.env` is missing, the agent creates it in the workspace from `.env.example`.
4. Fill `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA` in workspace `.env`.
5. Approve the agent to continue with discovery.

### Anti-patterns to avoid

- Do not tell users to create workspace `.env` before the first prompt.
- Do not expect workspace `.env` immediately after `npx skills add`.
- Do not use skill-folder `project.config.yml` for normal domain/profile/schema settings.
- Do not run discovery or dbt while workspace `.env` is missing or placeholder-only.

### Optional advanced overrides

Edit `.agents/skills/agentic-dbt-pipeline/project.config.yml` only when you need non-default skill behavior. Most users should configure the workspace `.env` instead.
