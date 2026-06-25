# Presentation Layer

Use this after marts, semantic layer, project evaluator, and documentation have completed.

## Purpose

Help the data engineer decide whether the completed dbt project should expose a user-facing presentation layer beyond dbt models and documentation.

The presentation artifact is optional, but the recommendation is required for full pipeline final delivery. Do not create dashboards, reports, slides, notebooks, or business intelligence artifacts unless the user approves.

## Presentation decision gate

After documentation generation in a full pipeline, the agent must stop at this gate and ask the user whether to create a presentation layer artifact. The agent must not mark the full delivery as complete while the presentation decision is still unanswered.

Use these statuses:

| User decision | Required status |
|---|---|
| Not asked yet | `Documentation complete - presentation decision pending` |
| User declines artifact | `Presentation recommendation complete - artifact declined` |
| User approves artifact | `Presentation artifact approved - presentation phase in progress` |
| Artifact completed | `Presentation artifact complete` |
| Artifact blocked | `Presentation artifact blocked` |

If the user approves a presentation artifact, treat it as a separate `presentation_layer` phase:

1. Write or update `AGENT_PLAN.md` with the exact artifact scope.
2. Confirm the output format, source models, metrics, privacy rules, and validation method.
3. Build only the approved artifact.
4. Validate the artifact.
5. Write or update `reports/agent/presentation_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`.
6. Only then continue to final delivery.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Completed marts, semantic/evaluator/documentation status, final model list, key performance indicator definitions, data quality notes, and privacy decisions |
| Allowed changes | Presentation recommendation report; presentation artifacts only after explicit user approval and a separate `presentation_layer` phase plan |
| Not allowed | Dashboards, reports, slides, notebooks, Power BI projects, guessed measures, or sensitive-field exposure without approval |
| Commands to run | Read-only model/metadata checks and artifact-specific validation only after the user approves artifact creation |
| Completion criteria | Best presentation option is recommended with evidence, possible key performance indicators are listed, caveats are clear, and the user is asked whether to create an artifact |
| Report required | Final report or `reports/agent/presentation_report.md`, plus `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md` |

## What to recommend

Review the final gold/marts models, semantic metrics, source data limitations, documented business rules, and [kpi-definitions.md](kpi-definitions.md). Then recommend presentation options with evidence:

| Option | When to recommend | What to include |
|---|---|---|
| dbt documentation only | The user only needs technical lineage and model docs | `dbt docs generate`, optional `dbt docs serve`, final model list |
| Presentation layer report | The user wants a concise business-facing summary | Key performance indicators, metrics, model grains, suggested analysis pages, limitations |
| Dashboard design | The user wants interactive consumption in a business intelligence tool | Suggested pages, filters, metrics, facts/dimensions, privacy notes |
| Power BI as code | The user explicitly requests a Power BI project artifact | Complete PBIP project, semantic model, report artifact, relationships, measures, parameters, and open/refresh notes |
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
- <metric name>: <business meaning, source model, grain, numerator, denominator, filters, time field, and caveat>

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
Documentation and dbt validation are complete. Before I close delivery, do you want me to create a presentation layer artifact?

I can prepare one of these:

1. dbt documentation only: serve the generated docs locally.
2. Presentation layer report: a concise business-facing Markdown report with final models, metrics, and suggested analysis pages.
3. Dashboard design: recommended dashboard pages, filters, and metric definitions for a business intelligence tool.
4. Power BI as code: a complete PBIP project only after you approve the exact Power BI scope.
5. Semantic layer refinement: review and improve MetricFlow metrics before any dashboard work.
6. Query handoff: sample SQL and model-grain guide for analysts.
```

Do not force the user to choose all options. Recommend the best next option based on the project evidence.

If the user says yes, asks for a report/dashboard/Power BI/query handoff, or chooses one of the options, create the presentation-layer phase plan and wait for approval when required by [phase-plan-approval.md](phase-plan-approval.md). Do not answer only with advice when the user approved artifact creation.

If the recommendation cannot be produced, mark it `BLOCKED` or `SKIPPED` with the exact reason in the final report, pipeline status, context tree, and final response. Do not silently omit the presentation-layer section.

## Guardrails

- Do not invent key performance indicators that are not supported by final marts or approved semantic metrics.
- Do not recommend advanced key performance indicators unless numerator, denominator, filters, time field, source model, and caveats are known or clearly marked as deferred.
- Prefer Kimball-style star schemas for Power BI and downstream presentation. Strongly discourage flat/wide-only presentation models and snowflake schemas inside Power BI when dbt can expose a simpler star schema.
- Recommend Import mode for smaller curated marts where refresh latency is acceptable; recommend DirectQuery or Composite models only when data volume, freshness, governance, or warehouse compute requirements justify them.
- Recommend dbt aggregate tables for high-level dashboards and Power BI aggregation behavior when detailed facts are too large or expensive for repeated dashboard scans.
- Do not expose sensitive fields, personally identifiable information, or protected health information in presentation outputs unless approved.
- Do not build dashboards from empty or unvalidated facts without clearly marking them as placeholders.
- Prefer semantic metrics over duplicated dashboard-only calculations.
- Include data limitations and confidence notes.
- Use full wording in user-facing summaries.

## Power BI as code guardrails

Use this section only when the user explicitly asks for a Power BI project, PBIP, TMDL, or Power BI presentation layer as code.

Before creating files:

- Confirm the final dbt gold/mart tables exist and have passed the relevant dbt build.
- Write or update `AGENT_PLAN.md` with the Power BI artifact plan and wait for approval.
- Confirm output location, model name, connection source, presentation pages, measures, and privacy rules.
- If a known-good PBIP project exists in the workspace and the user allows it as a reference, inspect its folder structure and metadata patterns before writing new files.

When creating PBIP:

- Create a complete PBIP project, not only loose TMDL text.
- Include the `.pbip` file, a Report artifact folder, and a SemanticModel artifact folder.
- Ensure the `.pbip` file points to a Report artifact when a report is requested, not only to a semantic model.
- Keep TMDL under the SemanticModel definition folder using the expected artifact layout for the chosen Power BI project format.
- Use parameters for host, database, schema, warehouse, or equivalent connection values instead of hardcoding environment-specific values where practical.
- Define relationships from the approved star schema and avoid ambiguous relationship paths.
- Put reusable business calculations in a measures table or equivalent semantic model construct.
- Use simple user-facing measure labels and keep technical column names inside model definitions.
- Add a local `powerbi/README.md` or equivalent handoff with open, refresh, and reload-from-disk guidance.

Validation before handoff:

- Verify every required PBIP, report, semantic model, definition, relationship, table, partition, and measure file exists.
- Parse JSON files with a real parser.
- Check TMDL indentation and root-level object placement against the selected PBIP structure.
- Compare key metadata paths and schema fields against a known-good local reference when one is available.
- Re-run a file-tree check after edits and include the result in the phase report.
- If Power BI Desktop is available and the user wants local validation, ask before opening the project; do not require Power BI Desktop for text validation.

Do not:

- Create a dataset-only PBIP when the user asked for a report.
- Create direct relationships that introduce ambiguous filter paths when a safer snowflake path exists.
- Hardcode one domain's table names, measures, or report pages into the skill.
- Tell the user to save over the generated files from Power BI Desktop as the default reload strategy.
- Mark the Power BI artifact complete if the structure is incomplete or validation was not run.
