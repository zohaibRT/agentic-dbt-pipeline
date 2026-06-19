# dbt Pipeline Prompt

Install once:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

Copy one of the prompts below into Cursor.

---

## Starter Prompt

Use this for a new dbt project. Fill in the values you know. Leave anything unknown blank; the agent will ask before running dbt.

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Build a dbt project for this domain:
- domain: <hospital | it_company | finance | retail | etc.>
- dbt_profile_name: <profile key from ~/.dbt/profiles.yml>
- source_schema: <raw/source schema to inspect>
- source_name: <friendly dbt source name>
- layer_schema_prefix: <usually same as source_name>
- github_repo_name: <repo slug only>

Use these medallion layers:
- bronze
- silver
- gold

Please:
1. Discover source tables with codegen.
2. Profile source tables before modeling: row counts, keys, relationships, dates, measures, and status/code fields.
3. Build sources, bronze, silver, gold, semantic layer, docs, and quality checks.
4. Create source-prefixed layer schemas such as <source_name>_bronze, <source_name>_silver, and <source_name>_gold.
5. Use mapping seeds or reference tables when I provide manual mappings or code translations.
6. Commit each stage separately.
7. Summarize assumptions, data quality notes, and open review decisions before final delivery.
8. If stuck, stop retrying, summarize the blocker, show the last command/result, and ask me for the next decision.
9. Ask before using another dbt profile, changing schema naming, adding secrets, or pushing to GitHub.
```

What the skill handles automatically:

- installs dbt Labs agent skills when missing
- installs dbt packages with `dbt deps`
- uses `dbt_utils`, `audit_helper`, and `dbt_project_evaluator` at the right stages
- profiles source data before modeling
- applies mapping seeds and coverage checks when mappings are provided
- generates dbt docs
- prepares human review and final handoff notes
- prepares Agents Schema after `target/manifest.json` exists
- asks before unclear or risky actions

---

## Optional Project Rules

Add this only when you have business rules, field mappings, joins, or privacy requirements.

```text
Project rules:
- Field mappings:
  - <source_table.source_column> -> <target_column>: <meaning/rule>
- Joins:
  - <left_table.column> -> <right_table.column>: <relationship>
- Metrics:
  - <metric_name>: <definition, grain, filters>
- Exclusions:
  - <tables/columns/records to ignore>
- Privacy:
  - <PII/PHI handling, masking, or exclusion rules>
- Naming:
  - <custom naming conventions>
- Special instructions:
  - <anything else the agent must follow>
```

If a rule is unclear, the agent should ask before modeling it.

---

## Example: Hospital

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Build a dbt project for this domain:
- domain: hospital
- dbt_profile_name: shopsphere_analytics_dbt
- source_schema: Source
- source_name: doctor_hospital_src
- layer_schema_prefix: doctor_hospital_src
- github_repo_name: local-only

Use these medallion layers:
- bronze
- silver
- gold

Project rules:
- Field mappings:
  - patients.patient_id -> patient_id: primary patient identifier
  - encounters.visit_date -> encounter_date: date of patient visit
- Joins:
  - encounters.patient_id -> patients.patient_id: many encounters per patient
- Privacy:
  - exclude direct patient identifiers from gold models unless explicitly approved

Please commit locally only. Do not push to GitHub.
```

---

## Single Phase Examples

Use these when you want to run only one part of the workflow.

```text
workflow_phase: init
```

```text
workflow_phase: sources
```

```text
workflow_phase: marts
```

```text
workflow_phase: semantic_layer
```

```text
workflow_phase: project_evaluator
```

```text
workflow_phase: agents_schema
```

---

## Optional Settings

Most users do not need these.

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
