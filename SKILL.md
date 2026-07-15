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
templates/
docs/
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
Copy-Item -Path (Join-Path $tmp "templates") -Destination $skillDir -Recurse -Force
Copy-Item -Path (Join-Path $tmp "docs") -Destination $skillDir -Recurse -Force
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
cp -R "$tmp/templates" "$skill_dir/"
cp -R "$tmp/docs" "$skill_dir/"
cp "$tmp/project.config.yml" "$skill_dir/"
cp "$tmp/prompt.md" "$skill_dir/"
cp "$tmp/.env.example" "$skill_dir/"
rm -rf "$tmp"
```

After hydration, read references and scripts from local disk only. If hydration fails because `git` or network access is unavailable, stop and tell the user the skill resources are missing instead of pretending the referenced files were read.

## Install and environment anti-patterns

Avoid these common first-run mistakes:

| Anti-pattern | Correct behavior |
|---|---|
| Expecting workspace `.env` immediately after `npx skills add` | `.env` is created on first agent run in the workspace, not during skill install |
| Telling the user to copy `.env.example` manually before the first prompt | Agent resolves `.env.example` and creates workspace `.env` when missing |
| Editing `.agents/skills/agentic-dbt-pipeline/project.config.yml` for normal project settings | Use workspace `.env` for `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA` |
| Running discovery or dbt while `.env` is missing or placeholder-only | Hard stop; ask for required values first |
| Looking for `.env.example` only in the workspace when the skill folder already has it | Also check `.agents/skills/agentic-dbt-pipeline/.env.example` |
| Filling `.env` from `profiles.yml`, warehouse schemas, or guesses | Only use values the user provides in chat or explicitly approves |

## Discovery first, then project setup and configuration

Read and execute [references/discovery-requirements.md](references/discovery-requirements.md) before project setup, project initialization, or full pipeline runs.

Discovery is read-only and project-oriented. It may inspect schemas, tables, columns, row counts, keys, relationships, dates, measures, and statuses. Its input/report/output must focus on the source data and analytics project, not environment setup. It must write `reports/agent/00_discovery/discovery_report.md`, `reports/agent/00_discovery/requirements.md`, `reports/agent/00_discovery/core_profile.json`, `reports/agent/00_discovery/discovery_raw.json`, `reports/agent/00_discovery/sql_proofs/`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` before the chat summary, even when the dbt project has not been initialized yet. Use the canonical templates under `templates/reports/00_discovery/` and `templates/reports/root/` for every file created or updated by the discovery checkpoint, including discovery report, requirements, structured JSON evidence, cardinality, relationship profile, discovery approval checklist, proof index, SQL proof files, pipeline status, context tree, report index, requirements traceability, and next-phase prompt. The template structure should stay consistent across projects; the content must change based on source evidence and user-approved rules. The requirements file must capture inferred requirements, recommended defaults, unknowns, user-decision needs, and blocked/deferred scope derived from the source evidence and business domain. The discovery `sql_proofs/` folder must include reusable source proof queries with captured results for table inventory, per-table row counts, candidate keys, important statuses such as active/open/closed counts, date coverage, numeric summaries, and relationship/cardinality checks wherever the source supports them. `discovery_raw.json.queries_executed[]` must link to the SQL proof files that support the discovery claims. It must create Mermaid discovery diagrams when the source evidence supports them, including an entity relationship diagram when credible relationships exist, plus other necessary source inventory, business process, or medallion direction diagrams. It must not install packages, run codegen, create warehouse schemas, or change profiles.

Do not assume the business domain. During discovery, understand source tables, table relationships, business processes, metrics required, data quality rules, required output models, and reporting needs before proposing dbt models.

If any of those areas cannot be properly understood or proven, do not assume. Ask the user for missing business meaning or approval, and defer dependent models, tests, metrics, semantic definitions, or presentation outputs until the uncertainty is resolved.

After discovery, send a normal assistant message with a visible Markdown **Discovery Complete** control-panel summary before asking for approval. Do not put the discovery findings only inside a native question card, approval widget, or `request_user_input` body. The chat summary must include status, source reviewed, key findings, validation or SQL proof highlights, reports written, open decisions, the recommended next step, what the next step will and will not include, and how to approve. Then ask a short native/clickable question only when the normal Markdown summary is visibly present directly above the question. The question should be compact, for example: `Do you approve this discovery scope and want automatic project setup to run next?` Recommended option: `Yes, continue to setup`. Other options: `Add requirements first` and `Tell me what to change`. If the runtime cannot guarantee that the normal summary is visible directly above the clickable question, do not use the clickable question; use the text fallback instead: `Do you approve this discovery scope and want automatic project setup to run next? Reply Yes to continue, or tell me what to change.`

After discovery, summarize what the agent concluded from the source data and ask whether the user wants to add requirements such as mappings, metrics, privacy rules, naming rules, included/excluded tables, or priority facts/dimensions. User responses are interpreted by the active workflow checkpoint, not by broad intent. At the discovery checkpoint, the next allowed action is only source confirmation and automatic project setup and configuration. Do not treat discovery acceptance as approval for sources, bronze/staging, silver/intermediate, gold/marts, semantic layer, evaluator, documentation, analytics insight reporting, presentation layer, continuous integration, Agents Schema, commits, pushes, or future schema switching.

### Discovery approval gate

After discovery completes, create `reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md` and `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` using [discovery-approval-checklist.md](references/discovery-approval-checklist.md) and [requirements-traceability-matrix.md](references/requirements-traceability-matrix.md). Do not continue to bootstrap/build until the checklist decision is `APPROVED` or `APPROVED WITH CONDITIONS`. If approved with conditions, write those conditions to `reports/agent/CONTEXT_TREE.md`, `AGENT_PLAN.md`, and `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md`.

## Project setup and configuration (automatic setup-only phase after discovery)

Read and execute [references/bootstrap.md](references/bootstrap.md) **before** any layer work:

1. **Check/install software prerequisites** - Python, venv, dbt-core, matching adapter, skill requirements - [software-prerequisites.md](references/software-prerequisites.md)
2. **Install dbt Agent Skills** + all dbt packages - see [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md)
3. **`dbt debug`** - verify connection
4. **`dbt deps` + codegen** - when sources/full pipeline
5. **Resolve git mode** - local commits by default; GitHub only when push is requested - [github-repo-resolution.md](references/github-repo-resolution.md)
6. **Create continuous integration and Agents Schema workflows** - when requested, or when `auto_agents_schema: true` and the destination is supported

User one-time manual steps: **profiles.yml password**, plus **GitHub repository or secret** only when remote push, continuous integration, or Agents Schema synchronization is requested.

If `dbt_profile_name` is provided in the prompt, use it as `{project.profile}` for dbt commands and generated `dbt_project.yml`. If it is missing and multiple profiles exist in `~/.dbt/profiles.yml`, ask the user which profile to use before running dbt commands. Never guess from the first profile.

Project setup and configuration is setup-only and auto-runs by default after the discovery requirements checkpoint is accepted. Do not ask for a separate setup approval response unless a setup safety gate is triggered. This phase may create the local dbt project scaffold, install `requirements.txt` from the installed skill or workspace, create the managed `reports/agent/` skeleton with SQL proof index files, install missing dbt Agent Skills and dbt packages, run `dbt debug`, run `dbt deps`, run `dbt parse`, and write setup reports. This phase does not approve source YAML generation, bronze/staging models, silver/intermediate models, gold/marts models, semantic layer files, documentation changes, continuous integration workflows, Agents Schema synchronization, warehouse model replacement, commits, or pushes.

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
| **Discovery** | First for new/full pipeline runs | [discovery-requirements.md](references/discovery-requirements.md), [discovery-artifacts.md](references/discovery-artifacts.md), [discovery-status-vocabulary.md](references/discovery-status-vocabulary.md), [table-inclusion-priority-filter.md](references/table-inclusion-priority-filter.md), [source-profiling.md](references/source-profiling.md) |
| **Project setup and configuration** | Automatic setup-only phase after discovery requirements are accepted | [bootstrap.md](references/bootstrap.md), [software-prerequisites.md](references/software-prerequisites.md) |
| **0 Inputs** | Always first | [skill-inputs.md](references/skill-inputs.md), [profile-listing.md](references/profile-listing.md), [profile-credential-keys.md](references/profile-credential-keys.md), [project-naming.md](references/project-naming.md), [env-configuration.md](references/env-configuration.md), [source-confirmation.md](references/source-confirmation.md), [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md), [security-and-credentials.md](references/security-and-credentials.md), [schema-isolation.md](references/schema-isolation.md), [code-agent-setup.md](references/code-agent-setup.md), [software-prerequisites.md](references/software-prerequisites.md) |
| **0a Knowledge layers** | Built-in reusable knowledge plus user dbt standards and domain rules | [skill-knowledge.md](references/skill-knowledge.md), [project-knowledge.md](references/project-knowledge.md) |
| **0b Subagents** | Optional speed-up | [subagent-workflow.md](references/subagent-workflow.md) |
| **0c Best practices** | Design guardrails | [data-engineering-best-practices.md](references/data-engineering-best-practices.md), [privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md), [reporting-coverage-requirements.md](references/reporting-coverage-requirements.md) |
| **0c Principal standards** | Advanced software-grade data engineering standards | [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md) |
| **0c Writing style** | Full wording, five-pillar reports, and rich dashboard design | [writing-style.md](references/writing-style.md), [reporting-standards.md](references/reporting-standards.md), [universal-analytics-framework.md](references/universal-analytics-framework.md) |
| **0d Engineer gate** | Explicit modeling decisions | [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) |
| **0e Phased discovery** | Discover just enough per phase | [phased-discovery.md](references/phased-discovery.md) |
| **0f Recommendations** | Agent recommends; data engineer approves | [recommendation-and-review.md](references/recommendation-and-review.md) |
| **0g Diagrams** | Mermaid-only diagrams with visibility checks | [mermaid-diagrams.md](references/mermaid-diagrams.md) |
| **0g1 Evidence-driven build** | Build only what can be proven | [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md) |
| **0h Layer data validation** | Warehouse query checks after every built layer | [layer-data-validation.md](references/layer-data-validation.md), [cardinality-validation.md](references/cardinality-validation.md), [layer-verification-ledger.md](references/layer-verification-ledger.md), [assumption-tests.md](references/assumption-tests.md) |
| **0h1 Independent verification** | Builder writes evidence; verifier reads repo only | [independent-verification-governance.md](references/independent-verification-governance.md), [agents/dbt-verifier-agent.md](agents/dbt-verifier-agent.md) |
| **0i Key performance indicators** | Business metric definitions, approval evidence, contracts, and reconciliation | [kpi-definitions.md](references/kpi-definitions.md), [kpi-definition-contract.md](references/kpi-definition-contract.md), [metric-verification.md](references/metric-verification.md), [metric-verification-checklist.md](references/metric-verification-checklist.md), [kpi-reconciliation.md](references/kpi-reconciliation.md) |
| **0j Advanced review** | Senior data-engineering completion gate | [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md) |
| **0k Rollback / redo** | Controlled rollback when a completed phase must be undone or rebuilt | [phase-rollback.md](references/phase-rollback.md) |
| **1 Init** | New project | [project-initialization.md](references/project-initialization.md), [software-prerequisites.md](references/software-prerequisites.md) |
| **2 Schemas** | After init | [warehouse-schema-setup.md](references/warehouse-schema-setup.md), [schema-isolation.md](references/schema-isolation.md) |
| **3 Sources** | Packages + source YAML | [packages-and-sources.md](references/packages-and-sources.md) |
| **3b Source profiling** | Before staging | [source-profiling.md](references/source-profiling.md), [cardinality-validation.md](references/cardinality-validation.md) |
| **4 Layer names** | Before models | [dbt-project-layers.md](references/dbt-project-layers.md) |
| **5 Staging** | Layer 1 | [staging-spec.md](references/staging-spec.md) |
| **6 Intermediate** | Layer 2 | [intermediate-spec.md](references/intermediate-spec.md), [mapping-seeds.md](references/mapping-seeds.md) |
| **7 Marts** | Layer 3 star schema | [marts-spec.md](references/marts-spec.md), [gold-dimension-completeness.md](references/gold-dimension-completeness.md), [materialization-rules.md](references/materialization-rules.md) |
| **7b Semantic** | Metrics on marts | [semantic-layer-spec.md](references/semantic-layer-spec.md) |
| **7c Evaluator** | Best-practice audit | [project-evaluator.md](references/project-evaluator.md), [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) |
| **8 Docs** | After layers | [documentation.md](references/documentation.md) |
| **8a Analytics insight reporting** | Business reporting design before presentation | [analytics-insight-reporting.md](references/analytics-insight-reporting.md), [universal-analytics-framework.md](references/universal-analytics-framework.md), [kpi-discovery-framework.md](references/kpi-discovery-framework.md) |
| **8b Presentation layer** | Optional final user-facing layer after analytics insight reporting | [presentation-layer.md](references/presentation-layer.md), [matplotlib-presentation-layer.md](references/matplotlib-presentation-layer.md), [powerbi-template.md](references/powerbi-template.md), [powerbi-thin-model-template.md](references/powerbi-thin-model-template.md), [powerbi-kpi-dax-tooling.md](references/powerbi-kpi-dax-tooling.md), [powerbi-official-docs.md](references/powerbi-official-docs.md), [powerbi-pbip-desktop-requirements.md](references/powerbi-pbip-desktop-requirements.md) when Power BI is approved |
| **9 Git** | After each stage | [github-repo-resolution.md](references/github-repo-resolution.md), [git-workflow.md](references/git-workflow.md) |
| **10 Agents Schema / continuous integration** | Metadata + automation | [agents-schema-setup.md](references/agents-schema-setup.md), [cicd-setup.md](references/cicd-setup.md) |
| **Plan approval** | Before each non-setup build phase | [phase-plan-approval.md](references/phase-plan-approval.md) |
| **Review** | Human approval points | [human-review.md](references/human-review.md), [kpi-gap-and-stakeholder-warnings.md](references/kpi-gap-and-stakeholder-warnings.md) |
| **Phase report** | After each completed phase | [phase-completion-report.md](references/phase-completion-report.md), [report-artifact-organization.md](references/report-artifact-organization.md), [human-attention-reporting.md](references/human-attention-reporting.md), [kpi-gap-and-stakeholder-warnings.md](references/kpi-gap-and-stakeholder-warnings.md), [stakeholder-layer-and-presentation-guide.md](references/stakeholder-layer-and-presentation-guide.md), [next-phase-prompt.md](references/next-phase-prompt.md) |
| **Context tree** | Ongoing project memory | [context-tree.md](references/context-tree.md) |
| **Done** | Final check + user summary | [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md), [independent-verification-governance.md](references/independent-verification-governance.md) |

Context prompt template: [agent-context-prompt.md](references/agent-context-prompt.md)

## Step 0 - Load configuration

Read [project.config.yml](project.config.yml), [skill-inputs.md](references/skill-inputs.md), [profile-listing.md](references/profile-listing.md), [project-naming.md](references/project-naming.md), [schema-isolation.md](references/schema-isolation.md), [env-configuration.md](references/env-configuration.md), [source-confirmation.md](references/source-confirmation.md), [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md), [skill-knowledge.md](references/skill-knowledge.md), [project-knowledge.md](references/project-knowledge.md), [discovery-requirements.md](references/discovery-requirements.md), [discovery-artifacts.md](references/discovery-artifacts.md), [discovery-status-vocabulary.md](references/discovery-status-vocabulary.md), [phased-discovery.md](references/phased-discovery.md), [recommendation-and-review.md](references/recommendation-and-review.md), [writing-style.md](references/writing-style.md), [reporting-standards.md](references/reporting-standards.md), [universal-analytics-framework.md](references/universal-analytics-framework.md), [analytics-insight-reporting.md](references/analytics-insight-reporting.md), [mermaid-diagrams.md](references/mermaid-diagrams.md), [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md), [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md), [layer-data-validation.md](references/layer-data-validation.md), [cardinality-validation.md](references/cardinality-validation.md), [kpi-definitions.md](references/kpi-definitions.md), [kpi-definition-contract.md](references/kpi-definition-contract.md), [metric-verification.md](references/metric-verification.md), [metric-verification-checklist.md](references/metric-verification-checklist.md), [kpi-reconciliation.md](references/kpi-reconciliation.md), [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md), [phase-plan-approval.md](references/phase-plan-approval.md), [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md), [phase-completion-report.md](references/phase-completion-report.md), [report-artifact-organization.md](references/report-artifact-organization.md), [next-phase-prompt.md](references/next-phase-prompt.md), and [context-tree.md](references/context-tree.md).

For smaller context windows, read required references fully, extract the rules that apply to the active checkpoint into the phase plan or working notes, and avoid carrying unused details forward. Prefer loading phase-specific references only when entering that phase. Do not skip required safety references, but summarize-and-discard details that are not relevant to the active checkpoint.

Resolve paths relative to workspace root. dbt project root = `{project.root}`.

Read [skill-knowledge.md](references/skill-knowledge.md) and [project-knowledge.md](references/project-knowledge.md) after loading configuration and before discovery summaries or phase plans. Use built-in skill knowledge for reusable dbt, big data, warehouse optimization, Power BI, semantic, privacy, and validation standards. Use project knowledge files such as `AGENT_KNOWLEDGE.md`, `docs/dbt_knowledge.md`, `docs/business_rules.md`, `.agents/project_knowledge.md`, and `reports/agent/CONTEXT_TREE.md` for local/domain overrides when they exist. Apply prompt `project_rules` first when there is a conflict. Ask before persisting new knowledge from chat.

**User prompt overrides `.env` and configuration** for schema, domain, layers, materialization, commit mode. Use `.env` for non-secret reusable inputs before asking the user. Workspace `.env` is not created by `npx skills add`; create it on first run when missing. If `.env` is missing in a fresh clone, follow [env-configuration.md](references/env-configuration.md): resolve `.env.example` from the workspace root, dbt project root, or installed skill folder, create a safe local workspace `.env` from that template with placeholder values only, list available dbt profiles with [profile-listing.md](references/profile-listing.md), stop before discovery or dbt commands, and ask the user for `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA`. Do not fill `.env` from profiles, profile target schemas, warehouse schemas, old runs, terminal output, examples, nearby workspaces, or guesses. Do not search the repository, inspect terminal output, infer, suggest, or summarize values from other workspaces or previous runs.

Read [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md) immediately after loading `.env` and before any discovery. Resolve the active dbt profile and adapter from `~/.dbt/profiles.yml`; use only that adapter's discovery path. Do not call AWS, Redshift, PostgreSQL, Snowflake, BigQuery, Databricks, cloud identity checks, warehouse connectors, metadata queries, or Model Context Protocol discovery servers before the selected profile adapter is resolved and announced. Do not call AWS, Redshift, or any other warehouse-specific path unless the selected profile adapter requires it or the user explicitly changes profiles.

If the configured source is missing, empty, inaccessible, ambiguous, or mismatched, read [source-confirmation.md](references/source-confirmation.md). Stop after metadata-only candidate listing. Recommend the likely replacement with evidence, then wait for user approval before changing database, dataset, catalog, schema, table, tenant, client, domain, environment, assumption, `.env`, profile settings, profiling, discovery reports, or continuing discovery.

For normal runs, collect only the values the agent cannot infer safely: `domain`, `dbt_profile_name`, and `source_schema`. Optionally accept `business_description` / `DBT_BUSINESS_DESCRIPTION` when the user wants to explain the client, process, reporting goals, or business context. When `dbt_profile_name` is missing or ambiguous, list available profiles using [profile-listing.md](references/profile-listing.md), then wait for the user to choose. Derive project name/root, project slug, dbt source name, schema prefix, layer names, commit behavior, and GitHub mode unless the user explicitly overrides them.

Resolve `project.name`, `project.root`, and `project_slug` before `dbt init`. Never use `dbt_profile_name` or raw `DBT_DOMAIN` as the folder/project name unless the user explicitly provides it as `dbt_project_name`, `dbt_project_root`, or `project_slug`. Prefer a clean name derived from `source_schema`, source name, existing project name, or descriptive profile database/catalog; use `domain` only as a last fallback and `github_repo_name` only when the user provided it for push. Use `DBT_BUSINESS_DESCRIPTION` only for analytics understanding, never for physical folder, schema, database, or model names.

Keep the source schema read-only and immutable. Never update, insert, delete, truncate, merge into, create, drop, alter, or repair data in the configured source schema or source tables. Even if the user asks to "mark records complete", "fix source rows", "delete bad source data", or similar, implement the logic only as dbt transformations, tests, seeds, snapshots, or audits in non-source schemas, then explain that the source remains unchanged. Never build dbt models, package models, evaluator tables, seeds, snapshots, or audit outputs into `source_schema`. Route evaluator outputs to `<layer_schema_prefix>_evaluator` and layer outputs to separate medallion schemas. Resolve `layer_schema_prefix` with [schema-isolation.md](references/schema-isolation.md); do not use short source names like `dh` as physical schema prefixes unless the user explicitly sets them.

Before each phase that changes models, semantic files, documentation files, workflow files, or warehouse objects, write/update `{project.root}/AGENT_PLAN.md`, explain the planned work in Markdown, and wait for approval for that phase. Read-only discovery is allowed before approval when needed for an accurate plan.

Project setup and configuration is the exception: after the user accepts discovery requirements, write/update `{project.root}/AGENT_PLAN.md` with the phase marked as automatic setup-only, run setup, then write `reports/agent/01_setup/setup_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`. If any setup safety gate from [bootstrap.md](references/bootstrap.md) is triggered, stop and ask before continuing.

Approval is controlled by workflow checkpoint. Never treat a user response at one checkpoint as permission to run multiple build phases. After automatic project setup and configuration finishes, stop at the next phase plan and ask for approval before generating source YAML or building bronze/staging.

## Step 0b - Optional subagents

Read [subagent-workflow.md](references/subagent-workflow.md) when source profiling, mapping review, model planning, documentation, or evaluator review can safely run in parallel. The main agent decides when to delegate and keeps dbt commands, shared file edits, commits, pushes, and final decisions.

## Step 0.1 - Domain neutrality

This skill is industry-agnostic. Processes, entities, dimensions, measures, and sensitive fields come from **this warehouse’s evidence** and the user’s project rules. Do not hardcode industry column names, brands, or entity catalogs into plans, gates, or scripts. Do not require a commerce/healthcare/subscription shape when those tables are absent. Examples in reference docs are illustrative only.

## Step 0.2 - Security

Read [security-and-credentials.md](references/security-and-credentials.md).

Never hardcode secrets. Ask before production changes.

## Step 0.3 - Data engineering guardrails

Read [data-engineering-best-practices.md](references/data-engineering-best-practices.md) and [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md) before model design and again before final delivery. Apply grain, test, incremental, snapshot, documentation, lineage, directed acyclic graph, freshness, macros, packages, build process, privacy, performance, state-based continuous integration, contracts/versioning, SQL style, warehouse optimization, modern table format, and downstream presentation guardrails.

Read [privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md) and [reporting-coverage-requirements.md](references/reporting-coverage-requirements.md) when discovery finds direct identifiers, sensitive fields, protected health information, personally identifiable information, or ambiguous, placeholder, abbreviated, or poorly named fields. The agent must recommend a safe default, document the recommendation, and ask only for approval or business definitions instead of leaving the whole decision to the user. When the user opts out of privacy minimization (for example `Do NOT apply privacy minimization unless I explicitly request it`), record that rule, build conformed reporting dimensions with business labels, and **show reporting attributes from gold on the presentation when useful** — discover fields from this project’s evidence; do not hardcode industry field lists. Do not hide attributes “to be safe” and do not write report copy that the presentation still avoids/hides identifiers after opt-out. Close OPEN Attention Board and KPI Gap Register privacy-minimization rows; only always-exclude classes (secrets/OTP/full bank dumps/national ID/PHI) stay excluded unless the user explicitly asks.

Read [writing-style.md](references/writing-style.md) and [reporting-standards.md](references/reporting-standards.md) before writing user-facing prompts, plans, reports, summaries, diagram notes, presentation artifacts, or final handoffs. Use full wording instead of shorthand, except for official tool names, commands, filenames, environment variables, and code identifiers. Every report must include the five reporting pillars when relevant: context and strategy, key performance indicators, trend analysis and variance, insights and attribution, and recommendations and next steps. If a pillar is not supported yet, mark it deferred with the reason instead of guessing.

Every `WARN`, `FAIL`, `BLOCKED`, or `SKIPPED` status in `PIPELINE_STATUS.md`, phase reports, approval checklists, SQL proof indexes, and final summaries must include why the status was used, the evidence path, what the data engineer should review, the required action, and whether it blocks the next checkpoint. Do not leave non-`PASS` statuses as unexplained labels.

Read [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) before writing each phase plan. The phase plan must show the agent's data-engineering decisions, evidence, and approval needs; do not hide grain, key, join, bridge table, mapping, privacy, metric, materialization, or validation choices inside code.

If the agent cannot understand the source tables, relationships, business processes, required metrics, data quality rules, required output models, or reporting needs for the current scope, stop the dependent scope and ask instead of guessing.

Read [phased-discovery.md](references/phased-discovery.md) before each phase. Discover only what is needed for the next layer or workflow step; do not fully design silver/gold/semantic outputs during initial discovery or bronze work.

Read [recommendation-and-review.md](references/recommendation-and-review.md) before writing discovery summaries, phase plans, phase reports, and final handoffs. The agent must recommend the best path with evidence, show what looks right and what is not ready, state confidence about proven vs uncertain items, and ask the data engineer only for business-impacting approvals. Do not make the user design everything from scratch.

Read [mermaid-diagrams.md](references/mermaid-diagrams.md) before creating or changing any diagram. All diagrams must be Mermaid blocks, entity relationships must use Mermaid `erDiagram`, and every added or changed Mermaid diagram must be verified as visible/parseable before the phase is marked complete.

Read [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md), [layer-data-validation.md](references/layer-data-validation.md), [cardinality-validation.md](references/cardinality-validation.md), [layer-verification-ledger.md](references/layer-verification-ledger.md), and [assumption-tests.md](references/assumption-tests.md) before building bronze/staging, silver/intermediate, or gold/marts. After each layer build, run warehouse validation queries for row presence, expected emptiness, grain, keys, relationships, cardinality, row-count movement, row loss, row multiplication, date coverage, status/category distributions, measures, mapping coverage, and privacy exposure. Save each validation query as a reusable SQL proof file under the phase `sql_proofs/` folder with purpose, expected result, captured result, status, and runnable SQL. Promote approved assumptions from discovery or the phase report into dbt singular or generic tests using [assumption-tests.md](references/assumption-tests.md) and `templates/dbt/tests/`. Add `Data Verification Results`, `SQL Proof Files`, `Assumption Tests`, and cardinality/grain evidence to the layer report, update `reports/agent/LAYER_VERIFICATION_LEDGER.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`, share the important results with the user, and stop before the next layer when a model that should contain data is empty or any validation issue is unexplained.

Read [universal-analytics-framework.md](references/universal-analytics-framework.md), [kpi-discovery-framework.md](references/kpi-discovery-framework.md), [kpi-definitions.md](references/kpi-definitions.md), [kpi-definition-contract.md](references/kpi-definition-contract.md), [metric-verification.md](references/metric-verification.md), [metric-verification-checklist.md](references/metric-verification-checklist.md), [kpi-reconciliation.md](references/kpi-reconciliation.md), and [cardinality-validation.md](references/cardinality-validation.md) before analytics insight reporting, semantic layer, presentation layer, and final delivery. The agent must construct business process, fact, dimension, broad measure, and contextual metric catalogs first, then propose strategic key performance indicators with business meaning, source model, grain, numerator, denominator, filters, time field, caveats, validation evidence, approval status, cardinality proof, and expected versus actual reconciliation. Create as many useful supported measures and contextual metrics as the validated data safely allows, but promote only decision-relevant, validated, and approved metrics to key performance indicators. Maintain `reports/agent/KPI_DEFINITION_CONTRACTS.md` and `reports/agent/METRIC_VERIFICATION_MATRIX.md`; these files are acceptance-gate inputs, not optional summaries. Do not create semantic metrics or presentation calculations from ambiguous or unreconciled key performance indicators. No key performance indicator is trusted until its source-to-final value, grain, cardinality, and SQL proof file are proven.

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

Validate the skill repository configuration before project work when operating inside the skill repository:

```powershell
python <installed-skill-path>/scripts/validate_config.py --root <installed-skill-path>
```

```powershell
cd {project.root}
$dbt = "dbt"          # prefer active venv/path; see validation-commands.md for fallbacks
& $dbt debug          # init / profile changes only
& $dbt parse --no-partial-parse
& $dbt build --select +path:<layer_folder>
```

After each bronze/staging, silver/intermediate, or gold/marts build, run [layer-data-validation.md](references/layer-data-validation.md). `dbt build` passing does not by itself prove the layer is usable.

## Independent verification governance

Read [independent-verification-governance.md](references/independent-verification-governance.md).

Verification must not depend only on the same agent or chat window. The builder agent writes evidence to files; a fresh verifier reads the repository, dbt artifacts, SQL proofs, and reports from zero context.

| Layer | Role |
|---|---|
| Builder agent | Discovery, build, SQL proofs, reports, status files |
| Independent verifier agent | [agents/dbt-verifier-agent.md](agents/dbt-verifier-agent.md) - audit from disk only |
| Acceptance script | `python <installed-skill-path>/scripts/run_acceptance_gate.py --root <project.root>` - deterministic pass/fail |
| CI gate | [.github/workflows/dbt_acceptance_gate.yml](.github/workflows/dbt_acceptance_gate.yml) |
| Human attention board | `reports/agent/HUMAN_ATTENTION_BOARD.md` |
| KPI gap register | `reports/agent/KPI_GAP_REGISTER.md` |
| Human sign-off | `reports/agent/HUMAN_VERIFICATION_GUIDE.md` |

MCP may provide access to repo, files, database, and dbt commands, but MCP is not the verifier.

Before final delivery, run:

```powershell
python <installed-skill-path>/scripts/run_acceptance_gate.py --root <project.root>
python <installed-skill-path>/scripts/check_requirement_traceability.py --root <project.root>
python <installed-skill-path>/scripts/check_layer_proof_coverage.py --root <project.root>
python <installed-skill-path>/scripts/verify_metric_reconciliation.py --root <project.root>
```

Do not claim project completion when the acceptance gate returns `FAIL`. Generated projects should include `reports/agent/ACCEPTANCE_GATE_REPORT.md` and `reports/agent/ACCEPTANCE_GATE_REPORT.json`.

After builder work is complete, run a fresh verifier agent with [agents/dbt-verifier-agent.md](agents/dbt-verifier-agent.md) and write `reports/agent/INDEPENDENT_VERIFICATION_REPORT.md` plus `.json`. Final delivery is blocked when independent verification is `FAIL`.

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
9. Analytics insight reporting - discover and document trusted business outputs, business process catalog, fact catalog, dimension catalog, key performance indicator catalogs, dashboard spec, and reporting readiness before presentation work - [analytics-insight-reporting.md](references/analytics-insight-reporting.md)
10. Presentation layer gate - required after analytics insight reporting and before final delivery; ask whether the user wants a presentation layer and which technology to use. Offer **Matplotlib** as the recommended default and Power BI as the alternative. If the user approves and does not name another technology, default to the Matplotlib refreshable web report workflow, run a separate `presentation_layer` phase, install missing `matplotlib`/`numpy`/`pandas` prerequisites when needed, map every recommended measure and key performance indicator from analytics insight catalogs into `kpi_figure_coverage.md`, and build a rich local browser report under `reports/agent/10_presentation/matplotlib/` with `serve_report.py`, `report.html`, colorful business tabs, executive cards, chart cards, insight captions, exception callouts, detail sections, live SVG/HTML or browser-native chart routes, SQL verification, `open_report.bat`, and business-friendly labels via `label_dictionary.md`. Validate the actual local report URL with `scripts/validate_local_web_report.py` before handoff; do not mark complete if the browser would see an empty response. Do not use PNG files as the primary web rendering path; use them only as optional exports/snapshots. If the user explicitly chooses Power BI, use the Power BI Desktop human-connected template workflow, create the handoff folder/checklist, wait for the user to save and confirm the connected PBIP, then inject only approved measures and safe reporting metadata.
11. Agents Schema - publish dbt metadata to `AGENTS.*` after `target/manifest.json` exists when enabled and supported
12. Automation - continuous integration workflow
13. **Acceptance gate + independent verification** - `python <installed-skill-path>/scripts/run_acceptance_gate.py --root <project.root>`, then fresh verifier agent per [agents/dbt-verifier-agent.md](agents/dbt-verifier-agent.md)
14. **Advanced review, acceptance + final summary** - [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md), [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md)

After project setup and configuration, each stage: **phase-specific discovery -> agent recommendation -> data engineer decision check -> write Markdown plan -> ask approval -> implement -> parse/build -> warehouse data validation queries -> write phase report with validation results in the managed reports folder -> update report index -> update context tree -> write `reports/agent/NEXT_PHASE_PROMPT.md` -> send a normal assistant message with a visible Markdown chat control-panel summary of what was completed and what is next -> paste the exact next-phase prompt in that chat message -> ask interactive approval for the displayed prompt when available -> ask commit**. Ask for push only when a non-local GitHub repository is configured or the user requested push. The native question card is not enough by itself; the visible chat summary must appear as a separate assistant message immediately before the clickable approval question.

## Step 2 - Sources

Read [packages-and-sources.md](references/packages-and-sources.md), [source-profiling.md](references/source-profiling.md), [schema-isolation.md](references/schema-isolation.md), and [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md).

All five mandatory packages in `packages.yml`: `codegen`, `dbt_utils`, `dbt_expectations`, `dbt_project_evaluator`, and `audit_helper`. Codegen for sources. Derive `source.name` from `source.schema` unless explicitly provided; use domain only as a last fallback when the source schema is generic. Write source YAML only under `models/sources/`, never under bronze, silver, or gold layer folders. Do not move source YAML into bronze/staging to satisfy evaluator source-directory warnings; document accepted exceptions or ask before changing structure. Add the configured `source.schema` to source YAML after generate. Profile row counts, candidate keys, relationships, important dates, measures, and status/code fields before staging.

## Step 3 - Layer 1 (staging)

Read [staging-spec.md](references/staging-spec.md) and [layer-data-validation.md](references/layer-data-validation.md). `source()` only. No business KPIs. After build, verify staging row counts against source tables and share the results.

## Step 4 - Layer 2 (intermediate)

Read [intermediate-spec.md](references/intermediate-spec.md), [mapping-seeds.md](references/mapping-seeds.md), [layer-data-validation.md](references/layer-data-validation.md), and [cardinality-validation.md](references/cardinality-validation.md). `ref()` only. Use mapping seeds or reference tables when `project_rules` include manual mappings or code translations. After build, verify row presence, grain, joins, cardinality, row loss, and row multiplication.

## Step 5 - Layer 3 (marts / star schema)

Read [marts-spec.md](references/marts-spec.md), [gold-dimension-completeness.md](references/gold-dimension-completeness.md), [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md), [layer-data-validation.md](references/layer-data-validation.md), [cardinality-validation.md](references/cardinality-validation.md), [kpi-definitions.md](references/kpi-definitions.md), [kpi-definition-contract.md](references/kpi-definition-contract.md), [metric-verification.md](references/metric-verification.md), [metric-verification-checklist.md](references/metric-verification-checklist.md), and [kpi-reconciliation.md](references/kpi-reconciliation.md). `ref()` only. Build domain-appropriate facts, dimensions, and reporting marts based on profiled source grain and user requirements. A fact-only gold layer is incomplete unless every missing dimension is explicitly BLOCKED/DEFERRED with proof. Prefer privacy-safe dimensions over dropping all dimensions. After build, verify every fact, dimension, and reporting mart has data when upstream data exists; treat unexpected empty gold models as blockers. Define and reconcile key performance indicators explicitly before promoting them to gold marts or semantic metrics. Run `scripts/check_gold_star_shape.py --root <project.root>` before calling gold complete.

## Step 5b - Semantic layer

Read [semantic-layer-spec.md](references/semantic-layer-spec.md), [kpi-definitions.md](references/kpi-definitions.md), [kpi-definition-contract.md](references/kpi-definition-contract.md), [metric-verification.md](references/metric-verification.md), [metric-verification-checklist.md](references/metric-verification-checklist.md), [kpi-reconciliation.md](references/kpi-reconciliation.md), and [cardinality-validation.md](references/cardinality-validation.md). Compose with `building-dbt-semantic-layer`. Legacy spec on dbt 1.10.x. Only create semantic metrics from approved, supported, and reconciled key performance indicator definitions with validated grain and cardinality.

## Step 5c - Project evaluator

Read [project-evaluator.md](references/project-evaluator.md). Before running evaluator, confirm `dbt_project.yml` routes `models: dbt_project_evaluator: +schema` to `<layer_schema_prefix>_evaluator` and sets evaluator vars for the active medallion folder names. Do not let evaluator package tables build in `source_schema`. When querying evaluator result tables, inspect available columns before selecting version-specific fields.

```powershell
& $dbt build --select package:dbt_project_evaluator
```

## Step 6 - Documentation

Read [documentation.md](references/documentation.md). Run `dbt docs generate`. Use `dbt docs serve` only as a non-blocking local viewing step and report the URL when started. In a full pipeline, do not mark delivery complete after documentation. Move to analytics insight reporting.

## Step 6a - Analytics insight reporting

Read [analytics-insight-reporting.md](references/analytics-insight-reporting.md), [report-artifact-organization.md](references/report-artifact-organization.md), [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md), [universal-analytics-framework.md](references/universal-analytics-framework.md), [kpi-discovery-framework.md](references/kpi-discovery-framework.md), [kpi-definition-contract.md](references/kpi-definition-contract.md), [metric-verification-checklist.md](references/metric-verification-checklist.md), [kpi-reconciliation.md](references/kpi-reconciliation.md), [cardinality-validation.md](references/cardinality-validation.md), [reporting-standards.md](references/reporting-standards.md), [kpi-definitions.md](references/kpi-definitions.md), [metric-verification.md](references/metric-verification.md), and [docs/kpi_proof_standards.md](docs/kpi_proof_standards.md). Before this phase, write/update `AGENT_PLAN.md` and wait for approval. Classify tables first, then discover and document the most useful business-facing outputs from validated marts and semantic metrics. Produce the analytics insight and key performance indicator deliverables in the managed folders from [report-artifact-organization.md](references/report-artifact-organization.md), including `business_process_catalog.md`, `fact_catalog.md`, `dimension_catalog.md`, `09_analytics_insights/`, `09_analytics_insights/kpis/`, `09_analytics_insights/kpis/sql_proofs/`, plus root `REPORT_INDEX.md`, `HUMAN_VERIFICATION_GUIDE.md`, `KPI_DEFINITION_CONTRACTS.md`, and `METRIC_VERIFICATION_MATRIX.md`. Do not create presentation artifacts in this phase.

### Analytics insight reporting hard rules

- Do not create fake insights.
- Do not suggest charts just because data exists.
- Every measure, metric, key performance indicator, and report candidate must map to validated marts or semantic metrics.
- Keep the hierarchy clear: measures are raw counts/sums/averages, metrics add time/dimension/ratio context, and key performance indicators are decision-relevant metrics tied to goals, thresholds, targets, risks, or management review.
- Generate business process, fact, dimension, broad measure, and metric catalogs before narrowing to strategic key performance indicators.
- Every visual must answer a real business question.
- Do not expose sensitive fields without approval.
- Clearly separate trusted outputs from uncertain or deferred outputs.
- Prefer useful, simple, business-friendly reporting over too many technical tables.
- Do not hardcode one domain's key performance indicators, page names, or sample values.
- Do not invent targets, benchmarks, attribution, or recommendations without evidence.
- Do not apply `5 key performance indicators per table` to dimensions, bridges, reference tables, or audit tables.
- Do not publish catalog numbers without linked `sql_proofs/*.sql` files per [docs/kpi_proof_standards.md](docs/kpi_proof_standards.md).
- Maximum means maximum useful business insight supported by validated data: business areas, processes, facts, dimensions, measures, metrics, strategic key performance indicators, report pages, and deferred opportunities with proof status, not maximum number of dashboards or arbitrary catalog row counts.
- Do **not** optimize for fixed 50+/100+ measure or metric counts. Generate complete analytical coverage for each validated business process. Coverage is complete when every material fact has appropriate volume, value, status, time, quality, segmentation, exception and lifecycle analysis, and every published result answers a documented business or engineering question. Read [analytics-product-completeness.md](references/analytics-product-completeness.md) and [reporting-coverage-requirements.md](references/reporting-coverage-requirements.md). Run `python <skill>/scripts/check_analytics_coverage.py --root <project.root>` and related completeness scripts before presentation.
- Maintain separate catalogs for business measures, contextual metrics, strategic KPIs, data-quality metrics, and pipeline-health metrics. Keep technical model row counts out of executive business pages.
- Create `analytics_coverage_matrix.md`, `fact_coverage_contracts.md`, `model_classification.md`, and `business_process_catalog.md` as primary gates.
- Build conformed dimensions that **this warehouse** evidence supports (entity, date, status/labels, and any other dims present); blank categorical chart axes are a presentation failure. Do not invent industry-specific dim types.
- Presentation `kpi_figure_coverage.md` must map published business metrics/KPIs as `RENDERED`, `BLOCKED`, or `DEFERRED`. Full raw dictionaries may live under Metric Dictionary pages.
- The live Matplotlib report must use **business display names** and **formatted values** on all business pages. All Measures / All Metrics may exist as dictionary pages but must not be SQL dumps of snake_case ids / raw floats. Add process-based pages from discovered processes, plus Dimensions / Data Quality / Pipeline Health when supported. See Rules 5b–5c and [report-page-contract.md](references/report-page-contract.md).
- Presentation `sql_verification/` must contain executed proofs with captured results for board measures/metrics and charts, plus `_proof_index.md` mapping RENDERED items to those proofs.
- Run live warehouse SQL for every `RENDERED` chart and prove the report refresh path; HTML shell HTTP 200 alone is not completion.

### Production analytics product completeness

Analytics completeness is based on supported business and engineering coverage, not a fixed number of catalog rows.

Before analytics insight reporting can pass:

1. Classify every in-scope model (see [universal-model-classification.md](references/universal-model-classification.md)).
2. Create `analytics_coverage_matrix.md` mapping every material business process to facts, dimensions, measures, metrics, KPIs, time analysis, segmentation, quality checks, reconciliations, report pages, and status.
3. Evaluate each validated fact for volume, value/quantity/duration, status/lifecycle, time trend/period comparison, dimensional segmentation, data quality, exceptions/aging, source reconciliation, and supported business questions.
4. Maintain separate catalogs for business measures, contextual business metrics, strategic KPIs, data-quality metrics, and pipeline-health metrics.
5. Keep technical model row counts, null checks, orphan counts and pipeline statistics out of executive business pages.
6. Every published KPI must include business question, decision supported, action when bad, owner, definition, formula, grain/counting key, included/excluded records, date field/role, dimensions, unit/currency/format, aggregation behavior, target or target-not-defined, desired direction, validation source, reconciliation tolerance, SQL proof, and approval/confidence status.
7. Every strategic KPI must be evaluated for time intelligence per [time-intelligence-standard.md](references/time-intelligence-standard.md); implement only comparisons supported by date coverage.
8. Every report page must declare a page contract per [report-page-contract.md](references/report-page-contract.md).
9. Treat raw technical names, blank labels, raw decimal ratios, unlabeled currency, KPIs without periods, unsupported additive totals, deleted-record definitions on executive pages, technical row counts as business KPIs, and charts without comparison/question/caption as presentation failures.
10. SQL execution is not sufficient business validation. Critical KPIs require reconciliation and business-owner approval or explicit pending-approval status.

After this phase, run `python <installed-skill-path>/scripts/validate_kpi_proofs.py --root <project.root>` and `python <installed-skill-path>/scripts/verify_metric_reconciliation.py --root <project.root>`, then record the results in the phase report. For medium projects with broad table scope, use project-scale targets or document each shortfall in `insight_backlog.md`. Update `reports/agent/09_analytics_insights/analytics_insight_reporting_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`, then stop at the presentation-layer gate unless the user already approved presentation work.

## Step 6b - Presentation layer recommendation

Read [presentation-layer.md](references/presentation-layer.md), [matplotlib-presentation-layer.md](references/matplotlib-presentation-layer.md), [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md), [universal-analytics-framework.md](references/universal-analytics-framework.md), [analytics-insight-reporting.md](references/analytics-insight-reporting.md), [reporting-standards.md](references/reporting-standards.md), [kpi-definitions.md](references/kpi-definitions.md), [kpi-definition-contract.md](references/kpi-definition-contract.md), [metric-verification.md](references/metric-verification.md), and [metric-verification-checklist.md](references/metric-verification-checklist.md). If Power BI is approved, also read [powerbi-template.md](references/powerbi-template.md), [powerbi-thin-model-template.md](references/powerbi-thin-model-template.md), [powerbi-kpi-dax-tooling.md](references/powerbi-kpi-dax-tooling.md), [powerbi-official-docs.md](references/powerbi-official-docs.md), and [powerbi-pbip-desktop-requirements.md](references/powerbi-pbip-desktop-requirements.md). After analytics insight reporting, recommend the best presentation-layer option using `dashboard_spec.md`, `business_process_catalog.md`, `fact_catalog.md`, `dimension_catalog.md`, `kpi_catalog.md`, `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, `reporting_catalog.md`, `insight_backlog.md`, `reporting_readiness_scorecard.md`, and `analytics_insight_report.md` as the scope contract. Before final delivery is closed, ask the presentation decision with a concise evidence summary and native clickable choices when available: `Yes - build Matplotlib refreshable web report (recommended)`, `Yes - prepare Power BI Desktop template handoff`, `No presentation layer - complete final delivery now`, and `Tell me what to change first`. If the user approves a presentation layer and does not specify another technology, default to the Matplotlib refreshable web report workflow: install missing `matplotlib`, `numpy`, and `pandas` when needed, map every recommended measure, metric, and key performance indicator into `kpi_figure_coverage.md`, render SQL-verified charts as live Matplotlib SVG/HTML endpoints or approved browser-native charts from refreshed JSON, and build a polished local browser report with `serve_report.py`, `report.html`, colorful business tabs, classified `report_pages/` modules, executive cards, chart cards, exception callouts, detail sections, refresh timestamp/control, open launcher, and business-friendly labels under `reports/agent/10_presentation/matplotlib/`. PNG/SVG files are optional exports or snapshots; do not use PNG as the primary web rendering path. If the user explicitly chooses Power BI, use the human-connected Desktop template workflow: create the Power BI output folder, write the table/relationship/storage-mode/measures-table checklist, ask the user to connect the approved gold or semantic data in Power BI Desktop, save the `.pbip` at the specified path/name, and confirm the path before any PBIP edits. After confirmation, the agent may inject only approved DAX measures, descriptions, format strings, display folders, and safe annotations into the approved measures table, then validate. Do not generate the full PBIP semantic model, source partitions, Power Query M, relationships, or visuals automatically unless the user explicitly approves generated PBIP mode. Power BI validation must detect and record the target Desktop version with `scripts/detect_powerbi_desktop.py` when Desktop validation is expected, run version-aware `scripts/validate_powerbi_pbip.py` when the version is available, and treat incompatible-version errors such as `NewerLinguisticSchemaVersion` as blockers. Power BI measures must come from `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, `kpi_catalog.md`, validated semantic metrics, or explicit user-approved requirements; do not invent Power BI-only key performance indicators or business logic. When internet access is available and PBIP structure is uncertain, check the official Microsoft Learn Power BI project docs before inventing structure. Do not silently adapt a local PBIP such as IHMS; local PBIPs may be used only as user-approved structural references after showing the exact path and what would be reused. The presentation layer must not invent pages, key performance indicators, visuals, or business scope that contradict analytics insight outputs unless the user explicitly overrides them. Power BI delivery is blocked if TMDL contains bare M steps at root, such as `AddedKey = Table.AddColumn(...)`, culture/linguistic schema artifacts that are not exact-version validated, or linguistic metadata content-type mismatches, such as JSON `{ "Version": "1.0.0" }` inside XML-typed metadata. Do not build dashboards, reports, slides, notebooks, or business intelligence artifacts without approval.

The presentation-layer recommendation and user decision gate are mandatory for full pipeline final delivery. If the user has not answered the presentation question, set status to `Analytics insight reporting complete - presentation decision pending`, not `Delivery complete`. If the recommendation cannot be produced, mark it `BLOCKED` or `SKIPPED` with evidence in the final report, pipeline status, context tree, and final response.

## Step 6c - Human review

Read [human-review.md](references/human-review.md). Summarize business assumptions, data quality notes, and open decisions after each layer. Ask for approval when business meaning, grain, mappings, metrics, or sensitive fields are unclear.

This review happens after implementation. The phase plan approval in [phase-plan-approval.md](references/phase-plan-approval.md) happens before implementation.

## Step 7 - Git

Read [git-workflow.md](references/git-workflow.md). Ask before every commit/push.

## Step 8 - Continuous Integration, Continuous Delivery, And Agents Schema *(when requested)*

- [agents-schema-setup.md](references/agents-schema-setup.md)
- [cicd-setup.md](references/cicd-setup.md)

Use Agents Schema after documentation generation or any step that produces `target/manifest.json`. Do not treat it as a replacement for dbt project files while editing; use it as the warehouse-side metadata layer that helps agents answer questions and understand built models.

## Step 9 - Final delivery summary

Read [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md), [phase-completion-report.md](references/phase-completion-report.md), [report-artifact-organization.md](references/report-artifact-organization.md), [reporting-standards.md](references/reporting-standards.md), [context-tree.md](references/context-tree.md), [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md), [independent-verification-governance.md](references/independent-verification-governance.md), and [final-delivery.md](references/final-delivery.md) before marking any full pipeline or requested phase complete.

Run `python <installed-skill-path>/scripts/run_acceptance_gate.py --root <project.root>` and record the result. Generated dbt projects do not need to contain the skill `scripts/` folder for this gate to run; use the scripts from the installed/hydrated skill folder against the project root. When full delivery is requested, also run or delegate a fresh independent verifier per [agents/dbt-verifier-agent.md](agents/dbt-verifier-agent.md) and record `reports/agent/INDEPENDENT_VERIFICATION_REPORT.md`.

## Universal iteration summary rule

After every completed or blocked iteration, print a normal user-facing Markdown summary in the chat pane before ending the turn or asking for approval. This applies to discovery, project setup and configuration, phase plans, sources, bronze/staging, silver/intermediate, gold/marts, semantic layer, project evaluator, documentation, analytics insight reporting, presentation-layer decisions, presentation artifacts, continuous integration, Agents Schema, fixes, validation-only runs, commits, pushes, rollbacks, blocked states, and final delivery.

Use canonical templates under `templates/reports/` for every generated phase report, layer report, SQL proof index, SQL proof file, analytics catalog, presentation report, operations report, and root control file when a matching template exists. The template provides the stable structure; the agent must replace placeholders with phase-specific evidence and keep sections present with `None`, `Not applicable`, `Skipped`, or `Blocked` when needed. Do not hand-invent report structures when a template exists.

Use [phase-completion-report.md](references/phase-completion-report.md) for phase/checkpoint summaries and [final-delivery.md](references/final-delivery.md) for task/final summaries. Do not end any iteration with only a file path, commit hash, clickable approval widget, "done", "see report", native question card, file diff, or hidden report reference. A native/clickable approval question may be used, but only after the normal chat summary has already explained what happened and what the approval would allow and is visibly present directly above the question. If the runtime cannot guarantee that visible ordering, use the text fallback instead of a clickable approval widget.

The chat summary must state:

1. Current checkpoint and status.
2. What was completed, built, changed, or verified.
3. Validation/proof results, including warnings, failures, skipped checks, or blockers.
4. Files changed or reports written.
5. Included scope and not-included/deferred scope.
6. Important notes, assumptions, open decisions, and risks.
7. Mandatory repeated section: **Still blocked — fix these or these KPIs stay missing** plus **Agent recommends (accept or override)** — for every OPEN Attention Board / Gap Register row, state the concrete agent recommendation, why, the KPIs unlocked if accepted, and ask Accept / Override / Defer. Include this even when the same warning was shown at prior checkpoints. If none, write `No open KPI gaps at this checkpoint.`
8. Trusted now vs still-blocked KPI lists (from `KPI_GAP_REGISTER.md` / approved contracts).
9. Recommended next action and exactly what approval would permit — and that next Yes does **not** unlock blocked KPIs unless matching OPEN recommendations are accepted or overridden.

Do not ask open-ended “what should we do?” for modeling or KPI decisions without a recommended default. Read [recommendation-and-review.md](references/recommendation-and-review.md), [kpi-gap-and-stakeholder-warnings.md](references/kpi-gap-and-stakeholder-warnings.md), and [stakeholder-layer-and-presentation-guide.md](references/stakeholder-layer-and-presentation-guide.md) before writing the checkpoint chat summary.

After any requested task, full pipeline, phase, fix, documentation update, presentation artifact, commit, push, or verification run is complete, print a complete summary in the chat pane using [final-delivery.md](references/final-delivery.md).

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

After every completed or blocked checkpoint, read [phase-completion-report.md](references/phase-completion-report.md), [report-artifact-organization.md](references/report-artifact-organization.md), [human-attention-reporting.md](references/human-attention-reporting.md), [recommendation-and-review.md](references/recommendation-and-review.md), [kpi-gap-and-stakeholder-warnings.md](references/kpi-gap-and-stakeholder-warnings.md), [stakeholder-layer-and-presentation-guide.md](references/stakeholder-layer-and-presentation-guide.md), and [next-phase-prompt.md](references/next-phase-prompt.md). Update `reports/agent/HUMAN_ATTENTION_BOARD.md` with only OPEN human decisions, concrete agent recommendations (not ask-only), KPI impact of those decisions, and carry-forward conditions. Update `reports/agent/KPI_GAP_REGISTER.md` with makeable KPIs still blocked by missing data, unclear definitions, privacy, units, mappings, dimensions, or approvals, plus agent recommendation / why / alternative rejected for each OPEN row, plus impossible/out-of-scope KPIs. Write or update `reports/agent/NEXT_PHASE_PROMPT.md` with the exact prompt for the recommended next phase, write or update `reports/agent/REPORT_INDEX.md`, then send a normal assistant message with a visible Markdown chat control-panel summary before asking approval. The chat summary must mirror the Attention Board OPEN rows, include the mandatory **Still blocked** and **Agent recommends (accept or override)** re-warning even when the human has seen it before, explain what was completed, what passed/warned/failed, what is recommended next, what the next phase will and will not include, how to approve, and paste the exact next-phase prompt in chat. Do not paste full inventories or cardinality matrices into chat. Do not only say that the prompt is in `NEXT_PHASE_PROMPT.md`. Do not show only a native question card, approval widget, or file diff; the user-facing summary must appear as a separate assistant message directly above the question so the run does not look stopped or abandoned. Do not put the full summary only inside the `request_user_input` or native question body. Ask through a native interactive question only when the runtime can keep the normal summary visibly present directly above that question. In Codex, use `request_user_input` or the current native question/approval UI only when that visible-summary ordering is guaranteed; keep the tool question short. Recommended question: `Do you want me to run this next-phase prompt as written?` Recommended option: `Yes, run this prompt`. Other options: `Tell me what to change` and `Not now`. If interactive questions are unavailable or the visible summary would not appear directly above the question, use the text fallback: `Do you want me to run this next-phase prompt as written? Reply Yes to proceed, or tell me what to change.`

When the user approves the displayed next-phase prompt, do not run `NEXT_PHASE_PROMPT.md` alone. First reload the approved next-phase context bundle from [next-phase-prompt.md](references/next-phase-prompt.md): `SKILL.md`, `prompt.md`, phase-specific references, `AGENT_PLAN.md`, `reports/agent/PIPELINE_STATUS.md`, `reports/agent/CONTEXT_TREE.md`, `reports/agent/00_discovery/requirements.md` when present, legacy `reports/agent/requirements.md` only when the canonical file is absent, the latest relevant phase report, `reports/agent/NEXT_PHASE_PROMPT.md`, and project knowledge files when present. Then execute only the approved next phase.

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
| [software-prerequisites.md](references/software-prerequisites.md) | Detect/install Python, dbt, adapters, git, Node/npx, gh, and presentation packages |
| [discovery-requirements.md](references/discovery-requirements.md) | Read-only schema/data discovery and requirements checkpoint before build planning |
| [discovery-artifacts.md](references/discovery-artifacts.md) | Mandatory discovery files including core_profile.json and discovery_raw.json |
| [discovery-status-vocabulary.md](references/discovery-status-vocabulary.md) | PASS, WARN, FAIL, BLOCKED, SKIPPED meanings for discovery outputs |
| [table-inclusion-priority-filter.md](references/table-inclusion-priority-filter.md) | How to include, defer, or exclude tables, lock first-pass scope, and keep runs repeatable |
| [project.config.yml](project.config.yml) | Defaults, paths, git, materialization |
| [skill-inputs.md](references/skill-inputs.md) | Required inputs |
| [profile-listing.md](references/profile-listing.md) | Safe available-profile table when `DBT_PROFILE_NAME` is missing or ambiguous |
| [profile-credential-keys.md](references/profile-credential-keys.md) | Map dbt `pass` and alternate `password` keys safely; avoid false missing-credential blockers |
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
| [universal-analytics-framework.md](references/universal-analytics-framework.md) | Business process, measure, metric, dimension, fact, and dashboard coverage framework |
| [mermaid-diagrams.md](references/mermaid-diagrams.md) | Mermaid-only diagrams and visibility verification |
| [evidence-driven-dbt-process.md](references/evidence-driven-dbt-process.md) | Evidence-first build and completion rules |
| [assumption-tests.md](references/assumption-tests.md) | Structural vs assumption dbt tests and promotion workflow |
| [docs/how-to-verify-generated-project.md](docs/how-to-verify-generated-project.md) | Human guide for verifying generated projects |
| [layer-data-validation.md](references/layer-data-validation.md) | Warehouse query checks after every bronze, silver, and gold layer build |
| [cardinality-validation.md](references/cardinality-validation.md) | Grain, relationship cardinality, join safety, row loss, row multiplication, and Power BI relationship readiness |
| [kpi-definitions.md](references/kpi-definitions.md) | Key performance indicator definitions, caveats, and approval status |
| [kpi-definition-contract.md](references/kpi-definition-contract.md) | Key performance indicator contract format |
| [metric-verification.md](references/metric-verification.md) | Cross-layer key performance indicator reconciliation |
| [metric-verification-checklist.md](references/metric-verification-checklist.md) | Metric verification matrix and proof checklist |
| [kpi-reconciliation.md](references/kpi-reconciliation.md) | Source-to-final key performance indicator proof chain, variance report, and proof SQL files |
| [advanced-data-engineering-review.md](references/advanced-data-engineering-review.md) | Required senior data-engineering review before final delivery |
| [project-naming.md](references/project-naming.md) | Derive project and folder names without using dbt profile |
| [env-configuration.md](references/env-configuration.md) | Optional `.env` settings and precedence |
| [source-confirmation.md](references/source-confirmation.md) | Ask-before-switching contract and approved source lock |
| [warehouse-adapter-routing.md](references/warehouse-adapter-routing.md) | Use the selected dbt profile adapter for discovery; do not probe unrelated warehouses |
| [schema-isolation.md](references/schema-isolation.md) | Keep source, medallion, evaluator, seeds, snapshots, and agent metadata schemas separate |
| [subagent-workflow.md](references/subagent-workflow.md) | Optional parallel analysis and review |
| [data-engineering-best-practices.md](references/data-engineering-best-practices.md) | Grain, tests, history, contracts, privacy, operations |
| [principal-data-engineering-standards.md](references/principal-data-engineering-standards.md) | Principal-level dbt, Power BI, storage, warehouse, and SQL standards |
| [privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md) | Safe defaults for sensitive fields and unclear coded fields; user privacy opt-out |
| [reporting-coverage-requirements.md](references/reporting-coverage-requirements.md) | Process-driven coverage, readable presentation, live SQL gates |
| [analytics-product-completeness.md](references/analytics-product-completeness.md) | Analytics product modules, metric families, fact contracts |
| [time-intelligence-standard.md](references/time-intelligence-standard.md) | Period comparisons and KPI card period/target display |
| [report-page-contract.md](references/report-page-contract.md) | Decision-oriented report page contracts |
| [universal-model-classification.md](references/universal-model-classification.md) | Domain-neutral model class register |
| [data-observability-standard.md](references/data-observability-standard.md) | DQ and pipeline-health observability |
| [exposure-coverage.md](references/exposure-coverage.md) | Downstream consumer / exposure coverage |
| [security-and-credentials.md](references/security-and-credentials.md) | Secrets & gitignore |
| [project-initialization.md](references/project-initialization.md) | venv, dbt init, debug, software prerequisite check |
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
| [marts-spec.md](references/marts-spec.md) | Star schema facts, dimensions, bridges |
| [gold-dimension-completeness.md](references/gold-dimension-completeness.md) | Prevent fact-only gold without dim register |
| [documentation.md](references/documentation.md) | Docs generate |
| [analytics-insight-reporting.md](references/analytics-insight-reporting.md) | Business reporting design before presentation |
| [universal-analytics-framework.md](references/universal-analytics-framework.md) | Maximum useful analytics coverage and rich dashboard page framework |
| [kpi-discovery-framework.md](references/kpi-discovery-framework.md) | Domain-neutral key performance indicator discovery, table classification, grain detection, archetypes, and confidence scoring |
| [presentation-layer.md](references/presentation-layer.md) | Optional presentation-layer recommendation after analytics insight reporting |
| [matplotlib-presentation-layer.md](references/matplotlib-presentation-layer.md) | Default Matplotlib refreshable web report workflow |
| [powerbi-template.md](references/powerbi-template.md) | Bundled neutral PBIP template location, generator behavior, fallback rules, and validation language |
| [powerbi-thin-model-template.md](references/powerbi-thin-model-template.md) | Desktop-created PBIP template workflow where the agent injects approved measures without editing physical model connections |
| [powerbi-kpi-dax-tooling.md](references/powerbi-kpi-dax-tooling.md) | Power BI key performance indicator, DAX, optional Model Context Protocol, optional `pbi-cli`, and validation ownership rules |
| [powerbi-official-docs.md](references/powerbi-official-docs.md) | Official Microsoft Power BI PBIP/PBIR/TMDL project documentation links and doc-driven constraints |
| [powerbi-pbip-desktop-requirements.md](references/powerbi-pbip-desktop-requirements.md) | Power BI PBIP/TMDL Desktop layout, metadata, page-content, and validation requirements |
| [human-review.md](references/human-review.md) | Engineer/domain review checkpoints |
| [human-attention-reporting.md](references/human-attention-reporting.md) | One Attention Board for human decisions; reduce report repetition |
| [kpi-gap-and-stakeholder-warnings.md](references/kpi-gap-and-stakeholder-warnings.md) | KPI Gap Register plus mandatory repeated chat warnings for blocked makeable KPIs |
| [stakeholder-layer-and-presentation-guide.md](references/stakeholder-layer-and-presentation-guide.md) | What to explain after each layer and what to show in presentation |
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
| [discovery-approval-checklist.md](references/discovery-approval-checklist.md) | Discovery approval gate before bootstrap/build |
| [requirements-traceability-matrix.md](references/requirements-traceability-matrix.md) | Requirement-to-artifact traceability |
| [layer-verification-ledger.md](references/layer-verification-ledger.md) | Per-model verification ledger |
| [independent-verification-governance.md](references/independent-verification-governance.md) | Builder, verifier, CI, and human approval model |
| [agents/dbt-verifier-agent.md](agents/dbt-verifier-agent.md) | Independent verifier agent instructions |
| [check_requirement_traceability.py](scripts/check_requirement_traceability.py) | Requirement traceability gate |
| [check_layer_proof_coverage.py](scripts/check_layer_proof_coverage.py) | Layer proof coverage gate |
| [verify_metric_reconciliation.py](scripts/verify_metric_reconciliation.py) | Metric and key performance indicator reconciliation gate |
| [dbt-project-layers.md](references/dbt-project-layers.md) | Layer naming |
| [separate-layer-builds.md](references/separate-layer-builds.md) | Build order |
| [prompt.md](prompt.md) | Paste-ready prompt |
