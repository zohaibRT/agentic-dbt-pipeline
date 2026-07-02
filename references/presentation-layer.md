# Presentation Layer

Use this after marts, semantic layer, project evaluator, documentation, and **analytics insight reporting** have completed.

For approved Power BI PBIP/TMDL artifacts, also read [powerbi-template.md](powerbi-template.md), [powerbi-thin-model-template.md](powerbi-thin-model-template.md), [powerbi-kpi-dax-tooling.md](powerbi-kpi-dax-tooling.md), [powerbi-official-docs.md](powerbi-official-docs.md), and [powerbi-pbip-desktop-requirements.md](powerbi-pbip-desktop-requirements.md). Those references contain the bundled template flow, thin model template workflow, key performance indicator and DAX ownership rules, optional Power BI tooling guidance, official Microsoft documentation links, Desktop-load guardrails for enhanced PBIR layout, `.platform` metadata, TMDL syntax, page visual inventory, and validation gates.

Read [analytics-insight-reporting.md](analytics-insight-reporting.md) first. The presentation layer consumes analytics insight outputs:

| Analytics insight output | Presentation use |
|---|---|
| `reports/agent/09_analytics_insights/dashboard_spec.md` | Page plan |
| `reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md` | Key performance indicator candidate evidence, confidence, and blocked/deferred reasoning |
| `reports/agent/09_analytics_insights/kpis/kpi_reconciliation_report.md` | Source-to-final metric proof, variance, and pass/fail evidence |
| `reports/agent/kpi_lineage_proofs.md` | First failing layer and lineage summary for trusted or blocked metrics |
| `reports/agent/kpi_variance_report.md` | Variance evidence for report caveats and blocked visuals |
| `reports/agent/09_analytics_insights/kpis/kpi_catalog.md` | Measure and key performance indicator source |
| `reports/agent/09_analytics_insights/reporting_catalog.md` | Report/page scope |
| `reports/agent/insight_backlog.md` | Blocked or deferred visuals |
| `reports/agent/reporting_readiness_scorecard.md` | Validation gate before artifact build |
| `reports/agent/09_analytics_insights/analytics_insight_report.md` | Business-facing rationale |

The presentation layer must not invent pages, key performance indicators, visuals, measures, denominators, filters, or business scope that contradict or bypass analytics insight reporting outputs unless the user explicitly overrides them.

Power BI measures must be generated only from `reports/agent/09_analytics_insights/kpis/kpi_catalog.md`, validated dbt semantic metrics, or explicit user-approved requirements. Each generated DAX measure must map back to the key performance indicator name, source dbt model, formula, time field, grain, allowed dimensions, confidence, caveats, cardinality proof, and verification evidence. Do not generate DAX for `LOW`, `BLOCKED`, or unreconciled key performance indicators from `kpi_discovery_matrix.md` and `kpi_reconciliation_report.md`.

## Purpose

Help the data engineer decide whether the completed dbt project should expose a user-facing presentation layer beyond dbt models and documentation.

The presentation artifact is optional, but the recommendation is required for full pipeline final delivery. Ask the user in simple terms whether they want a presentation layer. Do not ask them to choose "Power BI as code" unless they already used that wording.

Default artifact: if the user approves a presentation layer and does not specify another tool or artifact type, create a Power BI PBIP/TMDL project by default. Do not create dashboards, reports, slides, notebooks, or other business intelligence artifacts unless the user approves the presentation layer.

## Presentation decision gate

After analytics insight reporting in a full pipeline, the agent must stop at this gate and ask the user whether to create a presentation layer. The agent must not mark the full delivery as complete while the presentation decision is still unanswered.

The gate must be a user-facing decision, not a hidden note in a report. When the runtime supports native questions, buttons, choices, or approval widgets, ask with that interactive UI so the data engineer can click a choice. Do not make the user copy and paste a phrase when a clickable question is available.

Before asking, summarize the evidence in one concise paragraph:

- Analytics insight reporting status.
- Validated key performance indicators with values when available.
- Recommended presentation technology.
- Recommended page set.
- Important blockers or caveats.

Use this interactive question shape:

```text
Analytics insight reporting is complete. Validated key performance indicators: <short KPI/value summary>. <Recommended technology> is recommended with <page list>. <Important caveat if any>.

Do you want a presentation layer?
```

Recommended options:

- `Yes - build Power BI PBIP presentation layer` - approves only the separate presentation-layer phase using Power BI PBIP/TMDL as the default artifact.
- `No presentation layer - complete final delivery now` - records that the artifact was declined and moves to final delivery with dbt documentation and analytics insight outputs only.
- `Tell me what to change first` - pauses so the user can change scope, metrics, pages, privacy rules, technology, validation, or report design.

If another technology is clearly better than Power BI, replace the first option with that recommended technology and explain why. If the user already requested a specific technology, use that technology in the first option. If native interactive questions are unavailable, use the same wording as a text fallback and ask the user to choose one option.

Use these statuses:

| User decision | Required status |
|---|---|
| Not asked yet | `Analytics insight reporting complete - presentation decision pending` |
| Analytics insight reporting not complete | `Documentation complete - analytics insight reporting pending` |
| User declines artifact | `Presentation recommendation complete - artifact declined` |
| User approves artifact | `Presentation artifact approved - presentation phase in progress` |
| Artifact completed | `Presentation artifact complete` |
| Artifact blocked | `Presentation artifact blocked` |

If the user approves a presentation layer, treat it as a separate `presentation_layer` phase. Use Power BI PBIP/TMDL as the default artifact unless the user specifies another technology or asks for a Markdown-only guide/report:

1. Write or update `AGENT_PLAN.md` with the exact artifact scope.
2. Confirm the inferred output format in the plan, source models, metrics, privacy rules, and validation method.
3. Build only the approved artifact.
4. Validate the artifact.
5. Write or update `reports/agent/10_presentation/presentation_report.md`, `reports/agent/10_presentation/presentation_layer_report.md` when the project uses the friendlier filename, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`.
6. For approved Power BI work, also write or update `reports/agent/10_presentation/powerbi_model_plan.md`, `reports/agent/10_presentation/dashboard_pages.md`, and `reports/agent/10_presentation/dax_measures.md` with the model plan, page plan, DAX specifications, and validation evidence.
7. Only then continue to final delivery.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Completed marts, semantic/evaluator/documentation status, analytics insight reporting outputs (`dashboard_spec.md`, `kpi_catalog.md`, `reporting_catalog.md`, `insight_backlog.md`, `reporting_readiness_scorecard.md`, `analytics_insight_report.md`), final model list, key performance indicator definitions, data quality notes, and privacy decisions |
| Allowed changes | Presentation recommendation report; presentation artifacts only after explicit user approval and a separate `presentation_layer` phase plan |
| Not allowed | Dashboards, reports, slides, notebooks, Power BI projects, guessed measures, or sensitive-field exposure without approval |
| Commands to run | Read-only model/metadata checks and artifact-specific validation only after the user approves artifact creation |
| Completion criteria | Best presentation option is recommended with evidence, possible key performance indicators are listed, caveats are clear, and the user is asked whether to create an artifact |
| Report required | Final report or `reports/agent/10_presentation/presentation_report.md`; optional friendlier alias `reports/agent/10_presentation/presentation_layer_report.md`; `reports/agent/PIPELINE_STATUS.md`; `reports/agent/CONTEXT_TREE.md`; and Power BI planning files when Power BI is approved |

## What to recommend

Review `reports/agent/09_analytics_insights/analytics_insight_report.md`, `reports/agent/09_analytics_insights/dashboard_spec.md`, `reports/agent/09_analytics_insights/kpis/kpi_catalog.md`, `reports/agent/09_analytics_insights/reporting_catalog.md`, final gold/marts models, semantic metrics, source data limitations, documented business rules, and [kpi-definitions.md](kpi-definitions.md). Then recommend presentation options with evidence:

| Option | When to recommend | What to include |
|---|---|---|
| dbt documentation only | The user only needs technical lineage and model docs | `dbt docs generate`, optional `dbt docs serve`, final model list |
| Presentation layer report | The user wants a concise business-facing summary | Key performance indicators, metrics, model grains, suggested analysis pages, limitations |
| Dashboard design | The user wants interactive consumption in a business intelligence tool | Suggested pages, filters, metrics, facts/dimensions, privacy notes |
| Power BI PBIP/TMDL project | Default when the user says yes to presentation layer and does not specify another technology | Complete PBIP project, semantic model, report artifact, relationships, measures, parameters, report pages, and open/refresh notes |
| Semantic layer first | Metrics need governed definitions before dashboards | MetricFlow metrics, entities, dimensions, time dimensions, safe denominators |
| Export/query handoff | The user wants to query marts manually | Final schemas, sample SQL, model grains, recommended joins |

## Two visual content layers

Every approved presentation artifact must separate these two visual layers instead of treating them as the same thing:

| Visual layer | What it is | Examples |
|---|---|---|
| Domain key performance indicators | Business-defined measures that use approved flags, filters, and semantic definitions | Active subscriptions, payment success rate, reportable orders |
| Standard time showcase | Reusable trend and period visuals driven by fact date columns | Orders by year, payments by month, last calendar year total, year-to-date total, last 12 months total |

The presentation layer is incomplete if it includes only domain key performance indicator cards and omits the standard time showcase, unless the user explicitly declines trend reporting.

## Consultant-grade report design

The agent owns the first professional report design. Do not wait for the user to list every page, visual, slicer, or measure. Use validated gold facts, dimensions, semantic metrics, source profiling, data quality findings, and approved requirements to propose the richest useful presentation layer the data can support.

Maximum information means maximum validated, decision-useful information, not every available column. Prefer visuals and pages that answer business questions, expose trends, explain drivers, and show exceptions. Do not invent unsupported metrics or business meanings just to make the report look fuller.

Every professional report must cover five business pillars when the data supports them:

| Pillar | Report responsibility |
|---|---|
| Context and strategy | State the objective, audience, business process, target, benchmark, baseline, or why the report matters |
| Key performance indicators | Show leading and lagging measures with business definitions, filters, grain, and caveats |
| Trend analysis and variance | Show direction over time plus variance from target, benchmark, baseline, or prior period when available |
| Insights and attribution | Explain drivers, segments, anomalies, outliers, and root-cause hypotheses supported by the data |
| Recommendations and next steps | State actions, risks, decisions needed, and blocked items |

If targets, benchmarks, attribution evidence, or next-step owners are missing, keep the section visible and mark it `Needs business input` or `Deferred` with the reason. Do not silently omit the pillar.

Default report page set, included only when the validated data supports it:

| Page | Include when | Typical content |
|---|---|---|
| Context and Strategy | Any business-facing report is created | Objective, audience, scope, targets, benchmarks, assumptions, and open business inputs |
| Executive Overview | At least one approved fact or metric exists | Key performance indicator cards, leading and lagging measures, main trend, top drivers, status summary, important caveats |
| Trends and Variance | Fact date or timestamp columns exist | Standard time showcase, period comparisons, by-year and by-month visuals, variance from target or baseline when available |
| Financial or Value | Amount, revenue, payment, claim, order value, cost, or balance facts exist | Gross, net, paid, pending, refunded, outstanding, margin, or value trend views |
| Operations or Activity | Event, workflow, status, or lifecycle facts exist | Volumes, completed/cancelled/pending counts, success/failure rate, funnel or process movement |
| Insights and Attribution | Useful dimensions or segment fields exist | Top and bottom entities, driver breakdowns, segment changes, anomaly explanations, root-cause hypotheses with confidence |
| Entity Performance and Segmentation | Useful dimensions exist | Breakdown by customer, patient, provider, product, department, location, team, agent, service, status, channel, category, geography, type, or plan |
| Exceptions and Data Quality | Important warnings, empty facts, unknown mappings, stale sources, or privacy constraints exist | Data coverage, missing values, invalid statuses, failed relationships, open decisions, blocked visuals |
| Recommendations and Next Steps | Any business-facing report is created | Actions, decisions needed, risks, resource needs, and next approval checkpoint |
| Detail or Drillthrough | Row-level investigation is safe and useful | Approved non-sensitive detail tables, drillthrough filters, investigation fields, and supporting context |

Enterprise design rules:

- Build from the governed semantic model or star schema, not ad hoc flat tables.
- Use clear user-facing labels, consistent page titles, visual hierarchy, slicers, tooltips, and report navigation.
- Follow the fixed Power BI canvas standard from [reporting-standards.md](reporting-standards.md): header/navigation, prioritized key performance indicator summary cards, supporting key performance indicator coverage, interactive slicers, trends/comparison visuals, detail layer, smart tooltips or drill-throughs, and a Report Information or Report Settings page.
- Include slicers for date, status, major dimensions, and reportable flags when those fields are validated and useful.
- Hide technical keys, hashes, audit columns, and implementation fields from report view unless they are needed for safe drillthrough.
- Exclude, mask, or aggregate sensitive fields by default unless the user has approved exposure.
- Choose Import, DirectQuery, or Composite mode based on data volume, refresh need, and warehouse cost; default to Import for moderate curated marts.
- Keep pages information-dense but scannable. Avoid decorative, marketing-style, or column-dump layouts.
- Record the page rationale, source models, measures, filters, sensitive-field handling, and blocked visuals in `AGENT_PLAN.md` and `reports/agent/10_presentation/presentation_report.md`.
- Ask the user only for decisions that affect business meaning, privacy, cost, refresh behavior, or downstream usability.

## Standard time showcase

For Power BI PBIP/TMDL projects and dashboard/report artifacts, always include a `Trends` report page when validated facts contain usable date or timestamp columns.

Do not hardcode domain-specific field names in the skill. Discover primary time fields from final gold facts and marts by inspecting column names, model YAML, semantic models, and mart SQL. Prefer, in order:

1. Approved semantic time dimensions.
2. Date columns named for the fact event, such as `order_created_at`, `payment_created_at`, `transaction_created_at`, `service_start_date`, `appointment_date`, or `encounter_date`.
3. Generic but credible columns such as `created_at`, `updated_at`, `event_date`, `transaction_date`, or `<fact_name>_date`.
4. Ask or defer when multiple plausible dates would change the business meaning.

For each primary fact with a credible time field and an approved or supportable measure, add these visuals:

| Visual | Required behavior |
|---|---|
| Total last calendar year card | Filter the primary time field to the previous full calendar year |
| Total year to date card | Filter from the start of the current calendar year through the latest available date |
| Total last 12 months card | Filter to the trailing 12 months using the primary time field |
| By-year column chart | Show up to the last 10 calendar years and include empty years when the date table supports them |
| By-month line or column chart | Show the last 24 months or the full available history when less than 24 months exists |

Use governed measures and reportable filters first. If a measure such as `is_reportable_order`, `is_reportable_payment`, `is_successful_payment`, or an approved semantic metric exists, use it instead of raw row counts. If no governed measure exists, create a clearly named basic measure and mark it as a default recommendation with caveats.

Relate fact date columns to the governed date table or `time_spine_daily` for time intelligence whenever that relationship is safe and does not create ambiguous active paths. Disable Power BI automatic local date tables for generated models. Use inactive role-playing date relationships only when the measure pattern is documented. If a safe date-table relationship cannot be created, the report may use fact-date grouping, but the limitation must be documented.

Before delivery, validate every time showcase visual number with SQL against the final gold/mart schema. `reports/agent/10_presentation/presentation_report.md` must include the exact verification query, expected result, Power BI measure or visual checked, and pass/fail result for every card or chart aggregate. Do not trust a Power BI visual until its source aggregate has been checked.

When data history is shorter than the visual window, keep the reusable visual pattern but explain the data reality. For example, if facts only span 14 months, a 10-year by-year chart may show empty years; monthly and last-12-month views should be emphasized.

Example mapping, to be used only when these fields exist in the current project's validated gold layer:

| Fact | Candidate time field | Candidate measure |
|---|---|---|
| Orders fact | `order_created_at` | Reportable order count |
| Payments fact | `payment_created_at` | Payment amount collected |
| Subscriptions fact | `service_start_date` or `subscription_created_at` | Active subscriptions |
| Payment transactions fact | `transaction_created_at` | Transaction count or collected amount |

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
- Trends: <fact time fields, last calendar year, year to date, last 12 months, by-year, by-month visuals, and SQL verification status>

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

For full-pipeline runs, prefer the interactive presentation decision gate above over a plain text-only question. The user should see the recommendation, understand the key evidence, and click the desired path.

If the user says yes without specifying a technology, infer Power BI PBIP/TMDL as the approved default, create the presentation-layer phase plan, and wait for approval when required by [phase-plan-approval.md](phase-plan-approval.md). Do not ask the user to say "Power BI as code" explicitly. Do not answer only with advice when the user approved artifact creation.

If the recommendation cannot be produced, mark it `BLOCKED` or `SKIPPED` with the exact reason in the final report, pipeline status, context tree, and final response. Do not silently omit the presentation-layer section.

## Guardrails

- Do not invent key performance indicators that are not supported by final marts or approved semantic metrics.
- Do not recommend advanced key performance indicators unless numerator, denominator, filters, time field, source model, and caveats are known or clearly marked as deferred.
- Do not put a key performance indicator into Power BI until [metric-verification.md](metric-verification.md) reconciles expected versus actual numerator, denominator, and result from gold or semantic logic.
- Do not create Power BI-only key performance indicators or DAX measures that bypass `kpi_catalog.md`, validated semantic metrics, or user-approved requirements.
- Do not create missing keys, business flags, denominator logic, or relationship shortcuts in Power BI when they belong in dbt.
- Do not create Power BI measures when source-to-final reconciliation, grain proof, or cardinality proof is missing or failed.
- Do not ask the user to design every page. Recommend a consultant-grade default design from validated data and ask only for decisions that affect business meaning, privacy, cost, refresh behavior, or downstream usability.
- Do not maximize information by exposing every field. Maximize validated business insight.
- Do not skip the standard time showcase when validated facts have usable date columns. If no fact date columns exist, document that trend visuals are blocked.
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

## Preferred Power BI thin model template workflow

If the user provides or approves a Power BI Desktop-created PBIP template, prefer [powerbi-thin-model-template.md](powerbi-thin-model-template.md) over generating the full physical semantic model from scratch.

In this mode, the Power BI Desktop template owns source connections, credentials, physical imported tables, Power Query M, source partitions, date table, and relationships. The agent copies the approved template and injects only approved measures, descriptions, format strings, display folders, and safe annotations into the approved measures table such as `_KPI_Measures` or `_Measures`.

Do not edit physical source objects, schemas, table names, M code, credentials, or relationship paths in thin model mode unless the user explicitly approves that scope and dbt cardinality proof supports it. If the template does not include a measures table, pause and ask whether to add one in Desktop or approve the agent creating it.

If no approved PBIP template exists yet, create a human-connected template checkpoint instead of generating fragile source connections. List the approved gold, mart, bridge, and date/time tables, the relationship rules, the required measures table name, and the recommended storage mode. Ask the user to connect those tables in Power BI Desktop, confirm relationships, create the measures table, save as PBIP, and provide the PBIP path. Stop until that confirmation arrives.

The template must have opened successfully in Power BI Desktop before agent edits when Desktop is available. After edits, run the same validation loop as generated PBIP artifacts, plus a diff or explicit check proving that source partitions, M expressions, physical tables, and connection definitions were not changed.

## Power BI validation workflow

For Power BI PBIP/TMDL artifacts, never accept "files created" as done. The presentation phase can be marked complete only after the validation loop passes or a required external validation step is explicitly unavailable and documented as not run.

## Power BI Desktop version compatibility rule

Before final PBIP/TMDL delivery, detect and record the target Power BI Desktop version. Do not assume the generated PBIP schema is compatible with the user's installed Desktop.

Required behavior:

1. Run `python scripts/detect_powerbi_desktop.py` when Power BI Desktop validation is expected on the local machine.
2. Record the detected Desktop product version, release channel/month when known, enabled relevant preview features when available from error logs, and validation target in `reports/agent/10_presentation/presentation_report.md`.
3. Run `python scripts/validate_powerbi_pbip.py <pbip_project_folder> --require-powerbi-desktop-version --powerbi-desktop-version <detected_version>` before final presentation handoff.
4. Do not generate or keep PBIP metadata that is newer than the target Desktop can open.
5. Treat Desktop errors such as `This file is incompatible with your current version of Microsoft Power BI Desktop` and `NewerLinguisticSchemaVersion` as hard blockers, not as user-side update requests.

For April 2026 Desktop `2.153.1206.0`, avoid generated linguistic/culture metadata unless the exact files were created by that same Desktop version and validated. The bundled template must omit SemanticModel `definition/cultures/` files and `ref cultureInfo` references by default.

Microsoft's PBIP documentation says Power BI Projects are preview, externally edited files can prevent Desktop from opening, and Report Linguistic Schema is not supported with Power BI projects. Use official documentation when version behavior is unclear, and cite the checked page in the presentation report.

## Power BI MCP availability rule

Before validating a Power BI PBIP/TMDL artifact, the agent must actively check whether Power BI Modeling Model Context Protocol tools are available in the current environment. Do not assume they are unavailable because the tool list is not obvious, and do not rely on Cursor, Power BI Desktop, or static file checks alone when Model Context Protocol validation can be used.

Preferred official implementation: Microsoft Power BI Modeling Model Context Protocol, [microsoft/powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp). When the tool is not already exposed but Node.js and `npx` are available, use or recommend:

```powershell
npx @microsoft/powerbi-modeling-mcp@latest --start
```

Treat this as the preferred semantic-model validation path for PBIP/TMDL projects, while still running this repository's static validator and Power BI Desktop open validation when available.

Required behavior:

1. Search available tools/connectors for Power BI Modeling Model Context Protocol capabilities such as `ConnectFolder`, `ConnectToPBIP`, connection inspection, table operations, relationship operations, and DAX query operations.
2. If the Power BI Modeling Model Context Protocol tools are installed or exposed, use them. Running only static validation while available Model Context Protocol tools are skipped is a failed presentation phase.
3. If the tools are not exposed but a tool/plugin/connector installation mechanism is available, request or recommend installing the exact Power BI Modeling Model Context Protocol connector/plugin before final presentation validation. Prefer `@microsoft/powerbi-modeling-mcp` from the official Microsoft repository.
4. If installation is not possible in the current environment, mark Model Context Protocol validation as `NOT RUN` with the exact reason and mark the presentation phase `BLOCKED` when the user required open/load validation through Model Context Protocol.
5. Record the availability check, tool names found or missing, install attempt or instruction, and validation result in `reports/agent/10_presentation/presentation_report.md`.

The expected Model Context Protocol validation path is:

- Connect to the SemanticModel definition folder with `ConnectFolder`.
- If validating an entire PBIP is supported in the current tool surface, connect to the `.pbip` with `ConnectToPBIP`.
- Confirm the model connection loads.
- Inspect tables, columns, measures, relationships, and partitions.
- Run a simple DAX smoke query.
- Run at least one DAX query for core key performance indicator measures when possible and reconcile it to the gold/semantic SQL checks.

Required loop:

1. Build the PBIP/TMDL artifact.
2. Check Power BI Modeling Model Context Protocol availability using the rule above.
3. Run static file validation: file tree, JSON parsing, TMDL structure, path links, relationship ambiguity audit, and partition/source checks. Run `python scripts/validate_powerbi_pbip.py <pbip_project_folder>` when this repository script is available, and fix every failure before continuing.
4. Self-test the semantic model using the Power BI Modeling Model Context Protocol tools when available:
   - `ConnectFolder` against the SemanticModel definition folder.
   - `ListConnections` or `GetConnection` to confirm the model connection loaded.
   - Table and relationship operations to confirm expected tables, columns, and relationships exist.
   - DAX query operation with a smoke query such as `EVALUATE ROW("test", 1)`.
5. If Power BI Desktop is available, open or launch the `.pbip` and confirm it loads without project definition or relationship-path errors.
6. If any step fails, fix the PBIP/TMDL files and repeat the validation loop.
7. Only after passing validation, update `reports/agent/10_presentation/presentation_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` with `PASS`.

Do not mark the presentation phase complete if the user would see an error when opening the `.pbip`.

If the Power BI Modeling Model Context Protocol tools are unavailable in the current environment, mark the Model Context Protocol load test as `NOT RUN` with the exact reason. Do not claim the semantic model loaded through Model Context Protocol. If Power BI Desktop is unavailable, mark Desktop open validation as `NOT RUN` with the exact reason. If either validation is required by the user's contract and cannot be run, mark the presentation phase `BLOCKED`, not `PASS`.

If Power BI Modeling Model Context Protocol tools are available but were not used, mark Model Context Protocol validation as `FAIL`, not `NOT RUN`.

## Power BI self-test checklist

Before handoff, paste the validation results into the chat result summary and `reports/agent/10_presentation/presentation_report.md`:

| Check | What to verify |
|---|---|
| File tree | `.pbip`, Report folder, SemanticModel folder, `definition.pbism`, `database.tmdl`, `model.tmdl`, and `report.json` exist where expected |
| Static validator | `python scripts/validate_powerbi_pbip.py <pbip_project_folder>` passes when available |
| Desktop version evidence | `python scripts/detect_powerbi_desktop.py` result recorded when Desktop validation is expected |
| Version-aware static validator | `validate_powerbi_pbip.py --require-powerbi-desktop-version --powerbi-desktop-version <version>` passes before final handoff |
| JSON parse | All `.json` files parse cleanly |
| Path links | `.pbip` links to an existing `.Report` artifact folder, root-level `definition.pbir` exists and is non-empty, and that report definition links to an existing `.SemanticModel` artifact using correct relative paths |
| Relationships | No ambiguous active paths; approved active/inactive relationship rules are followed |
| Partitions | Import or source queries point to real approved gold/mart tables |
| Power BI Modeling Model Context Protocol load | `ConnectFolder` to the SemanticModel definition folder succeeds |
| Power BI Modeling Model Context Protocol inspection | Connections, tables, columns, relationships, and a simple DAX smoke query succeed |
| Power BI Modeling Model Context Protocol availability | Tool search/connector check is recorded; if available, Model Context Protocol validation was run |
| Power BI Desktop open | `.pbip` opens without load errors when Desktop is available |

If Power BI Desktop open fails after handoff, the agent must use the pasted error message as a blocker, fix the artifact, rerun static validation, rerun the relationship ambiguity audit, rerun the Power BI Modeling Model Context Protocol `ConnectFolder` test, rerun Desktop open validation when available, and update `reports/agent/10_presentation/presentation_report.md` with the fix and retest results.

Before creating files:

- Confirm the final dbt gold/mart tables exist and have passed the relevant dbt build.
- Write or update `AGENT_PLAN.md` with the Power BI artifact plan and wait for approval.
- Confirm output location, model name, connection source, consultant-grade page plan, measures, verification queries, blocked visuals, and privacy rules.
- Confirm metric verification queries for every key performance indicator measure, including numerator, denominator, filter logic, and expected versus actual result.
- Discover fact date columns and planned time showcase visuals before writing report pages.
- In the plan, state that Power BI PBIP/TMDL is the default because no other presentation technology was specified. Ask for changes only if the user wants a different technology or a Markdown-only guide.
- Prefer the bundled neutral PBIP template at `assets/powerbi/pbip_template/` and instantiate it with `scripts/generate_powerbi_pbip.py` before adding project-specific tables, measures, relationships, pages, and visuals.
- Detect the local Power BI Desktop version before final PBIP handoff. If Desktop cannot be detected, record that fact and do not claim version compatibility.
- If a known-good PBIP project exists in the workspace, do not silently adapt it. Show the exact `.pbip` path, state which structural files would be inspected, explain what would and would not be reused, and get user approval before using it as a reference.
- When the user names required source schemas or gold tables, verify those tables exist before wiring import queries or partitions.

When creating PBIP:

- Create a complete PBIP project, not only loose TMDL text.
- Use the bundled neutral PBIP template as the default structural base. Do not depend on local projects such as IHMS, ShopSphere, Hospital, or another nearby PBIP being present on the machine.
- To create the starting structure, run `python scripts/generate_powerbi_pbip.py --name <safe_pbip_name> --display-name "<report display name>" --output-dir <powerbi_parent_folder> --project-root <project_root>`, then add the approved project-specific semantic model and report content.
- If a local known-good PBIP is approved as a reference, use it only for file layout and metadata patterns. Do not copy source connections, business tables, relationships, measures, report pages, visuals, page names, branding, `.pbi/` cache files, logical IDs, lineage tags, source database names, or domain-specific text unless the user explicitly approves that specific content.
- Include the `.pbip` file, a Report artifact folder, and a SemanticModel artifact folder.
- Build the approved enterprise page set from validated facts and dimensions, including useful slicers, user-facing labels, hidden technical fields, tooltips, drillthrough/detail pages where safe, and data-quality/limitation notes where needed.
- Each main report page must use the standard Power BI canvas layout where supported: header/navigation bar, prioritized key performance indicator card row, visible primary slicers, trend and comparison visuals, secondary driver visuals, and matrix/detail or drill-through entry point.
- Apply the professional visual theme and color rules from [reporting-standards.md](reporting-standards.md). Do not leave report pages on default Power BI colors, default white-only styling, or unformatted placeholder visuals. Use a consistent palette, header treatment, card styling, chart series colors, slicer styling, detail-table formatting, and conditional colors for positive, warning, and failure states. If a brand palette is unavailable, use the skill's neutral enterprise palette and document the theme choices in the presentation report.
- Analyze the maximum useful supported key performance indicators from the validated model. Put the highest-priority three to five on the executive canvas row for readability, and place additional supported key performance indicators on a scorecard/details page, tooltip, drill-through, or Report Information page. List blocked or deferred key performance indicators with reasons.
- Create a Report Information, Report Settings, or About This Report page with report purpose, audience, data source, refresh details, page guide, key performance indicator definitions, slicer/filter definitions, metric caveats, data quality notes, privacy handling, grain/relationship summary, validation summary, and open decisions.
- Include report title, page title, last refreshed timestamp, reset filters button, and native page navigation when the chosen PBIP/report format supports them. If any element cannot be generated safely, document the reason in `reports/agent/10_presentation/presentation_report.md`.
- Use line or area charts for time series; use bar or column charts for category comparisons; use matrix visuals with conditional formatting for operational details where useful.
- Add report page tooltips and drill-through pages for important entities when safe, supported by the model, and useful for investigation.
- Ensure the `.pbip` file points to a Report artifact when a report is requested, not only to a semantic model.
- For the root `.pbip` shortcut file, do not use a `dataset` property for the artifact entry. A report PBIP must use the schema-allowed report artifact reference so Power BI does not fail with `Property 'dataset' has not been defined` or `Required properties are missing from object: report`.
- Ensure the `.pbip` report artifact path resolves to an existing `<name>.Report` folder.
- Ensure the Report artifact has root-level `definition.pbir`, that the file is non-empty, and that it contains a valid ReportDefinition object with `datasetReference.byPath.path`.
- Ensure `definition.pbir` links to an existing `<name>.SemanticModel` artifact using the correct relative path. Do not create legacy `definition/definition.pbir` for enhanced PBIR. Treat Power BI Desktop errors such as `ReportDefinition: Required artifact is missing`, `RequiredArtifactMissing: Path: definition.pbir`, or `RequiredArtifactMissing: ArtifactName: ReportDefinition` as hard validation failures.
- Ensure enhanced PBIR report metadata lives under the Report `definition/` folder: `definition/report.json`, `definition/version.json`, and `definition/pages/pages.json`.
- Do not create or keep legacy root-level `report.json` in the Report artifact when using enhanced PBIR.
- Ensure every page listed in `definition/pages/pages.json` has a page folder, `page.json`, and at least one `visual.json`. Page shells are not complete report pages.
- Ensure the Report artifact includes `definition/version.json` with the Power BI report definition version metadata schema and a non-empty version string.
- Keep TMDL under the SemanticModel definition folder using the expected artifact layout for the chosen Power BI project format.
- Create report definition files for the approved pages and visuals when the user asked for clickable/openable Power BI pages. Do not replace report pages with `dashboard_pages.md`.
- Use parameters for host, database, schema, warehouse, or equivalent connection values instead of hardcoding environment-specific values where practical.
- Define relationships from the approved star schema and avoid ambiguous relationship paths. Prefer one active route from each dimension to each fact area. Avoid convenience relationships from a dimension directly to a lower-grain fact when that lower-grain fact is already reachable through its parent fact.
- Do not add a direct active relationship when an active indirect relationship path already exists between the same entities. For example, if `subscriptions -> orders -> customers` is active, do not also keep `subscriptions -> customers` active unless the shortcut is made inactive and a documented measure pattern needs it.
- For parent-child fact designs, connect lower-grain satellite facts to the parent fact only when that is the approved canonical route, and do not also add direct active dimension shortcuts that create ambiguous paths.
- Use inactive relationships only for approved role-playing dates or alternate analysis paths, and document the measure pattern needed to activate them.
- Include approved bridge tables and their relationship directions when the gold layer contains bridge models or the approved presentation scope requires many-to-many analysis.
- Put reusable business calculations in a measures table or equivalent semantic model construct.
- For every Power BI/DAX measure, reconcile the result to the approved gold or semantic key performance indicator definition. Rates, ratios, percentages, and averages must show expected numerator, actual numerator, expected denominator, actual denominator, expected result, and actual result in `reports/agent/10_presentation/presentation_report.md`.
- Add the standard `Trends` page when fact date columns are available. Include last calendar year, year-to-date, last 12 months, by-year, and by-month visuals for each primary fact where the measure/date pairing is validated.
- In the Power BI semantic model, each table may have at most one column with `IsKey` set to `True`. If a dbt table has a composite business key, keep only one technical key column marked as the Power BI key or leave key metadata unset and document the composite grain in descriptions and relationships.
- Use dbt surrogate keys for composite business keys before exposing dimensions to Power BI. Any column used as a Power BI one-side relationship key must have `unique` and `not_null` tests in dbt. Do not use partial natural keys as one-side Power BI keys when they repeat in the dimension.
- Generated lineage tags must be unique across all TMDL files. Regenerate lineage tags when copying from a known-good PBIP template; do not reuse one table or metrics prefix across unrelated tables.
- Report and SemanticModel `.platform` logical IDs must be regenerated for every generated PBIP project. Never reuse logical IDs from the bundled template or a local reference PBIP.
- Use simple user-facing measure labels and keep technical column names inside model definitions.
- Validate that every report page and visual is supported by approved source models, measures, fields, and privacy rules. Remove or mark blocked any visual whose business meaning, grain, or source evidence is not clear.
- Validate that report pages use intentional formatting rather than default visuals. The presentation report must record theme path, palette source, color meanings, and any visual formatting limitations.
- When the user supplies exact measure labels, use those labels exactly unless the expression cannot be supported by the validated marts.
- Use supported PBIP/TMDL metadata versions for the target Power BI Desktop release. Known requirements from prior failures include `definition.pbism` using the semantic model definition-properties schema path, `database.tmdl` using `compatibilityLevel: 1605` when requested, `model.tmdl` table references at the root level when the chosen structure requires it, and `report.json` values such as `themeCollection.baseTheme.reportVersionAtImport` typed exactly as Power BI expects.
- For `.platform` files inside Report or SemanticModel artifact folders, verify `$schema` exists and matches the Power BI Desktop supported Fabric git integration platform properties schema pattern, such as `https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.x.y/schema.json`, and verify `config` exists as a non-empty object. Treat `UnrecognizedSchemaVersion: Path: .platform` and `ObjectNotPerSchema: Path: .platform` errors such as "Required properties are missing from object: config" as failed presentation phases.
- For `report.json`, always emit and verify `themeCollection.baseTheme.reportVersionAtImport` as a non-empty string. For the April 2026 Power BI Desktop PBIP format seen in prior failures, use the string value `"5.55"` when no better validated project reference overrides it. Do not emit it as a number, null, object, empty string, or omit it.
- If `report.json` includes `resourcePackages`, verify every package item `path` is a safe relative path and resolves to an existing file under the Report `definition/` folder. Treat missing theme files such as `BaseThemes/CY24SU10.json` as failed static validation because Power BI Desktop may reject or partially load the report.
- Do not generate SemanticModel `definition/cultures/` files, `ref cultureInfo`, report linguistic metadata, or other linguistic schema artifacts by default. These can trigger `NewerLinguisticSchemaVersion` and are not supported by Power BI Projects unless created and validated by the exact target Desktop version.
- Do not trust a local reference PBIP's `reportVersionAtImport` blindly. Some working or previously generated files may contain object-shaped version metadata that this skill treats as unsafe for generated reports. The generated artifact must pass `scripts/validate_powerbi_pbip.py`.
- For TMDL table files, do not write Markdown code fences in `.tmdl` files. Place Power Query M expressions only in the correct partition/source expression property syntax for the chosen TMDL format. Indented `let ... in ...` blocks are allowed when they follow a known-good TMDL partition pattern; unindented loose `let` or `in` lines are hard validation failures.
- Do not write bare Power Query M steps such as `AddedKey = Table.AddColumn(...)` at the root of a `.tmdl` file. M steps belong only inside valid partition source expression blocks.
- Do not generate linguistic metadata by default. If `LinguisticMetadata`, `culture`, `linguisticMetadata`, `content`, or content-type sections are written or copied, the declared content type and actual content format must match. XML content type requires valid XML; JSON content type requires valid JSON. JSON such as `{ "Version": "1.0.0" }` must never be written into XML-typed linguistic metadata. If uncertain, omit linguistic metadata.
- For PostgreSQL import partitions, keep only server and database as reusable expressions or parameters. Do not create a `PgSchema` expression. In each table partition, quote parameter references such as `#"PgServer"` and `#"PgDatabase"`, hardcode the approved gold schema in the source record, use `Table.SelectColumns` to load only modeled columns, use `Table.TransformColumnTypes` for dates and numeric fields, and include `annotation PBI_ResultType = Table` indented under the table object, never at TMDL root.
- Measures or metrics tables must have a calculated partition such as `ROW("MetricKey", 1)` so the semantic model loads correctly.
- Add a local `powerbi/README.md` or equivalent handoff with open, refresh, and reload-from-disk guidance.
- Do not tell the user to overwrite the generated project by saving from Power BI Desktop as the default fix. For reload-from-disk edits, instruct the user to close without saving when that is the safe workflow.

Validation before handoff:

- Verify every required PBIP, report, semantic model, definition, relationship, table, partition, and measure file exists.
- If the bundled template was used, record the template path, generator command, regenerated IDs, and static validation result in `reports/agent/10_presentation/presentation_report.md`.
- If a local reference PBIP was used, record the exact path, user approval, inspected structural files, reused patterns, and explicitly state that business content, IDs, lineage tags, and source connections were not copied.
- Parse JSON files with a real parser.
- Validate the root `.pbip` shortcut schema: artifact entries for report deliverables must contain the required `report` property and must not contain unsupported properties such as `dataset`. Treat `artifacts[0].dataset` or a missing `artifacts[0].report` as a failed presentation phase.
- Resolve every `.pbip` report artifact path and verify the referenced `.Report` folder exists. Then verify root-level `definition.pbir` exists, is non-empty, parses as JSON, contains `datasetReference.byPath.path`, and points to an existing `.SemanticModel` folder. Treat a missing, empty, unresolved, or legacy nested `definition/definition.pbir` as a failed presentation phase even if other report files exist.
- Verify enhanced PBIR report metadata exists at `definition/report.json`, `definition/version.json`, and `definition/pages/pages.json`; reject legacy root-level `report.json` for enhanced PBIR.
- Verify every page in `definition/pages/pages.json` has real visuals by counting `visual.json` files under each page folder. Record the visual inventory in `reports/agent/10_presentation/presentation_report.md`.
- Validate every `.platform` file with JSON parsing, schema-pattern check, and required artifact details check. The `$schema` value must match the supported Fabric git integration platform properties pattern for the target Desktop version, and `config` must be present as a non-empty object. Do not allow stale, guessed, missing, unsupported, or schema-stub-only `.platform` files.
- For `report.json`, explicitly assert `themeCollection.baseTheme.reportVersionAtImport` exists and has the correct type and value for the target Power BI Desktop schema. Run `python scripts/validate_powerbi_pbip.py <pbip_project_folder>` to enforce the default `"5.55"` value, or pass `--expected-report-version-at-import <value>` only when a known-good project reference proves another version. If this metadata check fails, repair with `python scripts/validate_powerbi_pbip.py <pbip_project_folder> --fix-report-version-at-import`, then rerun validation without the fix flag. Treat missing, empty, incorrectly typed, or wrong-valued `reportVersionAtImport` as a failed presentation phase.
- Verify all `report.json` `resourcePackages.items[].path` references resolve to existing files. Re-run `python scripts/validate_powerbi_pbip.py <pbip_project_folder>` after adding or removing theme/resource files.
- Verify no SemanticModel `definition/cultures/` folder, `ref cultureInfo`, or linguistic metadata block exists unless exact-version Desktop-generated support was approved and validated.
- Check TMDL indentation and root-level object placement against the selected PBIP structure.
- Scan table `.tmdl` files for root-level annotations such as unindented `annotation PBI_ResultType = Table`. Treat Power BI Desktop errors like `TMDL objects cannot be merged because both declare the same property: value` as failed validation caused by invalid annotation placement, not as a refresh issue.
- Scan TMDL table files for Markdown code fences and invalid loose Power Query keywords such as unindented standalone `let` or `in` lines outside the approved partition/source expression block. Treat `UnknownKeyword` or invalid indentation parser risks as failed static validation.
- Scan semantic model TMDL files for invalid linguistic metadata content-type mismatches. Treat Power BI Desktop errors such as `does not comply with the Xml content-type` and `Data at the root level is invalid. Line 1, position 1` as failed validation. Do not mark delivery ready while XML-typed metadata contains JSON or JSON-typed metadata contains XML.
- Audit TMDL column metadata so no table has more than one column with `IsKey` set to `True`. Do not mark every `*_id` column as a Power BI key. Mark only the table's single primary/technical key when one exists; leave foreign keys unmarked. Treat Power BI errors such as `PFE_TM_TABLE_TWO_KEY_COLUMNS` or "has two columns with the IsKey property set to True" as failed validation.
- Verify the `.pbip` points to the report artifact and the report points to the semantic model artifact.
- Verify the exact referenced Report artifact includes root-level `definition.pbir`; do not rely only on scanning for any `.Report` folder.
- Verify the Report artifact includes `definition/version.json`.
- Verify all TMDL lineage tags are unique.
- Verify PostgreSQL import partitions use only approved server/database expressions, quoted parameter references, hardcoded approved schema records, selected columns, changed types, and `PBI_ResultType`.
- Verify the measures or metrics table has a calculated partition.
- Verify approved report pages exist as Power BI report definition artifacts with actual `visual.json` files, not only Markdown page descriptions or empty page shells.
- Verify user-provided technical requirements exactly, including output path, artifact folder names, schema strings, compatibility level, parameter names, import partition source, relationship direction/activity, measure labels, report page names, and expected visuals.
- Verify every standard time showcase visual with SQL against the final gold/mart schema. Record exact verification queries and results in `reports/agent/10_presentation/presentation_report.md`.
- Verify every key performance indicator visual and DAX measure with [metric-verification.md](metric-verification.md). Treat mismatched numerator, denominator, filter, or final result as a failed presentation phase.
- For Power BI PBIP/TMDL artifacts, run a relationship ambiguity audit before handoff. Build a simple graph of active relationships and confirm there is no pair of tables connected by more than one active path through facts, bridge tables, or snowflaked dimensions. Record the checked paths and result in `reports/agent/10_presentation/presentation_report.md`. Treat `PFE_XL_USERELATIONSHIP_AMBIGUOUS_PATH` and Desktop errors that say "There are ambiguous paths between" as failed validation.
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
Report: reports/agent/10_presentation/presentation_report.md
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
- Mark a presentation artifact complete when validated facts have usable date columns but the report lacks a `Trends` page or equivalent standard time showcase.
- Mark a presentation artifact complete when time showcase visual numbers were not verified with SQL and recorded in the presentation report.
- Mark a Power BI artifact complete when the root `.pbip` shortcut file contains an unsupported `dataset` artifact property or is missing the required `report` artifact property for a report deliverable.
- Mark a Power BI artifact complete when any `.platform` file has a missing or unsupported `$schema` value, or a missing/empty `config` object, that Power BI Desktop reports as `UnrecognizedSchemaVersion` or `ObjectNotPerSchema`.
- Mark a Power BI artifact complete when any table has more than one column with `IsKey` set to `True`.
- Mark a Power BI artifact complete when duplicate TMDL lineage tags exist.
- Mark a Power BI artifact complete when a PostgreSQL partition uses `PgSchema`, unquoted parameter references, no `Table.SelectColumns`, no `Table.TransformColumnTypes`, or no `PBI_ResultType` annotation.
- Mark a Power BI artifact complete when any table `.tmdl` file contains root-level annotations such as unindented `annotation PBI_ResultType = Table`, or when Power BI Desktop reports duplicate annotation merge errors such as `both declare the same property: value`.
- Mark a Power BI artifact complete when the measures or metrics table is missing a calculated partition.
- Create direct relationships that introduce ambiguous filter paths when a safer snowflake path exists.
- Mark a Power BI artifact complete when the Power BI Modeling Model Context Protocol `ConnectFolder` test fails.
- Mark a Power BI artifact complete when `report.json` is missing `themeCollection.baseTheme.reportVersionAtImport` or has it as the wrong JSON type.
- Mark a Power BI artifact complete when `report.json` has `themeCollection.baseTheme.reportVersionAtImport` as an empty string or unvalidated string value.
- Mark a Power BI artifact complete when `report.json` references a missing resource package item, including a missing base theme JSON file.
- Mark a Power BI artifact complete when Desktop version was not checked for a PBIP intended to open on the user's machine.
- Mark a Power BI artifact complete after an incompatible-version Desktop error such as `NewerLinguisticSchemaVersion`.
- Mark a Power BI artifact complete when generated culture or linguistic schema files are present without exact target-version validation.
- Mark a Power BI artifact complete when the `.pbip` points to a Report artifact whose root-level `definition.pbir` file is missing, empty, invalid, or does not link to an existing SemanticModel artifact.
- Mark a Power BI artifact complete when any planned page is only a shell with no `visual.json` files.
- Mark a Power BI artifact complete when any TMDL table file contains Markdown code fences or invalid loose Power Query keywords such as an unindented standalone `in` line outside a valid expression block.
- Mark a Power BI artifact complete when Power BI Desktop reports ambiguous relationship paths or any project definition load error.
- Hardcode one domain's table names, measures, or report pages into the skill.
- Tell the user to save over the generated files from Power BI Desktop as the default reload strategy.
- Mark the Power BI artifact complete if the structure is incomplete or validation was not run.
