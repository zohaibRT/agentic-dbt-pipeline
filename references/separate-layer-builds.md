# Separate Layer Builds - Order, Schemas, and Examples

> **Skill default:** always create **all** layers. Use `bronze`/`silver`/`gold` unless the user or existing project provides different layer names. Names become `dbt_project.yml` keys, folders, and `+schema` values. See [dbt-project-layers.md](dbt-project-layers.md).

## Correct layer order (always - all layers)

```
1. Sources     ->  models/sources/ only
2. Layer 1     ->  models/{layer_1_name}/{project_slug}/  ->  warehouse schema: {layer_schema_prefix}_{layer_1_name}
3. Layer 2     ->  models/{layer_2_name}/{project_slug}/  ->  warehouse schema: {layer_schema_prefix}_{layer_2_name}
4. Layer 3     ->  models/{layer_3_name}/{project_slug}/  ->  warehouse schema: {layer_schema_prefix}_{layer_3_name}
```

Default names: `bronze`, `silver`, `gold`.

`staging`, `intermediate`, and `marts` are workflow/model roles. They are not additional physical folders when the active layer names are `bronze`, `silver`, and `gold`. Do not create duplicate folders such as both `models/bronze/` and `models/staging/`, or both `models/gold/` and `models/marts/`, in the same project unless the user explicitly approves a migration plan.

For a new full pipeline, run lightweight project Discovery & Requirements, then automatic project setup and configuration, before this build order. Then run phase-specific discovery before each layer.

A full-pipeline request defines the intended roadmap, not blanket approval to execute every layer. The active workflow checkpoint controls what may happen next: discovery approval moves only to automatic project setup and configuration; setup completion moves only to the sources phase plan; each approved layer moves only through its own build, validation, report, and next checkpoint. After each approved phase, write the phase report, write `reports/agent/NEXT_PHASE_PROMPT.md`, show the exact next-phase prompt, and stop unless the user approves that displayed prompt.

**Do not** build intermediate before staging exists.
**Do not** build marts before intermediate exists.

Generic example for one entity through all layers:

| Step | Layer | Example model | Warehouse schema |
|---|---|---|---|
| 1 | Source | `source('<source_name>', '<source_table>')` | `<source_schema>` |
| 2 | Staging | `stg_<source_name>__<source_table>` | `<layer_schema_prefix>_<layer_1_name>` |
| 3 | Intermediate | `int_<source_name>__<business_process_or_entity>` | `<layer_schema_prefix>_<layer_2_name>` |
| 4 | Marts | `dim_<business_entity>` or `fct_<business_event>` | `<layer_schema_prefix>_<layer_3_name>` |

Staging comes **before** intermediate. Marts (star schema) come **last**.

---

## Build one layer at a time

Set `workflow_phase:` in the prompt to run **only** that phase.

After project setup and configuration, for every non-setup phase: **phase-specific discovery -> agent recommendation -> data engineer decision check -> write `AGENT_PLAN.md` -> ask approval -> implement -> parse/build -> run layer data validation queries -> write `reports/agent/<phase>_report.md` with results -> update context tree -> write `reports/agent/NEXT_PHASE_PROMPT.md` -> summarize validation results and show the exact next-phase prompt -> ask natural approval for the displayed prompt -> ask commit**.

### Sources only

```text
workflow_phase: sources
```

Ensure `packages.yml` has the standard pinned package stack; the sources phase uses `codegen` from that stack - see [packages-and-sources.md](packages-and-sources.md).

```powershell
dbt deps
dbt run-operation generate_source --args '{"schema_name": "<source.schema>", "generate_columns": true}'
dbt parse --no-partial-parse
# No dbt build for sources alone - sources are YAML definitions
```

Explain the source YAML plan and get approval before running codegen or writing source files.
Generated and curated source YAML must stay under `models/sources/`; do not place source YAML in `models/<layer_1_name>/`, `models/<layer_2_name>/`, or `models/<layer_3_name>/`.
Write `reports/agent/sources_report.md`, update `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md`, write `reports/agent/NEXT_PHASE_PROMPT.md` for staging/bronze, show the prompt, ask whether to run it as written, then ask commit for `models/sources/` and `reports/agent/`.

---

### Layer 1 - Bronze / staging only

```text
workflow_phase: staging
```

Creates models like:
- `stg_<source>__<source_table>`
- `stg_<source>__<business_event_table>`
- `stg_<source>__<business_entity_table>`
- ... (one per source table)

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_1_name}/{project_slug}
```

**Builds:** staging models + tests + upstream source dependencies.
**Does NOT build:** intermediate or marts.

Warehouse models land in: **`<layer_schema_prefix>_<layer_1_name>`** (default materialization: `view`)

Run bronze discovery first: table grains, column pass/drop decisions, casts, naming, source tests, and sensitive-column handling. Recommend the staging path with evidence, then explain planned staging models, source tables, casts, tests, approval needs, schema target, and post-build data validation checks before creating files.
After `dbt build`, run [layer-data-validation.md](layer-data-validation.md). Verify source-to-staging row counts, staging row presence, grain/key checks, relationship tests, status/category distributions, and expected-empty sources. Share the validation results with the user.
Write `reports/agent/{layer_1_name}_report.md`, update `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md`, write `reports/agent/NEXT_PHASE_PROMPT.md` for intermediate/silver, show the prompt, ask whether to run it as written, then ask commit -> push `models/{layer_1_name}/{project_slug}/` and `reports/agent/`.

---

### Layer 2 - Silver / intermediate only

```text
workflow_phase: intermediate
```

Creates models like:
- `int_<source>__events_aggregated`
- `int_<source>__entities_enriched`
- `int_<source>__entity_metrics`

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_2_name}/{project_slug}
```

**Builds:** intermediate + staging (upstream) + tests.
**Does NOT build:** marts.

Warehouse models land in: **`<layer_schema_prefix>_<layer_2_name>`** (default materialization: `view`)

Run silver discovery first: join cardinality, grain preservation, mapping/reference needs, reusable business logic, flags, and tests. Recommend the intermediate path with evidence, then explain planned intermediate models, joins, grains, mappings, flags, approval needs, tests, and post-build data validation checks before creating files.
After `dbt build`, run [layer-data-validation.md](layer-data-validation.md). Verify row presence, expected-empty evidence, grain/key checks, row loss, row multiplication, relationship checks, mapping coverage, and derived measure/flag sanity. Share the validation results with the user.
Write `reports/agent/{layer_2_name}_report.md`, update `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md`, write `reports/agent/NEXT_PHASE_PROMPT.md` for marts/gold, show the prompt, ask whether to run it as written, then ask commit -> push `models/{layer_2_name}/{project_slug}/` and `reports/agent/`.

---

### Layer 3 - Gold / marts only

```text
workflow_phase: marts
```

Creates models like:
- **Dimensions:** `dim_<entity>`, `dim_dates`
- **Facts:** `fct_<business_event>`
- **Reporting:** `mart_<business_process>_performance`

```powershell
dbt parse --no-partial-parse
dbt build --select +path:models/{layer_3_name}/{project_slug}
```

**Builds:** marts + intermediate + staging (upstream) + tests.
**Does NOT build** downstream (there is none).

Warehouse models land in: **`<layer_schema_prefix>_<layer_3_name>`** (prod defaults: `dim_*`/`mart_*` = `table`, `fct_*` = `incremental`)

Run gold discovery first: approved facts, dimensions, metric grains, privacy exposure, reporting marts, and materializations. Recommend the mart path with evidence, then explain planned facts, dimensions, reporting marts, metrics, privacy handling, grains, approval needs, materializations, and post-build data validation checks before creating files.
After `dbt build`, run [layer-data-validation.md](layer-data-validation.md). Verify every fact, dimension, and reporting mart has data when upstream data exists; validate grain/key checks, relationships, date coverage, key performance indicator measures, and privacy exposure. Unexpected empty gold models are blockers until fixed or explicitly accepted. Share the validation results with the user.
Write `reports/agent/{layer_3_name}_report.md`, update `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md`, write `reports/agent/NEXT_PHASE_PROMPT.md` for the next applicable phase such as semantic layer or project evaluator, show the prompt, ask whether to run it as written, then ask commit -> push `models/{layer_3_name}/{project_slug}/`, `reports/agent/`, and `dbt_project.yml` if changed.

---

## Full pipeline (all layers, still separate commits)

```text
Run the default prompt without `workflow_phase`.
```

Run in order after automatic project setup and configuration, **stop for phase plan approval before each non-setup build and ask commit after each**:

1. Sources (if needed) -> source discovery -> plan approval -> source files -> phase report -> next-phase prompt -> ask natural approval -> ask commit
2. Staging -> bronze discovery -> plan approval -> build `+path:models/{layer_1_name}/{project_slug}` -> layer data validation -> phase report -> share results -> next-phase prompt -> ask natural approval -> ask commit
3. Intermediate -> silver discovery -> plan approval -> build `+path:models/{layer_2_name}/{project_slug}` -> layer data validation -> phase report -> share results -> next-phase prompt -> ask natural approval -> ask commit
4. Marts -> gold discovery -> plan approval -> build `+path:models/{layer_3_name}/{project_slug}` -> layer data validation -> phase report -> share results -> next-phase prompt -> ask natural approval -> ask commit

Each layer is a separate build and optional separate git push.

---

## Analytics insight reporting only

```text
workflow_phase: analytics_insight_reporting
```

Read [analytics-insight-reporting.md](analytics-insight-reporting.md). Requires completed and validated marts, semantic layer, evaluator, and documentation.

Before implementation: phase plan in `AGENT_PLAN.md` and approval.

After completion, write:

- `reports/agent/analytics_insight_report.md`
- `reports/agent/reporting_catalog.md`
- `reports/agent/kpi_catalog.md`
- `reports/agent/dashboard_spec.md`
- `reports/agent/insight_backlog.md`
- `reports/agent/reporting_readiness_scorecard.md`
- `reports/agent/analytics_insight_reporting_report.md`

Update `reports/agent/PIPELINE_STATUS.md`, `reports/agent/CONTEXT_TREE.md`, and `reports/agent/NEXT_PHASE_PROMPT.md`, then stop at the presentation-layer gate unless presentation work was explicitly approved.

Do not create Power BI, dashboard, slide, or notebook artifacts in this phase.

---

## Full pipeline order reminder

After automatic project setup and configuration, the default non-setup order is:

1. Sources
2. Staging / bronze
3. Intermediate / silver
4. Marts / gold
5. Semantic layer
6. Project evaluator
7. Documentation
8. Analytics insight reporting
9. Presentation layer recommendation
10. Optional Power BI / BI handoff after user approval
11. Continuous integration and Agents Schema when requested
12. Final delivery

---

## Optional: build a single model (advanced)

After creating one model in a layer:

```powershell
dbt build --select +stg_<source>__<source_table>
dbt build --select +int_<source>__<business_process_or_entity>
dbt build --select +dim_<business_entity>
```

`+model_name` builds that model and required upstream only.
Use for incremental work inside a layer; default skill flow still builds the **whole layer path** after all layer files are ready.

---

## What `+path` means

| Selector | Meaning |
|---|---|
| `path:models/{layer_1_name}/{project_slug}` | Only models in that folder |
| `+path:models/{layer_1_name}/{project_slug}` | That folder **+ all upstream** dependencies |

Prefer **`+path`** so upstream layers are built automatically when you build intermediate or marts alone.
