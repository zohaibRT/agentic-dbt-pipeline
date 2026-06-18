---
name: agentic-dbt-pipeline
description: >-
  Automate end-to-end dbt with an AI agent: bootstrap, layered models (staging,
  intermediate, marts), packages (codegen, utils, evaluator, audit_helper),
  semantic layer, docs, per-layer git commits, and GitHub push via gh CLI.
  Use when setting up or extending a dbt analytics project with agentic automation.
---

# dbt Pipeline

Full lifecycle orchestrator for the dbt project.  
**On every prompt:** agent runs [bootstrap.md](references/bootstrap.md) first (install skills, codegen, automation).  
**Default full pipeline:** bootstrap → sources → staging → intermediate → marts → semantic layer → project evaluator → docs → CI/Agents Schema.

Use `workflow_phase:` to run a single phase. Use `auto_bootstrap: false` only for layer-only edits.

**Install (one command):** `npx skills add zohaibRT/agentic-dbt-pipeline` — see [references/install-skill.md](references/install-skill.md).  
Bootstrap auto-installs dbt Agent Skills and dbt packages on first run.

## Bootstrap (mandatory — agent runs automatically)

Read and execute [references/bootstrap.md](references/bootstrap.md) **before** any layer work:

1. **Install dbt Agent Skills** + all dbt packages — see [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md)
2. **`dbt debug`** — verify connection
3. **`dbt deps` + codegen** — when sources/full pipeline
4. **Resolve GitHub repo** — owner from `gh api user`; ask user for `github_repo_name` — [github-repo-resolution.md](references/github-repo-resolution.md)
5. **Create CI + Agents Schema workflows** — when full pipeline or `auto_agents_schema: true`

User one-time manual steps: **profiles.yml password**, **GitHub secret** `WAREHOUSE_CREDENTIALS`, and **repo name** (`github_repo_name`).

If `dbt_profile_name` is provided in the prompt, use it as `{project.profile}` for dbt commands and generated `dbt_project.yml`. If it is missing and multiple profiles exist in `~/.dbt/profiles.yml`, ask the user which profile to use before running dbt commands. Never guess from the first profile.

## dbt packages & agent skills (mandatory stack)

Read [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md).

| Capability | Install / use |
|---|---|
| dbt Agent Skills | **Bootstrap auto-installs** if missing (`auto_install_dbt_skills: true`) |
| codegen | `packages.yml` + `generate_source` |
| dbt_utils | `packages.yml` — macros in models/tests |
| dbt_project_evaluator | `packages.yml` + `dispatch` + `dbt build --select package:dbt_project_evaluator` |
| audit_helper | `packages.yml` — compare queries on refactors |
| MetricFlow / Semantic Layer | [semantic-layer-spec.md](references/semantic-layer-spec.md) + `building-dbt-semantic-layer` |
| Agents Schema | [agents-schema-setup.md](references/agents-schema-setup.md) - publish dbt metadata to `AGENTS.*` for warehouse-side agent context |

Install agent skills: [references/install-dbt-agent-skills.md](references/install-dbt-agent-skills.md)

## Phase map

| Phase | When | Reference |
|---|---|---|
| **Bootstrap** | **Every run** (unless `auto_bootstrap: false`) | [bootstrap.md](references/bootstrap.md) |
| **0 Inputs** | Always first | [skill-inputs.md](references/skill-inputs.md), [security-and-credentials.md](references/security-and-credentials.md), [code-agent-setup.md](references/code-agent-setup.md) |
| **1 Init** | New project | [project-initialization.md](references/project-initialization.md) |
| **2 Schemas** | After init | [warehouse-schema-setup.md](references/warehouse-schema-setup.md) |
| **3 Sources** | Packages + source YAML | [packages-and-sources.md](references/packages-and-sources.md) |
| **4 Layer names** | Before models | [dbt-project-layers.md](references/dbt-project-layers.md) |
| **5 Staging** | Layer 1 | [staging-spec.md](references/staging-spec.md) |
| **6 Intermediate** | Layer 2 | [intermediate-spec.md](references/intermediate-spec.md) |
| **7 Marts** | Layer 3 star schema | [marts-spec.md](references/marts-spec.md), [materialization-rules.md](references/materialization-rules.md) |
| **7b Semantic** | Metrics on marts | [semantic-layer-spec.md](references/semantic-layer-spec.md) |
| **7c Evaluator** | Best-practice audit | [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) |
| **8 Docs** | After layers | [documentation.md](references/documentation.md) |
| **9 Git** | After each stage | [github-repo-resolution.md](references/github-repo-resolution.md), [git-workflow.md](references/git-workflow.md) |
| **10 Agents Schema / CI** | Metadata + automation | [agents-schema-setup.md](references/agents-schema-setup.md), [cicd-setup.md](references/cicd-setup.md) |
| **Done** | Final check | [acceptance-checklist.md](references/acceptance-checklist.md) |

Context prompt template: [agent-context-prompt.md](references/agent-context-prompt.md)

## Step 0 — Load config

Read [project.config.yml](project.config.yml) and [skill-inputs.md](references/skill-inputs.md).

Resolve paths relative to workspace root. dbt project root = `{project.root}`.

**User prompt overrides config** for schema, domain, layers, materialization, commit mode.

## Step 0.1 — Security

Read [security-and-credentials.md](references/security-and-credentials.md).

Never hardcode secrets. Ask before production changes.

## Step 0.5 — Ask user for layer names (required for model phases)

Read [references/dbt-project-layers.md](references/dbt-project-layers.md).

**Always build all model layers** unless `workflow_phase` limits scope.

> What names should I use in `dbt_project.yml`?
> - Layer 1 (`stg_*`) — default: `staging`
> - Layer 2 (`int_*`) — default: `intermediate`
> - Layer 3 (`dim_*`/`fct_*`/`mart_*`) — default: `marts`

Write `dbt_project.yml` per [materialization-rules.md](references/materialization-rules.md):

```yaml
models:
  {project.name}:
    {layer_1_name}:
      +schema: {layer_1_name}
      +materialized: view
    {layer_2_name}:
      +schema: {layer_2_name}
      +materialized: view
    {layer_3_name}:
      +schema: {layer_3_name}
      +materialized: table   # prod; use view for dev profile
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

## Step 1 — Full pipeline order

Read [separate-layer-builds.md](references/separate-layer-builds.md).

**Full pipeline (default):**

1. **Bootstrap** — [bootstrap.md](references/bootstrap.md)
2. Init *(if project missing)*
3. Sources — full `packages.yml`, `dbt deps`, codegen, source YAML
4. Staging → Intermediate → Marts
5. Semantic layer — metrics on marts facts
6. Project evaluator — `dbt build --select package:dbt_project_evaluator`
7. Docs — `dbt docs generate`
8. Agents Schema - publish dbt metadata to `AGENTS.*` after `target/manifest.json` exists
9. Automation - CI workflow
10. **Acceptance** - [acceptance-checklist.md](references/acceptance-checklist.md)

Each stage: **parse → build → summarize → ask commit/push** (repo: `https://github.com/{gh_user}/{github_repo_name}`).

## Step 2 — Sources

Read [packages-and-sources.md](references/packages-and-sources.md) and [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md).

All four packages in `packages.yml`. Codegen for sources. Add the configured `source.schema` to source YAML after generate.

## Step 3 — Layer 1 (staging)

Read [staging-spec.md](references/staging-spec.md). `source()` only. No business KPIs.

## Step 4 — Layer 2 (intermediate)

Read [intermediate-spec.md](references/intermediate-spec.md). `ref()` only.

## Step 5 — Layer 3 (marts / star schema)

Read [marts-spec.md](references/marts-spec.md). `ref()` only. 5 dims + 2 facts + 2 reporting marts.

## Step 5b — Semantic layer

Read [semantic-layer-spec.md](references/semantic-layer-spec.md). Compose with `building-dbt-semantic-layer`. Legacy spec on dbt 1.10.x.

## Step 5c — Project evaluator

```powershell
& $dbt build --select package:dbt_project_evaluator
```

## Step 6 — Documentation

Read [documentation.md](references/documentation.md). Run `dbt docs generate`.

## Step 7 — Git

Read [git-workflow.md](references/git-workflow.md). Ask before every commit/push.

## Step 8 — CI/CD & Agents Schema *(when requested)*

- [agents-schema-setup.md](references/agents-schema-setup.md)
- [cicd-setup.md](references/cicd-setup.md)

Use Agents Schema after docs generation or any step that produces `target/manifest.json`. Do not treat it as a replacement for dbt project files while editing; use it as the warehouse-side metadata layer that helps agents answer questions and understand built models.

## Failure handling

1. Identify failing model/test from build output.
2. Fix **only the current layer** unless upstream is broken.
3. Re-run `dbt build --select +path:<layer_path>`.
4. Use `troubleshooting-dbt-job-errors` for unclear errors.

## Summary template (end of each phase)

```text
1. Files created / updated
2. Grain / business logic
3. Tests / docs added
4. Assumptions used
5. dbt debug / parse / build results
6. Commit status (asked / skipped / done / pushed to github)
```

## Ambiguity — prompt overrides

- `workflow_phase:` init | sources | staging | intermediate | marts | semantic_layer | project_evaluator | docs | ci | agents_schema
- `dbt_profile_name:` dbt profile key from `~/.dbt/profiles.yml`; ask if missing or ambiguous
- `domain:` business/domain folder name; ask if missing
- `source_schema:` warehouse schema to inspect with codegen; ask if missing
- `source_name:` dbt source name to write in source YAML; ask if missing
- `auto_bootstrap:` true *(default)* | false
- `auto_agents_schema:` true *(default on full pipeline)* | false
- `auto_install_dbt_skills:` true *(default)* | false
- `layer_names:` layer_1, layer_2, layer_3
- `domain:` (default from `project.config.yml`)
- `github_repo_name:` repo slug *(ask user; owner from `gh api user`)*
- `github_repo:` full URL or `owner/repo` *(optional override)*
- `push_to_github:` true *(default on full pipeline)* | false
- `commit:` ask | auto_yes | skip_all
- `materialization_profile:` prod | dev
- `regenerate_sources:` true | false

## One-shot prompt

[prompt.md](prompt.md) · [agent-context-prompt.md](references/agent-context-prompt.md)

## Do not use this skill for

- Power BI / dashboard build
- Ad-hoc business questions → `answering-natural-language-questions-with-dbt` *(use that skill directly)*

## Reference files

| File | Purpose |
|---|---|
| [install-skill.md](references/install-skill.md) | Install via npx or `.agents/skills/` |
| [bootstrap.md](references/bootstrap.md) | **Auto-run:** skills install, codegen, CI/Agents workflows |
| [project.config.yml](project.config.yml) | Defaults, paths, git, materialization |
| [skill-inputs.md](references/skill-inputs.md) | Required inputs |
| [security-and-credentials.md](references/security-and-credentials.md) | Secrets & gitignore |
| [project-initialization.md](references/project-initialization.md) | venv, dbt init, debug |
| [warehouse-schema-setup.md](references/warehouse-schema-setup.md) | Postgres schemas |
| [dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | codegen, utils, evaluator, audit_helper, agent skills |
| [semantic-layer-spec.md](references/semantic-layer-spec.md) | MetricFlow / semantic metrics |
| [github-repo-resolution.md](references/github-repo-resolution.md) | `gh` CLI owner + repo name |
| [packages-and-sources.md](references/packages-and-sources.md) | Codegen, source YAML |
| [staging-spec.md](references/staging-spec.md) | Layer 1 |
| [intermediate-spec.md](references/intermediate-spec.md) | Layer 2 |
| [marts-spec.md](references/marts-spec.md) | Star schema |
| [documentation.md](references/documentation.md) | Docs generate |
| [validation-commands.md](references/validation-commands.md) | debug, parse, build, docs |
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
