# Code Agent Setup

What the agent needs before dbt pipeline work.

## Access requirements

- [ ] dbt project folder: `{project.root}`
- [ ] dbt profile name: prompt `dbt_profile_name` or configured `project.profile`
- [ ] dbt CLI: active environment `dbt`; fallback rules in [validation-commands.md](validation-commands.md)
- [ ] Python 3.12 venv with `dbt-core` + the adapter package for the selected dbt profile
- [ ] Warehouse credentials via `~/.dbt/profiles.yml` - never in repo
- [ ] `agentic-dbt-pipeline` skill installed - [install-skill.md](install-skill.md)
- [ ] dbt-labs skills installed - [install-dbt-agent-skills.md](install-dbt-agent-skills.md)

## Agent behavior rules

1. Run [bootstrap.md](bootstrap.md) **first** on every invocation (`auto_bootstrap: true` default).
2. Install dbt-labs skills automatically if missing - do not tell user to install manually.
3. Run `dbt deps` + codegen during sources phase - do not tell user to run manually.
4. Create CI + Agents Schema workflow files during full pipeline.
5. Read `project.config.yml` and [skill-inputs.md](skill-inputs.md).
6. Run [validation-commands.md](validation-commands.md) after edits.
7. Commit each layer separately - [git-workflow.md](git-workflow.md).
8. Ask before production changes and before git push.

## Session start checklist

```text
1. Load project.config.yml
2. Confirm dbt debug passes (or run init phase)
3. Confirm `dbt_profile_name` if multiple profiles exist, then resolve the adapter package from that selected profile
4. Confirm workflow_phase and commit mode from user prompt
4. Compose with using-dbt-for-analytics-engineering + running-dbt-commands
```
