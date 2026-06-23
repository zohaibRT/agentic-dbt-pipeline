---
name: agentic-dbt-pipeline
description: >-
  Automate end-to-end dbt with an AI agent: bootstrap, medallion layers
  (bronze/silver/gold by default), packages (codegen, utils, evaluator, audit_helper),
  semantic layer, docs, per-layer git commits, optional GitHub push via gh CLI, and
  user-facing final run summaries with senior data-engineering decision gates.
  Use when setting up or extending a dbt analytics project with agentic automation.
---

# dbt Pipeline

Full lifecycle orchestrator for the dbt project.
**On every new/full-pipeline prompt:** agent runs read-only [discovery-requirements.md](references/discovery-requirements.md) first, explains what it concluded from the source data, and asks for requirements before any build plan.
**Default full pipeline:** discovery -> bootstrap -> sources -> bronze -> silver -> gold -> semantic layer -> project evaluator -> docs -> CI, plus Agents Schema when enabled and supported.

Use `workflow_phase:` to run a single phase. Use `auto_bootstrap: false` only for layer-only edits.

**Install (one command):** `npx skills add zohaibRT/agentic-dbt-pipeline` - see [references/install-skill.md](references/install-skill.md).
Bootstrap auto-installs dbt Agent Skills and dbt packages on first run.

## Discovery first, then bootstrap

Read and execute [references/discovery-requirements.md](references/discovery-requirements.md) before bootstrap/init on new projects or full pipeline runs.

Discovery is read-only and project-oriented. It may inspect schemas, tables, columns, row counts, keys, relationships, dates, measures, and statuses. Its input/report/output must focus on the source data and analytics project, not environment setup. It must write `reports/agent/discovery_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` before the chat summary, even when the dbt project has not been initialized yet. It must not install packages, run codegen, create warehouse schemas, or change profiles.

After discovery, summarize what the agent concluded from the source data and ask whether the user wants to add requirements such as mappings, metrics, privacy rules, naming rules, included/excluded tables, or priority facts/dimensions. Continue to Bootstrap & Init only after the user replies with requirements or says to continue.

## Bootstrap (build phase - after discovery approval)

Read and execute [references/bootstrap.md](references/bootstrap.md) **before** any layer work:

1. **Install dbt Agent Skills** + all dbt packages - see [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md)
2. **`dbt debug`** - verify connection
3. **`dbt deps` + codegen** - when sources/full pipeline
4. **Resolve git mode** - local commits by default; GitHub only when push is requested - [github-repo-resolution.md](references/github-repo-resolution.md)
5. **Create CI + Agents Schema workflows** - when requested, or when `auto_agents_schema: true` and the destination is supported

User one-time manual steps: **profiles.yml password**, plus **GitHub repo/secret** only when remote push, CI, or Agents Schema sync is requested.

If `dbt_profile_name` is provided in the prompt, use it as `{project.profile}` for dbt commands and generated `dbt_project.yml`. If it is missing and multiple profiles exist in `~/.dbt/profiles.yml`, ask the user which profile to use before running dbt commands. Never guess from the first profile.

## dbt packages & agent skills (mandatory stack)

Read [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md).

| Capability | Install / use |
|---|---|
| dbt Agent Skills | **Bootstrap auto-installs** if missing (`auto_install_dbt_skills: true`) |
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
| **Bootstrap** | First build phase after discovery | [bootstrap.md](references/bootstrap.md) |
| **0 Inputs** | Always first | [skill-inputs.md](references/skill-inputs.md), [project-naming.md](references/project-naming.md), [env-configuration.md](references/env-configuration.md), [security-and-credentials.md](references/security-and-credentials.md), [schema-isolation.md](references/schema-isolation.md), [code-agent-setup.md](references/code-agent-setup.md) |
| **0b Subagents** | Optional speed-up | [subagent-workflow.md](references/subagent-workflow.md) |
| **0c Best practices** | Design guardrails | [data-engineering-best-practices.md](references/data-engineering-best-practices.md) |
| **0d Engineer gate** | Explicit modeling decisions | [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) |
| **0e Phased discovery** | Discover just enough per phase | [phased-discovery.md](references/phased-discovery.md) |
| **0f Recommendations** | Agent recommends; data engineer approves | [recommendation-and-review.md](references/recommendation-and-review.md) |
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
| **9 Git** | After each stage | [github-repo-resolution.md](references/github-repo-resolution.md), [git-workflow.md](references/git-workflow.md) |
| **10 Agents Schema / CI** | Metadata + automation | [agents-schema-setup.md](references/agents-schema-setup.md), [cicd-setup.md](references/cicd-setup.md) |
| **Plan approval** | Before each build phase | [phase-plan-approval.md](references/phase-plan-approval.md) |
| **Review** | Human approval points | [human-review.md](references/human-review.md) |
| **Phase report** | After each completed phase | [phase-completion-report.md](references/phase-completion-report.md) |
| **Context tree** | Ongoing project memory | [context-tree.md](references/context-tree.md) |
| **Done** | Final check + user summary | [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md) |

Context prompt template: [agent-context-prompt.md](references/agent-context-prompt.md)

## Step 0 - Load config

Read [project.config.yml](project.config.yml), [skill-inputs.md](references/skill-inputs.md), [project-naming.md](references/project-naming.md), [schema-isolation.md](references/schema-isolation.md), [env-configuration.md](references/env-configuration.md), [discovery-requirements.md](references/discovery-requirements.md), [phased-discovery.md](references/phased-discovery.md), [recommendation-and-review.md](references/recommendation-and-review.md), [phase-plan-approval.md](references/phase-plan-approval.md), [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md), [phase-completion-report.md](references/phase-completion-report.md), and [context-tree.md](references/context-tree.md).

Resolve paths relative to workspace root. dbt project root = `{project.root}`.

**User prompt overrides `.env` and config** for schema, domain, layers, materialization, commit mode. Use `.env` for non-secret reusable inputs before asking the user. If `.env` is missing in a fresh clone, follow [env-configuration.md](references/env-configuration.md): create a safe local `.env` from `.env.example`, stop before discovery or dbt commands, and ask the user for `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA`. Do not search the repo, inspect terminal output, infer, suggest, or summarize values from other workspaces or previous runs.

For normal runs, collect only the values the agent cannot infer safely: `domain`, `dbt_profile_name`, and `source_schema`. Derive project name/root, dbt source name, schema prefix, layer names, commit behavior, and GitHub mode unless the user explicitly overrides them.

Resolve `project.name` and `project.root` before `dbt init`. Never use `dbt_profile_name` as the folder/project name unless the user explicitly provides it as `dbt_project_name`. Prefer a clean name derived from `source_schema` or `domain`; use `github_repo_name` only when the user provided it for push.

Keep the source schema read-only. Never build dbt models, package models, evaluator tables, seeds, snapshots, or audit outputs into `source_schema`. Route evaluator outputs to `<layer_schema_prefix>_evaluator` and layer outputs to separate medallion schemas. Resolve `layer_schema_prefix` with [schema-isolation.md](references/schema-isolation.md); do not use short source names like `dh` as physical schema prefixes unless the user explicitly sets them.

Before each phase that changes files or builds warehouse objects, write/update `{project.root}/AGENT_PLAN.md`, explain the planned work in Markdown, and wait for approval for that phase. Read-only discovery is allowed before approval when needed for an accurate plan.

## Step 0b - Optional subagents

Read [subagent-workflow.md](references/subagent-workflow.md) when source profiling, mapping review, model planning, docs, or evaluator review can safely run in parallel. The main agent decides when to delegate and keeps dbt commands, shared file edits, commits, pushes, and final decisions.

## Step 0.1 - Security

Read [security-and-credentials.md](references/security-and-credentials.md).

Never hardcode secrets. Ask before production changes.

## Step 0.2 - Data engineering guardrails

Read [data-engineering-best-practices.md](references/data-engineering-best-practices.md) before model design and again before final delivery. Apply grain, test, incremental, snapshot, documentation, privacy, and performance guardrails.

Read [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) before writing each phase plan. The phase plan must show the agent's data-engineering decisions, evidence, and approval needs; do not hide grain, key, join, mapping, privacy, metric, materialization, or validation choices inside code.

Read [phased-discovery.md](references/phased-discovery.md) before each phase. Discover only what is needed for the next layer or workflow step; do not fully design silver/gold/semantic outputs during initial discovery or bronze work.

Read [recommendation-and-review.md](references/recommendation-and-review.md) before writing discovery summaries, phase plans, phase reports, and final handoffs. The agent must recommend the best path with evidence, show what looks right and what is not ready, and ask the data engineer only for business-impacting approvals. Do not make the user design everything from scratch.

## Step 0.5 - Resolve layer names

Read [references/dbt-project-layers.md](references/dbt-project-layers.md).

**Always build all model layers** unless `workflow_phase` limits scope.

Use `layer_names` from the prompt, `.env`, or `project.config.yml` when provided. Otherwise use:

- Layer 1 (`stg_*`): `bronze`
- Layer 2 (`int_*`): `silver`
- Layer 3 (`dim_*`/`fct_*`/`mart_*`): `gold`

Do not ask for layer names unless the user requests a non-default naming convention or an existing project already uses different folders. Resolve `layer_schema_prefix` from explicit config, existing medallion schemas, domain, source schema, or descriptive source name. Ask only when existing schemas create a real conflict that the agent cannot resolve safely.

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

## Step 1 - Full pipeline order

Read [separate-layer-builds.md](references/separate-layer-builds.md).

**Full pipeline (default):**

1. **Discovery & requirements** - [discovery-requirements.md](references/discovery-requirements.md)
2. **Bootstrap** - [bootstrap.md](references/bootstrap.md)
3. Init *(if project missing)*
4. Sources - full `packages.yml`, `dbt deps`, codegen, source YAML
5. Staging -> Intermediate -> Marts
6. Semantic layer - metrics on marts facts
7. Project evaluator - `dbt build --select package:dbt_project_evaluator` after confirming it is routed to `<layer_schema_prefix>_evaluator`
8. Docs - `dbt docs generate`; use `dbt docs serve` for local viewing when requested or appropriate for an interactive local run
9. Agents Schema - publish dbt metadata to `AGENTS.*` after `target/manifest.json` exists when enabled and supported
10. Automation - CI workflow
11. **Acceptance + final summary** - [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md)

Each stage: **phase-specific discovery -> agent recommendation -> data engineer decision check -> write Markdown plan -> ask approval -> implement -> parse/build -> write phase report -> update context tree -> summarize -> ask commit**. Ask for push only when a non-local GitHub repo is configured or the user requested push.

## Step 2 - Sources

Read [packages-and-sources.md](references/packages-and-sources.md), [source-profiling.md](references/source-profiling.md), [schema-isolation.md](references/schema-isolation.md), and [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md).

All four packages in `packages.yml`. Codegen for sources. Derive `source.name` from `source.schema` / `domain` unless explicitly provided. Add the configured `source.schema` to source YAML after generate. Profile row counts, candidate keys, relationships, important dates, measures, and status/code fields before staging.

## Step 3 - Layer 1 (staging)

Read [staging-spec.md](references/staging-spec.md). `source()` only. No business KPIs.

## Step 4 - Layer 2 (intermediate)

Read [intermediate-spec.md](references/intermediate-spec.md) and [mapping-seeds.md](references/mapping-seeds.md). `ref()` only. Use mapping seeds or reference tables when `project_rules` include manual mappings or code translations.

## Step 5 - Layer 3 (marts / star schema)

Read [marts-spec.md](references/marts-spec.md). `ref()` only. Build domain-appropriate facts, dimensions, and reporting marts based on profiled source grain and user requirements.

## Step 5b - Semantic layer

Read [semantic-layer-spec.md](references/semantic-layer-spec.md). Compose with `building-dbt-semantic-layer`. Legacy spec on dbt 1.10.x.

## Step 5c - Project evaluator

Read [project-evaluator.md](references/project-evaluator.md). Before running evaluator, confirm `dbt_project.yml` routes `models: dbt_project_evaluator: +schema` to `<layer_schema_prefix>_evaluator` and sets evaluator vars for the active medallion folder names. Do not let evaluator package tables build in `source_schema`.

```powershell
& $dbt build --select package:dbt_project_evaluator
```

## Step 6 - Documentation

Read [documentation.md](references/documentation.md). Run `dbt docs generate`. Use `dbt docs serve` only as a non-blocking local viewing step and report the URL when started.

## Step 6b - Human review

Read [human-review.md](references/human-review.md). Summarize business assumptions, data quality notes, and open decisions after each layer. Ask for approval when business meaning, grain, mappings, metrics, or sensitive fields are unclear.

This review happens after implementation. The phase plan approval in [phase-plan-approval.md](references/phase-plan-approval.md) happens before implementation.

## Step 7 - Git

Read [git-workflow.md](references/git-workflow.md). Ask before every commit/push.

## Step 8 - CI/CD & Agents Schema *(when requested)*

- [agents-schema-setup.md](references/agents-schema-setup.md)
- [cicd-setup.md](references/cicd-setup.md)

Use Agents Schema after docs generation or any step that produces `target/manifest.json`. Do not treat it as a replacement for dbt project files while editing; use it as the warehouse-side metadata layer that helps agents answer questions and understand built models.

## Step 9 - Final delivery summary

Read [phase-completion-report.md](references/phase-completion-report.md), [context-tree.md](references/context-tree.md), and [final-delivery.md](references/final-delivery.md) before marking any full pipeline or requested phase complete.

Always finish with a user-facing summary that starts short, then gives the useful details:

1. Short summary: what was built and whether it passed.
2. Results: profile, domain, source, schemas, layers, row counts when known.
3. Models created or changed by layer.
4. Validation: dbt debug/parse/build/docs/evaluator results.
5. Data quality notes and assumptions.
6. Git, CI, and Agents Schema status.
7. Open decisions and recommended next actions.

Keep the first section concise enough for a new user to understand in under one minute.

## Failure handling

Read [stuck-recovery.md](references/stuck-recovery.md) whenever a command hangs, validation fails repeatedly, required input is missing, or the agent cannot decide safely.

1. Identify failing model/test from build output.
2. Fix **only the current layer** unless upstream is broken.
3. Re-run `dbt build --select +path:<layer_path>`.
4. Use `troubleshooting-dbt-job-errors` for unclear errors.
5. If still blocked, stop and ask with the current phase, last command, error, changed files, `git status`, and concrete options.

## Summary template (end of each phase)

```text
1. Plan approval status
2. Files created / updated
3. Grain / business logic
4. Data-engineering decisions and evidence
5. Agent recommendation, what looks right, and what is not ready
6. Tests / docs added
7. Assumptions used
8. dbt debug / parse / build results
9. Phase report path and status
10. Context tree update status
11. Commit status (asked / skipped / done / pushed to github)
```

For the final response, use [final-delivery.md](references/final-delivery.md) instead of only the phase template.

## Ambiguity - prompt overrides

- `workflow_phase:` init | sources | staging | intermediate | marts | semantic_layer | project_evaluator | docs | ci | agents_schema
- `dbt_profile_name:` dbt profile key from `~/.dbt/profiles.yml`; ask if missing or ambiguous
- `dbt_project_name:` optional explicit dbt project name; otherwise derive from source/domain
- `dbt_project_root:` optional explicit folder name; otherwise use `dbt_project_name`
- `domain:` business/domain folder name; ask if missing
- `source_schema:` warehouse schema to inspect with codegen; ask if missing
- `source_name:` optional dbt source name override; derive from `source_schema` / `domain` when missing
- `layer_schema_prefix:` prefix for physical output schemas; derive by [schema-isolation.md](references/schema-isolation.md) unless explicitly provided
- `project_rules:` optional field mappings, joins, metrics, exclusions, privacy rules, naming rules, and special instructions. Apply exactly; ask if unclear.
- `auto_bootstrap:` true *(default)* | false
- `auto_agents_schema:` true | false *(default false for local/unsupported adapters; enable for Snowflake, Databricks, or BigQuery)*
- `auto_install_dbt_skills:` true *(default)* | false
- `layer_names:` layer_1, layer_2, layer_3 *(default: bronze, silver, gold)*
- `domain:` (default from `project.config.yml`)
- `github_repo_name:` optional repo slug; ask only when push is requested and no repo can be inferred
- `github_repo:` full URL or `owner/repo` *(optional override)*
- `push_to_github:` true | false *(default: false for `local-only`, otherwise ask before pushing)*
- `commit:` ask | auto_yes | skip_all
- `materialization_profile:` prod | dev
- `regenerate_sources:` true | false

## One-shot prompt

[prompt.md](prompt.md) - [agent-context-prompt.md](references/agent-context-prompt.md)

## Do not use this skill for

- Power BI / dashboard build
- Ad-hoc business questions -> `answering-natural-language-questions-with-dbt` *(use that skill directly)*

## Reference files

| File | Purpose |
|---|---|
| [install-skill.md](references/install-skill.md) | Install via npx or `.agents/skills/` |
| [bootstrap.md](references/bootstrap.md) | First approved build phase: skills install, packages, debug, CI/Agents workflows |
| [discovery-requirements.md](references/discovery-requirements.md) | Read-only schema/data discovery and requirements checkpoint before build planning |
| [project.config.yml](project.config.yml) | Defaults, paths, git, materialization |
| [skill-inputs.md](references/skill-inputs.md) | Required inputs |
| [phase-plan-approval.md](references/phase-plan-approval.md) | Markdown plan and approval gate before every phase |
| [phase-completion-report.md](references/phase-completion-report.md) | Per-phase report files showing done/correct/wrong/open items |
| [context-tree.md](references/context-tree.md) | Curated project memory: inputs, outputs, decisions, reports, and open items |
| [data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) | Senior data-engineering decisions that must be explicit before build |
| [phased-discovery.md](references/phased-discovery.md) | Layer-by-layer discovery that keeps the data engineer in control |
| [recommendation-and-review.md](references/recommendation-and-review.md) | Agent recommendations, risks, and approval boundaries |
| [project-naming.md](references/project-naming.md) | Derive project and folder names without using dbt profile |
| [env-configuration.md](references/env-configuration.md) | Optional `.env` settings and precedence |
| [schema-isolation.md](references/schema-isolation.md) | Keep source, medallion, evaluator, seeds, snapshots, and agent metadata schemas separate |
| [subagent-workflow.md](references/subagent-workflow.md) | Optional parallel analysis and review |
| [data-engineering-best-practices.md](references/data-engineering-best-practices.md) | Grain, tests, history, contracts, privacy, operations |
| [security-and-credentials.md](references/security-and-credentials.md) | Secrets & gitignore |
| [project-initialization.md](references/project-initialization.md) | venv, dbt init, debug |
| [warehouse-schema-setup.md](references/warehouse-schema-setup.md) | Postgres schemas |
| [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | codegen, utils, evaluator, audit_helper, agent skills |
| [project-evaluator.md](references/project-evaluator.md) | Align dbt_project_evaluator with bronze/silver/gold and accepted warnings |
| [semantic-layer-spec.md](references/semantic-layer-spec.md) | MetricFlow / semantic metrics |
| [github-repo-resolution.md](references/github-repo-resolution.md) | `gh` CLI owner + repo name |
| [packages-and-sources.md](references/packages-and-sources.md) | Codegen, source YAML |
| [source-profiling.md](references/source-profiling.md) | Row counts, keys, dates, status/code values |
| [staging-spec.md](references/staging-spec.md) | Layer 1 |
| [intermediate-spec.md](references/intermediate-spec.md) | Layer 2 |
| [mapping-seeds.md](references/mapping-seeds.md) | Manual mapping seeds and coverage tests |
| [marts-spec.md](references/marts-spec.md) | Star schema |
| [documentation.md](references/documentation.md) | Docs generate |
| [human-review.md](references/human-review.md) | Engineer/domain review checkpoints |
| [final-delivery.md](references/final-delivery.md) | Final handoff checklist |
| [validation-commands.md](references/validation-commands.md) | debug, parse, build, docs |
| [stuck-recovery.md](references/stuck-recovery.md) | Stuck command and blocker recovery |
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
