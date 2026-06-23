# Discovery & Requirements Checkpoint

Use this as the first phase for a new dbt project or full pipeline request.

## Goal

Analyze the available source schemas and explain what the agent understands before planning any build work.

This phase is read-only. Do not create dbt projects, install packages, run codegen, write model files, create warehouse schemas, or change profiles during discovery.

Do not start discovery until the active `domain`, `dbt_profile_name`, and `source_schema` are confirmed from the prompt or `.env`. If `.env` is missing, follow [env-configuration.md](env-configuration.md) and stop for user input first. Sibling projects and prior workspaces are hints only, not authorization to choose a source schema, and not a reason to run discovery.

## Allowed read-only actions

- Load `.env` and non-secret config values
- Confirm the selected dbt profile name and adapter
- Run `dbt debug` only when a dbt project/profile already exists and the command is needed to verify read-only access
- Inspect source schemas, tables, columns, and row counts
- Check candidate primary keys, foreign keys, date columns, measures, status/code columns, and empty tables
- Inspect existing project files if the project already exists

## Discovery summary

After discovery, explain in Markdown:

- Resolved config: domain, dbt profile, source schema, inferred project name, inferred source name, inferred layer schemas
- Source schemas/tables found and row counts
- Important entities and likely relationships
- Candidate business processes, such as appointments, encounters, claims, orders, tickets, or events
- Candidate facts, dimensions, and metrics implied by the source
- Empty tables, suspicious columns, missing keys, date ranges, and data quality notes
- Privacy/sensitive-field observations
- What the agent is confident about
- What the agent is not confident about

## Requirements checkpoint

Before creating the bootstrap/init plan, ask whether the user wants to add or change requirements.

Use this wording:

```text
Discovery is complete. I have not built or changed anything yet.

Here is what I concluded from the source data:
<short Markdown summary>

Before I plan the dbt build, do you want to add any requirements?
Examples: field mappings, columns to exclude, metric definitions, privacy rules, naming rules, facts/dimensions to prioritize, or tables to ignore.

Reply with your requirements, or reply "continue" and I will prepare the Bootstrap & Init plan for approval.
```

If the user replies `continue`, `no changes`, `go ahead`, or similar, proceed to [phase-plan-approval.md](phase-plan-approval.md) for Bootstrap & Init.

If the user provides requirements, add them to the plan as `project_rules` and use them in later phases.

## Do not

- Treat discovery as approval to build.
- Ask for commit approval during discovery because no files should change.
- Skip the requirements checkpoint on a new full pipeline.
- Hide inferred business logic. Explain what was inferred and what still needs confirmation.

After discovery is summarized, create `reports/agent/discovery_report.md` and update `reports/agent/PIPELINE_STATUS.md` if a project root already exists. If the dbt project root does not exist yet, include the discovery report content in chat and create the file during Bootstrap & Init.
