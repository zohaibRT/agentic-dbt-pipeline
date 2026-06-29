# Acceptance Checklist

Verify before marking the dbt pipeline workflow complete.

## Skill structure

- [ ] `SKILL.md` has `name` and `description` only in frontmatter
- [ ] Workflow instructions in body; details in `references/`
- [ ] `agents/openai.yaml` exists and matches the skill
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
- [ ] After valid required inputs were confirmed, discovery created `reports/agent/discovery_report.md` before the chat summary, even if the dbt project root did not exist yet
- [ ] Discovery created `reports/agent/requirements.md` before the chat summary with source-derived requirements, evidence, confidence, recommended defaults, open questions, and deferred or blocked scope
- [ ] Discovery report includes recommended medallion direction for sources, bronze/staging, silver/intermediate, and gold/marts
- [ ] Discovery report includes a Mermaid entity relationship diagram when credible relationships exist
- [ ] Discovery report includes other necessary Mermaid diagrams, such as source inventory, business process flow, or high-level medallion direction, when they help review the project
- [ ] `reports/agent/<phase>_report.md` created or updated for each implemented phase
- [ ] `reports/agent/PIPELINE_STATUS.md` updated after each phase
- [ ] `reports/agent/CONTEXT_TREE.md` updated with user inputs, decisions, phase outputs, report links, and open items
- [ ] Final delivery included a presentation layer recommendation and asked whether the user wants a presentation layer
- [ ] Presentation layer recommendation was not skipped silently; if blocked or skipped, the reason was written to final report, pipeline status, context tree, and final response
- [ ] Any diagram created or changed uses Mermaid and has visibility/parse verification recorded
- [ ] User-facing output uses full wording and avoids shorthand except for official tool names, commands, filenames, environment variables, package names, or code identifiers
- [ ] Project knowledge files and `project_rules` were read when present and summarized in phase plans/reports
- [ ] New reusable dbt knowledge from chat was persisted only after user approval and without secrets

## dbt Agent Skills & packages

- [ ] dbt Agent Skills installed ([install-dbt-agent-skills.md](install-dbt-agent-skills.md))
- [ ] `packages.yml`: codegen, dbt_utils, dbt_expectations, dbt_project_evaluator, audit_helper
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

- [ ] Project name/root were derived from source/domain or explicitly provided; not accidentally copied from `dbt_profile_name`
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
- [ ] Semantic layer: metrics on marts ([semantic-layer-spec.md](semantic-layer-spec.md))
- [ ] Gold/marts report includes key performance indicator definitions or explicitly deferred metrics with missing evidence
- [ ] Semantic metrics trace to approved or clearly supported key performance indicator definitions
- [ ] Each layer: `dbt parse` + `dbt build --select +path:...` PASS
- [ ] Each bronze/staging, silver/intermediate, and gold/marts layer ran warehouse data validation queries after `dbt build`
- [ ] Each layer report includes `Data Verification Results` with row counts, expected-empty evidence, grain checks, relationship checks, measure checks, result, and notes
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
- [ ] Ambiguous key performance indicators were deferred or sent for user approval instead of silently implemented

## Data engineering guardrails

- [ ] Each model has one documented grain
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
- [ ] Presentation options were recommended after documentation: documentation only, business-facing report, dashboard design, semantic layer refinement, or query handoff
- [ ] Power BI PBIP/TMDL was created when the user approved a presentation layer and did not specify another technology
- [ ] If Power BI PBIP/TMDL was created, PBIP includes the project file, Report artifact, SemanticModel artifact, TMDL/definition files, relationships, measures, parameters, and handoff README
- [ ] If Power BI PBIP/TMDL was created from a user-provided contract, every required output path, artifact folder, schema string, compatibility level, parameter, source partition, relationship, measure label, report page, and visual was checked against that contract
- [ ] If Power BI PBIP/TMDL was created, the `.pbip` points to the Report artifact, and the Report artifact definition links to the SemanticModel artifact with the correct relative path
- [ ] If Power BI PBIP/TMDL was created as a report deliverable, the root `.pbip` shortcut artifact entry uses the required `report` property and does not use unsupported properties such as `dataset`
- [ ] If Power BI PBIP/TMDL was created, import partitions use approved parameters for host, database, schema, warehouse, or equivalent connection values
- [ ] If Power BI PBIP/TMDL was created, approved report pages exist as Power BI report definition artifacts, not only Markdown page descriptions
- [ ] If a presentation artifact was created, the agent produced a consultant-grade page plan from validated facts, dimensions, semantic metrics, source profiling, and data quality evidence instead of asking the user to design every visual
- [ ] If a presentation artifact or business-facing report was created, it includes the five report pillars: context and strategy, key performance indicators, trend analysis and variance, insights and attribution, and recommendations and next steps; unsupported pillars are visibly deferred with reasons
- [ ] If a Power BI report was created, each main page follows the fixed canvas standard when supported: header/navigation, last refreshed timestamp, reset filters, prioritized key performance indicator cards, primary slicers, trend/comparison visuals, detail layer, and tooltip or drill-through behavior
- [ ] If a Power BI report was created, the agent analyzed the maximum useful supported key performance indicators, prioritized the executive card row, placed supporting key performance indicators in a suitable detail/report information area, and listed deferred key performance indicators with reasons
- [ ] If a Power BI report was created, it includes a Report Information, Report Settings, or About This Report page with purpose, audience, data source, refresh details, page guide, key performance indicator definitions, filter definitions, caveats, privacy handling, validation summary, and open decisions
- [ ] If a Power BI report could not include a canvas-standard element, `reports/agent/presentation_report.md` documents the missing element and reason
- [ ] Presentation pages were included, deferred, or blocked based on current project evidence, not hardcoded from another domain
- [ ] Presentation design maximizes validated business insight with executive overview, trends, financial or value, operations or activity, entity performance, segmentation, exceptions, and detail or drillthrough pages when supported
- [ ] Presentation design does not expose every available column as a substitute for insight; technical fields are hidden and sensitive fields are excluded, masked, aggregated, or explicitly approved
- [ ] Presentation plan and report record page rationale, source models, measures, filters, slicers, privacy handling, blocked visuals, and verification queries
- [ ] If Power BI PBIP/TMDL or another presentation artifact was created and validated facts have usable date columns, a `Trends` page or equivalent standard time showcase was included
- [ ] Standard time showcase visuals include last calendar year, year to date, last 12 months, by-year, and by-month views for each primary fact where a measure and time field were validated
- [ ] Fact time fields were discovered from gold facts, model YAML, semantic models, or mart SQL; field names were not hardcoded from one domain unless present in the current project
- [ ] Time showcase visuals use governed measures or reportable filters where they exist
- [ ] Time showcase visual numbers were validated with SQL, and `reports/agent/presentation_report.md` includes the exact query and result for each visual
- [ ] If Power BI PBIP/TMDL was created, Markdown import guides, DAX snippets, relationship notes, or dashboard page descriptions were not marked as the completed Power BI artifact
- [ ] If Power BI PBIP/TMDL was created, JSON parse checks, TMDL structure checks, file-tree checks, and known metadata-version checks were run and recorded
- [ ] If Power BI PBIP/TMDL was created and `scripts/validate_powerbi_pbip.py` was available, the script passed and its result was recorded in `reports/agent/presentation_report.md`
- [ ] If Power BI PBIP/TMDL was created, every `.platform` file has a `$schema` value matching the supported Fabric git integration platform properties schema pattern for the target Power BI Desktop version
- [ ] If Power BI PBIP/TMDL was created, `report.json` includes `themeCollection.baseTheme.reportVersionAtImport` with the correct JSON type and target-version value
- [ ] If Power BI PBIP/TMDL was created, TMDL table files were checked for invalid loose Power Query keywords such as standalone `let` or `in` lines outside a valid partition/source expression block
- [ ] If Power BI PBIP/TMDL was created, TMDL column metadata was checked so no table has more than one column with `IsKey` set to `True`
- [ ] If Power BI PBIP/TMDL was created, the generator did not mark every `*_id` column as `IsKey`; foreign keys stayed unmarked unless explicitly required by a validated Power BI pattern
- [ ] If Power BI PBIP/TMDL was created, active relationships were audited for ambiguous filter paths, including multiple active paths between dimensions through facts or bridge tables
- [ ] If Power BI PBIP/TMDL was created, lower-grain facts, parent facts, bridge tables, and role-playing date relationships were reviewed so only the approved active paths are active
- [ ] If Power BI PBIP/TMDL was created and Power BI Modeling Model Context Protocol tools were available, `ConnectFolder` to the SemanticModel definition folder succeeded
- [ ] If Power BI PBIP/TMDL was created and Power BI Modeling Model Context Protocol tools were available, connection inspection, table inspection, relationship inspection, and a simple DAX smoke query succeeded
- [ ] If Power BI PBIP/TMDL was created and Power BI Modeling Model Context Protocol validation was not run, the presentation report clearly says it was not run and why; it does not claim the semantic model loaded successfully
- [ ] If Power BI PBIP/TMDL was created and Power BI Desktop was available, the generated `.pbip` was opened or launched for load validation, and any Desktop load error was fixed before marking the presentation phase complete
- [ ] If Power BI PBIP/TMDL was created and Power BI Desktop validation was not run, the presentation report clearly says it was not run and why; it does not claim the project was opened successfully
- [ ] If Power BI PBIP/TMDL was created, `reports/agent/presentation_report.md` records file validation, relationship audit, Power BI Modeling Model Context Protocol validation, Desktop open validation, fixes applied, and final result
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

## Final delivery

- [ ] If a presentation artifact was approved, presentation validation was completed before final delivery, or the presentation phase was marked `BLOCKED` with exact evidence; final delivery was not marked complete while validation was pending
- [ ] Final handoff notes or README include domain, profile name, schemas, final models, metrics, run commands, and known limitations
- [ ] Final response starts with a short summary, then includes results, validation, data notes, git/automation status, and open decisions
- [ ] Final response references `AGENT_PLAN.md`, `reports/agent/PIPELINE_STATUS.md`, `reports/agent/CONTEXT_TREE.md`, and relevant phase reports
- [ ] Final response includes the advanced data-engineering review status
- [ ] Phase commits created or intentionally skipped
- [ ] Final response summarizes build status, documentation status, evaluator status, Agents Schema status, git status, limitations, and open decisions
- [ ] Final response includes possible key performance indicators, semantic metrics, and presentation pages when enough final mart evidence exists
- [ ] Final response lists deferred or blocked key performance indicator definitions when definitions or data are missing
