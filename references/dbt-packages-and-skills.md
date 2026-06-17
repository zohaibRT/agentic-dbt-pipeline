# dbt Packages & Agent Skills Stack

The pipeline uses **six dbt capabilities** together. Agent installs and runs them during bootstrap and the full pipeline.

| # | Capability | Type | Purpose in pipeline |
|---|---|---|---|
| 1 | **dbt Agent Skills** | Cursor/agent skills | Orchestration, CLI, troubleshooting, semantic layer authoring |
| 2 | **dbt-codegen** | dbt package | `generate_source` for source YAML bootstrap |
| 3 | **dbt-utils** | dbt package | `star()`, `surrogate_key`, generic tests, cross-db macros |
| 4 | **dbt-project-evaluator** | dbt package | Best-practice checks on DAG, tests, docs, structure |
| 5 | **audit_helper** | dbt package | Row-level audits when validating refactors or prod comparisons |
| 6 | **MetricFlow / Semantic Layer** | dbt YAML + skill | Business metrics on marts (`semantic_models`, `metrics`) |

---

## 1. dbt Agent Skills (bootstrap)

Install when `auto_install_dbt_skills: true` — see [install-dbt-agent-skills.md](install-dbt-agent-skills.md).

**Always compose:**

| Skill | When |
|---|---|
| `agentic-dbt-pipeline` | Full pipeline orchestration, git, GitHub push |
| `using-dbt-for-analytics-engineering` | Models, tests, docs |
| `running-dbt-commands` | CLI formatting |
| `building-dbt-semantic-layer` | After marts — semantic models & metrics |
| `troubleshooting-dbt-job-errors` | On job/CI failures |
| `adding-dbt-unit-test` | When adding unit tests |
| `answering-natural-language-questions-with-dbt` | Ad-hoc metric questions *(optional)* |

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt
```

---

## 2–5. `packages.yml` (all dbt packages)

Declare **all** standard packages in `{project.root}/packages.yml`:

```yaml
packages:
  - package: dbt-labs/codegen
    version: 0.14.1
  - package: dbt-labs/dbt_utils
    version: 1.3.3
  - package: dbt-labs/dbt_project_evaluator
    version: 1.3.0
  - package: dbt-labs/audit_helper
    version: 0.14.0
```

```powershell
dbt deps
```

### codegen — source bootstrap

```powershell
$dbt = "$env:APPDATA\Python\Python312\Scripts\dbt.exe"
& $dbt --quiet run-operation generate_source `
  --args '{"schema_name": "ecommerce", "generate_columns": true}' `
  > models\sources\ecommerce_sources_generated.yml
```

See [packages-and-sources.md](packages-and-sources.md) for post-codegen rules.

### dbt_utils — in models and tests

Use where helpful (not required on every model):

- `{{ dbt_utils.star(from=ref('stg_ecommerce__orders'), except=['_loaded_at']) }}`
- `dbt_utils.expression_is_true`, `dbt_utils.unique_combination_of_columns`
- `dbt_utils.generate_surrogate_key` in dims when needed

### dbt_project_evaluator — after layers built

Add to `dbt_project.yml`:

```yaml
dispatch:
  - macro_namespace: dbt
    search_order: ['dbt_project_evaluator', 'dbt']
```

Run after marts build passes:

```powershell
& $dbt build --select package:dbt_project_evaluator
```

Review `dbt_project_evaluator` results; fix critical issues or document accepted exceptions.

### audit_helper — validation & refactors

Use macros (in analyses or one-off ops) when comparing model versions:

```sql
{% set old_relation = ref('fct_orders') %}
{% set new_relation = ref('fct_orders') %}
{{ audit_helper.compare_queries(
    a_query="select * from " ~ old_relation,
    b_query="select * from " ~ new_relation,
    primary_key="order_id"
) }}
```

Run during acceptance or after large refactors — not on every layer commit.

---

## 6. MetricFlow / Semantic Layer

**Phase:** after marts, before docs (or extend docs phase).

Read [semantic-layer-spec.md](semantic-layer-spec.md) and compose with `building-dbt-semantic-layer`.

On dbt Core **1.10.x** → use **legacy spec** (`semantic_models:` top-level YAML).

Validate:

```powershell
& $dbt parse --no-partial-parse
# dbt Cloud Semantic Layer: dbt sl validate  (if configured)
```

---

## Bootstrap package checklist

| Step | Command / action |
|---|---|
| Write `packages.yml` | All 4 packages listed above |
| Install | `dbt deps` |
| Codegen sources | `generate_source` run-operation |
| Configure evaluator | `dispatch` block in `dbt_project.yml` |
| After marts | `dbt build --select package:dbt_project_evaluator` |
| After marts | Add semantic models per [semantic-layer-spec.md](semantic-layer-spec.md) |
| Acceptance | `audit_helper` only when comparing relations |

---

## Commit order

| Stage | Paths | Message |
|---|---|---|
| Packages | `packages.yml` | `Add dbt packages` |
| Lock | `package-lock.yml` | `Install dbt packages` |
| Evaluator config | `dbt_project.yml` dispatch | `Configure dbt project evaluator` |
| Semantic layer | `models/semantic/` or `*_semantic.yml` | `Add semantic layer metrics` |

Ask before each commit — see [git-workflow.md](git-workflow.md).
