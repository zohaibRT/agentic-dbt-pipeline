# dbt Pipeline Prompt

Install once:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Create `.env` from `.env.example` and fill the project settings there. Then use this prompt.

## Recommended Prompt

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Build the dbt project using the settings from `.env`.
Run the full pipeline from source discovery through final delivery.

First, perform read-only discovery only: inspect source schemas/tables, summarize what you conclude from the data, and ask whether I want to add requirements.

After I answer, before each build phase, write/update `AGENT_PLAN.md`, explain in Markdown what you will build, and wait for my approval before implementing that phase.

Ask me only when required `.env` values are missing, credentials or secrets are needed, a business rule is unclear, phase build approval is needed, or before committing, pushing, or changing schema behavior.
```

## Optional Project Rules

Add this only when the project has business-specific rules, mappings, joins, or privacy requirements.

```text
Project rules:
- Field mappings:
  - <source_table.source_column> -> <target_column>: <meaning/rule>
- Joins:
  - <left_table.column> -> <right_table.column>: <relationship>
- Metrics:
  - <metric_name>: <definition, grain, filters>
- Exclusions:
  - <tables/columns/records to ignore>
- Privacy:
  - <PII/PHI handling, masking, or exclusion rules>
- Naming:
  - <custom naming conventions>
- Special instructions:
  - <anything else the agent must follow>
```

If a rule is unclear, the agent should ask before modeling it.

## Single Phase

Use this only when you want one part of the workflow:

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Use settings from `.env`.
workflow_phase: <init | sources | staging | intermediate | marts | semantic_layer | project_evaluator | docs | ci | agents_schema>

Before building this phase, explain the plan in Markdown and wait for my approval.
```
