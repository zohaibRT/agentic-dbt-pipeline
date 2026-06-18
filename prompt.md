# dbt Pipeline Prompt

Install once:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Bootstrap installs the required dbt Labs agent skills and dbt packages when they are missing.

Copy the prompt below into Cursor. See also [references/agent-context-prompt.md](references/agent-context-prompt.md).

---

## Full Pipeline

Use this for any new analytics project. Fill in the values that are known. Leave unknown values blank and the agent will ask before running dbt commands.

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Goal: Build a <domain> dbt project using medallion layers from the available source schemas.

Required inputs:
- domain: <hospital | it_company | finance | retail | etc.>
- dbt_profile_name: <profile key from ~/.dbt/profiles.yml>
- source_schema: <raw/source schema to inspect>
- source_name: <friendly dbt source name>
- layer_schema_prefix: <usually same as source_name>
- github_repo_name: <repo slug only>

layer_names:
  layer_1: bronze
  layer_2: silver
  layer_3: gold

project_rules:
  field_mappings:
    - <source_table.source_column> -> <target_column>: <meaning/rule>
  joins:
    - <left_table.column> -> <right_table.column>: <relationship>
  metrics:
    - <metric_name>: <definition, grain, filters>
  exclusions:
    - <tables/columns/records to ignore>
  privacy:
    - <PII/PHI handling, masking, or exclusion rules>
  naming:
    - <custom naming conventions>
  special_instructions:
    - <anything else the agent must follow>

Task:
1. Set up the dbt project and install any required dbt agent skills or dbt packages.
2. Run the full pipeline: sources -> bronze -> silver -> gold -> semantic layer -> project evaluator -> docs.
3. Use dbt packages and metadata tools at the correct phase:
   - codegen: generate source YAML from the provided source schema; do not invent columns.
   - dbt_utils: use standard macros/tests while building bronze, silver, and gold models.
   - audit_helper: compare old vs new model outputs during refactors or validation.
   - dbt_project_evaluator: run after gold models to check project quality, tests, docs, and DAG structure.
   - MetricFlow/semantic layer: define metrics on final gold models.
   - Agents Schema: publish target/manifest.json metadata to AGENTS.* after docs/manifest generation.
4. Create the Agents Schema workflow after target/manifest.json exists, then create CI workflow files.
5. Create layer schemas prefixed by layer_schema_prefix. Example: doctor_hospital_src_bronze, doctor_hospital_src_silver, doctor_hospital_src_gold.
6. If dbt's default schema behavior would create analytics_bronze instead, add a safe generate_schema_name macro or ask before changing schema generation.
7. Apply project_rules exactly. If any mapping, join, metric, or privacy rule is unclear, ask before modeling it.
8. Initialize git if needed; commit initialization, sources, bronze, silver, gold, docs, CI, and Agents Schema separately.
9. If dbt_profile_name, source_schema, source_name, layer_schema_prefix, or github_repo_name is missing, ask me before running dbt commands.
10. If multiple dbt profiles exist in profiles.yml, ask which one to use. Do not guess.
11. Ask me only for missing source/profile details, unclear project_rules, missing credentials/secrets, and commit or push approval.
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

## Example Inputs

Hospital:

```text
domain: hospital
dbt_profile_name: hospital_analytics
source_schema: hospital_raw
source_name: hospital
layer_schema_prefix: hospital
github_repo_name: hospital-analytics

project_rules:
  field_mappings:
    - patients.patient_id -> patient_id: primary patient identifier
    - encounters.visit_date -> encounter_date: date of patient visit
  joins:
    - encounters.patient_id -> patients.patient_id: many encounters per patient
  metrics:
    - total_encounters: count of encounters at daily grain
  privacy:
    - exclude direct patient identifiers from gold models unless explicitly needed
```

IT company:

```text
domain: it_company
dbt_profile_name: it_analytics
source_schema: raw
source_name: it_company
layer_schema_prefix: it_company
github_repo_name: it-company-analytics

project_rules:
  field_mappings:
    - tickets.created_at -> ticket_created_at: ticket creation timestamp
    - employees.employee_id -> employee_id: internal employee key
  joins:
    - tickets.assignee_id -> employees.employee_id: ticket owner
  metrics:
    - open_tickets: count of tickets where status is not closed
```

Retail:

```text
domain: retail
dbt_profile_name: retail_analytics
source_schema: raw_orders
source_name: retail
layer_schema_prefix: retail
github_repo_name: retail-analytics

project_rules:
  field_mappings:
    - orders.order_id -> order_id: primary order identifier
    - order_items.quantity -> item_quantity: units sold
  joins:
    - order_items.order_id -> orders.order_id: one order has many items
  metrics:
    - gross_revenue: sum of item_quantity * unit_price
```

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
| Full phase order and security rules | dbt profile name |
| dbt packages and validation steps | Layer names |
| Model prefixes such as `stg_`, `int_`, `dim_`, `fct_` | Domain and source schema |
| GitHub owner from logged-in `gh` account | GitHub repo name |
| Ask before commit/push | Warehouse credentials and secrets |
