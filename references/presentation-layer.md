# Presentation Layer

Use this after marts, semantic layer, project evaluator, and documentation have completed.

## Purpose

Help the data engineer decide whether the completed dbt project should expose a user-facing presentation layer beyond dbt models and documentation.

The presentation artifact is optional, but the recommendation is required for full pipeline final delivery. Ask the user in simple terms whether they want a presentation layer. Do not ask them to choose "Power BI as code" unless they already used that wording.

Default artifact: if the user approves a presentation layer and does not specify another tool or artifact type, create a Power BI PBIP/TMDL project by default. Do not create dashboards, reports, slides, notebooks, or other business intelligence artifacts unless the user approves the presentation layer.

## Presentation decision gate

After documentation generation in a full pipeline, the agent must stop at this gate and ask the user whether to create a presentation layer. The agent must not mark the full delivery as complete while the presentation decision is still unanswered.

Use these statuses:

| User decision | Required status |
|---|---|
| Not asked yet | `Documentation complete - presentation decision pending` |
| User declines artifact | `Presentation recommendation complete - artifact declined` |
| User approves artifact | `Presentation artifact approved - presentation phase in progress` |
| Artifact completed | `Presentation artifact complete` |
| Artifact blocked | `Presentation artifact blocked` |

If the user approves a presentation layer, treat it as a separate `presentation_layer` phase. Use Power BI PBIP/TMDL as the default artifact unless the user specifies another technology or asks for a Markdown-only guide/report:

1. Write or update `AGENT_PLAN.md` with the exact artifact scope.
2. Confirm the inferred output format in the plan, source models, metrics, privacy rules, and validation method.
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
| Power BI PBIP/TMDL project | Default when the user says yes to presentation layer and does not specify another technology | Complete PBIP project, semantic model, report artifact, relationships, measures, parameters, report pages, and open/refresh notes |
| Semantic layer first | Metrics need governed definitions before dashboards | MetricFlow metrics, entities, dimensions, time dimensions, safe denominators |
| Export/query handoff | The user wants to query marts manually | Final schemas, sample SQL, model grains, recommended joins |

## Artifact type distinction

Do not treat Markdown instructions, DAX snippets, relationship notes, or dashboard page descriptions as **Power BI as code**.

These are different deliverables:

| User asks for | Required deliverable |
|---|---|
| Presentation layer, with no technology specified | A complete Power BI PBIP/TMDL project by default |
| Power BI, PBIP, TMDL, or a Power BI Desktop file/project | A complete PBIP project that Power BI Desktop can open, with report and semantic model artifacts |
| Dashboard design | Markdown design/specification only, unless the user later approves PBIP creation |
| Presentation layer report | Markdown report only |
| Query handoff | SQL examples and model-grain guide only |

If the user approves the default presentation layer, the agent must create PBIP/TMDL files, not only explain what to do manually.

## Required recommendation section

Add this section to the final handoff and final report:

```markdown
## Presentation Layer Recommendation

Recommended option: <Power BI PBIP/TMDL project / dbt documentation only / presentation layer report / dashboard design / semantic layer first / export or query handoff>

Why:
- <evidence from final marts, metrics, data quality, and user goals>

Possible key performance indicators and metrics:
- <metric name>: <business meaning, source model, grain, numerator, denominator, filters, time field, and caveat>

Suggested presentation pages:
- <page name>: <purpose, primary metrics, filters, and source models>

Not ready yet:
- <missing metric definition, empty source table, privacy approval, or data quality concern>

Decision needed:
- Do you want me to create the presentation layer now?
```

## Ask the user

Ask clearly after final validation:

```text
Documentation and dbt validation are complete. Before I close delivery, do you want me to create a presentation layer artifact?

Recommended default: Power BI Desktop presentation layer as code, using a PBIP/TMDL project with report pages and a semantic model.

Reply "yes" to use the default Power BI project, "no" to stop at dbt documentation, or name another option such as Markdown report, dashboard design only, semantic layer refinement, or query handoff.
```

Do not force the user to choose all options. Recommend the best next option based on the project evidence.

If the user says yes without specifying a technology, infer Power BI PBIP/TMDL as the approved default, create the presentation-layer phase plan, and wait for approval when required by [phase-plan-approval.md](phase-plan-approval.md). Do not ask the user to say "Power BI as code" explicitly. Do not answer only with advice when the user approved artifact creation.

If the recommendation cannot be produced, mark it `BLOCKED` or `SKIPPED` with the exact reason in the final report, pipeline status, context tree, and final response. Do not silently omit the presentation-layer section.

## Guardrails

- Do not invent key performance indicators that are not supported by final marts or approved semantic metrics.
- Do not recommend advanced key performance indicators unless numerator, denominator, filters, time field, source model, and caveats are known or clearly marked as deferred.
- Prefer Kimball-style star schemas for Power BI and downstream presentation. Strongly discourage flat/wide-only presentation models and snowflake schemas inside Power BI when dbt can expose a simpler star schema.
- Check whether approved dbt bridge tables are needed in the Power BI semantic model. Use bridge tables for true many-to-many filtering or allocation; avoid Power BI many-to-many relationships and bidirectional filters unless there is a documented reason.
- For Power BI PBIP/TMDL artifacts only, validate relationship paths before handoff. A Power BI semantic model must not contain multiple active filter paths between the same two presentation entities. For example, do not allow both `customers -> orders -> order_items -> products` and `customers -> order_items -> products` to be active. Choose one canonical path, remove the shortcut relationship, make the shortcut inactive only when there is a documented measure need, or create a proper bridge/aggregate model.
- Recommend Import mode for smaller curated marts where refresh latency is acceptable; recommend DirectQuery or Composite models only when data volume, freshness, governance, or warehouse compute requirements justify them.
- Recommend dbt aggregate tables for high-level dashboards and Power BI aggregation behavior when detailed facts are too large or expensive for repeated dashboard scans.
- Do not expose sensitive fields, personally identifiable information, or protected health information in presentation outputs unless approved.
- Do not build dashboards from empty or unvalidated facts without clearly marking them as placeholders.
- Prefer semantic metrics over duplicated dashboard-only calculations.
- Include data limitations and confidence notes.
- Use full wording in user-facing summaries.

## Power BI as code guardrails

Use this section when the user explicitly asks for a Power BI project, PBIP, TMDL, or Power BI presentation layer as code, or when the user says yes to the default presentation layer without specifying another technology.

Power BI as code completion means the generated project is intended to open from a `.pbip` file in Power BI Desktop. A folder containing only `import_guide.md`, `relationships.md`, `kpi_measures.dax`, and `dashboard_pages.md` is a useful dashboard design handoff, but it is not Power BI as code and must not be marked complete as such.

When the user provides a detailed Power BI contract, copy the contract into the presentation phase plan and validate against every item. Do not generalize away user-provided table names, relationship rules, measure labels, report page names, output paths, schema versions, or known technical fixes.

## Power BI validation workflow

For Power BI PBIP/TMDL artifacts, never accept "files created" as done. The presentation phase can be marked complete only after the validation loop passes or a required external validation step is explicitly unavailable and documented as not run.

Required loop:

1. Build the PBIP/TMDL artifact.
2. Run static file validation: file tree, JSON parsing, TMDL structure, path links, relationship ambiguity audit, and partition/source checks.
3. Self-test the semantic model using the Power BI Modeling Model Context Protocol tools when available:
   - `ConnectFolder` against the SemanticModel definition folder.
   - `ListConnections` or `GetConnection` to confirm the model connection loaded.
   - Table and relationship operations to confirm expected tables, columns, and relationships exist.
   - DAX query operation with a smoke query such as `EVALUATE ROW("test", 1)`.
4. If Power BI Desktop is available, open or launch the `.pbip` and confirm it loads without project definition or relationship-path errors.
5. If any step fails, fix the PBIP/TMDL files and repeat the validation loop.
6. Only after passing validation, update `reports/agent/presentation_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` with `PASS`.

Do not mark the presentation phase complete if the user would see an error when opening the `.pbip`.

If the Power BI Modeling Model Context Protocol tools are unavailable in the current environment, mark the Model Context Protocol load test as `NOT RUN` with the exact reason. Do not claim the semantic model loaded through Model Context Protocol. If Power BI Desktop is unavailable, mark Desktop open validation as `NOT RUN` with the exact reason. If either validation is required by the user's contract and cannot be run, mark the presentation phase `BLOCKED`, not `PASS`.

## Power BI self-test checklist

Before handoff, paste the validation results into the chat result summary and `reports/agent/presentation_report.md`:

| Check | What to verify |
|---|---|
| File tree | `.pbip`, Report folder, SemanticModel folder, `definition.pbism`, `database.tmdl`, `model.tmdl`, and `report.json` exist where expected |
| JSON parse | All `.json` files parse cleanly |
| Path links | `.pbip` links to the Report artifact, and the Report artifact links to the SemanticModel artifact using correct relative paths |
| Relationships | No ambiguous active paths; approved active/inactive relationship rules are followed |
| Partitions | Import or source queries point to real approved gold/mart tables |
| Power BI Modeling Model Context Protocol load | `ConnectFolder` to the SemanticModel definition folder succeeds |
| Power BI Modeling Model Context Protocol inspection | Connections, tables, columns, relationships, and a simple DAX smoke query succeed |
| Power BI Desktop open | `.pbip` opens without load errors when Desktop is available |

If Power BI Desktop open fails after handoff, the agent must use the pasted error message as a blocker, fix the artifact, rerun static validation, rerun the relationship ambiguity audit, rerun the Power BI Modeling Model Context Protocol `ConnectFolder` test, rerun Desktop open validation when available, and update `reports/agent/presentation_report.md` with the fix and retest results.

Before creating files:

- Confirm the final dbt gold/mart tables exist and have passed the relevant dbt build.
- Write or update `AGENT_PLAN.md` with the Power BI artifact plan and wait for approval.
- Confirm output location, model name, connection source, presentation pages, measures, and privacy rules.
- In the plan, state that Power BI PBIP/TMDL is the default because no other presentation technology was specified. Ask for changes only if the user wants a different technology or a Markdown-only guide.
- If a known-good PBIP project exists in the workspace and the user allows it as a reference, inspect its folder structure and metadata patterns before writing new files.
- When the user names required source schemas or gold tables, verify those tables exist before wiring import queries or partitions.

When creating PBIP:

- Create a complete PBIP project, not only loose TMDL text.
- Include the `.pbip` file, a Report artifact folder, and a SemanticModel artifact folder.
- Ensure the `.pbip` file points to a Report artifact when a report is requested, not only to a semantic model.
- Ensure the Report artifact has a definition file that links to the SemanticModel artifact using the correct relative path.
- Keep TMDL under the SemanticModel definition folder using the expected artifact layout for the chosen Power BI project format.
- Create report definition files for the approved pages and visuals when the user asked for clickable/openable Power BI pages. Do not replace report pages with `dashboard_pages.md`.
- Use parameters for host, database, schema, warehouse, or equivalent connection values instead of hardcoding environment-specific values where practical.
- Define relationships from the approved star schema and avoid ambiguous relationship paths. Prefer one active route from each dimension to each fact area. Avoid convenience relationships from a dimension directly to a lower-grain fact when that lower-grain fact is already reachable through its parent fact.
- For parent-child fact designs, connect lower-grain satellite facts to the parent fact only when that is the approved canonical route, and do not also add direct active dimension shortcuts that create ambiguous paths.
- Use inactive relationships only for approved role-playing dates or alternate analysis paths, and document the measure pattern needed to activate them.
- Include approved bridge tables and their relationship directions when the gold layer contains bridge models or the approved presentation scope requires many-to-many analysis.
- Put reusable business calculations in a measures table or equivalent semantic model construct.
- Use simple user-facing measure labels and keep technical column names inside model definitions.
- When the user supplies exact measure labels, use those labels exactly unless the expression cannot be supported by the validated marts.
- Use supported PBIP/TMDL metadata versions for the target Power BI Desktop release. Known requirements from prior failures include `definition.pbism` using the semantic model definition-properties schema path, `database.tmdl` using `compatibilityLevel: 1605` when requested, `model.tmdl` table references at the root level when the chosen structure requires it, and `report.json` values such as `themeCollection.baseTheme.reportVersionAtImport` typed exactly as Power BI expects.
- Add a local `powerbi/README.md` or equivalent handoff with open, refresh, and reload-from-disk guidance.
- Do not tell the user to overwrite the generated project by saving from Power BI Desktop as the default fix. For reload-from-disk edits, instruct the user to close without saving when that is the safe workflow.

Validation before handoff:

- Verify every required PBIP, report, semantic model, definition, relationship, table, partition, and measure file exists.
- Parse JSON files with a real parser.
- Check TMDL indentation and root-level object placement against the selected PBIP structure.
- Verify the `.pbip` points to the report artifact and the report points to the semantic model artifact.
- Verify approved report pages exist as Power BI report definition artifacts, not only Markdown page descriptions.
- Verify user-provided technical requirements exactly, including output path, artifact folder names, schema strings, compatibility level, parameter names, import partition source, relationship direction/activity, measure labels, report page names, and expected visuals.
- For Power BI PBIP/TMDL artifacts, run a relationship ambiguity audit before handoff. Build a simple graph of active relationships and confirm there is no pair of dimensions or presentation entities connected by more than one active path through facts, bridge tables, or snowflaked dimensions. Record the checked paths and result in `reports/agent/presentation_report.md`.
- For Power BI PBIP/TMDL artifacts, run Power BI Modeling Model Context Protocol self-tests when tools are available: `ConnectFolder`, connection inspection, table inspection, relationship inspection, and a simple DAX smoke query. Treat `ConnectFolder` failure as a failed presentation phase and fix the artifact before handoff.
- Compare key metadata paths and schema fields against a known-good local reference when one is available.
- Re-run a file-tree check after edits and include the result in the phase report.
- If Power BI Desktop is available on the machine and the deliverable is meant to be opened in Power BI Desktop, launch the `.pbip` as a validation step after text validation. Treat a Desktop load error, including ambiguous relationship path errors, as a failed presentation phase. Fix and re-test before marking the artifact complete. If Desktop is unavailable or cannot be launched in the current environment, mark the artifact as `Presentation artifact created - Desktop open validation not run`, explain why, and do not imply it was opened successfully.

## Power BI done gate

The final "work is done" update for a Power BI PBIP/TMDL artifact must use this shape:

```text
Presentation layer: COMPLETE

PBIP path: <path>
File validation: PASS
Relationship audit: PASS (no ambiguous paths)
Power BI Modeling Model Context Protocol model load: PASS
Power BI Desktop open test: PASS
Report: reports/agent/presentation_report.md
Pipeline status: reports/agent/PIPELINE_STATUS.md
```

If Desktop validation was not run, do not say the project opens successfully. Say:

```text
Power BI Desktop open validation: NOT RUN (reason: <reason>). Please open and confirm, or rerun validation when Desktop is available.
```

If Model Context Protocol validation was not run, do not say the semantic model loaded successfully. Say:

```text
Power BI Modeling Model Context Protocol validation: NOT RUN (reason: <reason>).
```

Do not:

- Create a dataset-only PBIP when the user asked for a report.
- Mark Markdown, DAX text, relationship notes, or an import guide as a completed Power BI as code artifact.
- Create direct relationships that introduce ambiguous filter paths when a safer snowflake path exists.
- Mark a Power BI artifact complete when the Power BI Modeling Model Context Protocol `ConnectFolder` test fails.
- Mark a Power BI artifact complete when Power BI Desktop reports ambiguous relationship paths or any project definition load error.
- Hardcode one domain's table names, measures, or report pages into the skill.
- Tell the user to save over the generated files from Power BI Desktop as the default reload strategy.
- Mark the Power BI artifact complete if the structure is incomplete or validation was not run.
