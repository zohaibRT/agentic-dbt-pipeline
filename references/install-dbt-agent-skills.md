# Install dbt Agent Skills (Mandatory Bootstrap)

The agent **runs this automatically** on every agentic dbt pipeline skill invocation when `auto_install_dbt_skills: true` (default).

## Check first

```text
.agents/skills/using-dbt-for-analytics-engineering/SKILL.md exists?
```

If **yes** → skip install, proceed to layer work.

If **no** → install now (do not ask user to do it manually):

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

Full install (optional):

```bash
npx skills add dbt-labs/dbt-agent-skills
```

## After install — always compose with

1. `agentic-dbt-pipeline` (pipeline orchestration + GitHub)
2. `using-dbt-for-analytics-engineering` (models, tests, docs)
3. `running-dbt-commands` (CLI)
4. `building-dbt-semantic-layer` (MetricFlow / semantic models — after marts)
5. `troubleshooting-dbt-job-errors` (on failures)
6. `adding-dbt-unit-test` (when adding unit tests)

See also [dbt-packages-and-skills.md](dbt-packages-and-skills.md) for dbt **packages** (codegen, dbt_utils, dbt_project_evaluator, audit_helper).

## Verify

List `.agents/skills/` and confirm at least:

- `using-dbt-for-analytics-engineering`
- `running-dbt-commands`
- `building-dbt-semantic-layer`

Report install result to user before continuing.
