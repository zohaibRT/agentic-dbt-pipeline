# Analytics Product Completeness Migration

## Problem

Earlier skill versions optimized for fixed catalog volume (for example 50+ measures and 50+ metrics) and sometimes used industry-shaped dimension lists. Generated presentations could dump snake_case SQL ids and raw floats onto business tabs.

## What changed

- Completion mode defaults to **process coverage** via `analytics_policy` in `project.config.yml`.
- Primary gate artifacts: `analytics_coverage_matrix.md`, `fact_coverage_contracts.md`, `business_process_catalog.md`, `model_classification.md`.
- Metric families split: business measures/metrics, KPIs, data-quality, pipeline-health.
- Presentation Rule 5c requires display names + formatted values; Dimensions browse tables when gold dims exist.
- New validators wired into `run_acceptance_gate.py`.
- Fixed 50+ count gates removed from default executable behavior (advisory only when configured).

## Backward compatibility

| Legacy artifact | Status |
|---|---|
| `measure_catalog.md` / `metric_catalog.md` | Still supported as combined/legacy views |
| `kpi_catalog.md` | Still required for strategic KPIs |
| `kpi_figure_coverage.md` | Still required for presentation |
| `KPI_DEFINITION_CONTRACTS.md` | Extended with decision fields |
| `METRIC_VERIFICATION_MATRIX.md` | Unchanged consumers remain valid |

New catalogs are additive. Existing projects should add coverage matrix / fact contracts / display-name columns when re-entering analytics or presentation phases.

## Migration steps for an existing generated project

1. Add `analytics_policy` from skill `project.config.yml` (or accept skill defaults via gate common loader).
2. Create `reports/agent/09_analytics_insights/analytics_coverage_matrix.md` from the template.
3. Create `fact_coverage_contracts.md`, `business_process_catalog.md`, and `model_classification.md`.
4. Split QA row-count metrics into `data_quality_metric_catalog.md`.
5. Add Display name + Format columns to measure/metric catalogs.
6. Rebuild presentation boards to emit `display_name` and `formatted_value`.
7. Add `reports/agent/10_presentation/report_page_contracts.md`.
8. Re-run `python <skill>/scripts/run_acceptance_gate.py --root <project.root> --skip-dbt`.

## Breaking behavior

- Acceptance may FAIL projects that previously passed only because they had 50+ thin catalog rows without process coverage.
- Presentation boards that show snake_case ids / raw floats will FAIL readability checks.
