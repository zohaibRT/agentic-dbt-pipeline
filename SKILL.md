---
name: agentic-dbt-pipeline
description: >-
  Automate end-to-end dbt with an AI agent: project setup and configuration, medallion layers
  (bronze/silver/gold by default), packages (codegen, utils, evaluator, audit_helper),
  semantic layer, documentation, analytics insight reporting, per-layer git commits, optional GitHub push via GitHub command line interface, and
  user-facing final run summaries with senior data-engineering decision gates.
  Use when setting up or extending a dbt analytics project with agentic automation.
---

# dbt Analytics Engineer

Full lifecycle orchestrator for the dbt project.
**On every new/full-pipeline prompt:** agent runs read-only [discovery-requirements.md](references/discovery-requirements.md) first, explains what it concluded from the source data, and asks for requirements before any build plan.
**Default full pipeline:** discovery -> project setup and configuration -> sources -> bronze -> silver -> gold -> semantic layer -> project evaluator -> documentation -> analytics insight reporting -> presentation layer recommendation -> continuous integration, plus Agents Schema when enabled and supported.

Use `workflow_phase:` to run a single phase. Project setup and configuration runs automatically for new/full pipeline work unless the user explicitly disables automatic setup.

**Install (one command):** `npx skills add zohaibRT/agentic-dbt-pipeline` - see [references/install-skill.md](references/install-skill.md).
Project setup and configuration auto-installs dbt Agent Skills and dbt packages on first run.

## Local resource hydration

Some versions of `npx skills add` install only this `SKILL.md` entry file into agent folders. This skill is intentionally multi-file, so before reading any `references/`, running any `scripts/`, or using `project.config.yml`, verify that these resources exist next to this `SKILL.md`:

```text
references/
scripts/
agents/
project.config.yml
prompt.md
.env.example
```

If any are missing, hydrate the installed skill folder from the repository before continuing. Use the directory containing this `SKILL.md` as `{skill_dir}`. Do not hydrate into the user's dbt project root.

PowerShell:

```powershell
$skillDir = "<directory containing this SKILL.md>"
$tmp = Join-Path $env:TEMP ("agentic-dbt-pipeline-" + [guid]::NewGuid().ToString())
git clone --depth 1 https://github.com/zohaibRT/agentic-dbt-pipeline.git $tmp
Copy-Item -Path (Join-Path $tmp "references") -Destination $skillDir -Recurse -Force
Copy-Item -Path (Join-Path $tmp "scripts") -Destination $skillDir -Recurse -Force
Copy-Item -Path (Join-Path $tmp "agents") -Destination $skillDir -Recurse -Force
Copy-Item -Path (Join-Path $tmp "project.config.yml") -Destination $skillDir -Force
Copy-Item -Path (Join-Path $tmp "prompt.md") -Destination $skillDir -Force
Copy-Item -Path (Join-Path $tmp ".env.example") -Destination $skillDir -Force
Remove-Item -LiteralPath $tmp -Recurse -Force
```

Bash:

```bash
skill_dir="<directory containing this SKILL.md>"
tmp="$(mktemp -d)"
git clone --depth 1 https://github.com/zohaibRT/agentic-dbt-pipeline.git "$tmp"
cp -R "$tmp/references" "$skill_dir/"
cp -R "$tmp/scripts" "$skill_dir/"
cp -R "$tmp/agents" "$skill_dir/"
cp "$tmp/project.config.yml" "$skill_dir/"
cp "$tmp/prompt.md" "$skill_dir/"
cp "$tmp/.env.example" "$skill_dir/"
rm -rf "$tmp"
```

After hydration, read references and scripts from local disk only. If hydration fails because `git` or network access is unavailable, stop and tell the user the skill resources are missing instead of pretending the referenced files were read.

## Discovery first, then project setup and configuration

Read and execute [references/discovery-requirements.md](references/discovery-requirements.md) before project setup, project initialization, or full pipeline runs.

Discovery is read-only and project-oriented. It may inspect schemas, tables, columns, row counts, keys, relationships, dates, measures, and statuses. Its input/report/output must focus on the source data and analytics project, not environment setup. It must write `reports/agent/discovery_report.md`, `reports/agent/requirements.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` before the chat summary, even when the dbt project has not been initialized yet. The requirements file must capture inferred requirements, recommended defaults, unknowns, user-decision needs, and blocked/deferred scope derived from the source evidence and business domain. It must create Mermaid discovery diagrams when the source evidence supports them, including an entity relationship diagram when credible relationships exist, plus other necessary source inventory, business process, or medallion direction diagrams. It must not install packages, run codegen, create warehouse schemas, or change profiles.

Do not assume the business domain. During discovery, understand source tables, table relationships, business processes, metrics required, data quality rules, required output models, and reporting needs before proposing dbt models.

If any of those areas cannot be properly understood or proven, do not assume. Ask the user for missing business meaning or approval, and defer dependent models, tests, metrics, semantic definitions, or presentation outputs until the uncertainty is resolved.

After discovery, summarize what the agent concluded from the source data and ask whether the user wants to add requirements such as mappings, metrics, privacy rules, naming rules, included/excluded tables, or priority facts/dimensions. User responses are interpreted by the active workflow checkpoint, not by broad intent. At the discovery checkpoint, the next allowed action is only source confirmation and automatic project setup and configuration. Do not treat discovery acceptance as approval for sources, bronze/staging, silver/intermediate, gold/marts, semantic layer, evaluator, documentation, analytics insight reporting, presentation layer, continuous integration, Agents Schema, commits, pushes, or future schema switching.

## Project setup and configuration (automatic setup-only phase after discovery)

Read and execute [references/bootstrap.md](references/bootstrap.md) **before** any layer work:

1. **Install dbt Agent Skills** + all dbt packages - see [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md)
2. **`dbt debug`** - verify connection
3. **`dbt deps` + codegen** - when sources/full pipeline
4. **Resolve git mode** - local commits by default; GitHub only when push is requested - [github-repo-resolution.md](references/github-repo-resolution.md)
5. **Create continuous integration and Agents Schema workflows** - when requested, or when `auto_agents_schema: true` and the destination is supported

User one-time manual steps: **profiles.yml password**, plus **GitHub repository or secret** only when remote push, continuous integration, or Agents Schema synchronization is requested.

If `dbt_profile_name` is provided in the prompt, use it as `{project.profile}` for dbt commands and generated `dbt_project.yml`. If it is missing and multiple profiles exist in `~/.dbt/profiles.yml`, ask the user which profile to use before running dbt commands. Never guess from the first profile.

Project setup and configuration is setup-only and auto-runs by default after the discovery requirements checkpoint is accepted. Do not ask for a separate setup approval response unless a setup safety gate is triggered. This phase may create the local dbt project scaffold, install missing dbt Agent Skills and dbt packages, run `dbt debug`, run `dbt deps`, run `dbt parse`, and write setup reports. This phase does not approve source YAML generation, bronze/staging models, silver/intermediate models, gold/marts models, semantic layer files, documentation changes, continuous integration workflows, Agents Schema synchronization, warehouse model replacement, commits, or pushes.

Stop and ask before project setup and configuration if required `.env` values are missing, the selected profile is ambiguous or failing, the profile target schema equals the source schema and needs a user-approved change, existing project files would be overwritten, warehouse objects would be created or replaced beyond setup validation, credentials or secrets are needed, automatic project setup is explicitly disabled, or the user explicitly asked to approve setup manually.

## dbt packages & agent skills (mandatory stack)

Read [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md).

| Capability | Install / use |
|---|---|
| dbt Agent Skills | **Project setup auto-installs** if missing (`auto_install_dbt_skills: true`) |
| codegen | `packages.yml` + `generate_source` |
| dbt_utils | `packages.yml` - macros in models/tests |
| dbt_project_evaluator | `packages.yml` + `dispatch` + `dbt build --select package:dbt_project_evaluator` |
| audit_helper | `packages.yml` - compare queries on refactors |
| MetricFlow / Semantic Layer | [semantic-layer-spec.md](references/semantic-layer-spec.md) + `building-dbt-semantic-layer` |
| Agents Schema | [agents-schema-setup.md](references/agents-schema-setup.md) - publish dbt metadata to `AGENTS.*` for warehouse-side agent context when the destination is supported |

Install agent skills: [references/install-dbt-agent-skills.md](references/install-dbt-agent-skills.md)

## Phase map

| Phase | When | Reference |
|---|---|---|
| **Discovery** | First for new/full pipeline runs | [discovery-requirements.md](references/discovery-requirements.md), [source-profiling.md](references/source-profiling.md) |
| **Project setup and configuration** | Automatic setup-only phase after discovery requirements are accepted | [bootstrap.md](references/bootstrap.md) |
| **0 Inputs** | Always first | [skill-inputs.md](references/skill-inputs.md), [profile-listing.md](references/profile-listing.md), [project-naming.md](references/project-naming.md), [env-configuration.md](references/env-configuration.md), [source-confirmation.md](references/source-confirmation.md), [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md), [security-and-credentials.md](references/security-and-credentials.md), [schema-isolation.md](references/schema-isolation.md), [code-agent-setup.md](references/code-agent-setup.md) |
| **0a Knowledge layers** | Built-in reusable knowledge plus user dbt standards and domain rules | [skill-knowledge.md](references/skill-knowledge.md), [project-knowledge.md](references/project-knowledge.md) |
| **0b Subagents** | Optional speed-up | [subagent-workflow.md](references/subagent-workflow.md) |
| **0c Best practices** | Design guardrails | [data-engineering-best-practices.md](references/data-engineering-best-practices.md), [privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md) |
| **0c Principal standards** | Advanced software-grade data engineering standards | [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md) |
| **0c Writing style** | Full wording and five-pillar reports | [writing-style.md](references/writing-style.md), [reporting-standards.md](references/reporting-standards.md) |
| **0d Engineer gate** | Explicit modeling decisions | [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) |
| **0e Phased discovery** | Discover just enough per phase | [phased-discovery.md](references/phased-discovery.md) |
| **0f Recommendations** | Agent recommends; data engineer approves | [recommendation-and-review.md](references/recommendation-and-review.md) |
| **0g Diagrams** | Mermaid-only diagrams with visibility checks | [mermaid-diagrams.md](references/mermaid-diagrams.md) |
| **0h Layer data validation** | Warehouse query checks after every built layer | [layer-data-validation.md](references/layer-data-validation.md) |
| **0i Key performance indicators** | Business metric definitions, approval evidence, and reconciliation | [kpi-definitions.md](references/kpi-definitions.md), [metric-verification.md](references/metric-verification.md) |
| **0j Advanced review** | Senior data-engineering completion gate | [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md) |
| **0k Rollback / redo** | Controlled rollback when a completed phase must be undone or rebuilt | [phase-rollback.md](references/phase-rollback.md) |
| **1 Init** | New project | [project-initialization.md](references/project-initialization.md) |
| **2 Schemas** | After init | [warehouse-schema-setup.md](references/warehouse-schema-setup.md), [schema-isolation.md](references/schema-isolation.md) |
| **3 Sources** | Packages + source YAML | [packages-and-sources.md](references/packages-and-sources.md) |
| **3b Source profiling** | Before staging | [source-profiling.md](references/source-profiling.md) |
| **4 Layer names** | Before models | [dbt-project-layers.md](references/dbt-project-layers.md) |
| **5 Staging** | Layer 1 | [staging-spec.md](references/staging-spec.md) |
| **6 Intermediate** | Layer 2 | [intermediate-spec.md](references/intermediate-spec.md), [mapping-seeds.md](references/mapping-seeds.md) |
| **7 Marts** | Layer 3 star schema | [marts-spec.md](references/marts-spec.md), [materialization-rules.md](references/materialization-rules.md) |
| **7b Semantic** | Metrics on marts | [semantic-layer-spec.md](references/semantic-layer-spec.md) |
| **7c Evaluator** | Best-practice audit | [project-evaluator.md](references/project-evaluator.md), [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) |
| **8 Docs** | After layers | [documentation.md](references/documentation.md) |
| **8a Analytics insight reporting** | Business reporting design before presentation | [analytics-insight-reporting.md](references/analytics-insight-reporting.md) |
| **8b Presentation layer** | Optional final user-facing layer after analytics insight reporting | [presentation-layer.md](references/presentation-layer.md), [powerbi-pbip-desktop-requirements.md](references/powerbi-pbip-desktop-requirements.md) when Power BI is approved |
| **9 Git** | After each stage | [github-repo-resolution.md](references/github-repo-resolution.md), [git-workflow.md](references/git-workflow.md) |
| **10 Agents Schema / continuous integration** | Metadata + automation | [agents-schema-setup.md](references/agents-schema-setup.md), [cicd-setup.md](references/cicd-setup.md) |
| **Plan approval** | Before each non-setup build phase | [phase-plan-approval.md](references/phase-plan-approval.md) |
| **Review** | Human approval points | [human-review.md](references/human-review.md) |
| **Phase report** | After each completed phase | [phase-completion-report.md](references/phase-completion-report.md), [next-phase-prompt.md](references/next-phase-prompt.md) |
| **Context tree** | Ongoing project memory | [context-tree.md](references/context-tree.md) |
| **Done** | Final check + user summary | [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md) |

Context prompt template: [agent-context-prompt.md](references/agent-context-prompt.md)

## Step 0 - Load configuration

Read [project.config.yml](project.config.yml), [skill-inputs.md](references/skill-inputs.md), [profile-listing.md](references/profile-listing.md), [project-naming.md](references/project-naming.md), [schema-isolation.md](references/schema-isolation.md), [env-configuration.md](references/env-configuration.md), [source-confirmation.md](references/source-confirmation.md), [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md), [skill-knowledge.md](references/skill-knowledge.md), [project-knowledge.md](references/project-knowledge.md), [discovery-requirements.md](references/discovery-requirements.md), [phased-discovery.md](references/phased-discovery.md), [recommendation-and-review.md](references/recommendation-and-review.md), [writing-style.md](references/writing-style.md), [reporting-standards.md](references/reporting-standards.md), [analytics-insight-reporting.md](references/analytics-insight-reporting.md), [mermaid-diagrams.md](references/mermaid-diagrams.md), [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md), [layer-data-validation.md](references/layer-data-validation.md), [kpi-definitions.md](references/kpi-definitions.md), [metric-verification.md](references/metric-verification.md), [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md), [phase-plan-approval.md](references/phase-plan-approval.md), [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md), [phase-completion-report.md](references/phase-completion-report.md), [next-phase-prompt.md](references/next-phase-prompt.md), and [context-tree.md](references/context-tree.md).

For smaller context windows, read required references fully, extract the rules that apply to the active checkpoint into the phase plan or working notes, and avoid carrying unused details forward. Prefer loading phase-specific references only when entering that phase. Do not skip required safety references, but summarize-and-discard details that are not relevant to the active checkpoint.

Resolve paths relative to workspace root. dbt project root = `{project.root}`.

Read [skill-knowledge.md](references/skill-knowledge.md) and [project-knowledge.md](references/project-knowledge.md) after loading configuration and before discovery summaries or phase plans. Use built-in skill knowledge for reusable dbt, big data, warehouse optimization, Power BI, semantic, privacy, and validation standards. Use project knowledge files such as `AGENT_KNOWLEDGE.md`, `docs/dbt_knowledge.md`, `docs/business_rules.md`, `.agents/project_knowledge.md`, and `reports/agent/CONTEXT_TREE.md` for local/domain overrides when they exist. Apply prompt `project_rules` first when there is a conflict. Ask before persisting new knowledge from chat.

**User prompt overrides `.env` and configuration** for schema, domain, layers, materialization, commit mode. Use `.env` for non-secret reusable inputs before asking the user. If `.env` is missing in a fresh clone, follow [env-configuration.md](references/env-configuration.md): create a safe local `.env` from `.env.example` with placeholder values only, list available dbt profiles with [profile-listing.md](references/profile-listing.md), stop before discovery or dbt commands, and ask the user for `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA`. Do not fill `.env` from profiles, profile target schemas, warehouse schemas, old runs, terminal output, examples, nearby workspaces, or guesses. Do not search the repository, inspect terminal output, infer, suggest, or summarize values from other workspaces or previous runs.

Read [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md) immediately after loading `.env` and before any discovery. Resolve the active dbt profile and adapter from `~/.dbt/profiles.yml`; use only that adapter's discovery path. Do not call AWS, Redshift, PostgreSQL, Snowflake, BigQuery, Databricks, cloud identity checks, warehouse connectors, metadata queries, or Model Context Protocol discovery servers before the selected profile adapter is resolved and announced. Do not call AWS, Redshift, or any other warehouse-specific path unless the selected profile adapter requires it or the user explicitly changes profiles.

If the configured source is missing, empty, inaccessible, ambiguous, or mismatched, read [source-confirmation.md](references/source-confirmation.md). Stop after metadata-only candidate listing. Recommend the likely replacement with evidence, then wait for user approval before changing database, dataset, catalog, schema, table, tenant, client, domain, environment, assumption, `.env`, profile settings, profiling, discovery reports, or continuing discovery.

For normal runs, collect only the values the agent cannot infer safely: `domain`, `dbt_profile_name`, and `source_schema`. Optionally accept `business_description` / `DBT_BUSINESS_DESCRIPTION` when the user wants to explain the client, process, reporting goals, or business context. When `dbt_profile_name` is missing or ambiguous, list available profiles using [profile-listing.md](references/profile-listing.md), then wait for the user to choose. Derive project name/root, project slug, dbt source name, schema prefix, layer names, commit behavior, and GitHub mode unless the user explicitly overrides them.

Resolve `project.name`, `project.root`, and `project_slug` before `dbt init`. Never use `dbt_profile_name` or raw `DBT_DOMAIN` as the folder/project name unless the user explicitly provides it as `dbt_project_name`, `dbt_project_root`, or `project_slug`. Prefer a clean name derived from `source_schema`, source name, existing project name, or descriptive profile database/catalog; use `domain` only as a last fallback and `github_repo_name` only when the user provided it for push. Use `DBT_BUSINESS_DESCRIPTION` only for analytics understanding, never for physical folder, schema, database, or model names.

Keep the source schema read-only and immutable. Never update, insert, delete, truncate, merge into, create, drop, alter, or repair data in the configured source schema or source tables. Even if the user asks to "mark records complete", "fix source rows", "delete bad source data", or similar, implement the logic only as dbt transformations, tests, seeds, snapshots, or audits in non-source schemas, then explain that the source remains unchanged. Never build dbt models, package models, evaluator tables, seeds, snapshots, or audit outputs into `source_schema`. Route evaluator outputs to `<layer_schema_prefix>_evaluator` and layer outputs to separate medallion schemas. Resolve `layer_schema_prefix` with [schema-isolation.md](references/schema-isolation.md); do not use short source names like `dh` as physical schema prefixes unless the user explicitly sets them.

Before each phase that changes models, semantic files, documentation files, workflow files, or warehouse objects, write/update `{project.root}/AGENT_PLAN.md`, explain the planned work in Markdown, and wait for approval for that phase. Read-only discovery is allowed before approval when needed for an accurate plan.

Project setup and configuration is the exception: after the user accepts discovery requirements, write/update `{project.root}/AGENT_PLAN.md` with the phase marked as automatic setup-only, run setup, then write `reports/agent/setup_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`. If any setup safety gate from [bootstrap.md](references/bootstrap.md) is triggered, stop and ask before continuing.

Approval is controlled by workflow checkpoint. Never treat a user response at one checkpoint as permission to run multiple build phases. After automatic project setup and configuration finishes, stop at the next phase plan and ask for approval before generating source YAML or building bronze/staging.

## Step 0b - Optional subagents

Read [subagent-workflow.md](references/subagent-workflow.md) when source profiling, mapping review, model planning, documentation, or evaluator review can safely run in parallel. The main agent decides when to delegate and keeps dbt commands, shared file edits, commits, pushes, and final decisions.

## Step 0.1 - Security

Read [security-and-credentials.md](references/security-and-credentials.md).

Never hardcode secrets. Ask before production changes.

## Step 0.2 - Data engineering guardrails

Read [data-engineering-best-practices.md](references/data-engineering-best-practices.md) and [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md) before model design and again before final delivery. Apply grain, test, incremental, snapshot, documentation, lineage, directed acyclic graph, freshness, macros, packages, build process, privacy, performance, state-based continuous integration, contracts/versioning, SQL style, warehouse optimization, modern table format, and downstream presentation guardrails.

Read [privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md) when discovery finds direct identifiers, sensitive fields, protected health information, personally identifiable information, or ambiguous, placeholder, abbreviated, or poorly named fields. The agent must recommend a safe default, document the recommendation, and ask only for approval or business definitions instead of leaving the whole decision to the user.

Read [writing-style.md](references/writing-style.md) and [reporting-standards.md](references/reporting-standards.md) before writing user-facing prompts, plans, reports, summaries, diagram notes, presentation artifacts, or final handoffs. Use full wording instead of shorthand, except for official tool names, commands, filenames, environment variables, and code identifiers. Every report must include the five reporting pillars when relevant: context and strategy, key performance indicators, trend analysis and variance, insights and attribution, and recommendations and next steps. If a pillar is not supported yet, mark it deferred with the reason instead of guessing.

Read [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) before writing each phase plan. The phase plan must show the agent's data-engineering decisions, evidence, and approval needs; do not hide grain, key, join, bridge table, mapping, privacy, metric, materialization, or validation choices inside code.

If the agent cannot understand the source tables, relationships, business processes, required metrics, data quality rules, required output models, or reporting needs for the current scope, stop the dependent scope and ask instead of guessing.

Read [phased-discovery.md](references/phased-discovery.md) before each phase. Discover only what is needed for the next layer or workflow step; do not fully design silver/gold/semantic outputs during initial discovery or bronze work.

Read [recommendation-and-review.md](references/recommendation-and-review.md) before writing discovery summaries, phase plans, phase reports, and final handoffs. The agent must recommend the best path with evidence, show what looks right and what is not ready, state confidence about proven vs uncertain items, and ask the data engineer only for business-impacting approvals. Do not make the user design everything from scratch.

Read [mermaid-diagrams.md](references/mermaid-diagrams.md) before creating or changing any diagram. All diagrams must be Mermaid blocks, entity relationships must use Mermaid `erDiagram`, and every added or changed Mermaid diagram must be verified as visible/parseable before the phase is marked complete.

Read [layer-data-validation.md](references/layer-data-validation.md) before building bronze/staging, silver/intermediate, or gold/marts. After each layer build, run warehouse validation queries for row presence, expected emptiness, grain, keys, relationships, row-count movement, date coverage, status/category distributions, measures, mapping coverage, and privacy exposure. Add a `Data Verification Results` section to the layer report, share the important results with the user, and stop before the next layer when a model that should contain data is empty or any validation issue is unexplained.

Read [kpi-definitions.md](references/kpi-definitions.md) and [metric-verification.md](references/metric-verification.md) before gold/marts, semantic layer, presentation layer, and final delivery. The agent must propose supported key performance indicators with business meaning, source model, grain, numerator, denominator, filters, time field, caveats, validation evidence, approval status, and expected versus actual reconciliation. Do not create semantic metrics or presentation calculations from ambiguous or unreconciled key performance indicators.

Read [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md) before final delivery. The pipeline is not complete until advanced review areas are reported, including source lock, schema hygiene, layer validation, grain, tests, data quality, privacy, key performance indicators, semantic layer, evaluator, documentation, analytics insight reporting, presentation-layer recommendation, and operations.

## Step 0.5 - Resolve layer names

Read [references/dbt-project-layers.md](references/dbt-project-layers.md).

For a full pipeline, plan to deliver all model layers, but build them one approved phase at a time. If `workflow_phase` limits scope, plan and build only that requested phase.

Layer role names and physical folder names must not be mixed. With default layer names, staging models go in `models/bronze/`, intermediate models go in `models/silver/`, and facts/dimensions/reporting marts go in `models/gold/`. Do not also create `models/staging/`, `models/intermediate/`, or `models/marts/` unless the user explicitly configured those as the physical layer names.

Use `layer_names` from the prompt, `.env`, or `project.config.yml` when provided. Otherwise use:

- Layer 1 (`stg_*`): `bronze`
- Layer 2 (`int_*`): `silver`
- Layer 3 (`dim_*`/`fct_*`/`mart_*`): `gold`

Do not ask for layer names unless the user requests a non-default naming convention or an existing project already uses different folders. Resolve `project_slug` from [project-naming.md](references/project-naming.md) for model folder paths. Resolve `layer_schema_prefix` from explicit configuration, existing approved medallion schemas, source schema, project slug, or descriptive source name; use domain only as a last fallback. Ask only when existing schemas create a real conflict that the agent cannot resolve safely.

Write `dbt_project.yml` per [materialization-rules.md](references/materialization-rules.md):

```yaml
models:
  {project.name}:
    {layer_1_name}:
      +schema: {layer_schema_prefix}_{layer_1_name}
      +materialized: view
    {layer_2_name}:
      +schema: {layer_schema_prefix}_{layer_2_name}
      +materialized: view
    {layer_3_name}:
      +schema: {layer_schema_prefix}_{layer_3_name}
      +materialized: table   # prod; use view for dev profile
  dbt_project_evaluator:
    +schema: {layer_schema_prefix}_evaluator
    +materialized: table
seeds:
  {project.name}:
    +schema: {layer_schema_prefix}_seeds
snapshots:
  {project.name}:
    +schema: {layer_schema_prefix}_snapshots
vars:
  dbt_project_evaluator:
    staging_folder_name: {layer_1_name}
    intermediate_folder_name: {layer_2_name}
    marts_folder_name: {layer_3_name}
    marts_prefixes: ['fct_', 'dim_', 'mart_']
    other_prefixes: ['rpt_']
```

`fct_*` models: `incremental` with `unique_key` in SQL when `materialization_profile: prod`.

## Mandatory validation

Read [validation-commands.md](references/validation-commands.md).

**Never mark a phase complete without successful validation.**

Validate the skill configuration before project work:

```powershell
python scripts/validate_config.py --root .
```

```powershell
cd {project.root}
$dbt = "dbt"          # prefer active venv/path; see validation-commands.md for fallbacks
& $dbt debug          # init / profile changes only
& $dbt parse --no-partial-parse
& $dbt build --select +path:<layer_folder>
```

After each bronze/staging, silver/intermediate, or gold/marts build, run [layer-data-validation.md](references/layer-data-validation.md). `dbt build` passing does not by itself prove the layer is usable.

## Step 1 - Full pipeline order

Read [separate-layer-builds.md](references/separate-layer-builds.md).

**Full pipeline (default):**

1. **Discovery & requirements** - [discovery-requirements.md](references/discovery-requirements.md)
2. **Project setup and configuration** - setup-only and automatic after discovery requirements are accepted - [bootstrap.md](references/bootstrap.md)
3. Init *(if project missing)*
4. Sources - full `packages.yml`, `dbt deps`, codegen, source YAML
5. Staging -> Intermediate -> Marts
6. Semantic layer - metrics on marts facts
7. Project evaluator - `dbt build --select package:dbt_project_evaluator` after confirming it is routed to `<layer_schema_prefix>_evaluator`
8. Documentation - `dbt docs generate`; use `dbt docs serve` for local viewing when requested or appropriate for an interactive local run
9. Analytics insight reporting - discover and document trusted business outputs, key performance indicator catalogs, dashboard spec, and reporting readiness before presentation work - [analytics-insight-reporting.md](references/analytics-insight-reporting.md)
10. Presentation layer gate - required after analytics insight reporting and before final delivery; ask whether the user wants a presentation layer. If the user approves and does not name another technology, default to a Power BI PBIP/TMDL project, run a separate `presentation_layer` phase, and create the approved artifact.
11. Agents Schema - publish dbt metadata to `AGENTS.*` after `target/manifest.json` exists when enabled and supported
12. Automation - continuous integration workflow
13. **Advanced review, acceptance + final summary** - [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md), [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md)

After project setup and configuration, each stage: **phase-specific discovery -> agent recommendation -> data engineer decision check -> write Markdown plan -> ask approval -> implement -> parse/build -> warehouse data validation queries -> write phase report with validation results -> update context tree -> write `reports/agent/NEXT_PHASE_PROMPT.md` -> summarize validation results and show the exact next-phase prompt -> ask interactive approval for the displayed prompt when available -> ask commit**. Ask for push only when a non-local GitHub repository is configured or the user requested push.

## Step 2 - Sources

Read [packages-and-sources.md](references/packages-and-sources.md), [source-profiling.md](references/source-profiling.md), [schema-isolation.md](references/schema-isolation.md), and [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md).

All four packages in `packages.yml`. Codegen for sources. Derive `source.name` from `source.schema` unless explicitly provided; use domain only as a last fallback when the source schema is generic. Write source YAML only under `models/sources/`, never under bronze, silver, or gold layer folders. Do not move source YAML into bronze/staging to satisfy evaluator source-directory warnings; document accepted exceptions or ask before changing structure. Add the configured `source.schema` to source YAML after generate. Profile row counts, candidate keys, relationships, important dates, measures, and status/code fields before staging.

## Step 3 - Layer 1 (staging)

Read [staging-spec.md](references/staging-spec.md) and [layer-data-validation.md](references/layer-data-validation.md). `source()` only. No business KPIs. After build, verify staging row counts against source tables and share the results.

## Step 4 - Layer 2 (intermediate)

Read [intermediate-spec.md](references/intermediate-spec.md), [mapping-seeds.md](references/mapping-seeds.md), and [layer-data-validation.md](references/layer-data-validation.md). `ref()` only. Use mapping seeds or reference tables when `project_rules` include manual mappings or code translations. After build, verify row presence, grain, joins, row loss, and row multiplication.

## Step 5 - Layer 3 (marts / star schema)

Read [marts-spec.md](references/marts-spec.md), [layer-data-validation.md](references/layer-data-validation.md), [kpi-definitions.md](references/kpi-definitions.md), and [metric-verification.md](references/metric-verification.md). `ref()` only. Build domain-appropriate facts, dimensions, and reporting marts based on profiled source grain and user requirements. After build, verify every fact, dimension, and reporting mart has data when upstream data exists; treat unexpected empty gold models as blockers. Define and reconcile key performance indicators explicitly before promoting them to gold marts or semantic metrics.

## Step 5b - Semantic layer

Read [semantic-layer-spec.md](references/semantic-layer-spec.md), [kpi-definitions.md](references/kpi-definitions.md), and [metric-verification.md](references/metric-verification.md). Compose with `building-dbt-semantic-layer`. Legacy spec on dbt 1.10.x. Only create semantic metrics from approved, supported, and reconciled key performance indicator definitions.

## Step 5c - Project evaluator

Read [project-evaluator.md](references/project-evaluator.md). Before running evaluator, confirm `dbt_project.yml` routes `models: dbt_project_evaluator: +schema` to `<layer_schema_prefix>_evaluator` and sets evaluator vars for the active medallion folder names. Do not let evaluator package tables build in `source_schema`. When querying evaluator result tables, inspect available columns before selecting version-specific fields.

```powershell
& $dbt build --select package:dbt_project_evaluator
```

## Step 6 - Documentation

Read [documentation.md](references/documentation.md). Run `dbt docs generate`. Use `dbt docs serve` only as a non-blocking local viewing step and report the URL when started. In a full pipeline, do not mark delivery complete after documentation. Move to analytics insight reporting.

## Step 6a - Analytics insight reporting

Read [analytics-insight-reporting.md](references/analytics-insight-reporting.md), [reporting-standards.md](references/reporting-standards.md), [kpi-definitions.md](references/kpi-definitions.md), and [metric-verification.md](references/metric-verification.md). Before this phase, write/update `AGENT_PLAN.md` and wait for approval. Discover and document the most useful business-facing outputs from validated marts and semantic metrics. Produce `analytics_insight_report.md`, `reporting_catalog.md`, `kpi_catalog.md`, `dashboard_spec.md`, `insight_backlog.md`, `reporting_readiness_scorecard.md`, and `analytics_insight_reporting_report.md` under `reports/agent/`. Do not create presentation artifacts in this phase.

### Analytics insight reporting hard rules

- Do not create fake insights.
- Do not suggest charts just because data exists.
- Every key performance indicator and report candidate must map to validated marts or semantic metrics.
- Every visual must answer a real business question.
- Do not expose sensitive fields without approval.
- Clearly separate trusted outputs from uncertain or deferred outputs.
- Prefer useful, simple, business-friendly reporting over too many technical tables.
- Do not hardcode one domain's key performance indicators, page names, or sample values.
- Do not invent targets, benchmarks, attribution, or recommendations without evidence.
- Maximum means maximum useful business insight supported by validated data, not maximum number of dashboards.

After this phase, update `reports/agent/analytics_insight_reporting_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`, then stop at the presentation-layer gate unless the user already approved presentation work.

## Step 6b - Presentation layer recommendation

Read [presentation-layer.md](references/presentation-layer.md), [analytics-insight-reporting.md](references/analytics-insight-reporting.md), [kpi-definitions.md](references/kpi-definitions.md), and [metric-verification.md](references/metric-verification.md). If Power BI is approved, also read [powerbi-pbip-desktop-requirements.md](references/powerbi-pbip-desktop-requirements.md). After analytics insight reporting, recommend the best presentation-layer option using `dashboard_spec.md`, `kpi_catalog.md`, `reporting_catalog.md`, `insight_backlog.md`, `reporting_readiness_scorecard.md`, and `analytics_insight_report.md` as the scope contract. Ask simply whether the user wants a presentation layer before final delivery is closed. If the user approves and does not specify another technology, default to Power BI PBIP/TMDL, create the `presentation_layer` phase plan, instantiate the bundled neutral PBIP template from `assets/powerbi/pbip_template/` with `scripts/create_powerbi_pbip_from_template.py`, build only the approved artifact, validate it, and write the presentation report. Do not silently adapt a local PBIP such as IHMS; local PBIPs may be used only as user-approved structural references after showing the exact path and what would be reused. The presentation layer must not invent pages, key performance indicators, visuals, or business scope that contradict analytics insight outputs unless the user explicitly overrides them. Do not build dashboards, reports, slides, notebooks, or business intelligence artifacts without approval.

The presentation-layer recommendation and user decision gate are mandatory for full pipeline final delivery. If the user has not answered the presentation question, set status to `Analytics insight reporting complete - presentation decision pending`, not `Delivery complete`. If the recommendation cannot be produced, mark it `BLOCKED` or `SKIPPED` with evidence in the final report, pipeline status, context tree, and final response.

## Step 6b - Human review

Read [human-review.md](references/human-review.md). Summarize business assumptions, data quality notes, and open decisions after each layer. Ask for approval when business meaning, grain, mappings, metrics, or sensitive fields are unclear.

This review happens after implementation. The phase plan approval in [phase-plan-approval.md](references/phase-plan-approval.md) happens before implementation.

## Step 7 - Git

Read [git-workflow.md](references/git-workflow.md). Ask before every commit/push.

## Step 8 - Continuous Integration, Continuous Delivery, And Agents Schema *(when requested)*

- [agents-schema-setup.md](references/agents-schema-setup.md)
- [cicd-setup.md](references/cicd-setup.md)

Use Agents Schema after documentation generation or any step that produces `target/manifest.json`. Do not treat it as a replacement for dbt project files while editing; use it as the warehouse-side metadata layer that helps agents answer questions and understand built models.

## Step 9 - Final delivery summary

Read [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md), [phase-completion-report.md](references/phase-completion-report.md), [reporting-standards.md](references/reporting-standards.md), [context-tree.md](references/context-tree.md), and [final-delivery.md](references/final-delivery.md) before marking any full pipeline or requested phase complete.

Always finish with a user-facing summary that starts short, then gives the useful details:

1. Short summary: what was built and whether it passed.
2. Results: profile, domain, source, schemas, layers, row counts when known.
3. Models created or changed by layer.
4. Validation: dbt debug, parse, build, documentation, and evaluator results.
5. Data quality notes and assumptions.
6. Git, continuous integration, and Agents Schema status.
7. Analytics insight reporting status and links to reporting design files.
8. Presentation-layer recommendation status.
9. Advanced data-engineering review status.
10. Open decisions and recommended next actions.

Keep the first section concise enough for a new user to understand in under one minute.

## Failure handling

Read [stuck-recovery.md](references/stuck-recovery.md) whenever a command hangs, validation fails repeatedly, required input is missing, or the agent cannot decide safely.

1. Identify failing model/test from build output.
2. Fix **only the current layer** unless upstream is broken.
3. Re-run `dbt build --select +path:<layer_path>`.
4. Use `troubleshooting-dbt-job-errors` for unclear errors.
5. If still blocked, stop and ask with the current phase, last command, error, changed files, `git status`, and concrete options.

## Rollback and redo

Read [phase-rollback.md](references/phase-rollback.md) when a completed phase must be undone, rebuilt differently, or marked stale because a grain, mapping, privacy, metric, naming, source, or presentation decision changed. Do not quietly delete files, drop warehouse objects, or leave `PIPELINE_STATUS.md` / `CONTEXT_TREE.md` claiming a rolled-back phase is complete. Write a rollback plan, ask for approval when warehouse objects or shared reports are affected, update status/context files, and then return to the normal phase plan workflow.

## Next-phase prompt after each phase

After every completed or blocked checkpoint, read [next-phase-prompt.md](references/next-phase-prompt.md). Write or update `reports/agent/NEXT_PHASE_PROMPT.md` with the exact prompt for the recommended next phase, show that prompt in chat, and ask through a native interactive question when the runtime supports it. In Codex, use `request_user_input` or the current native question/approval UI when available in the active mode. Recommended question: `Do you want me to run this next-phase prompt as written?` Recommended option: `Yes, run this prompt`. Other options: `Tell me what to change` and `Not now`. If interactive questions are unavailable, use the text fallback: `Do you want me to run this next-phase prompt as written? Reply Yes to proceed, or tell me what to change.`

Natural approval responses such as `Yes`, `Proceed`, `Approved`, `Continue`, `Run this prompt`, `Looks good`, or `Go ahead` approve only the displayed next-phase prompt for the active checkpoint. Silence is never approval. If the user changes scope, models, key performance indicators, privacy, schemas, validation, materialization, or files, update `AGENT_PLAN.md` and `reports/agent/NEXT_PHASE_PROMPT.md`, show the revised prompt, and ask again before proceeding.

## Summary template (end of each phase)

```text
1. Plan approval status
2. Files created / updated
3. Grain / business logic
4. Data-engineering decisions and evidence
5. Agent recommendation, what looks right, what is not ready, and confidence
6. Tests / documentation added
7. Assumptions used
8. dbt debug, parse, build, and documentation results
9. Mermaid diagram verification status when diagrams were added or changed
10. Phase report path and status
11. Context tree update status
12. Next-phase prompt path and exact interactive approval question or fallback text question
13. Commit status (asked / skipped / completed / pushed to GitHub)
```

For the final response, use [final-delivery.md](references/final-delivery.md) instead of only the phase template.

## Ambiguity - prompt overrides

- `workflow_phase:` init | sources | staging | intermediate | marts | semantic_layer | project_evaluator | docs | analytics_insight_reporting | presentation_layer | ci | agents_schema
- `dbt_profile_name:` dbt profile key from `~/.dbt/profiles.yml`; ask if missing or ambiguous
- `dbt_project_name:` optional explicit dbt project name; otherwise derive from source/project signals
- `dbt_project_root:` optional explicit folder name; otherwise use `dbt_project_name`
- `project_slug:` optional explicit model folder slug; otherwise derive from source/project signals
- `domain:` business/domain context; ask if missing, but do not use it directly as a folder/schema prefix
- `business_description:` optional plain-English business/client context for analytics insight reporting and presentation planning
- `source_schema:` warehouse schema to inspect with codegen; ask if missing
- `source_name:` optional dbt source name override; derive from `source_schema` when missing
- `layer_schema_prefix:` prefix for physical output schemas; derive by [schema-isolation.md](references/schema-isolation.md) unless explicitly provided
- `project_rules:` optional field mappings, joins, metrics, exclusions, privacy rules, naming rules, and special instructions. Apply exactly; ask if unclear.
- `auto_bootstrap:` true *(default)* | false *(backward-compatible config key for automatic project setup; avoid showing this in normal user-facing prompts)*
- `auto_agents_schema:` true | false *(default false for local/unsupported adapters; enable for Snowflake, Databricks, or BigQuery)*
- `auto_install_dbt_skills:` true *(default)* | false
- `layer_names:` layer_1, layer_2, layer_3 *(default: bronze, silver, gold)*
- `domain:` (default from `project.config.yml`)
- `github_repo_name:` optional repository slug; ask only when push is requested and no repository can be inferred
- `github_repo:` full URL or `owner/repo` *(optional override)*
- `push_to_github:` true | false *(default: false for `local-only`, otherwise ask before pushing)*
- `commit:` ask | auto_yes | skip_all
- `materialization_profile:` prod | dev
- `regenerate_sources:` true | false

## One-shot prompt

[prompt.md](prompt.md) - [agent-context-prompt.md](references/agent-context-prompt.md)

## Do not use this skill for

- Do not directly build Power BI dashboards, reports, slides, notebooks, or business intelligence artifacts unless the user approves the separate `presentation_layer` or BI handoff phase. The skill may document analytics insight reporting outputs after marts, semantic layer, evaluator, documentation, and validation are complete, and may prepare Power BI-ready semantic outputs, DAX measure drafts, PBIP/TMDL handoff files, or approved PBIP/TMDL artifacts only after analytics insight reporting and user approval.
- Ad-hoc business questions -> `answering-natural-language-questions-with-dbt` *(use that skill directly)*

## Reference files

| File | Purpose |
|---|---|
| [install-skill.md](references/install-skill.md) | Install via npx or `.agents/skills/` |
| [bootstrap.md](references/bootstrap.md) | Automatic project setup and configuration: skills install, packages, debug, dependency install, parse, and setup reports |
| [discovery-requirements.md](references/discovery-requirements.md) | Read-only schema/data discovery and requirements checkpoint before build planning |
| [project.config.yml](project.config.yml) | Defaults, paths, git, materialization |
| [skill-inputs.md](references/skill-inputs.md) | Required inputs |
| [profile-listing.md](references/profile-listing.md) | Safe available-profile table when `DBT_PROFILE_NAME` is missing or ambiguous |
| [phase-plan-approval.md](references/phase-plan-approval.md) | Markdown plan and approval gate before every phase |
| [phase-completion-report.md](references/phase-completion-report.md) | Per-phase report files showing done/correct/wrong/open items |
| [next-phase-prompt.md](references/next-phase-prompt.md) | Required next-phase execution prompt and interactive approval gate after each phase |
| [context-tree.md](references/context-tree.md) | Curated project memory: inputs, outputs, decisions, reports, and open items |
| [skill-knowledge.md](references/skill-knowledge.md) | Built-in reusable dbt, big data, warehouse, semantic, Power BI, privacy, and validation knowledge |
| [project-knowledge.md](references/project-knowledge.md) | User-provided dbt standards, domain knowledge, and business rules |
| [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) | Senior data-engineering decisions that must be explicit before build |
| [phased-discovery.md](references/phased-discovery.md) | Layer-by-layer discovery that keeps the data engineer in control |
| [recommendation-and-review.md](references/recommendation-and-review.md) | Agent recommendations, risks, and approval boundaries |
| [writing-style.md](references/writing-style.md) | Full wording for user-facing output |
| [reporting-standards.md](references/reporting-standards.md) | Five-pillar actionable report standard |
| [mermaid-diagrams.md](references/mermaid-diagrams.md) | Mermaid-only diagrams and visibility verification |
| [layer-data-validation.md](references/layer-data-validation.md) | Warehouse query checks after every bronze, silver, and gold layer build |
| [kpi-definitions.md](references/kpi-definitions.md) | Key performance indicator definitions, caveats, and approval status |
| [metric-verification.md](references/metric-verification.md) | Cross-layer key performance indicator reconciliation |
| [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md) | Required senior data-engineering review before final delivery |
| [project-naming.md](references/project-naming.md) | Derive project and folder names without using dbt profile |
| [env-configuration.md](references/env-configuration.md) | Optional `.env` settings and precedence |
| [source-confirmation.md](references/source-confirmation.md) | Ask-before-switching contract and approved source lock |
| [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md) | Use the selected dbt profile adapter for discovery; do not probe unrelated warehouses |
| [schema-isolation.md](references/schema-isolation.md) | Keep source, medallion, evaluator, seeds, snapshots, and agent metadata schemas separate |
| [subagent-workflow.md](references/subagent-workflow.md) | Optional parallel analysis and review |
| [data-engineering-best-practices.md](references/data-engineering-best-practices.md) | Grain, tests, history, contracts, privacy, operations |
| [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md) | Principal-level dbt, Power BI, storage, warehouse, and SQL standards |
| [privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md) | Safe defaults for sensitive fields and unclear coded fields |
| [security-and-credentials.md](references/security-and-credentials.md) | Secrets & gitignore |
| [project-initialization.md](references/project-initialization.md) | venv, dbt init, debug |
| [warehouse-schema-setup.md](references/warehouse-schema-setup.md) | Warehouse schemas |
| [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | codegen, utils, evaluator, audit_helper, agent skills |
| [project-evaluator.md](references/project-evaluator.md) | Align dbt_project_evaluator with bronze/silver/gold and accepted warnings |
| [semantic-layer-spec.md](references/semantic-layer-spec.md) | MetricFlow / semantic metrics |
| [github-repo-resolution.md](references/github-repo-resolution.md) | `gh` command line interface owner and repository name |
| [packages-and-sources.md](references/packages-and-sources.md) | Codegen, source YAML |
| [source-profiling.md](references/source-profiling.md) | Row counts, keys, dates, status/code values |
| [staging-spec.md](references/staging-spec.md) | Layer 1 |
| [intermediate-spec.md](references/intermediate-spec.md) | Layer 2 |
| [mapping-seeds.md](references/mapping-seeds.md) | Manual mapping seeds and coverage tests |
| [marts-spec.md](references/marts-spec.md) | Star schema |
| [documentation.md](references/documentation.md) | Docs generate |
| [analytics-insight-reporting.md](references/analytics-insight-reporting.md) | Business reporting design before presentation |
| [presentation-layer.md](references/presentation-layer.md) | Optional presentation-layer recommendation after analytics insight reporting |
| [powerbi-pbip-desktop-requirements.md](references/powerbi-pbip-desktop-requirements.md) | Power BI PBIP/TMDL bundled template, Desktop layout, metadata, page-content, and validation requirements |
| [human-review.md](references/human-review.md) | Engineer/domain review checkpoints |
| [final-delivery.md](references/final-delivery.md) | Final handoff checklist |
| [validation-commands.md](references/validation-commands.md) | debug, parse, build, documentation |
| [stuck-recovery.md](references/stuck-recovery.md) | Stuck command and blocker recovery |
| [phase-rollback.md](references/phase-rollback.md) | Controlled rollback and redo workflow |
| [github-setup.md](references/github-setup.md) | Initial git + commit order |
| [git-workflow.md](references/git-workflow.md) | Per-layer commits |
| [code-agent-setup.md](references/code-agent-setup.md) | Agent access & behavior |
| [install-dbt-agent-skills.md](references/install-dbt-agent-skills.md) | dbt-labs skills |
| [agents-schema-setup.md](references/agents-schema-setup.md) | AGENTS schema |
| [cicd-setup.md](references/cicd-setup.md) | GitHub Actions |
| [agent-context-prompt.md](references/agent-context-prompt.md) | Session prompt |
| [acceptance-checklist.md](references/acceptance-checklist.md) | Final verification |
| [dbt-project-layers.md](references/dbt-project-layers.md) | Layer naming |
| [separate-layer-builds.md](references/separate-layer-builds.md) | Build order |
| [prompt.md](prompt.md) | Paste-ready prompt |
