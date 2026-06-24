# Presentation Layer

Use this after marts, semantic layer, project evaluator, and documentation have completed.

## Purpose

Help the data engineer decide whether the completed dbt project should expose a user-facing presentation layer beyond dbt models and documentation.

The presentation layer is optional. Do not create dashboards, reports, slides, notebooks, or business intelligence artifacts unless the user approves.

## What to recommend

Review the final gold/marts models, semantic metrics, source data limitations, and documented business rules. Then recommend presentation options with evidence:

| Option | When to recommend | What to include |
|---|---|---|
| dbt documentation only | The user only needs technical lineage and model docs | `dbt docs generate`, optional `dbt docs serve`, final model list |
| Presentation layer report | The user wants a concise business-facing summary | Key performance indicators, metrics, model grains, suggested analysis pages, limitations |
| Dashboard design | The user wants interactive consumption in a business intelligence tool | Suggested pages, filters, metrics, facts/dimensions, privacy notes |
| Semantic layer first | Metrics need governed definitions before dashboards | MetricFlow metrics, entities, dimensions, time dimensions, safe denominators |
| Export/query handoff | The user wants to query marts manually | Final schemas, sample SQL, model grains, recommended joins |

## Required recommendation section

Add this section to the final handoff and final report:

```markdown
## Presentation Layer Recommendation

Recommended option: <dbt documentation only / presentation layer report / dashboard design / semantic layer first / export or query handoff>

Why:
- <evidence from final marts, metrics, data quality, and user goals>

Possible key performance indicators and metrics:
- <metric name>: <business meaning, source model, grain, and caveat>

Suggested presentation pages:
- <page name>: <purpose, primary metrics, filters, and source models>

Not ready yet:
- <missing metric definition, empty source table, privacy approval, or data quality concern>

Decision needed:
- Do you want me to create a presentation layer artifact now?
```

## Ask the user

Ask clearly after final validation:

```text
The dbt pipeline is complete. Do you want a presentation layer next?

I can prepare one of these:

1. dbt documentation only: serve the generated docs locally.
2. Presentation layer report: a concise business-facing Markdown report with final models, metrics, and suggested analysis pages.
3. Dashboard design: recommended dashboard pages, filters, and metric definitions for a business intelligence tool.
4. Semantic layer refinement: review and improve MetricFlow metrics before any dashboard work.
5. Query handoff: sample SQL and model-grain guide for analysts.
```

Do not force the user to choose all options. Recommend the best next option based on the project evidence.

## Guardrails

- Do not invent key performance indicators that are not supported by final marts or approved semantic metrics.
- Do not expose sensitive fields, personally identifiable information, or protected health information in presentation outputs unless approved.
- Do not build dashboards from empty or unvalidated facts without clearly marking them as placeholders.
- Prefer semantic metrics over duplicated dashboard-only calculations.
- Include data limitations and confidence notes.
- Use full wording in user-facing summaries.
