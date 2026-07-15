#!/usr/bin/env python3
"""Build four multi-domain analytics fixtures and run gate validators.

Fixtures are clearly marked test data. They prove domain-neutral validators
pass without changing core skill code across structurally different domains.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "analytics"
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
from lib_fixture_control_plane import write_control_plane_files  # noqa: E402
from lib_gate_common import REQUIRED_OBSERVABILITY_DOMAINS  # noqa: E402
from fixture_kpi_contracts import (  # noqa: E402
    approval_register_markdown,
    attention_board_markdown,
    decision_log_markdown,
    kpi_contracts_markdown,
    matrix_markdown,
    rate_sql,
    volume_sql,
)
from lib_interactive_presentation import write_interactive_presentation  # noqa: E402

TIME_INTEL_METRICS = [
    "KPI-001",
    "KPI-002",
    "volume_kpi",
    "completion_kpi",
    "completion_rate",
    "failure_rate",
    "avg_amount",
    "mom_volume_change",
]


def fact_coverage_table(fact: str) -> str:
    return f"""
# Fact Coverage Contracts (TEST FIXTURE)

| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {fact} | one row per event | event_id | event_date | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | volume and completion | Fixture | PASS |
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def observability_coverage_table() -> str:
    na_domains = {
        "consistency",
        "freshness",
        "incident history",
        "mean time to detect",
        "mean time to resolve",
    }
    rows = []
    for domain in sorted(REQUIRED_OBSERVABILITY_DOMAINS):
        if domain in na_domains:
            rows.append(
                f"| {domain} | fixture scope | n/a | n/a | Is {domain} monitored? | n/a | n/a | n/a | n/a | n/a | analytics | none | NOT_APPLICABLE | Fixture has no second source or incident system | Reassess when source exists |"
            )
        else:
            rows.append(
                f"| {domain} | all gold models | fct_events | orphan_rate | Is {domain} healthy? | dbt tests | sql proof | SLA n/a | 0 | 0 | analytics | none | PASS | Checked in fixture | n/a |"
            )
    header = (
        "# Data Observability Coverage (TEST FIXTURE)\n\n"
        "| Domain | Scope | Models | Metric IDs | Business or Engineering Question | Validation Method | Proof or Telemetry | Threshold or SLA | Expected Result | Actual Result | Owner | Incident or Action | Status | Notes | Reassessment Condition |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    return header + "\n".join(rows)


def time_intelligence_table() -> str:
    rows = [
        f"| {metric} | event_date | occurred | yes | yes | yes | yes | yes | Target not defined | PASS |"
        for metric in TIME_INTEL_METRICS
    ]
    header = (
        "# Time Intelligence Coverage (TEST FIXTURE)\n\n"
        "Reporting period labeling is required on KPI cards.\n\n"
        "| Metric ID | Date field | Date role | Current period | Prior period | MoM/YoY | MTD/QTD/YTD | Rolling | Target/baseline | Status |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
    )
    return header + "\n".join(rows)


def common_project(slug: str, process: str, fact: str, dims: list[str]) -> Path:
    base = FIX / slug
    write(
        base / "project.config.yml",
        f"""
project:
  name: fixture_{slug}
analytics_policy:
  completion_mode: process_coverage
  advisory_measure_target: null
  advisory_metric_target: null
  critical_fact_coverage_required: 1.0
  critical_kpi_contract_coverage_required: 1.0
  critical_reconciliation_coverage_required: 1.0
  business_process_coverage_required: 0.9
  time_intelligence_coverage_required: 0.8
  model_classification_coverage_required: 1.0
  business_label_coverage_required: 1.0
  report_traceability_required: 1.0
  rendered_proof_coverage_required: 1.0
  report_page_contract_coverage_required: 1.0
  observability_domain_coverage_required: 1.0
  critical_data_quality_coverage_required: 1.0
  critical_process_module_coverage_required: 1.0
  production_exposure_coverage_required: 1.0
presentation_policy:
  require_stable_visual_ids: true
  require_bidirectional_page_contract_mapping: true
  require_bidirectional_proof_mapping: true
  approved_kpis_required_for_trusted_executive_pages: true
  pending_kpis_allowed_in_draft_pages: true
acceptance_policy:
  final_fail_on_warning: true
  require_explicit_warning_acceptance: true
""",
    )
    write(base / "models" / "gold" / f"{fact}.sql", f"-- TEST FIXTURE ONLY\nselect 1 as id\n")
    for dim in dims:
        write(base / "models" / "gold" / f"{dim}.sql", f"-- TEST FIXTURE ONLY\nselect 1 as id\n")

    seed_name = fact.replace("fct_", "raw_").replace("activity_events", "raw_activities")
    if not seed_name.startswith("raw_"):
        seed_name = f"raw_{fact}"
    write(
        base / "models" / "sources" / "raw.yml",
        f"""
version: 2
sources:
  - name: raw
    description: TEST FIXTURE source stub for gate evidence
    schema: main
    tables:
      - name: {seed_name}
        description: TEST FIXTURE seed table
""",
    )

    insights = base / "reports" / "agent" / "09_analytics_insights"
    kpis = insights / "kpis"

    write(
        insights / "business_process_catalog.md",
        f"""
# Business Process Catalog (TEST FIXTURE — illustrative only)

| Process | Event | Grain | Status Fields | Dates | Dimensions | Business Questions | Confidence | Approval | Status |
|---|---|---|---|---|---|---|---|---|---|
| {process} | primary event | one row per event | status | event_date | {', '.join(dims)} | What is volume and completion rate? | HIGH | APPROVED | PASS |
""",
    )
    write(
        insights / "analytics_coverage_matrix.md",
        f"""
# Analytics Coverage Matrix (TEST FIXTURE)

| Business Process | Fact/Event Models | Dimensions | Grain Proven | Measures | Contextual Metrics | Strategic KPIs | Time Intelligence | Segmentation | Exceptions | Data Quality | Reconciliation | Report Page | Owner/Approval | Status | Missing Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {process} | {fact} | {', '.join(dims)} | yes | 6 | 4 | 2 | current+prior | yes | yes | yes | yes | Executive Overview | owner | PASS | none |
""",
    )
    write(insights / "fact_coverage_contracts.md", fact_coverage_table(fact))
    write(
        insights / "model_classification.md",
        f"""
# Model Classification (TEST FIXTURE)

| Model | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {fact} | fact/event | primary measurable event | event | event_id | event_date | count, amount | {', '.join(dims)} | not_null | PASS | table | HIGH | PASS |
"""
        + "\n".join(
            f"| {dim} | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |"
            for dim in dims
        ),
    )
    write(insights / "time_intelligence_coverage.md", time_intelligence_table())
    write(
        insights / "exposure_coverage.md",
        f"""
# Exposure Coverage (TEST FIXTURE)

| Exposure | Type | Owner | Dependent Models | Dependent Metrics | Refresh | Business Purpose | Criticality | Validation Status |
|---|---|---|---|---|---|---|---|---|
| browser_report | browser report | analytics | {fact} | Volume KPI | daily | {process} overview | high | PASS |
""",
    )
    write(insights / "data_observability_coverage.md", observability_coverage_table())
    write(
        insights / "data_observability_report.md",
        """
# Data Observability Report (TEST FIXTURE)

## Completeness
Checked.

## Freshness
Deferred — no live warehouse in fixture.

## Referential integrity
Checked via orphan measure.

## Reconciliation
Within tolerance.
""",
    )
    write(
        insights / "fact_catalog.md",
        f"""
# Fact Catalog (TEST FIXTURE)

| Fact Model | Grain | Status |
|---|---|---|
| {fact} | event | PASS |
""",
    )
    write(
        kpis / "business_measure_catalog.md",
        """
# Business Measure Catalog (TEST FIXTURE)

| Measure | Display name | Format | Status |
|---|---|---|---|
| event_count | Event count | integer | PASS |
| completed_count | Completed count | integer | PASS |
| amount_sum | Amount sum | currency | PASS |
| duration_avg | Average duration | decimal | PASS |
| open_count | Open count | integer | PASS |
| failed_count | Failed count | integer | PASS |
""",
    )
    write(
        kpis / "business_metric_catalog.md",
        """
# Business Metric Catalog (TEST FIXTURE)

| Metric | Display name | Format | Status |
|---|---|---|---|
| completion_rate | Completion rate | percent | PASS |
| failure_rate | Failure rate | percent | PASS |
| avg_amount | Average amount | currency | PASS |
| mom_volume_change | Month-over-month volume change | percent | PASS |
""",
    )
    write(
        kpis / "kpi_catalog.md",
        """
# KPI Catalog (TEST FIXTURE)

| KPI | Display name | Status |
|---|---|---|
| volume_kpi | Volume KPI | PASS |
| completion_kpi | Completion rate KPI | PASS |
""",
    )
    write(
        kpis / "measure_catalog.md",
        """
# Measure Catalog (legacy combined view — TEST FIXTURE)

| Measure | Display name | Format | Status |
|---|---|---|---|
| event_count | Event count | integer | PASS |
| completed_count | Completed count | integer | PASS |
""",
    )
    write(
        kpis / "metric_catalog.md",
        """
# Metric Catalog (legacy combined view — TEST FIXTURE)

| Metric | Display name | Format | Status |
|---|---|---|---|
| completion_rate | Completion rate | percent | PASS |
""",
    )
    write(
        kpis / "data_quality_metric_catalog.md",
        """
# Data Quality Metric Catalog (TEST FIXTURE)

| Metric | Display name | Format | Status |
|---|---|---|---|
| orphan_rate | Orphan rate | percent | PASS |
| null_key_rate | Null key rate | percent | PASS |
""",
    )
    write(
        kpis / "pipeline_health_metric_catalog.md",
        """
# Pipeline Health Metric Catalog (TEST FIXTURE)

| Metric | Display name | Format | Status |
|---|---|---|---|
| build_success_rate | Build success rate | percent | PASS |
| failed_test_count | Failed test count | integer | PASS |
""",
    )
    write(
        base / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md",
        kpi_contracts_markdown(process=process, fact=fact, volume_expected="100"),
    )
    write(
        base / "reports" / "agent" / "BUSINESS_APPROVAL_REGISTER.md",
        approval_register_markdown(process=process, fact=fact, volume_expected="100"),
    )
    write(
        base / "reports" / "agent" / "DECISION_LOG.md",
        decision_log_markdown(),
    )
    write(
        base / "reports" / "agent" / "HUMAN_ATTENTION_BOARD.md",
        attention_board_markdown(),
    )
    write(
        base / "reports" / "agent" / "METRIC_VERIFICATION_MATRIX.md",
        matrix_markdown(volume_expected="100"),
    )
    write(
        base / "reports" / "agent" / "sql_proofs" / "010_volume.sql",
        volume_sql(kpi_id="KPI-001", expected="100"),
    )
    write(
        base / "reports" / "agent" / "sql_proofs" / "020_rate.sql",
        rate_sql(kpi_id="KPI-002", expected="0.8"),
    )

    matplotlib = base / "reports" / "agent" / "10_presentation" / "matplotlib"
    write(
        base / "reports" / "agent" / "10_presentation" / "report_page_contracts.md",
        f"""
# Report Page Contracts (TEST FIXTURE)

| Page ID | Page Name | Page Class | Audience | Business Processes | Business Questions | Decisions Supported | Primary KPIs | Driver Metrics | Guardrail Metrics | Dimensions | Filters | Reporting Period | Visuals | Exceptions | Insight Narrative | Recommended Actions | Caveats | Technical Validation Status | Business Approval Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| executive_overview | Executive Overview | executive_overview | leadership | {process} | What is volume and completion? | Prioritize interventions | KPI-001, KPI-002 | KPI-002 | NOT_APPLICABLE: no DQ guardrails on executive | {', '.join(dims)} | period | Current month | visual_volume_trend, visual_completion_rate_trend, card_volume, card_completion | Open exceptions listed | Volume stable; completion on target | Act on failure spike | SYNTHETIC_FIXTURE | PASS | APPROVED |
| exceptions_and_data_quality | Exceptions and Data Quality | exceptions_quality | data engineering | {process} | Where is quality failing? | Fix pipeline issues | DQ-001 | NOT_APPLICABLE: DQ page | orphan_rate | NOT_APPLICABLE: quality page | status | All time | NOT_APPLICABLE: table view | Source/transform issues | Orphans within tolerance | Repair orphans | SYNTHETIC_FIXTURE | PASS | APPROVED |
| pipeline_health | Pipeline Health | pipeline_health | platform | {process} | Is delivery healthy? | Restore SLA | PIPE-001 | NOT_APPLICABLE: pipeline page | build_success_rate | NOT_APPLICABLE: pipeline page | run_date | Current week | NOT_APPLICABLE: status cards | Failed tests | Builds succeeding | Rerun failed models | SYNTHETIC_FIXTURE | PASS | APPROVED |
| all_measures | All Measures | metric_dictionary | analysts | {process} | Which measures exist? | Trace definitions | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | {', '.join(dims)} | NOT_APPLICABLE: no filters on dictionary | All time | measure_board | NOT_APPLICABLE: no exceptions on dictionary | Browse measures with display names | Use dictionary | SYNTHETIC_FIXTURE | PASS | APPROVED |
| all_metrics | All Metrics | metric_dictionary | analysts | {process} | Which metrics exist? | Trace definitions | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | {', '.join(dims)} | NOT_APPLICABLE: no filters on dictionary | All time | metric_board | NOT_APPLICABLE: no exceptions on dictionary | Browse metrics with display names | Use dictionary | SYNTHETIC_FIXTURE | PASS | APPROVED |
| all_dimensions | Dimensions | dimension_explorer | analysts | {process} | Which segments exist? | Understand segments | NOT_APPLICABLE: dimension browse | NOT_APPLICABLE: dimension browse | NOT_APPLICABLE: dimension browse | {', '.join(dims)} | dim filters | All time | dimension_board | NOT_APPLICABLE: no exceptions on dimension browse | Browse dimension labels | Filter reports | SYNTHETIC_FIXTURE | PASS | APPROVED |
""",
    )
    write(
        matplotlib / "kpi_figure_coverage.md",
        """
# KPI Figure Coverage (TEST FIXTURE)

| Item | Status | Proof |
|---|---|---|
| Volume KPI | RENDERED | sql_verification/010_volume.sql |
| Completion rate KPI | RENDERED | sql_verification/020_rate.sql |
| Orphan rate | RENDERED | sql_verification/030_dq.sql |
""",
    )
    write(
        matplotlib / "label_dictionary.md",
        """
# Label Dictionary (TEST FIXTURE)

| field_name | raw_code | business_label | source | confidence |
|---|---|---|---|---|
| status_code | C | Completed | seed | HIGH |
| status_code | F | Failed | seed | HIGH |
""",
    )
    write_interactive_presentation(matplotlib, volume_total=100, completion_rate=0.8)
    write(
        matplotlib / "sql_verification" / "010_volume.sql",
        """
-- purpose: volume
-- expected result: 100
-- captured result: 100
-- status: PASS
select count(*) from fct;
""",
    )
    write(
        matplotlib / "sql_verification" / "020_rate.sql",
        """
-- purpose: completion rate
-- expected result: 0.8
-- captured result: 0.8
-- status: PASS
select 0.8;
""",
    )
    write(
        matplotlib / "sql_verification" / "030_dq.sql",
        """
-- purpose: orphan rate
-- expected result: 0
-- captured result: 0
-- status: PASS
select 0;
""",
    )
    write(
        matplotlib / "sql_verification" / "_proof_index.md",
        """
# Proof Index (TEST FIXTURE)

| Proof ID | Item | Metric ID | Proof | Status |
|---|---|---|---|---|
| PROOF-010_volume | Volume KPI | KPI-001 | 010_volume.sql | PASS |
| PROOF-020_rate | Completion rate KPI | KPI-002 | 020_rate.sql | PASS |
| PROOF-030_dq | Orphan rate | DQ-001 | 030_dq.sql | PASS |
""",
    )
    write(
        base / "reports" / "agent" / "10_presentation" / "presentation_report.md",
        """
# Presentation Report (TEST FIXTURE)

Live SQL verification completed for RENDERED KPIs. Refresh path exercised in fixture mode.
""",
    )
    staging = [f"stg_{fact.replace('fct_', '')}"]
    intermediate = [f"int_{fact.replace('fct_', '')}_enriched"]
    write_control_plane_files(
        write,
        base,
        slug=slug,
        process=process,
        seeds=[seed_name],
        staging_models=staging,
        intermediate_models=intermediate,
        facts=[fact],
        dims=dims,
        profile_name="fixture_analytics",
        adapter="duckdb",
    )
    return base


def main() -> int:
    fixtures = [
        (
            "domain_a_transactional",
            "Transactional lifecycle",
            "fct_events",
            ["dim_entities", "dim_catalog_items", "dim_statuses"],
        ),
        (
            "domain_b_encounter",
            "Encounter lifecycle",
            "fct_encounters",
            ["dim_providers", "dim_locations", "dim_statuses"],
        ),
        (
            "domain_c_asset_events",
            "Asset event monitoring",
            "fct_asset_events",
            ["dim_assets", "dim_statuses"],
        ),
        (
            "domain_d_case_activity",
            "Case activity lifecycle",
            "fct_case_activities",
            ["dim_people", "dim_organizations", "dim_statuses"],
        ),
    ]
    for slug, process, fact, dims in fixtures:
        path = common_project(slug, process, fact, dims)
        print(f"Wrote fixture {path}")

    checks = [
        "check_analytics_coverage.py",
        "check_analytics_product_completeness.py",
        "check_fact_analytical_coverage.py",
        "check_model_classification_coverage.py",
        "check_metric_contract_completeness.py",
        "verify_metric_reconciliation.py",
        "validate_kpi_proofs.py",
        "check_human_approval_coverage.py",
        "check_time_intelligence_coverage.py",
        "check_data_observability_coverage.py",
        "check_presentation_coverage.py",
        "check_report_page_contracts.py",
        "check_report_business_readability.py",
        "check_exposure_coverage.py",
        "validate_rendered_report_content.py",
        "validate_chart_registry.py",
        "check_presentation_traceability.py",
        "validate_live_report_dom.py",
    ]
    failures = 0
    for slug, _, _, _ in fixtures:
        root = FIX / slug
        for script in checks:
            cmd = [sys.executable, str(SCRIPTS / script), "--root", str(root)]
            if script == "validate_live_report_dom.py":
                cmd.append("--allow-skip")
            proc = subprocess.run(cmd, cwd=str(SCRIPTS), capture_output=True, text=True)
            status = "PASS" if proc.returncode == 0 else "FAIL"
            if proc.returncode != 0:
                failures += 1
            print(f"[{status}] {slug} :: {script}")
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
