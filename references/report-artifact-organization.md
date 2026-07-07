# Report Artifact Organization

Use this whenever the skill writes files under `reports/agent/`.

## Goal

Keep reports easy for a data engineer to review. Do not dump every artifact into one flat folder. Use a small root control plane plus phase folders, and write an index that explains where to look.

## Root Control Plane

Keep only these high-level files at `reports/agent/`:

```text
reports/agent/
  PIPELINE_STATUS.md
  CONTEXT_TREE.md
  NEXT_PHASE_PROMPT.md
  REPORT_INDEX.md
  HUMAN_VERIFICATION_GUIDE.md
  REQUIREMENTS_TRACEABILITY_MATRIX.md
  LAYER_VERIFICATION_LEDGER.md
  KPI_DEFINITION_CONTRACTS.md
  METRIC_VERIFICATION_MATRIX.md
  ACCEPTANCE_GATE_REPORT.md
  ACCEPTANCE_GATE_REPORT.json
  INDEPENDENT_VERIFICATION_REPORT.md
  INDEPENDENT_VERIFICATION_REPORT.json
  final_delivery.md
```

`REPORT_INDEX.md` is mandatory after the first phase report. It must group reports by phase and include the path, status, purpose, and what the human should check.

`HUMAN_VERIFICATION_GUIDE.md` is mandatory after analytics insight reporting and final delivery. It must explain how to verify layers, key performance indicators, blocked items, presentation artifacts, and next actions.

The traceability, ledger, contract, metric matrix, acceptance gate, and independent verification reports are allowed at the root because they are cross-phase evidence control files. Do not write phase-specific reports, logs, codegen output, relationship reports, cardinality reports, analytics files, presentation files, or validation files directly under `reports/agent/` for new projects. Put them in the canonical phase folder below.

## Canonical Folder Layout

Write new phase artifacts to these folders:

```text
reports/agent/
  00_discovery/
    sql_proofs/
  01_setup/
  02_sources/
    sql_proofs/
  03_bronze/
    sql_proofs/
  04_silver/
    sql_proofs/
  05_gold/
    sql_proofs/
  06_semantic/
    sql_proofs/
  07_evaluator/
    sql_proofs/
  08_documentation/
  09_analytics_insights/
    kpis/
      sql_proofs/
  10_presentation/
    matplotlib/
    report_pages/
    figures/
    sql_verification/
    report.html
    open_report.bat
  11_operations/
```

Use the folder that matches the current phase. Do not put phase-specific files at the root unless the file is one of the root control-plane files.

During project setup and configuration, run:

```powershell
python <path-to-installed-skill-or-workspace>\scripts\create_report_skeleton.py --root <project.root-or-workspace.root>
```

This creates the managed folders and `_proof_index.md` files before the first proof query is written. Do not delete those index files; use them as the human-facing map for what each proof folder contains.

For discovery and discovery-created control files, use the canonical templates under:

```text
templates/reports/00_discovery/
templates/reports/root/
```

These templates define the fixed report structure for discovery, requirements, cardinality, relationship profiling, discovery approval, proof index, SQL proof files, pipeline status, context tree, report index, requirements traceability, and next-phase prompt. Copy/fill them only after required discovery inputs are confirmed. The template structure should stay consistent across projects; the content should change based on the source evidence and approved user requirements.

## Standard File Locations

| Artifact | Canonical Path |
|---|---|
| Discovery report | `reports/agent/00_discovery/discovery_report.md` |
| Requirements | `reports/agent/00_discovery/requirements.md` |
| Requirements traceability matrix | `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` |
| Layer verification ledger | `reports/agent/LAYER_VERIFICATION_LEDGER.md` |
| Key performance indicator definition contracts | `reports/agent/KPI_DEFINITION_CONTRACTS.md` |
| Metric verification matrix | `reports/agent/METRIC_VERIFICATION_MATRIX.md` |
| Acceptance gate report | `reports/agent/ACCEPTANCE_GATE_REPORT.md` and `reports/agent/ACCEPTANCE_GATE_REPORT.json` |
| Independent verification report | `reports/agent/INDEPENDENT_VERIFICATION_REPORT.md` and `reports/agent/INDEPENDENT_VERIFICATION_REPORT.json` |
| Relationship profile | `reports/agent/00_discovery/relationship_profile.md` |
| Cardinality report | `reports/agent/00_discovery/cardinality_report.md` or the phase folder where the check was run |
| Discovery SQL proofs | `reports/agent/00_discovery/sql_proofs/` |
| Setup report | `reports/agent/01_setup/setup_report.md` |
| Sources report | `reports/agent/02_sources/sources_report.md` |
| Sources SQL proofs | `reports/agent/02_sources/sql_proofs/` |
| Codegen logs | `reports/agent/02_sources/codegen_stdout.txt` and `reports/agent/02_sources/codegen_stderr.txt` |
| Bronze report | `reports/agent/03_bronze/bronze_report.md` |
| Bronze SQL proofs | `reports/agent/03_bronze/sql_proofs/` |
| Silver report | `reports/agent/04_silver/silver_report.md` |
| Silver SQL proofs | `reports/agent/04_silver/sql_proofs/` |
| Gold report | `reports/agent/05_gold/gold_report.md` |
| Gold SQL proofs | `reports/agent/05_gold/sql_proofs/` |
| Semantic report | `reports/agent/06_semantic/semantic_report.md` |
| Semantic SQL proofs | `reports/agent/06_semantic/sql_proofs/` |
| Evaluator report | `reports/agent/07_evaluator/evaluator_report.md` |
| Evaluator SQL proofs | `reports/agent/07_evaluator/sql_proofs/` |
| Documentation report | `reports/agent/08_documentation/docs_report.md` |
| Analytics insight report | `reports/agent/09_analytics_insights/analytics_insight_report.md` |
| Business process catalog | `reports/agent/09_analytics_insights/business_process_catalog.md` |
| Dimension catalog | `reports/agent/09_analytics_insights/dimension_catalog.md` |
| Fact catalog | `reports/agent/09_analytics_insights/fact_catalog.md` |
| Reporting catalog | `reports/agent/09_analytics_insights/reporting_catalog.md` |
| Dashboard specification | `reports/agent/09_analytics_insights/dashboard_spec.md` |
| Insight backlog | `reports/agent/09_analytics_insights/insight_backlog.md` |
| Reporting readiness scorecard | `reports/agent/09_analytics_insights/reporting_readiness_scorecard.md` |
| Measure catalog | `reports/agent/09_analytics_insights/kpis/measure_catalog.md` |
| Metric catalog | `reports/agent/09_analytics_insights/kpis/metric_catalog.md` |
| KPI catalog | `reports/agent/09_analytics_insights/kpis/kpi_catalog.md` |
| KPI discovery matrix | `reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md` |
| KPI reconciliation | `reports/agent/09_analytics_insights/kpis/kpi_reconciliation_report.md` |
| KPI lineage proofs | `reports/agent/09_analytics_insights/kpis/kpi_lineage_proofs.md` |
| KPI variance report | `reports/agent/09_analytics_insights/kpis/kpi_variance_report.md` |
| KPI SQL proofs | `reports/agent/09_analytics_insights/kpis/sql_proofs/` |
| Presentation report | `reports/agent/10_presentation/presentation_report.md` |
| Matplotlib README | `reports/agent/10_presentation/matplotlib/README.md` |
| Matplotlib requirements | `reports/agent/10_presentation/matplotlib/requirements-matplotlib.txt` |
| Matplotlib report spec | `reports/agent/10_presentation/matplotlib/report_spec.md` |
| Matplotlib KPI figure coverage | `reports/agent/10_presentation/matplotlib/kpi_figure_coverage.md` |
| Matplotlib label dictionary | `reports/agent/10_presentation/matplotlib/label_dictionary.md` |
| Matplotlib report theme | `reports/agent/10_presentation/matplotlib/report_theme.md` |
| Matplotlib theme constants | `reports/agent/10_presentation/matplotlib/report_theme.py` |
| Matplotlib browser report | `reports/agent/10_presentation/matplotlib/report.html` |
| Matplotlib report launcher | `reports/agent/10_presentation/matplotlib/open_report.bat` |
| Matplotlib page modules | `reports/agent/10_presentation/matplotlib/report_pages/` |
| Matplotlib generation script | `reports/agent/10_presentation/matplotlib/generate_report.py` |
| Matplotlib web report | `reports/agent/10_presentation/matplotlib/` |
| Matplotlib SQL verification | `reports/agent/10_presentation/matplotlib/sql_verification/` |
| Power BI model plan | `reports/agent/10_presentation/powerbi_model_plan.md` |
| Dashboard pages | `reports/agent/10_presentation/dashboard_pages.md` |
| DAX measures | `reports/agent/10_presentation/dax_measures.md` |
| Continuous integration report | `reports/agent/11_operations/ci_report.md` |
| Agents Schema report | `reports/agent/11_operations/agents_schema_report.md` |

## Backward Compatibility

Older projects may already have flat files such as `reports/agent/kpi_catalog.md`. When reading context, check the canonical path first, then the legacy flat path if the canonical file is missing.

For new writes, prefer canonical paths. If an existing project already has the flat layout, do not move files without user approval. Instead:

1. Create `REPORT_INDEX.md`.
2. Create `HUMAN_VERIFICATION_GUIDE.md` when relevant.
3. Add a note that the project uses a legacy flat layout.
4. Continue writing new files to canonical folders unless the user asks to preserve the old layout.

If the user approves cleanup of a legacy flat layout, migrate files by phase into the canonical folders, leave root control-plane files at the root, update `REPORT_INDEX.md`, and document the migration in the next phase report. Do not delete legacy files until the migrated copies are verified.

## Human-Facing Summary Requirement

Every phase report and index entry must answer:

- Why this report exists
- How to use it
- What the data engineer should verify
- What passed, warned, failed, skipped, or blocked
- What to do next

## Chat Summary Requirement

After each phase, the chat response must summarize the result directly. Do not rely only on files. Include the completed work, validation results, important warnings or blockers, the next phase, and the exact approval question.

## SQL Proof File Standard

Every phase that runs warehouse discovery, validation, metric verification, or reporting verification must write reusable proof files under that phase's `sql_proofs/` folder, or the more specific canonical verification folder such as `reports/agent/09_analytics_insights/kpis/sql_proofs/` or `reports/agent/10_presentation/matplotlib/sql_verification/`.

Use one file per logical proof so a data engineer can re-run it later. Prefer descriptive, sortable filenames:

```text
reports/agent/<phase>/sql_proofs/
  001_source_table_inventory.sql
  010_<table>_row_count.sql
  020_<table>_primary_key_check.sql
  030_<relationship>_orphan_check.sql
  040_<model>_measure_summary.sql
```

Each `.sql` proof file must contain:

```sql
/*
Proof name: <business friendly name>
Phase: <discovery | sources | bronze | silver | gold | semantic | evaluator | analytics_insight | presentation>
Purpose: <what this proves and why it matters>
Source objects: <schema.table or ref/model names>
Expected result: <expected row count, zero duplicates, allowed statuses, non-negative amount, etc.>
Captured result at run time:
<small markdown-style or plain-text result table from the command output>
Status: PASS | WARN | FAIL | BLOCKED | SKIPPED
Re-run notes: <profile/target/schema assumptions and any safe filters>
*/

<runnable SQL query>;
```

Rules:

- Store aggregate results only. Do not write sensitive row-level samples, direct identifiers, credentials, or secrets into proof files.
- Keep queries runnable through the selected dbt profile/adapter. Use adapter-appropriate quoting and schema names.
- Include captured results as comments above the query, not as a replacement for the query.
- Link proof files from the phase report `Data Verification Results` section and from `REPORT_INDEX.md`.
- If a query was not run, still create a blocked/skipped proof note only when the missing proof affects phase acceptance.
