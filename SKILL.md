---
name: agentic-dbt-pipeline
description: >-
  Automate end-to-end dbt with an AI agent: bootstrap, medallion layers
  (bronze/silver/gold by default), packages (codegen, utils, evaluator, audit_helper),
  semantic layer, docs, per-layer git commits, optional GitHub push via gh CLI, and
  user-facing final run summaries.
  Use when setting up or extending a dbt analytics project with agentic automation.
---

# dbt Pipeline

Full lifecycle orchestrator for the dbt project.
**On every prompt:** agent runs [bootstrap.md](references/bootstrap.md) first (install skills, codegen, automation).
**Default full pipeline:** bootstrap -> sources -> bronze -> silver -> gold -> semantic layer -> project evaluator -> docs -> CI, plus Agents Schema when enabled and supported.

Use `workflow_phase:` to run a single phase. Use `auto_bootstrap: false` only for layer-only edits.

**Install (one command):** `npx skills add zohaibRT/agentic-dbt-pipeline` - see [references/install-skill.md](references/install-skill.md).
Bootstrap auto-installs dbt Agent Skills and dbt packages on first run.

## Bootstrap (mandatory - agent runs automatically)

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
| **Bootstrap** | **Every run** (unless `auto_bootstrap: false`) | [bootstrap.md](references/bootstrap.md) |
| **0 Inputs** | Always first | [skill-inputs.md](references/skill-inputs.md), [project-naming.md](references/project-naming.md), [env-configuration.md](references/env-configuration.md), [security-and-credentials.md](references/security-and-credentials.md), [schema-isolation.md](references/schema-isolation.md), [code-agent-setup.md](references/code-agent-setup.md) |
| **0b Subagents** | Optional speed-up | [subagent-workflow.md](references/subagent-workflow.md) |
| **0c Best practices** | Design guardrails | [data-engineering-best-practices.md](references/data-engineering-best-practices.md) |
| **1 Init** | New project | [project-initialization.md](references/project-initialization.md) |
| **2 Schemas** | After init | [warehouse-schema-setup.md](references/warehouse-schema-setup.md), [schema-isolation.md](references/schema-isolation.md) |
| **3 Sources** | Packages + source YAML | [packages-and-sources.md](references/packages-and-sources.md) |
| **3b Source profiling** | Before staging | [source-profiling.md](references/source-profiling.md) |
| **4 Layer names** | Before models | [dbt-project-layers.md](references/dbt-project-layers.md) |
| **5 Staging** | Layer 1 | [staging-spec.md](references/staging-spec.md) |
| **6 Intermediate** | Layer 2 | [intermediate-spec.md](references/intermediate-spec.md), [mapping-seeds.md](references/mapping-seeds.md) |
| **7 Marts** | Layer 3 star schema | [marts-spec.md](references/marts-spec.md), [materialization-rules.md](references/materialization-rules.md) |
| **7b Semantic** | Metrics on marts | [semantic-layer-spec.md](references/semantic-layer-spec.md) |
| **7c Evaluator** | Best-practice audit | [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) |
| **8 Docs** | After layers | [documentation.md](references/documentation.md) |
| **9 Git** | After each stage | [github-repo-resolution.md](references/github-repo-resolution.md), [git-workflow.md](references/git-workflow.md) |
| **10 Agents Schema / CI** | Metadata + automation | [agents-schema-setup.md](references/agents-schema-setup.md), [cicd-setup.md](references/cicd-setup.md) |
| **Review** | Human approval points | [human-review.md](references/human-review.md) |
| **Done** | Final check + user summary | [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md) |

Context prompt template: [agent-context-prompt.md](references/agent-context-prompt.md)

## Step 0 - Load config

Read [project.config.yml](project.config.yml), [skill-inputs.md](references/skill-inputs.md), [project-naming.md](references/project-naming.md), [schema-isolation.md](references/schema-isolation.md), and [env-configuration.md](references/env-configuration.md).

Resolve paths relative to workspace root. dbt project root = `{project.root}`.

**User prompt overrides `.env` and config** for schema, domain, layers, materialization, commit mode. Use `.env` for non-secret reusable inputs before asking the user.

For normal runs, collect only the values the agent cannot infer safely: `domain`, `dbt_profile_name`, and `source_schema`. Derive project name/root, dbt source name, schema prefix, layer names, commit behavior, and GitHub mode unless the user explicitly overrides them.

Resolve `project.name` and `project.root` before `dbt init`. Never use `dbt_profile_name` as the folder/project name unless the user explicitly provides it as `dbt_project_name`. Prefer a clean name derived from `source_schema` or `domain`; use `github_repo_name` only when the user provided it for push.

Keep the source schema read-only. Never build dbt models, package models, evaluator tables, seeds, snapshots, or audit outputs into `source_schema`. Route evaluator outputs to `<layer_schema_prefix>_evaluator` and layer outputs to separate medallion schemas. Resolve `layer_schema_prefix` with [schema-isolation.md](references/schema-isolation.md); do not use short source names like `dh` as physical schema prefixes unless the user explicitly sets them.

## Step 0b - Optional subagents

Read [subagent-workflow.md](references/subagent-workflow.md) when source profiling, mapping review, model planning, docs, or evaluator review can safely run in parallel. The main agent decides when to delegate and keeps dbt commands, shared file edits, commits, pushes, and final decisions.

## Step 0.1 - Security

Read [security-and-credentials.md](references/security-and-credentials.md).

Never hardcode secrets. Ask before production changes.

## Step 0.2 - Data engineering guardrails

Read [data-engineering-best-practices.md](references/data-engineering-best-practices.md) before model design and again before final delivery. Apply grain, test, incremental, snapshot, documentation, privacy, and performance guardrails.

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

1. **Bootstrap** - [bootstrap.md](references/bootstrap.md)
2. Init *(if project missing)*
3. Sources - full `packages.yml`, `dbt deps`, codegen, source YAML
4. Staging -> Intermediate -> Marts
5. Semantic layer - metrics on marts facts
6. Project evaluator - `dbt build --select package:dbt_project_evaluator` after confirming it is routed to `<layer_schema_prefix>_evaluator`
7. Docs - `dbt docs generate`; use `dbt docs serve` for local viewing when requested or appropriate for an interactive local run
8. Agents Schema - publish dbt metadata to `AGENTS.*` after `target/manifest.json` exists when enabled and supported
9. Automation - CI workflow
10. **Acceptance + final summary** - [acceptance-checklist.md](references/acceptance-checklist.md), [final-delivery.md](references/final-delivery.md)

Each stage: **parse -> build -> summarize -> ask commit**. Ask for push only when a non-local GitHub repo is configured or the user requested push.

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

Before running evaluator, confirm `dbt_project.yml` routes `models: dbt_project_evaluator: +schema` to `<layer_schema_prefix>_evaluator`. Do not let evaluator package tables build in `source_schema`.

```powershell
& $dbt build --select package:dbt_project_evaluator
```

## Step 6 - Documentation

Read [documentation.md](references/documentation.md). Run `dbt docs generate`. Use `dbt docs serve` only as a non-blocking local viewing step and report the URL when started.

## Step 6b - Human review

Read [human-review.md](references/human-review.md). Summarize business assumptions, data quality notes, and open decisions after each layer. Ask for approval when business meaning, grain, mappings, metrics, or sensitive fields are unclear.

## Step 7 - Git

Read [git-workflow.md](references/git-workflow.md). Ask before every commit/push.

## Step 8 - CI/CD & Agents Schema *(when requested)*

- [agents-schema-setup.md](references/agents-schema-setup.md)
- [cicd-setup.md](references/cicd-setup.md)

Use Agents Schema after docs generation or any step that produces `target/manifest.json`. Do not treat it as a replacement for dbt project files while editing; use it as the warehouse-side metadata layer that helps agents answer questions and understand built models.

## Step 9 - Final delivery summary

Read [final-delivery.md](references/final-delivery.md) before marking any full pipeline or requested phase complete.

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
1. Files created / updated
2. Grain / business logic
3. Tests / docs added
4. Assumptions used
5. dbt debug / parse / build results
6. Commit status (asked / skipped / done / pushed to github)
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
| [bootstrap.md](references/bootstrap.md) | **Auto-run:** skills install, codegen, CI/Agents workflows |
| [project.config.yml](project.config.yml) | Defaults, paths, git, materialization |
| [skill-inputs.md](references/skill-inputs.md) | Required inputs |
| [project-naming.md](references/project-naming.md) | Derive project and folder names without using dbt profile |
| [env-configuration.md](references/env-configuration.md) | Optional `.env` settings and precedence |
| [schema-isolation.md](references/schema-isolation.md) | Keep source, medallion, evaluator, seeds, snapshots, and agent metadata schemas separate |
| [subagent-workflow.md](references/subagent-workflow.md) | Optional parallel analysis and review |
| [data-engineering-best-practices.md](references/data-engineering-best-practices.md) | Grain, tests, history, contracts, privacy, operations |
| [security-and-credentials.md](references/security-and-credentials.md) | Secrets & gitignore |
| [project-initialization.md](references/project-initialization.md) | venv, dbt init, debug |
| [warehouse-schema-setup.md](references/warehouse-schema-setup.md) | Postgres schemas |
| [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | codegen, utils, evaluator, audit_helper, agent skills |
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
