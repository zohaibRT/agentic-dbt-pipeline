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
  final_delivery.md
```

`REPORT_INDEX.md` is mandatory after the first phase report. It must group reports by phase and include the path, status, purpose, and what the human should check.

`HUMAN_VERIFICATION_GUIDE.md` is mandatory after analytics insight reporting and final delivery. It must explain how to verify layers, key performance indicators, blocked items, presentation artifacts, and next actions.

Do not write phase-specific reports, logs, codegen output, relationship reports, cardinality reports, analytics files, presentation files, or validation files directly under `reports/agent/` for new projects. Put them in the canonical phase folder below.

## Canonical Folder Layout

Write new phase artifacts to these folders:

```text
reports/agent/
  00_discovery/
  01_setup/
  02_sources/
  03_bronze/
  04_silver/
  05_gold/
  06_semantic/
  07_evaluator/
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

## Standard File Locations

| Artifact | Canonical Path |
|---|---|
| Discovery report | `reports/agent/00_discovery/discovery_report.md` |
| Requirements | `reports/agent/00_discovery/requirements.md` |
| Relationship profile | `reports/agent/00_discovery/relationship_profile.md` |
| Cardinality report | `reports/agent/00_discovery/cardinality_report.md` or the phase folder where the check was run |
| Setup report | `reports/agent/01_setup/setup_report.md` |
| Sources report | `reports/agent/02_sources/sources_report.md` |
| Codegen logs | `reports/agent/02_sources/codegen_stdout.txt` and `reports/agent/02_sources/codegen_stderr.txt` |
| Bronze report | `reports/agent/03_bronze/bronze_report.md` |
| Silver report | `reports/agent/04_silver/silver_report.md` |
| Gold report | `reports/agent/05_gold/gold_report.md` |
| Semantic report | `reports/agent/06_semantic/semantic_report.md` |
| Evaluator report | `reports/agent/07_evaluator/evaluator_report.md` |
| Documentation report | `reports/agent/08_documentation/docs_report.md` |
| Analytics insight report | `reports/agent/09_analytics_insights/analytics_insight_report.md` |
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
| Matplotlib figures | `reports/agent/10_presentation/matplotlib/figures/` |
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
