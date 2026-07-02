# Final Delivery Checklist

Use this before calling a dbt pipeline complete.

## Presentation gate before completion

Do not call a full pipeline complete immediately after documentation or analytics insight reporting. Full delivery can be marked complete only after analytics insight reporting outputs exist and the presentation-layer gate in [presentation-layer.md](presentation-layer.md) has one of these outcomes:

- Presentation recommendation was produced and the user declined artifact creation.
- Presentation recommendation was produced, the user approved an artifact, and the presentation artifact phase completed.
- Presentation recommendation was produced, the user approved an artifact, and the artifact is explicitly blocked with evidence.
- The user explicitly asked to stop after documentation or after analytics insight reporting.

If analytics insight reporting is not complete, set status to `Documentation complete - analytics insight reporting pending` and run [analytics-insight-reporting.md](analytics-insight-reporting.md) before the presentation question.

When a presentation artifact is approved, final delivery is not allowed until that presentation phase reaches one of these recorded states in `reports/agent/10_presentation/presentation_report.md` and `reports/agent/PIPELINE_STATUS.md`:

- `PASS`: all required artifact validation completed and evidence is recorded.
- `BLOCKED`: validation failed or could not run, the exact blocker is recorded, and the user is told delivery is blocked.
- `SKIPPED`: the user explicitly cancelled or declined the presentation artifact.

Do not use `Delivery complete` while Power BI PBIP/TMDL static checks, Model Context Protocol load checks, DAX smoke tests, or Desktop open validation are still pending.

If the presentation decision has not been asked or answered, set status to `Analytics insight reporting complete - presentation decision pending` and ask the presentation-layer question. Do not write `Delivery complete`, `final completed state`, or equivalent close-out language yet.

## Deliverables

- Source YAML generated from real source schema
- Discovery report and requirements file produced before build planning
- Staging, intermediate, and mart models built successfully
- Tests added for primary keys, relationships, accepted values, and mapping coverage where applicable
- Semantic layer or metrics added on final mart models when requested
- dbt documentation generated
- Analytics insight reporting outputs created under `reports/agent/`: `analytics_insight_report.md`, `kpi_discovery_matrix.md`, `reporting_catalog.md`, `kpi_catalog.md`, `dashboard_spec.md`, `insight_backlog.md`, `reporting_readiness_scorecard.md`, and `analytics_insight_reporting_report.md`
- Key performance indicator reconciliation outputs created when key performance indicators are approved or implemented: `kpi_reconciliation_report.md`, `kpi_lineage_proofs.md`, `kpi_variance_report.md`, and `kpi_sql_proofs/`
- Cardinality and grain outputs created when relationships, joins, final models, or Power BI relationships exist: `cardinality_report.md`, `relationship_profile.md`, `join_safety_report.md`, and `grain_validation_report.md`
- Project evaluator run and warnings summarized
- Presentation layer recommendation produced after final validation, with user-facing options and suggested metrics
- Advanced data-engineering review completed before final delivery
- Agents Schema workflow prepared after `target/manifest.json` exists, when supported by the warehouse destination
- Continuous integration workflow prepared when GitHub automation is requested
- Commits created by phase
- `AGENT_PLAN.md` records approved phase plans and short phase results
- `reports/agent/` contains phase reports, `PIPELINE_STATUS.md`, `CONTEXT_TREE.md`, and `NEXT_PHASE_PROMPT.md`
- `reports/agent/final_delivery.md` records the final delivery status, validation evidence, presentation gate outcome, open decisions, and next actions
- When Power BI is approved, `reports/agent/10_presentation/powerbi_model_plan.md`, `reports/agent/10_presentation/dashboard_pages.md`, and `reports/agent/10_presentation/dax_measures.md` capture the Power BI-ready star schema handoff, semantic model plan, report page plan, and DAX measure specifications

## README or handoff notes

Update or create project handoff notes with:

- Domain and source schema used
- dbt profile name used, without secrets
- Layer names and physical schema naming
- Schema isolation status, including evaluator/seeds/snapshots schemas and whether source schema stayed clean
- Important source tables
- Source discovery conclusions and requirements captured before build
- Link to `reports/agent/00_discovery/requirements.md` with source-derived requirements, evidence, confidence, recommended defaults, open questions, and deferred or blocked scope
- Final facts, dimensions, marts, and metrics
- Bridge table decisions: built, not needed, deferred, or blocked
- Key performance indicator definitions with numerator, denominator, filters, time field, source model, caveats, validation evidence, and approval status
- Key performance indicator discovery matrix status: table classification, grain, archetype, confidence score, targeted questions, trusted metrics, and deferred or blocked metrics
- Key performance indicator reconciliation proof status: source, bronze, silver, gold, semantic, and Power BI proof files where applicable; first failing layer; variance; and recommended debugging action
- Cardinality and relationship-grain status: duplicate keys, null keys, row multiplication, row loss, join safety, bridge table decisions, and Power BI one-side key readiness
- Metric verification results for every implemented key performance indicator: expected numerator, actual numerator, expected denominator, actual denominator, expected result, actual result, status, and evidence
- Presentation layer recommendation, including possible key performance indicators, semantic metrics, suggested report or dashboard pages, and query handoff options
- Consultant-grade presentation design summary when a presentation artifact was approved: pages created, pages deferred or blocked, source models, measures, slicers, filters, privacy handling, and why the selected visuals are useful for business review
- Five report pillars status for business-facing reports and presentation artifacts: context and strategy, key performance indicators, trend analysis and variance, insights and attribution, and recommendations and next steps
- Power BI canvas standard status when Power BI is created: header/navigation, last refreshed timestamp, reset filters, prioritized executive key performance indicator cards, supporting key performance indicator coverage, slicers, trends/comparisons, detail layer, tooltips, drill-throughs, Report Information page, and any unsupported elements with reasons
- Report Information page summary when Power BI is created: purpose, audience, data source, refresh details, page guide, key performance indicator definitions, filter definitions, caveats, privacy handling, validation summary, and open decisions
- Standard time showcase status for presentation artifacts: fact date columns discovered, time visuals included or blocked, and SQL verification evidence
- Project knowledge used, including `project_rules`, `AGENT_KNOWLEDGE.md`, `docs/dbt_knowledge.md`, `docs/business_rules.md`, `.agents/project_knowledge.md`, or context tree decisions when present
- Matplotlib presentation status when used as the default or requested presentation technology, including prerequisite install status, `kpi_figure_coverage.md` completeness, figure generation, SQL verification, and blocked visuals
- Power BI PBIP/TMDL status when explicitly chosen as the presentation technology, including PBIP structure validation and open/refresh notes
- Power BI template status when used: bundled template path or generator fallback, generator command, planning inputs consumed, regenerated logical IDs/lineage tags, local reference PBIP approval if any, and proof that no credentials or local business content were copied
- Power BI Modeling Model Context Protocol status when Power BI is created: availability check, install attempt or install recommendation, tools used, `ConnectFolder` result, inspection result, DAX smoke test result, and any reason validation was blocked or not run
- Known empty tables or data quality limitations
- Confidence notes: what was validated vs what still needs confirmation
- Mermaid diagrams created or updated, with visibility verification status
- Incremental, snapshot, exposure, and privacy decisions
- How to run `dbt build`, `dbt docs generate`, and `dbt docs serve`
- What still needs business review
- Which phase plans were approved before build
- Links to phase reports showing what was done, correct, warning, failed, and open
- Link to `reports/agent/CONTEXT_TREE.md` for reusable project context

## Final validation

Run:

```powershell
dbt parse --no-partial-parse
dbt build
dbt docs generate
```

If a full `dbt build` is too expensive, explain why and run the most complete safe build.

For local documentation viewing after `dbt docs generate`:

```powershell
dbt docs serve --host 127.0.0.1 --port 8080
```

If the agent starts docs serving, do it as a non-blocking/background process and report the URL.

## Final response

Always start with a concise user-facing summary before detailed handoff notes.

Use this order:

### Short summary

In 3-6 lines, say:

- Whether the pipeline or requested phase completed successfully
- What domain/source was used
- Which layers/models were created or changed
- Whether validation passed
- Whether anything important still needs user review

### Results

Use a compact table when helpful:

| Area | Result |
|---|---|
| Project | `<dbt_project_name>` in `<dbt_project_root>` |
| Profile | `<dbt_profile_name>` |
| Domain | `<domain>` |
| Source | `<source_schema>` / `<source_name>` |
| Layers | `<layer_1>` -> `<layer_2>` -> `<layer_3>` |
| Schemas | `<schema_1>`, `<schema_2>`, `<schema_3>` |
| Evaluator schema | `<layer_schema_prefix>_evaluator` |
| Plan file | `AGENT_PLAN.md` |
| Phase reports | `reports/agent/` |
| Context tree | `reports/agent/CONTEXT_TREE.md` |
| Next-phase prompt | `reports/agent/NEXT_PHASE_PROMPT.md` |
| Git | `<commit/push status>` |

### What changed

- Files/layers created
- Important models created by layer
- Semantic models and metrics added
- Presentation layer recommendation and whether the user approved any follow-up artifact
- Presentation artifact type: Matplotlib report figures, Power BI PBIP/TMDL project, dashboard design guide, presentation report, or query handoff
- Five report pillars covered or deferred: context and strategy, key performance indicators, trend analysis and variance, insights and attribution, and recommendations and next steps
- Power BI canvas standard coverage when Power BI is created: navigation/header, refresh timestamp, reset filters, prioritized executive key performance indicator cards, supporting key performance indicator coverage, slicers, trend/comparison visuals, matrix/detail layer, tooltips, drill-through pages, and Report Information page
- Standard time showcase pages or visuals created, including last calendar year, year to date, last 12 months, by-year, and by-month coverage where supported
- Advanced data-engineering review result
- Continuous integration or Agents Schema workflow changes
- Mermaid diagrams created or updated
- Documentation generated and documentation serve URL when started

### Validation results

- Build and documentation results
- Project evaluator result
- Schema isolation check result
- Profile target schema hygiene result
- Key performance indicator definition status
- Key performance indicator discovery status: `kpi_discovery_matrix.md` exists, includes confidence scoring, and only `HIGH` or approved `MEDIUM` metrics were promoted
- Metric verification status: expected versus actual numerator, denominator, filter logic, semantic result, presentation result, and unreconciled metrics
- Key performance indicator reconciliation status: source-to-final proof chain, first failing layer, variance percentage, proof file paths, and blocked metrics
- Cardinality validation status: grain validation, relationship cardinality, join safety, row multiplier, row loss, and Power BI one-side key uniqueness/not-nullness
- Bridge table review status
- Key pass/warn/fail counts when available
- Phase plan approval status
- Phase report status and path
- Next-phase prompt status and path
- Power BI PBIP/TMDL validation status when used: file validation, relationship ambiguity audit, Power BI Modeling Model Context Protocol model load, DAX smoke test, Desktop open test, and unresolved load errors
- Power BI TMDL parser safety status when used: no bare M steps at TMDL root, no invalid linguistic metadata content-type mismatch, no JSON payload such as `{ "Version": "1.0.0" }` inside XML-typed metadata
- Power BI template/generator status when used: bundled template found or fallback used, `dashboard_spec.md` and `kpi_catalog.md` consumed or blocked, no credentials found, no duplicate lineage tags, and local PBIP references approved before use
- Power BI Modeling Model Context Protocol availability status: checked, available and used, unavailable with install path, unavailable with reason, or failed
- Presentation time showcase validation status: discovered fact date fields, governed measures used, SQL verification queries, and any blocked trend visuals
- Presentation delivery gate result: `PASS`, `BLOCKED`, `SKIPPED`, or `PENDING`; never omit this when a presentation artifact was approved
- Mermaid diagram visibility/parse status when diagrams were created or changed
- Advanced data-engineering review status

### Data notes

- Source row counts and empty tables
- Known data quality limitations
- Important assumptions used
- Confidence: what is proven and what is uncertain
- PII/PHI or sensitive-field decisions

### Git and automation

- Git commit status
- Agents Schema status
- Continuous integration status
- Advanced data-engineering review status

### Open decisions

- Open user decisions
- Any deferred or blocked key performance indicator definitions
- Any unreconciled key performance indicators and the layer where the mismatch was found
- Whether to create a presentation layer artifact such as a business-facing report, dashboard design, semantic layer refinement, or query handoff
- Whether presentation layer recommendation was blocked or skipped, with reason
- Recommended next actions

Keep the final response readable for a new dbt user. Do not bury blockers, failed validation, unsupported Agents Schema destinations, or sensitive-data risks inside long prose.
