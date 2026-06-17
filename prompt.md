# Prompt — Agentic dbt Pipeline

**Install once:** `npx skills add zohaibRT/agentic-dbt-pipeline`  
Bootstrap auto-installs dbt Agent Skills + packages on first run.

Copy into Cursor. See also [references/agent-context-prompt.md](references/agent-context-prompt.md).

---

## Full pipeline (default — agent does everything)

```text
Use the agentic-dbt-pipeline skill.

auto_bootstrap: true
auto_install_dbt_skills: true
auto_agents_schema: true
commit: ask
push_to_github: true
materialization_profile: prod

# Ask me for repo name only — owner from GitHub CLI logged-in account (gh api user)
github_repo_name: analytics

layer_names:
  layer_1: staging
  layer_2: intermediate
  layer_3: marts

## Task

1. Run bootstrap.md (dbt Agent Skills, all packages, dbt debug, codegen/deps).
2. Run full pipeline: sources → staging → intermediate → marts → semantic layer → project evaluator → docs.
3. Utilize: codegen, dbt_utils, audit_helper, MetricFlow/semantic layer, dbt_project_evaluator.
4. Create CI + Agents Schema GitHub workflow files.
5. Initialize git if needed; commit per layer; push to https://github.com/{gh_user}/{github_repo_name} on approval.
6. Ask me only for: github_repo_name (if not set), WAREHOUSE_CREDENTIALS (if not set), and commit/push approval.
```

---

## Single phase examples

**Initialize project only**
```text
workflow_phase: init
commit: ask
```

**Sources only**
```text
workflow_phase: sources
commit: ask
```

**Marts only** *(staging + intermediate must exist)*
```text
workflow_phase: marts
materialization_profile: prod
commit: ask
```

**Semantic layer only** *(marts must exist)*
```text
workflow_phase: semantic_layer
commit: ask
```

**Project evaluator only**
```text
workflow_phase: project_evaluator
commit: ask
```

**Agents Schema**
```text
workflow_phase: agents_schema
commit: ask
```

---

## Materialization profiles

**Production (default)**
```yaml
# dbt_project.yml
marts:
  +schema: marts
  +materialized: table
# fct_*.sql: {{ config(materialized='incremental', unique_key='order_id') }}
```

**Development (fast iteration)**
```text
materialization_profile: dev
# all layers +materialized: view
```

---

## Build commands

```powershell
$dbt = "dbt"
& $dbt debug
& $dbt deps
& $dbt parse --no-partial-parse
& $dbt build --select +path:models/<layer_1_name>/<domain>
& $dbt build --select +path:models/<layer_2_name>/<domain>
& $dbt build --select +path:models/<layer_3_name>/<domain>
& $dbt build --select package:dbt_project_evaluator
& $dbt docs generate
```

---

## What stays fixed vs user-defined

| Fixed | User-defined |
|---|---|
| Full phase order & security rules | Layer folder names in dbt_project.yml |
| Model prefixes stg_/int_/dim_/fct_/mart_ | +schema suffixes |
| All standard dbt packages (see dbt-packages-and-skills.md) | `github_repo_name` (repo slug) |
| GitHub owner from `gh` logged-in account | domain folder |
| Ask before commit/push (default) | materialization_profile prod/dev |
