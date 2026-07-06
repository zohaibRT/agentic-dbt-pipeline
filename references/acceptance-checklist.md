# Acceptance Checklist

Verify before marking the dbt pipeline workflow complete.

## Skill structure

- [ ] `SKILL.md` has `name` and `description` only in frontmatter
- [ ] Workflow instructions in body; details in `references/`
- [ ] `agents/openai.yaml` exists and matches the skill
- [ ] Installed skill folder contains local `references/`, `scripts/`, `agents/`, `project.config.yml`, `prompt.md`, and `.env.example`, or `SKILL.md` hydrated them before reading references
- [ ] Skill install alone did not require a pre-existing workspace `.env`; first run created workspace `.env` from `.env.example` when missing
- [ ] `requirements.txt` exists in the installed skill or workspace and was installed during setup, or the skip/blocker was documented
- [ ] `scripts/create_report_skeleton.py --root <project-or-workspace-root>` ran during setup, or the skip/blocker was documented
- [ ] `python scripts/validate_config.py --root .` passes
- [ ] No secrets or hardcoded GitHub accounts in skill files
- [ ] `project.config.yml` has non-secret defaults

## Environment

- [ ] New/full pipeline started with read-only Discovery & Requirements before automatic project setup and configuration
- [ ] Project setup and configuration auto-ran only after discovery requirements were accepted, or stopped because a setup safety gate was triggered
- [ ] Project setup and configuration stayed setup-only: scaffold, dependency install, connection validation, parse validation, and reports only
- [ ] Project setup and configuration did not generate source YAML, build medallion layers, create automation workflows, replace warehouse objects, commit, or push
- [ ] Initial discovery stayed lightweight; detailed discovery happened phase-by-phase before sources/bronze/silver/gold/etc.
- [ ] Python venv and dbt adapter installed
- [ ] `dbt debug` passes
- [ ] Profile target schema hygiene was checked and written to setup report and pipeline status
- [ ] Profile target schema does not equal source schema, or every output is explicitly routed and the mitigation is documented
- [ ] No `UPDATE`, `INSERT`, `DELETE`, `TRUNCATE`, `MERGE`, `CREATE`, `DROP`, `ALTER`, backfill, repair, or status-changing action was run against the configured source schema or source tables
- [ ] Any user request that sounded like changing source rows was implemented only as dbt model logic, a non-source seed/mapping, a dbt test, an audit, or a non-source snapshot, and the source remained unchanged
- [ ] Generic or risky profile target schemas were documented with explicit routing evidence before builds
- [ ] `.gitignore` excludes credentials and generated files
- [ ] `.env` loaded for non-secret inputs when present; `.env.example` contains no secrets when committed
- [ ] Active dbt profile adapter was resolved before discovery
- [ ] No warehouse connector, cloud identity check, metadata query, or Model Context Protocol warehouse discovery ran before `.env` and the selected dbt profile adapter were resolved
- [ ] Discovery announced the selected profile and adapter before querying the warehouse
- [ ] Discovery used only the selected dbt profile adapter and did not probe unrelated warehouses or cloud connectors
- [ ] If the configured source was missing, empty, inaccessible, ambiguous, mismatched, or wrong, the agent stopped after metadata-only candidate listing and asked for approval before switching
- [ ] The agent did not change database, dataset, catalog, schema, table, tenant, client, domain, environment, assumption, `.env`, or profile settings before source approval
- [ ] The agent did not profile candidate tables, infer relationships, create diagrams, update `.env`, or write discovery reports for a replacement source before approval
- [ ] Once a source was approved, the approved source stayed locked for the run unless the user approved a later switch
- [ ] Fresh clone without `.env` creates a safe local `.env` template and stops for required user inputs before dbt commands
- [ ] Generated `.env` contains placeholders only until the user provides real values
- [ ] The agent did not fill `.env` from profile target schema, profile database name, warehouse schemas, previous runs, examples, or guesses
- [ ] Discovery reports were not created or updated while `.env` was missing, invalid, or placeholder-only
- [ ] Missing required first-run values were requested directly from the user, not found by repository search, terminal inspection, other workspaces, or previous runs
- [ ] Missing `DBT_PROFILE_NAME` was requested as a clear profile-selection question with adapter/database/schema context for each option
- [ ] When `DBT_PROFILE_NAME` was missing or ambiguous, available profiles were listed with adapter and non-secret notes, and the agent did not choose one automatically
- [ ] Any subagent delegation was read-only/draft work; main agent kept dbt commands, edits, commits, and final decisions
- [ ] `AGENT_PLAN.md` created or updated with automatic setup-only project setup status and approved plans for each implemented non-setup phase
- [ ] After valid required inputs were confirmed, discovery created `reports/agent/00_discovery/discovery_report.md` before the chat summary, even if the dbt project root did not exist yet
- [ ] Discovery inspected schemas, tables, columns, row counts, candidate keys, date fields, status fields, amount fields, relationships, grain evidence, possible facts, possible dimensions, possible marts, and possible metrics where supported by the adapter and source evidence
- [ ] Discovery created or updated `reports/agent/00_discovery/cardinality_report.md` and `reports/agent/00_discovery/relationship_profile.md` when relationships or candidate joins existed
- [ ] Discovery created `reports/agent/00_discovery/requirements.md` before the chat summary with source-derived requirements, evidence, confidence, recommended defaults, open questions, and deferred or blocked scope
- [ ] Discovery created reusable SQL proof files under `reports/agent/00_discovery/sql_proofs/` for table inventory, row counts, candidate keys, important status or business-state counts, date coverage, numeric summaries, and relationship/cardinality checks where supported
- [ ] Every discovery SQL proof file includes purpose, expected result, captured result, status, and runnable SQL
- [ ] Discovery report includes recommended medallion direction for sources, bronze/staging, silver/intermediate, and gold/marts
- [ ] Discovery report includes a Mermaid entity relationship diagram when credible relationships exist
- [ ] Discovery report includes other necessary Mermaid diagrams, such as source inventory, business process flow, or high-level medallion direction, when they help review the project
- [ ] Canonical phase report paths from `references/report-artifact-organization.md` were created or updated for each implemented phase
- [ ] Managed report skeleton exists with `_proof_index.md` files in every SQL proof folder so humans can identify what each proof folder is for
- [ ] `reports/agent/PIPELINE_STATUS.md` updated after each phase
- [ ] `reports/agent/CONTEXT_TREE.md` updated with user inputs, decisions, phase outputs, report links, and open items
- [ ] `reports/agent/NEXT_PHASE_PROMPT.md` created or updated after each completed or blocked checkpoint when a next phase is recommended
- [ ] `reports/agent/REPORT_INDEX.md` exists and groups reports by phase, status, purpose, and human verification action
- [ ] New phase-specific reports use the managed folder layout from `references/report-artifact-organization.md`, or legacy flat layout is explicitly documented for an existing project
- [ ] New projects do not contain phase-specific reports, logs, codegen output, relationship reports, cardinality reports, analytics files, or presentation files directly under `reports/agent/`
- [ ] If a legacy flat layout exists, `REPORT_INDEX.md` labels those files as legacy and points to canonical files for new writes
- [ ] `reports/agent/HUMAN_VERIFICATION_GUIDE.md` exists after analytics insight reporting or final delivery and explains where to verify layers, key performance indicators, blocked items, and presentation artifacts
- [ ] The next-phase prompt shown to the user includes current completed phase, recommended next phase, why it is next, exact prompt to run, included scope, not included scope, known caveats, reports/files to create, and approval question
- [ ] Chat summary after each completed or blocked checkpoint explained what was completed, what passed/warned/failed, what is recommended next, what the next phase will and will not include, and pasted the exact next-phase prompt; it did not only point to `NEXT_PHASE_PROMPT.md`
- [ ] When the agent runtime supports native questions, buttons, choice prompts, or approval widgets, the agent asked approval through that interactive UI instead of making the user copy/paste or type a magic phrase
- [ ] Interactive next-phase approval offered `Yes, run this prompt` as the recommended option and included a change/pause option; if unavailable, the text fallback was shown
- [ ] Natural approval responses such as Yes, Proceed, Approved, Continue, Run this prompt, Looks good, or Go ahead were accepted only after the exact plan or next-phase prompt was shown
- [ ] The agent did not require exact magic phrases such as `approve sources`, `approve bronze`, `approve silver`, or `approve gold` after showing the exact prompt
- [ ] The agent did not treat silence as approval and did not auto-run the next phase immediately after phase completion
- [ ] If the user requested changes to scope, models, key performance indicators, privacy, schemas, validation, materialization, or files, `AGENT_PLAN.md` and `NEXT_PHASE_PROMPT.md` were revised before proceeding
- [ ] Before executing an approved `NEXT_PHASE_PROMPT.md`, the agent reloaded the approved next-phase context bundle and did not run the next prompt in isolation
- [ ] Final delivery included analytics insight reporting outputs before the presentation-layer recommendation
- [ ] Analytics insight reporting separated raw measures, contextual metrics, and strategic key performance indicators instead of treating all measures as key performance indicators
- [ ] `business_process_catalog.md`, `fact_catalog.md`, and `dimension_catalog.md` were created or updated when analytics insight reporting ran
- [ ] `measure_catalog.md` was created or updated with broad validated raw measures from supported facts, dimensions, and marts using table-classification minimums, not a flat `5 key performance indicators per table` rule
- [ ] `metric_catalog.md` was created or updated with contextual metrics promoted from measures
- [ ] `kpi_discovery_matrix.md` covers fact tables × measure families with confidence `HIGH`, `MEDIUM`, `LOW`, or `BLOCKED`
- [ ] `kpi_catalog.md` contains only decision-relevant reconciled key performance indicators; useful non-strategic items remain in measure or metric catalogs or `insight_backlog.md`
- [ ] Every published measure, metric, and key performance indicator in catalogs or executive outputs links to `sql_proofs/*.sql` per `docs/kpi_proof_standards.md`
- [ ] `python scripts/validate_kpi_proofs.py --root .` passed, or the phase report documents each failure with evidence and `insight_backlog.md` explains catalog shortfalls
- [ ] After analytics insight reporting, the agent asked the presentation-layer decision with a concise evidence summary, recommended technology/page set, key caveats, and native clickable options when available
- [ ] Presentation decision options included the equivalent of `Yes - build Matplotlib refreshable web report (recommended)`, `Yes - prepare Power BI Desktop template handoff`, `No presentation layer - complete final delivery now`, and `Tell me what to change first`
- [ ] `reports/agent/09_analytics_insights/analytics_insight_report.md`, `kpi_discovery_matrix.md`, `reporting_catalog.md`, `kpi_catalog.md`, `dashboard_spec.md`, `insight_backlog.md`, and `reporting_readiness_scorecard.md` exist when analytics insight reporting ran
- [ ] `reports/agent/09_analytics_insights/kpis/kpi_reconciliation_report.md`, `kpi_lineage_proofs.md`, `kpi_variance_report.md`, and `sql_proofs/` exist when approved or implemented key performance indicators exist
- [ ] Measure, metric, key performance indicator, reconciliation, and presentation verification proofs are written as reusable SQL proof files with captured results, not only pasted into Markdown tables
- [ ] Analytics insight reporting separated trusted outputs from uncertain or deferred outputs
- [ ] Analytics insight reporting classified tables, detected grain, mapped candidate metrics to generic archetypes, scored confidence, and asked only targeted business questions for uncertain key performance indicators
- [ ] `kpi_catalog.md`, semantic metrics, and Power BI DAX measures promoted only `HIGH` confidence or user-approved `MEDIUM` confidence key performance indicators
- [ ] `LOW` and `BLOCKED` key performance indicators were deferred to `insight_backlog.md` with the missing grain, mapping, formula, relationship, privacy, or business-rule reason
- [ ] Every cataloged key performance indicator and report/page maps to validated marts or semantic metrics
- [ ] Presentation layer used analytics insight outputs as scope and did not invent contradictory pages, key performance indicators, or visuals without explicit user override
- [ ] Final delivery included a presentation layer recommendation and asked whether the user wants a presentation layer
- [ ] Presentation layer recommendation was not skipped silently; if blocked or skipped, the reason was written to final report, pipeline status, context tree, and final response
- [ ] Any diagram created or changed uses Mermaid and has visibility/parse verification recorded
- [ ] User-facing output uses full wording and avoids shorthand except for official tool names, commands, filenames, environment variables, package names, or code identifiers
- [ ] Project knowledge files and `project_rules` were read when present and summarized in phase plans/reports
- [ ] New reusable dbt knowledge from chat was persisted only after user approval and without secrets

## dbt Agent Skills & packages

- [ ] dbt Agent Skills installed ([install-dbt-agent-skills.md](install-dbt-agent-skills.md))
- [ ] `packages.yml`: codegen, dbt_utils, dbt_expectations, dbt_project_evaluator, audit_helper
- [ ] Every standard dbt package in `packages.yml` has a pinned exact or range-bounded `version:` and `package-lock.yml` was reviewed after `dbt deps`
- [ ] `dbt deps` succeeds
- [ ] `dispatch` block for dbt_project_evaluator in `dbt_project.yml`
- [ ] Evaluator vars align package checks with active layer names (`bronze/silver/gold` by default)
- [ ] `mart_` reporting models are accepted through `marts_prefixes`
- [ ] `dbt build --select package:dbt_project_evaluator` run (review results)
- [ ] Evaluator result queries inspected available columns before selecting version-specific fields
- [ ] Evaluator warnings fixed or documented as accepted exceptions

## Warehouse

- [ ] Source schema accessible
- [ ] Source schema remains read-only input; no dbt-created models, evaluator tables, seeds, snapshots, or audit outputs were materialized there
- [ ] Layer schemas build using configured layer schema suffixes
- [ ] dbt_project_evaluator outputs build in `<layer_schema_prefix>_evaluator`, not `source_schema`

## Source profiling

- [ ] Row counts reviewed for each source table
- [ ] Candidate primary keys and important relationships reviewed
- [ ] Entity relationships, when diagrammed, use Mermaid `erDiagram`
- [ ] Important date, amount/measure, status, type, and code columns identified
- [ ] Empty tables, duplicate keys, null keys, and major data quality concerns summarized

## dbt project

- [ ] Project name/root and project slug were derived from source/project signals or explicitly provided; not accidentally copied from `dbt_profile_name` or raw `DBT_DOMAIN`
- [ ] `DBT_DOMAIN` and `DBT_BUSINESS_DESCRIPTION` were used for business context only, not directly as folder paths, physical schema prefixes, database names, or source names
- [ ] Source YAML UTF-8 with `schema:` set
- [ ] Source YAML is stored under `models/sources/`, not under bronze/silver/gold layer folders
- [ ] Source YAML was not moved into bronze/staging only to satisfy evaluator source-directory warnings
- [ ] `dbt_project.yml` layer blocks match user layer names
- [ ] Materialization matches `materialization_profile`

## Layers

- [ ] Each non-setup phase had Markdown plan approval before implementation
- [ ] Each phase plan was based on focused phase discovery, not a full upfront design
- [ ] Each phase plan included an agent recommendation, evidence, what looks right, what is not ready, confidence, and approval needs
- [ ] The agent recommended a path instead of asking the user to design every model from scratch
- [ ] Each phase report documents what passed, warned, failed, or needs review
- [ ] Staging: all source tables, tests pass
- [ ] Intermediate: domain-appropriate reusable business logic models build successfully
- [ ] Marts: domain-appropriate facts, dimensions, and reporting marts build successfully
- [ ] Many-to-many relationships were reviewed during marts planning; required bridge tables were built and tested, or deferrals were documented with evidence
- [ ] Marts were created based on source evidence and approved requirements; no fixed number of dimensions, facts, bridge tables, reporting marts, or metrics was forced
- [ ] Final facts document grain, measures, additive/semi-additive/non-additive behavior, date field, dimension keys, validation evidence, assumptions, and caveats
- [ ] Final dimensions document business entity, primary key, descriptive attributes, privacy notes, validation evidence, assumptions, and caveats
- [ ] Semantic layer: metrics on marts ([semantic-layer-spec.md](semantic-layer-spec.md))
- [ ] Gold/marts report includes key performance indicator definitions or explicitly deferred metrics with missing evidence
- [ ] Gold/marts report includes metric verification results for implemented key performance indicators, including expected versus actual numerator, denominator, filter logic, and final result
- [ ] Semantic metrics trace to approved or clearly supported key performance indicator definitions
- [ ] Semantic metrics trace to reconciled key performance indicators and match gold SQL verification
- [ ] Each layer: `dbt parse` + `dbt build --select +path:...` PASS
- [ ] Each bronze/staging, silver/intermediate, and gold/marts layer ran warehouse data validation queries after `dbt build`
- [ ] Each layer report includes `Data Verification Results` with row counts, expected-empty evidence, grain checks, relationship checks, measure checks, result, and notes
- [ ] Each bronze/staging, silver/intermediate, and gold/marts layer wrote reusable SQL proof files under that phase's `sql_proofs/` folder for row counts, upstream comparisons, grain/key checks, relationships, status distributions, date coverage, numeric measure summaries, and privacy checks where applicable
- [ ] Each layer report includes a `SQL Proof Files` section linking proof paths to the captured result summary and status
- [ ] `grain_validation_report.md`, `join_safety_report.md`, `cardinality_report.md`, and `relationship_profile.md` were created or updated when joins, relationships, final models, or Power BI relationships were in scope
- [ ] The user-facing summary after each layer shared the important data validation results, not only the dbt command result
- [ ] Bronze/staging row counts were compared to source tables where one-to-one staging was expected
- [ ] Silver/intermediate models were checked for row presence, grain preservation, row loss, row multiplication, relationship integrity, and mapping coverage when mappings were used
- [ ] Gold/marts facts, dimensions, and reporting marts were checked for data presence when upstream data existed
- [ ] Unexpected empty gold/marts models stopped the pipeline before semantic layer, documentation, presentation layer, or final delivery unless the user explicitly accepted the issue
- [ ] Empty models with empty upstream sources were documented as expected-empty warnings instead of silently passing

## Mappings and business rules

- [ ] `project_rules` applied or explicitly marked not provided
- [ ] Manual mappings implemented as seeds or reference-table joins where appropriate
- [ ] Mapping coverage checked; unmapped values summarized or approved
- [ ] Business grain and key assumptions documented in model YAML or handoff notes
- [ ] Key performance indicators include business meaning, source model, grain, numerator, denominator, filters, time field, caveats, validation evidence, and approval status
- [ ] Key performance indicators include expected versus actual reconciliation from upstream logic to gold, semantic, and presentation layers where implemented
- [ ] Key performance indicators include source-to-final proof, first failing layer when variance exists, variance percentage, proof file paths, and cardinality/grain proof
- [ ] Final delivery did not mark any approved key performance indicator as trusted when source-to-final variance was unexplained
- [ ] Metrics define numerator, denominator where applicable, filters, time field, allowed dimensions, caveats, approval status, and validation evidence
- [ ] Ambiguous key performance indicators were deferred or sent for user approval instead of silently implemented

## Data engineering guardrails

- [ ] Each model has one documented grain
- [ ] Each final model has grain validation with row count, distinct grain key count, duplicate grain keys, null grain keys, status, and notes
- [ ] Joins that can change grain have row multiplier, row loss, and safe/unsafe status documented
- [ ] Each phase plan includes a data-engineering decision check with evidence
- [ ] Recommendations are recorded in `CONTEXT_TREE.md` with approved/changed/deferred status
- [ ] Confidence notes are recorded in `CONTEXT_TREE.md` with proven facts separated from uncertain business assumptions
- [ ] Any business-impacting decision that could not be proven from source data was approved by the user
- [ ] Incremental models have a unique key and clear update/filter rule
- [ ] Snapshots considered for slowly changing dimensions or historical attributes
- [ ] Source freshness added only when a reliable loaded-at timestamp exists
- [ ] Exposures added or recommended for known dashboards and downstream consumers
- [ ] Sensitive fields reviewed before reaching marts
- [ ] Direct identifiers and sensitive fields were excluded, masked, hashed, or explicitly approved before reaching gold/marts
- [ ] Unclear coded fields were passed through bronze/staging as raw unmapped codes, mapped from approved definitions, or explicitly approved for raw audit exposure
- [ ] Ambiguous, placeholder, abbreviated, generic, or poorly named fields were not renamed unless the user approved exact final names after value-pattern review
- [ ] The agent recommended safe defaults for sensitive and unclear fields instead of only asking the user what to do

## Git

- [ ] Git mode is local-only by default; GitHub repository owner resolved only when push was requested
- [ ] Staged commits per layer ([github-setup.md](github-setup.md))
- [ ] Pushed only when repository mode is not `local-only` and user approved
- [ ] No secrets in commits

## Documentation

- [ ] Model/column descriptions in YAML
- [ ] `dbt docs generate` -> manifest + catalog exist
- [ ] Documentation serve command or local documentation URL provided when user wants to view documentation
- [ ] Presentation options were recommended after analytics insight reporting: documentation only, business-facing report, dashboard design, semantic layer refinement, or query handoff
- [ ] If the user approved a presentation layer and did not specify another technology, the agent used the Matplotlib refreshable web report workflow by default and created `reports/agent/10_presentation/matplotlib/` artifacts with SQL verification
- [ ] If Matplotlib artifacts were created, missing `matplotlib`, `numpy`, or `pandas` packages were installed or the install blocker was documented with exact commands attempted
- [ ] If Matplotlib artifacts were created, `kpi_figure_coverage.md` maps **every key performance indicator in `kpi_catalog.md`** to `RENDERED`, `BLOCKED`, or `DEFERRED`, and recommended measures/metrics appear in supporting tabs
- [ ] If Matplotlib presentation artifacts were created, `serve_report.py` and `report.html` are the primary deliverable, with rich colorful classified tabs, summary cards, chart cards, captions, caveats, validation status, refresh timestamp/control, and `open_report.bat` or an equivalent browser launcher documented
- [ ] If a presentation artifact was created, the dashboard/report uses a polished professional design with clear page hierarchy, intentional color palette, cards, captions, exception callouts, detail sections, and Report Information content rather than default or plain styling
- [ ] If Matplotlib presentation artifacts were created, charts render through live Matplotlib SVG/HTML endpoints or approved browser-native charts from refreshed JSON; PNG is not the primary rendering path
- [ ] If Matplotlib presentation artifacts were created, PNG/SVG files are optional exports or snapshots only and are clearly labeled as not automatically updating
- [ ] If Matplotlib artifacts were created, chart axes, legends, and HTML section titles use business labels from dimensions/mappings/`label_dictionary.md`, not raw codes
- [ ] If Matplotlib artifacts were created, `label_dictionary.md` documents code-to-label mappings used in the report pack
- [ ] If Matplotlib presentation artifacts were created, `report_theme.md`, `report_theme.py`, and custom CSS were applied for eye-comfortable charts and colorful HTML tabs/cards, not default gray matplotlib output or unstyled browser-default HTML
- [ ] If Matplotlib presentation artifacts were created, `serve_report.py --smoke-test` or the documented server smoke test ran or the blocker was documented, `scripts/validate_local_web_report.py` proved the local report URL returned HTTP 200 and non-empty HTML, every `RENDERED` row appears in the correct HTML tab/section with SQL proof, and chart scope matches `dashboard_spec.md`
- [ ] If the user explicitly chose Power BI, the agent used the Power BI Desktop human-connected template workflow instead of generating a full PBIP automatically
- [ ] The human-connected Power BI checkpoint created the output folder and provided the exact PBIP path/name, approved table list, relationship checklist, storage-mode recommendation, measures table requirement, and confirmation request
- [ ] The agent stopped before injecting measures, visuals, or editing PBIP files until the user confirmed the PBIP was saved and data was attached
- [ ] Generated PBIP mode was not used unless the user explicitly approved generated PBIP/TMDL creation
- [ ] If the user provided or approved a Power BI Desktop-created PBIP template, the thin model template workflow was used and the approved path was recorded
- [ ] If the thin model template workflow was used, the exact template path, approval, copied output path, and pre-edit Desktop open status were recorded
- [ ] If the thin model template workflow was used, the agent injected only approved DAX measures, descriptions, format strings, display folders, and safe annotations into the approved measures table such as `_KPI_Measures` or `_Measures`
- [ ] If the thin model template workflow was used, Power Query M, connection definitions, credentials, physical imported tables, source partitions, schemas, and relationships were verified unchanged unless explicitly approved
- [ ] If the thin model template workflow was used and no measures table existed, the agent paused for approval before creating one
- [ ] If generated Power BI PBIP/TMDL mode was explicitly approved, the bundled neutral template at `assets/powerbi/pbip_template/` was used as the default structural base, or any local PBIP reference was explicitly approved by the user with the exact path documented
- [ ] If Power BI PBIP/TMDL structure was uncertain and internet access was available, official Microsoft Power BI project documentation was checked and cited in `reports/agent/10_presentation/presentation_report.md` or a documented legacy presentation report
- [ ] If Power BI PBIP/TMDL was created from the bundled template, `scripts/generate_powerbi_pbip.py` was used or an equivalent generator fallback was documented
- [ ] If a local PBIP reference was used, only structural patterns were reused; source connections, business content, measures, relationships, visuals, page names, branding, `.pbi/` cache files, logical IDs, lineage tags, and source database names were not copied unless explicitly approved
- [ ] If the bundled template or a local reference was used, Report and SemanticModel logical IDs and TMDL lineage tags were regenerated
- [ ] If Power BI PBIP/TMDL was created, PBIP includes the project file, Report artifact, SemanticModel artifact, TMDL/definition files, relationships, measures, parameters, and handoff README
- [ ] If Power BI or another presentation layer was approved, `reports/agent/10_presentation/powerbi_model_plan.md`, `reports/agent/10_presentation/dashboard_pages.md`, `reports/agent/10_presentation/dax_measures.md`, or equivalent technology-specific planning files were created when applicable
- [ ] If Power BI PBIP/TMDL was created from a user-provided contract, every required output path, artifact folder, schema string, compatibility level, parameter, source partition, relationship, measure label, report page, and visual was checked against that contract
- [ ] If Power BI PBIP/TMDL was created, the `.pbip` points to the Report artifact, and the Report artifact definition links to the SemanticModel artifact with the correct relative path
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, the root `.pbip` shortcut artifact entry uses the required `report` property and does not use unsupported properties such as `dataset`
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, every `.pbip` report artifact path resolves to an existing `.Report` folder
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, the referenced Report artifact includes root-level `definition.pbir`, the file is non-empty, parses as JSON, and contains `datasetReference.byPath.path`
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, root-level `definition.pbir` points to an existing `.SemanticModel` artifact folder with the correct relative path
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, legacy nested `definition/definition.pbir` was not created for enhanced PBIR
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, the Report artifact includes `definition/version.json` with the report definition version metadata schema and a non-empty version string
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, enhanced PBIR metadata exists at `definition/report.json`, `definition/version.json`, and `definition/pages/pages.json`
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, legacy root-level `report.json` was not created for enhanced PBIR
- [ ] If Power BI PBIP/TMDL was created, import partitions use approved parameters for host, database, schema, warehouse, or equivalent connection values
- [ ] If Power BI PBIP/TMDL was created from PostgreSQL, import partitions do not use a `PgSchema` expression, quote server/database parameter references, hardcode the approved schema in each source record, select only modeled columns, transform date and numeric types, and include `PBI_ResultType = Table`
- [ ] If Power BI PBIP/TMDL was created, approved report pages exist as Power BI report definition artifacts with actual `visual.json` files, not only Markdown page descriptions or empty page shells
- [ ] If a presentation artifact was created, the agent produced a consultant-grade page plan from validated facts, dimensions, semantic metrics, source profiling, and data quality evidence instead of asking the user to design every visual
- [ ] If a presentation artifact was created, every key performance indicator visual or measure was reconciled to gold or semantic SQL, including numerator, denominator, filters, and final result
- [ ] If a Power BI artifact was created, every DAX measure maps to `reports/agent/09_analytics_insights/kpis/kpi_catalog.md`, a validated semantic metric, or an explicit user-approved requirement
- [ ] If a Power BI artifact was created, every DAX measure maps to source-to-final key performance indicator reconciliation and cardinality proof
- [ ] If a Power BI artifact was created, no Power BI-only key performance indicator, denominator, business flag, surrogate key, or relationship shortcut was invented to compensate for missing dbt logic
- [ ] If a presentation artifact or business-facing report was created, it includes the five report pillars: context and strategy, key performance indicators, trend analysis and variance, insights and attribution, and recommendations and next steps; unsupported pillars are visibly deferred with reasons
- [ ] If a Power BI report was created, each main page follows the fixed canvas standard when supported: header/navigation, last refreshed timestamp, reset filters, prioritized key performance indicator cards, primary slicers, trend/comparison visuals, detail layer, and tooltip or drill-through behavior
- [ ] If a Power BI report was created, it uses an intentional professional theme instead of default Power BI styling, and `presentation_report.md` records the palette source, color meanings, theme path, and formatting limitations
- [ ] If a Power BI report was created, the agent analyzed the maximum useful supported key performance indicators, prioritized the executive card row, placed supporting key performance indicators in a suitable detail/report information area, and listed deferred key performance indicators with reasons
- [ ] If a Power BI report was created, it includes a Report Information, Report Settings, or About This Report page with purpose, audience, data source, refresh details, page guide, key performance indicator definitions, filter definitions, caveats, privacy handling, validation summary, and open decisions
- [ ] If a Power BI report could not include a canvas-standard element, `reports/agent/10_presentation/presentation_report.md` documents the missing element and reason
- [ ] Presentation pages were included, deferred, or blocked based on current project evidence, not hardcoded from another domain
- [ ] Presentation design maximizes validated business insight with executive overview, trends, financial or value, operations or activity, entity performance, segmentation, exceptions, and detail or drillthrough pages when supported
- [ ] Presentation design does not expose every available column as a substitute for insight; technical fields are hidden and sensitive fields are excluded, masked, aggregated, or explicitly approved
- [ ] Presentation plan and report record page rationale, source models, measures, filters, slicers, privacy handling, blocked visuals, and verification queries
- [ ] If Power BI PBIP/TMDL or another presentation artifact was created and validated facts have usable date columns, a `Trends` page or equivalent standard time showcase was included
- [ ] Standard time showcase visuals include last calendar year, year to date, last 12 months, by-year, and by-month views for each primary fact where a measure and time field were validated
- [ ] Fact time fields were discovered from gold facts, model YAML, semantic models, or mart SQL; field names were not hardcoded from one domain unless present in the current project
- [ ] Time showcase visuals use governed measures or reportable filters where they exist
- [ ] Time showcase visual numbers were validated with SQL, and `reports/agent/10_presentation/presentation_report.md` includes the exact query and result for each visual
- [ ] If Power BI PBIP/TMDL was created, Markdown import guides, DAX snippets, relationship notes, or dashboard page descriptions were not marked as the completed Power BI artifact
- [ ] If Power BI PBIP/TMDL was created, JSON parse checks, TMDL structure checks, file-tree checks, and known metadata-version checks were run and recorded
- [ ] If Power BI PBIP/TMDL was created and `scripts/validate_powerbi_pbip.py` was available, the script passed and its result was recorded in `reports/agent/10_presentation/presentation_report.md`
- [ ] If Power BI PBIP/TMDL was created for Power BI Desktop, the target Desktop version was detected or explicitly recorded as unavailable, and the result was recorded in `reports/agent/10_presentation/presentation_report.md` or the legacy presentation report
- [ ] If Power BI PBIP/TMDL was created for Power BI Desktop, version-aware static validation was run with `--require-powerbi-desktop-version --powerbi-desktop-version <version>` when a Desktop version was available
- [ ] If Power BI PBIP/TMDL was created, the agent checked whether Power BI Modeling Model Context Protocol tools were available or installable before handoff
- [ ] If Power BI Modeling Model Context Protocol tools were not already exposed, the agent checked or recommended the official Microsoft package `@microsoft/powerbi-modeling-mcp` from `https://github.com/microsoft/powerbi-modeling-mcp`
- [ ] If Power BI Modeling Model Context Protocol tools were available, they were used for `ConnectFolder`, model inspection, relationship inspection, and DAX smoke testing; availability without use is a validation failure
- [ ] If Power BI Modeling Model Context Protocol tools were not available, the presentation report records the tool search/connector check, install attempt or install recommendation, and exact reason validation was not run
- [ ] If `pbi-cli` was available or approved, it was used only as an optional helper for DAX validation, semantic model audit, relationship checks, or report-layer inspection, not as the source of business truth
- [ ] If Power BI PBIP/TMDL was created, every `.platform` file has a `$schema` value matching the supported Fabric git integration platform properties schema pattern for the target Power BI Desktop version
- [ ] If Power BI PBIP/TMDL was created, every `.platform` file has a non-empty `config` object and is not only a schema stub
- [ ] If Power BI PBIP/TMDL was created, every `.platform` file has `config.version` set to `"2.0"` and `config.logicalId` set to a stable UUID string
- [ ] If Power BI PBIP/TMDL was created, every `report.json` includes `themeCollection.baseTheme.reportVersionAtImport` as a non-empty string with the target-version value, defaulting to `"5.55"` unless a known-good project reference proves another value
- [ ] If Power BI PBIP/TMDL was created, every `report.json` `resourcePackages.items[].path` reference resolves to an existing file under the Report definition folder, including base theme JSON files
- [ ] If Power BI PBIP/TMDL was created, TMDL table files were checked for Markdown code fences and invalid unindented loose Power Query keywords outside a valid partition/source expression block
- [ ] If Power BI PBIP/TMDL was created, TMDL files were checked for bare Power Query M steps such as `AddedKey = Table.AddColumn(...)` outside valid partition source expression blocks
- [ ] If Power BI PBIP/TMDL was created, table `.tmdl` files do not contain root-level annotations such as unindented `annotation PBI_ResultType = Table`
- [ ] If Power BI Desktop reports duplicate annotation merge errors such as `TMDL objects cannot be merged because both declare the same property: value`, the presentation phase is marked failed and fixed before handoff
- [ ] If Power BI PBIP/TMDL was created, linguistic metadata content type and actual content format were checked; XML-typed metadata does not contain JSON and JSON-typed metadata does not contain XML
- [ ] If Power BI PBIP/TMDL was created, JSON such as `{ "Version": "1.0.0" }` was not written into XML-typed linguistic metadata
- [ ] If Power BI PBIP/TMDL was created, SemanticModel `definition/cultures/` files, `ref cultureInfo`, and report linguistic schema artifacts were omitted unless exact target-version Desktop-generated support was approved and validated
- [ ] If Power BI PBIP/TMDL was created, TMDL column metadata was checked so no table has more than one column with `IsKey` set to `True`
- [ ] If Power BI PBIP/TMDL was created, the generator did not mark every `*_id` column as `IsKey`; foreign keys stayed unmarked unless explicitly required by a validated Power BI pattern
- [ ] If Power BI PBIP/TMDL was created, every one-side relationship key is unique and not null in dbt, and composite business keys use a surrogate key instead of a repeated partial natural key
- [ ] If Power BI PBIP/TMDL was created, many-to-many relationships were not created unless explicitly approved and backed by a tested bridge table
- [ ] If Power BI PBIP/TMDL was created, all TMDL `lineageTag` values are unique across the semantic model
- [ ] If Power BI PBIP/TMDL was created, the measures or metrics table has a calculated partition such as `ROW("MetricKey", 1)`
- [ ] If Power BI PBIP/TMDL was created, calculated measures or metrics table columns such as `MetricKey` include `sourceColumn` metadata such as `sourceColumn: [MetricKey]`
- [ ] If Power BI Desktop reports `PFE_TM_METADATA_CALCTABLE_COLUMN_MISSING_SOURCECOLUMN`, the presentation phase is marked failed and fixed before handoff
- [ ] If Power BI PBIP/TMDL was created, active relationships were audited for ambiguous filter paths, including multiple active paths between dimensions through facts or bridge tables
- [ ] If Power BI PBIP/TMDL was created, lower-grain facts, parent facts, bridge tables, and role-playing date relationships were reviewed so only the approved active paths are active
- [ ] If Power BI PBIP/TMDL was created and Power BI Modeling Model Context Protocol tools were available, `ConnectFolder` to the SemanticModel definition folder succeeded
- [ ] If Power BI PBIP/TMDL was created and Power BI Modeling Model Context Protocol tools were available, connection inspection, table inspection, relationship inspection, and a simple DAX smoke query succeeded
- [ ] If Power BI PBIP/TMDL was created and Power BI Modeling Model Context Protocol validation was not run, the presentation report clearly says it was not run and why; it does not claim the semantic model loaded successfully
- [ ] If Power BI PBIP/TMDL was created and Power BI Desktop was available, the generated `.pbip` was opened or launched for load validation, and any Desktop load error was fixed before marking the presentation phase complete
- [ ] If Power BI Desktop reported an incompatible-version error such as `NewerLinguisticSchemaVersion`, the presentation phase was marked blocked until the PBIP metadata was downgraded/removed or regenerated for the target version
- [ ] If Power BI PBIP/TMDL was created and Power BI Desktop validation was not run, the presentation report clearly says it was not run and why; it does not claim the project was opened successfully
- [ ] If Power BI PBIP/TMDL was created, `reports/agent/10_presentation/presentation_report.md` records file validation, relationship audit, Power BI Modeling Model Context Protocol validation, Desktop open validation, fixes applied, and final result
- [ ] If Power BI PBIP/TMDL was created, `reports/agent/PIPELINE_STATUS.md` marks presentation `PASS` only after required validation passed, or `BLOCKED` when required validation could not run or failed

## Human review

- [ ] Pre-build plan approval captured for sources, staging, intermediate, marts, semantic, evaluator, and documentation as applicable
- [ ] Staging review summary produced
- [ ] Intermediate review summary produced
- [ ] Marts and metric review summary produced
- [ ] Open business decisions, assumptions, privacy concerns, and data limitations listed

## Automation *(optional)*

- [ ] Continuous integration workflow: dependencies + parse (+ build when credentials available)
- [ ] Agents Schema workflow present
- [ ] `target/manifest.json` generated and committed when Agents Schema workflow needs it
- [ ] `WAREHOUSE_CREDENTIALS` secret configured for Snowflake, Databricks, or BigQuery
- [ ] `AGENTS` schema verified in warehouse
- [ ] Agent can query `AGENTS.ROOT` and `AGENTS.DBT_MODEL`

## Agent readiness

- [ ] Full stack documented in [dbt-packages-and-skills.md](dbt-packages-and-skills.md)
- [ ] [agent-context-prompt.md](agent-context-prompt.md) available for sessions
- [ ] Stuck or blocked runs followed [stuck-recovery.md](stuck-recovery.md)
- [ ] Phase rollback or redo requests followed [phase-rollback.md](phase-rollback.md), including status/context updates and downstream stale markers

## Final delivery

- [ ] If a presentation artifact was approved, presentation validation was completed before final delivery, or the presentation phase was marked `BLOCKED` with exact evidence; final delivery was not marked complete while validation was pending
- [ ] Final handoff notes or README include domain, profile name, schemas, final models, metrics, run commands, and known limitations
- [ ] Final response starts with a short summary, then includes results, validation, data notes, git/automation status, and open decisions
- [ ] Final response references `AGENT_PLAN.md`, `reports/agent/PIPELINE_STATUS.md`, `reports/agent/CONTEXT_TREE.md`, and relevant phase reports
- [ ] Final response references `reports/agent/NEXT_PHASE_PROMPT.md` when a recommended next action remains
- [ ] Final response includes the advanced data-engineering review status
- [ ] Phase commits created or intentionally skipped
- [ ] Final response summarizes build status, documentation status, evaluator status, Agents Schema status, git status, limitations, and open decisions
- [ ] Final response includes possible key performance indicators, semantic metrics, and presentation pages when enough final mart evidence exists
- [ ] Final response lists deferred or blocked key performance indicator definitions when definitions or data are missing
- [ ] Final response summarizes metric verification status and names any unreconciled key performance indicators
- [ ] Final response summarizes key performance indicator reconciliation, first failing layers, cardinality/grain validation, and any unexplained variance
