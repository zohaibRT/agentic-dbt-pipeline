# Analytics Insight Reporting

Use this after marts/gold, semantic layer, `dbt_project_evaluator`, and documentation are complete and validated. Run this before the presentation-layer recommendation or any Power BI / business intelligence handoff.

Also read [report-artifact-organization.md](report-artifact-organization.md), [kpi-discovery-framework.md](kpi-discovery-framework.md), [kpi-reconciliation.md](kpi-reconciliation.md), [cardinality-validation.md](cardinality-validation.md), [reporting-standards.md](reporting-standards.md), [kpi-definitions.md](kpi-definitions.md), [metric-verification.md](metric-verification.md), [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md), and [writing-style.md](writing-style.md).

## Phase purpose

Discover, design, and document the most useful business-facing outputs from validated data. This phase answers what the business can meaningfully see, which measures are available, which contextual metrics are useful, which key performance indicators are trusted, which reports or dashboard pages are worth building, and what must stay deferred.

This phase does **not** create Power BI projects, dashboards, slide decks, notebooks, or other presentation artifacts. It produces reporting design contracts that the presentation layer must consume.

The goal is maximum **useful** business insight supported by validated data, not the maximum number of dashboards or charts.

## Phase position

Official workflow order:

1. discovery
2. requirements
3. project setup / configuration
4. sources
5. staging / bronze
6. intermediate / silver
7. marts / gold
8. semantic layer
9. `dbt_project_evaluator`
10. docs
11. **analytics insight reporting**
12. presentation layer recommendation
13. optional Power BI / BI handoff after user approval
14. final delivery

Single-phase invocation:

```text
workflow_phase: analytics_insight_reporting
```

## Hard rules

These rules apply to every domain, source schema, and warehouse adapter:

- Do not create fake insights.
- Do not suggest charts just because data exists.
- Every key performance indicator and report candidate must map to validated marts or semantic metrics.
- Key performance indicator discovery must be schema-driven, grain-aware, and confidence-scored; do not hardcode domain-specific metrics.
- Trusted key performance indicators must have source-to-current-layer reconciliation and grain/cardinality proof.
- Every visual must answer a real business question.
- Keep measures, metrics, and key performance indicators separate. Do not promote every useful metric to a key performance indicator.
- Do not expose sensitive fields without approval.
- Clearly separate trusted outputs from uncertain or deferred outputs.
- Prefer useful, simple, business-friendly reporting over too many technical tables.
- Do not hardcode one domain's key performance indicators, page names, or sample values.
- Do not invent targets, benchmarks, attribution, or recommendations without evidence.
- Maximum means maximum useful business insight supported by validated data, not maximum number of dashboards.
- Do not build presentation artifacts in this phase.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Completed and validated gold/marts, semantic layer status, evaluator results, documentation artifacts, key performance indicator definitions, metric verification results, layer validation evidence, privacy decisions, and `reports/agent/08_documentation/docs_report.md` |
| Allowed changes | Analytics insight reporting files under `reports/agent/09_analytics_insights/`, key performance indicator files under `reports/agent/09_analytics_insights/kpis/`, root `REPORT_INDEX.md`, root `HUMAN_VERIFICATION_GUIDE.md`, and read-only warehouse queries for validation and evidence |
| Not allowed | dbt model SQL/YAML changes, semantic file changes, Power BI/PBIP/TMDL files, dashboards, slides, notebooks, guessed measures, or sensitive-field exposure without approval |
| Commands to run | Read-only `dbt ls`, manifest/catalog review, approved warehouse aggregate queries, and metric reconciliation checks from [metric-verification.md](metric-verification.md) |
| Completion criteria | All required reporting deliverables exist, trusted vs deferred outputs are separated, readiness scorecard is recorded, and presentation-layer gate is ready |
| Report required | `reports/agent/09_analytics_insights/analytics_insight_reporting_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` |

## Approval gate

Before implementation, follow [phase-plan-approval.md](phase-plan-approval.md).

Write or update `{project.root}/AGENT_PLAN.md` and wait for approval. The plan must explain:

- What will be analyzed
- Which validated marts and semantic metrics will be used
- What evidence supports reporting readiness
- What is trusted
- What is uncertain
- What is blocked or deferred
- What needs user approval

After the phase completes, write or update all required deliverables, update `reports/agent/PIPELINE_STATUS.md` and `reports/agent/CONTEXT_TREE.md`, then stop at the presentation-layer gate unless the user already approved presentation work in the same checkpoint.

Set status to `Analytics insight reporting complete - presentation decision pending`, not `Delivery complete`.

## Discovery checklist

Before drafting catalogs and specs, verify:

| Check | Evidence to collect |
|---|---|
| Model readiness | Gold facts, dimensions, and reporting marts built and non-empty when upstream data exists |
| Metric readiness | Approved key performance indicators with reconciled numerator, denominator, filters, and time field |
| Semantic readiness | Semantic metrics trace to supported marts when semantic layer exists |
| Data quality | Empty tables, row-count movement, date coverage, status distributions, and known limitations documented |
| Relationship readiness | Star-schema relationships are unambiguous for reporting; bridge tables built or deferrals documented |
| Privacy readiness | Sensitive, direct identifier, personally identifiable information, and protected health information fields identified and excluded or approved |
| Evaluator readiness | Evaluator warnings fixed, accepted, or documented |
| Documentation readiness | `dbt docs generate` completed; model purpose and grain documented |
| Business questions | Real questions the validated data can answer, not generic dashboard filler |
| Key performance indicator discovery | Table classification, grain, candidate measures, archetypes, confidence score, and targeted questions documented |
| Key performance indicator reconciliation | Proof SQL files, layer results, variance, first failing layer, and cardinality assumptions documented for trusted metrics |
| Time analysis | Usable date/time columns for trends and comparisons |
| Segmentation | Safe dimensions for filters, slicers, and breakdowns |
| Executive vs operational use | Which outputs serve leadership summary vs operational investigation |

## Required deliverables

After phase completion, create or update these files. Use canonical paths for new projects; when reading older projects, fall back to the legacy flat `reports/agent/<file>` path if the canonical file is missing.

| File | Purpose |
|---|---|
| `reports/agent/09_analytics_insights/analytics_insight_report.md` | Executive summary of what the business can meaningfully see; trusted facts, dimensions, metrics; useful questions; recommended dashboards; visuals; filters; drill-downs; caveats; sensitive fields; missing/deferred insights |
| `reports/agent/09_analytics_insights/kpis/measure_catalog.md` | Broad raw measure catalog with counts, amounts, quantities, dates, status distributions, and quality measures that are supported by validated models |
| `reports/agent/09_analytics_insights/kpis/metric_catalog.md` | Contextual metric catalog built from measures with time, dimension, ratio, average, ranking, aging, or quality context |
| `reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md` | Domain-neutral key performance indicator candidate matrix with table classification, grain, formula, confidence, caveats, validation query, and approval status |
| `reports/agent/09_analytics_insights/kpis/kpi_reconciliation_report.md` | Layer-by-layer key performance indicator proof table with result, expected result, variance, status, and notes |
| `reports/agent/09_analytics_insights/kpis/kpi_lineage_proofs.md` | Source-to-final key performance indicator lineage summary showing where values changed |
| `reports/agent/09_analytics_insights/kpis/kpi_variance_report.md` | First-layer versus final-layer variance and likely cause for each reconciled key performance indicator |
| `reports/agent/09_analytics_insights/kpis/sql_proofs/` | SQL and DAX proof files for each key performance indicator and layer where applicable |
| `reports/agent/09_analytics_insights/reporting_catalog.md` | Catalog of report/page candidates |
| `reports/agent/09_analytics_insights/kpis/kpi_catalog.md` | Catalog of trusted and deferred key performance indicators with definitions, confidence, and caveats |
| `reports/agent/09_analytics_insights/dashboard_spec.md` | Full dashboard/report design spec for the presentation phase |
| `reports/agent/09_analytics_insights/insight_backlog.md` | Useful insights not ready yet and what unlocks them |
| `reports/agent/09_analytics_insights/reporting_readiness_scorecard.md` | PASS/WARN/FAIL/BLOCKED scorecard across readiness areas |
| `reports/agent/09_analytics_insights/analytics_insight_reporting_report.md` | Phase completion report consistent with other `<phase>_report.md` files |
| `reports/agent/REPORT_INDEX.md` | Human-readable index of all reports, status, purpose, and verification action |
| `reports/agent/HUMAN_VERIFICATION_GUIDE.md` | Short guide that tells the data engineer what to review and how to verify key results |

## Output templates

### `analytics_insight_report.md`

```markdown
# Analytics Insight Report

## Executive Summary

## Available Business Domains

## Trusted Facts

## Trusted Dimensions

## Trusted Metrics

## Available Measures

## Useful Metrics

## Useful Business Questions

## Suggested Reports and Dashboards

## Recommended Dashboard Pages

## Recommended Visuals

## Required Filters and Slicers

## Drill-Down Recommendations

## Data Caveats

## Sensitive Fields to Avoid

## Missing Data

## Deferred Insights

## Next Recommended Reporting Steps
```

### `reporting_catalog.md`

| Report/Page | Business Question | Fact Model | Dimensions | Metrics | Filters | Suggested Visuals | Confidence | Caveats |
|---|---|---|---|---|---|---|---|---|
| `<page_or_report_name>` | `<question>` | `<ref() model>` | `<dimensions>` | `<metrics>` | `<filters>` | `<visual_types>` | `<HIGH/MEDIUM/LOW/DEFERRED>` | `<caveats>` |

### `measure_catalog.md`

Populate from [kpi-discovery-framework.md](kpi-discovery-framework.md). Include broad, validated raw measures even when they are not strategic key performance indicators.

| Measure | Measure Type | Source Model | Grain | Formula | Time Field | Allowed Dimensions | Validation Query | Status | Caveats |
|---|---|---|---|---|---|---|---|---|---|
| `<measure_name>` | `<count/amount/quantity/date/status/quality>` | `<model>` | `<grain>` | `<formula>` | `<time_field_or_not_applicable>` | `<dimensions>` | `<query_or_not_ready>` | `<ready/deferred/blocked>` | `<caveats>` |

### `metric_catalog.md`

Promote supported measures into contextual metrics. A metric may be useful for reports even when it is not a strategic key performance indicator.

| Metric | Metric Type | Business Question | Source Measures | Source Model | Grain | Formula | Time Field | Allowed Dimensions | Filters | Validation Query | Confidence | Caveats | Promotion Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `<metric_name>` | `<time/dimension/ratio/average/ranking/aging/quality>` | `<question>` | `<measures>` | `<model>` | `<grain>` | `<formula>` | `<time_field>` | `<dimensions>` | `<filters>` | `<query_or_not_ready>` | `<HIGH/MEDIUM/LOW/BLOCKED>` | `<caveats>` | `<report_metric/kpi_candidate/deferred/blocked>` |

### `kpi_discovery_matrix.md`

Populate from [kpi-discovery-framework.md](kpi-discovery-framework.md). Include all trusted, uncertain, deferred, and blocked candidates.

| Key Performance Indicator | Business Question | Metric Type | Source Metric | Source Model | Grain | Formula | Numerator | Denominator | Time Field | Allowed Dimensions | Filters | Validation Query | Confidence | Caveats | Approval Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `<kpi_name>` | `<question>` | `<volume/value/ratio/funnel/trend/etc>` | `<metric_name>` | `<model>` | `<grain>` | `<formula>` | `<numerator>` | `<denominator>` | `<time_field>` | `<dimensions>` | `<filters>` | `<query_or_not_ready>` | `<HIGH/MEDIUM/LOW/BLOCKED>` | `<caveats>` | `<approved/pending/deferred/blocked>` |

### `kpi_catalog.md`

Generate from `metric_catalog.md`, `kpi_discovery_matrix.md`, reconciliation files from [kpi-reconciliation.md](kpi-reconciliation.md), approved definitions in [kpi-definitions.md](kpi-definitions.md), and reconciliation in [metric-verification.md](metric-verification.md). Promote only `HIGH` confidence and user-approved `MEDIUM` confidence key performance indicators into implemented metrics when grain, cardinality, and source-to-current-layer reconciliation are proven. Keep useful non-strategic metrics in `metric_catalog.md`. Keep `LOW`, `BLOCKED`, and unreconciled candidates as deferred or blocked with reasons.

| Key Performance Indicator | Definition | Source Model | Formula/Measure | Time Field | Grain | Allowed Dimensions | Business Use | Confidence | Caveats |
|---|---|---|---|---|---|---|---|---|---|
| `<kpi_name>` | `<business_meaning>` | `<model>` | `<formula_or_semantic_metric>` | `<time_field>` | `<grain>` | `<dimensions>` | `<use_case>` | `<HIGH/MEDIUM/LOW/DEFERRED/BLOCKED>` | `<caveats>` |

### `dashboard_spec.md`

```markdown
# Dashboard Specification

## Dashboard Name

## Target Audience

## Page List

| Page | Purpose | Key Performance Indicators | Visuals | Filters/Slicers | Drill-Through Paths |
|---|---|---|---|---|---|

## Refresh Expectations

## Data Limitations
```

### `insight_backlog.md`

| Useful Insight | Reason Not Ready | Missing Data/Model/Metric/Requirement | What Unlocks It |
|---|---|---|---|
| `<insight>` | `<reason>` | `<gap>` | `<unlock_action>` |

### `reporting_readiness_scorecard.md`

Score each area PASS, WARN, FAIL, or BLOCKED with evidence:

| Area | Status | Evidence | Action Needed |
|---|---|---|---|
| Model readiness | | | |
| Metric readiness | | | |
| Data quality readiness | | | |
| Relationship readiness | | | |
| Power BI readiness | | | |
| Privacy readiness | | | |
| Executive dashboard readiness | | | |
| Operational dashboard readiness | | | |

## Presentation-layer handoff rules

The presentation layer must consume these outputs:

| Analytics insight output | Presentation use |
|---|---|
| `dashboard_spec.md` | Page plan and scope |
| `kpi_discovery_matrix.md` | Candidate metric evidence, confidence, and deferred/blocked reasoning |
| `kpi_reconciliation_report.md` | Proof that trusted key performance indicators reconcile across layers |
| `kpi_lineage_proofs.md` | First failing layer and lineage summary for presentation caveats |
| `kpi_variance_report.md` | Variance evidence and blocked metric reasons |
| `kpi_catalog.md` | Measure and key performance indicator source |
| `reporting_catalog.md` | Report/page scope |
| `insight_backlog.md` | Blocked or deferred visuals |
| `reporting_readiness_scorecard.md` | Validation gate before artifact build |
| `analytics_insight_report.md` | Business-facing rationale |

Read [presentation-layer.md](presentation-layer.md) and [powerbi-template.md](powerbi-template.md) after this phase when a presentation artifact is being considered. The presentation layer must not invent pages, key performance indicators, visuals, or business scope that contradict or bypass these outputs unless the user explicitly overrides them.

For Power BI PBIP/TMDL, these files are the scope contract for the generator and must be used or explicitly marked missing/blocking:

- `dashboard_spec.md`
- `measure_catalog.md`
- `metric_catalog.md`
- `kpi_discovery_matrix.md`
- `kpi_reconciliation_report.md`
- `kpi_lineage_proofs.md`
- `kpi_variance_report.md`
- `kpi_catalog.md`
- `reporting_catalog.md`
- `analytics_insight_report.md`
- `reporting_readiness_scorecard.md`
- `insight_backlog.md`

For Matplotlib report figures, use the same scope contract. Read [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md) and map every recommended measure, metric, and key performance indicator into `kpi_figure_coverage.md` or an explicit blocked/deferred note.

Blocked or deferred visuals from `insight_backlog.md` must not be generated silently.

## Consultant reporting guidance

Use [reporting-standards.md](reporting-standards.md) for the five report pillars. In this phase, apply the pillars to **design** only:

- Context and strategy: why each report or page matters
- Key performance indicators: trusted metrics only
- Trend analysis and variance: only when validated time fields exist
- Insights and attribution: evidence-backed drivers only; mark hypotheses clearly
- Recommendations and next steps: presentation-phase actions and approval needs

Do not duplicate the full Power BI canvas standard here. Reference [reporting-standards.md](reporting-standards.md) and [presentation-layer.md](presentation-layer.md) for artifact layout rules.

## Phase completion

After all deliverables exist:

1. Write `reports/agent/09_analytics_insights/analytics_insight_reporting_report.md` using [phase-completion-report.md](phase-completion-report.md).
2. Update `reports/agent/PIPELINE_STATUS.md` with phase status PASS, WARN, FAIL, or BLOCKED.
3. Update `reports/agent/CONTEXT_TREE.md` with trusted metrics, deferred insights, and links to reporting files.
4. Summarize trusted vs deferred outputs in chat.
5. Stop at the presentation-layer gate unless presentation work was explicitly approved in the same checkpoint.

## Commit

When commit mode allows:

```powershell
git add reports/agent/
git commit -m "Add analytics insight reporting design"
```

Ask before commit unless `commit: auto_yes`.
