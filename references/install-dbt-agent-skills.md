# Install dbt Agent Skills (Automatic Project Setup)

**User does not run this manually.**
Project setup and configuration runs this when `auto_install_dbt_skills: true` (default) and dbt skills are missing.

User only installs:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

## Agent check (bootstrap step 1)

```text
.agents/skills/using-dbt-for-analytics-engineering/SKILL.md exists?
```

If **yes** -> skip, proceed.

If **no** -> agent runs automatically:

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

Do not ask the user to install dbt skills manually unless `npx` fails.

## After install - agent composes with

1. `agentic-dbt-pipeline` (orchestration + GitHub)
2. `using-dbt-for-analytics-engineering`
3. `running-dbt-commands`
4. `building-dbt-semantic-layer`
5. `troubleshooting-dbt-job-errors` *(on failures)*

See also [dbt-packages-and-skills.md](dbt-packages-and-skills.md) for dbt **packages** (`dbt deps`).

## Verify

Confirm at least:

- `using-dbt-for-analytics-engineering`
- `running-dbt-commands`
- `building-dbt-semantic-layer`

Report install result before continuing layer work.
