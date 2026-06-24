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

If `.env` is missing, create it safely from `.env.example`, stop before discovery or dbt commands, and ask me for DBT_DOMAIN, DBT_PROFILE_NAME, and DBT_SOURCE_SCHEMA. Do not search the repo, inspect terminal output, infer, suggest, or summarize values from other workspaces or previous runs.

First, perform lightweight read-only project discovery only: inspect source schemas/tables, write `reports/agent/discovery_report.md`, update `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md`, summarize what you conclude about the data project, and ask whether I want to add requirements. Keep discovery output focused on source data, entities, relationships, data quality, candidate models/metrics, and open modeling decisions; keep setup details out of the discovery summary except for a short inputs-used note. Do not fully design every layer upfront; run focused discovery again before sources, bronze, silver, gold, semantic, evaluator, and docs phases.

Use Mermaid for every diagram. For entity relationships, use Mermaid `erDiagram`. Verify every Mermaid diagram you add or change is visible/parseable, and record the result in the phase report.

After I answer, before each build phase, write/update `AGENT_PLAN.md`, explain in Markdown what you will build, and wait for my approval before implementing that phase.

In each discovery summary and phase plan, recommend the best next path with evidence, show what looks right, what is not ready yet, confidence about proven vs uncertain items, and what needs my approval. Do not ask me to design everything from scratch.

In each phase plan, include a Data Engineer Decision Check covering grain, keys, joins, mappings, metrics, privacy, materialization, tests, and validation evidence. Ask me before guessing any decision that affects business meaning, privacy, correctness, cost, or downstream usability.

After each completed phase, write/update `reports/agent/<phase>_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` with what was done, what passed, warnings/failures/skips, assumptions, user decisions, phase outputs, report links, and open decisions.

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

Before building this phase, explain the plan in Markdown with your recommendation, evidence, confidence, risks, and approval needs, then wait for my approval. After it completes, write/update the phase report, pipeline status, and context tree files.
```
