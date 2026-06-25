# dbt Packages & Agent Skills Stack

The pipeline uses **seven dbt capabilities** together. Agent installs and runs them during bootstrap and the full pipeline.

| # | Capability | Type | Purpose in pipeline |
|---|---|---|---|
| 1 | **dbt Agent Skills** | Agent skills | Orchestration, CLI, troubleshooting, semantic layer authoring |
| 2 | **dbt-codegen** | dbt package | `generate_source` for source YAML bootstrap |
| 3 | **dbt-utils** | dbt package | `star()`, `surrogate_key`, generic tests, cross-db macros |
| 4 | **dbt-expectations** | dbt package | Expressive data quality tests such as ranges, row counts, and column value expectations |
| 5 | **dbt-project-evaluator** | dbt package | Best-practice checks on DAG, tests, docs, structure |
| 6 | **audit_helper** | dbt package | Row-level audits when validating refactors or prod comparisons |
| 7 | **MetricFlow / Semantic Layer** | dbt YAML + skill | Business metrics on marts (`semantic_models`, `metrics`) |

---

## 1. dbt Agent Skills (bootstrap - not manual install)

User installs **only** `agentic-dbt-pipeline`. Project setup and configuration runs `npx skills add dbt-labs/dbt-agent-skills/skills/dbt` when skills are missing - see [install-dbt-agent-skills.md](install-dbt-agent-skills.md).

Install when `auto_install_dbt_skills: true` (default).

**Always compose:**

| Skill | When |
|---|---|
| `agentic-dbt-pipeline` | Full pipeline orchestration, git, GitHub push |
| `using-dbt-for-analytics-engineering` | Models, tests, docs |
| `running-dbt-commands` | CLI formatting |
| `building-dbt-semantic-layer` | After marts - semantic models & metrics |
| `troubleshooting-dbt-job-errors` | On job/CI failures |
| `adding-dbt-unit-test` | When adding unit tests |
| `answering-natural-language-questions-with-dbt` | Ad-hoc metric questions *(optional)* |

```bash
npx skills add dbt-labs/dbt-agent-skills/skills/dbt   # agent runs this in bootstrap if missing
```

User's only manual skill install:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

---

## 2-6. `packages.yml` (all dbt packages)

Declare **all** standard packages in `{project.root}/packages.yml`:

```yaml
packages:
  - package: dbt-labs/codegen
    version: 0.14.1
  - package: dbt-labs/dbt_utils
    version: 1.3.3
  - package: calogica/dbt_expectations
    version: 0.10.4
  - package: dbt-labs/dbt_project_evaluator
    version: 1.3.0
  - package: dbt-labs/audit_helper
    version: 0.14.0
```

```powershell
dbt deps
```

### codegen - source bootstrap

```powershell
$dbt = "dbt"
& $dbt --quiet run-operation generate_source `
  --args '{"schema_name": "<source.schema>", "generate_columns": true}' `
  > models\sources\<source.name>_sources_generated.yml
```

See [packages-and-sources.md](packages-and-sources.md) for post-codegen rules.

### dbt_utils - in models and tests

Use where helpful (not required on every model):

- `{{ dbt_utils.star(from=ref('stg_ecommerce__orders'), except=['_loaded_at']) }}`
- `dbt_utils.expression_is_true`, `dbt_utils.unique_combination_of_columns`
- `dbt_utils.generate_surrogate_key` in dims when needed

### dbt_expectations - expressive tests

Use where helpful for stronger governance, especially in marts and important intermediate models:

- Accepted ranges for percentages, rates, and amounts
- Row count comparisons when business rules expect bounded movement
- Non-negative measures and valid date ranges
- Boolean and categorical expectations that are more expressive than built-in generic tests

Do not add expectation tests that encode unapproved business assumptions.

### dbt_project_evaluator - after layers built

Read [project-evaluator.md](project-evaluator.md). Add to `dbt_project.yml`:

```yaml
dispatch:
  - macro_namespace: dbt
    search_order: ['dbt_project_evaluator', 'dbt']

models:
  dbt_project_evaluator:
    +schema: <layer_schema_prefix>_evaluator
    +materialized: table

vars:
  dbt_project_evaluator:
    staging_folder_name: <layer_1_name>
    intermediate_folder_name: <layer_2_name>
    marts_folder_name: <layer_3_name>
    marts_prefixes: ['fct_', 'dim_', 'mart_']
    other_prefixes: ['rpt_']
```

The evaluator package must not build into `source_schema`. If `base_*`, `stg_*`, or `fct_*` evaluator tables appear beside raw source tables, fix schema routing before accepting the run. See [schema-isolation.md](schema-isolation.md).

Use the evaluator vars to keep the skill's bronze/silver/gold layers. Do not restructure to `staging/intermediate/marts` only to satisfy package defaults.

Run after marts build passes:

```powershell
& $dbt build --select package:dbt_project_evaluator
```

Review `dbt_project_evaluator` results; fix critical issues or document accepted exceptions. Use an exceptions seed only for intentional patterns, such as reviewed rejoining warnings.

### audit_helper - validation & refactors

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

Run during acceptance or after large refactors - not on every layer commit.

---

## 6. MetricFlow / Semantic Layer

**Phase:** after marts, before docs (or extend docs phase).

Read [semantic-layer-spec.md](semantic-layer-spec.md) and compose with `building-dbt-semantic-layer`.

On dbt Core **1.10.x** -> use **legacy spec** (`semantic_models:` top-level YAML).

Validate:

```powershell
& $dbt parse --no-partial-parse
# dbt Cloud Semantic Layer: dbt sl validate  (if configured)
```

---

## Project setup package checklist

| Step | Command / action |
|---|---|
| Write `packages.yml` | All 5 packages listed above |
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

Ask before each commit - see [git-workflow.md](git-workflow.md).
