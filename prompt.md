# dbt Pipeline Prompt

Install once:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Bootstrap installs the required dbt Labs agent skills and dbt packages when they are missing.

Copy the prompt below into Cursor. See also [references/agent-context-prompt.md](references/agent-context-prompt.md).

---

## Full Pipeline

Use this for a new hospital analytics project.

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Goal: Build a hospital dbt project using medallion layers from the available source schemas.

github_repo_name: hospital-analytics

layer_names:
  layer_1: bronze
  layer_2: silver
  layer_3: gold

Task:
1. Set up the dbt project and install any required dbt agent skills or dbt packages.
2. Run the full pipeline: sources -> bronze -> silver -> gold -> semantic layer -> project evaluator -> docs.
3. Use dbt packages and metadata tools at the correct phase:
   - codegen: generate source YAML from hospital source schemas; do not invent columns.
   - dbt_utils: use standard macros/tests while building bronze, silver, and gold models.
   - audit_helper: compare old vs new model outputs during refactors or validation.
   - dbt_project_evaluator: run after gold models to check project quality, tests, docs, and DAG structure.
   - MetricFlow/semantic layer: define metrics on final gold models.
   - Agents Schema: publish target/manifest.json metadata to AGENTS.* after docs/manifest generation.
4. Create the Agents Schema workflow after target/manifest.json exists, then create CI workflow files.
5. Initialize git if needed; commit initialization, sources, bronze, silver, gold, docs, CI, and Agents Schema separately.
6. Ask me only for missing repo name, missing credentials/secrets, and commit or push approval.
```

Defaults:

- Bootstrap is enabled.
- dbt Labs agent skills install automatically when missing.
- The agent asks before commits and pushes.
- Production materialization is used unless changed.
- Agents Schema runs after dbt metadata exists.

---

## Single Phase Examples

Use these when you want to run only one part of the workflow.

**Initialize project only**

```text
workflow_phase: init
```

**Sources only**

```text
workflow_phase: sources
```

**Gold layer only**  
Bronze and silver must already exist.

```text
workflow_phase: marts
```

**Semantic layer only**  
Gold models must already exist.

```text
workflow_phase: semantic_layer
```

**Project evaluator only**

```text
workflow_phase: project_evaluator
```

**Agents Schema only**

```text
workflow_phase: agents_schema
```

After sync, verify the agent can query `AGENTS.ROOT` and `AGENTS.DBT_MODEL`.

---

## Optional Settings

Use these only when you want to override the defaults.

```text
commit: ask
push_to_github: true
materialization_profile: prod
auto_agents_schema: true
```

For faster development:

```text
materialization_profile: dev
```

---

## Build Commands

The agent normally runs these. They are shown here for visibility.

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

## What Users Usually Change

| Usually fixed | User-defined |
|---|---|
| Full phase order and security rules | GitHub repo name |
| dbt packages and validation steps | Layer names |
| Model prefixes such as `stg_`, `int_`, `dim_`, `fct_` | Domain folder |
| GitHub owner from logged-in `gh` account | Development vs production materialization |
| Ask before commit/push | Warehouse credentials and secrets |
