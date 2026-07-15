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


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def common_project(slug: str, process: str, fact: str, dims: list[str]) -> Path:
    base = FIX / slug
    write(
        base / "project.config.yml",
        """
project:
  name: fixture_%s
analytics_policy:
  completion_mode: process_coverage
  advisory_measure_target: null
  advisory_metric_target: null
  business_process_coverage_required: 0.9
  time_intelligence_coverage_required: 0.8
  critical_fact_coverage_required: 1.0
  model_classification_coverage_required: 1.0
"""
        % slug,
    )
    # Minimal models for classification coverage
    write(base / "models" / "gold" / f"{fact}.sql", f"-- TEST FIXTURE ONLY\nselect 1 as id\n")
    for dim in dims:
        write(base / "models" / "gold" / f"{dim}.sql", f"-- TEST FIXTURE ONLY\nselect 1 as id\n")

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
    write(
        insights / "fact_coverage_contracts.md",
        f"""
# Fact Coverage Contracts (TEST FIXTURE)

| Fact | Grain | Counting Key | Volume | Value | Status | Time | Dimensions | Quality | Reconciliation | Business Questions | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| {fact} | one row per event | event_id | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | volume and completion | PASS |
""",
    )
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
    write(
        insights / "time_intelligence_coverage.md",
        f"""
# Time Intelligence Coverage (TEST FIXTURE)

Reporting period labeling is required on KPI cards.

| Metric / KPI | Date field | Date role | Current period | Prior period | MoM/YoY | MTD/QTD/YTD | Rolling | Target/baseline | Status |
|---|---|---|---|---|---|---|---|---|---|
| Volume KPI | event_date | occurred | yes | yes | yes | yes | yes | Target not defined | PASS |
| Completion rate | event_date | completed | yes | yes | no | yes | yes | Target not defined | PASS |
""",
    )
    write(
        insights / "exposure_coverage.md",
        f"""
# Exposure Coverage (TEST FIXTURE)

| Exposure | Type | Owner | Dependent Models | Dependent Metrics | Refresh | Business Purpose | Criticality | Validation Status |
|---|---|---|---|---|---|---|---|---|
| browser_report | browser report | analytics | {fact} | Volume KPI | daily | process overview | high | PASS |
""",
    )
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
        """
# Key Performance Indicator Definition Contracts (TEST FIXTURE)

| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Unit/Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | Volume KPI | kpi | process | How many events occurred? | Capacity planning | Investigate drop | analytics | count(*) | event | event_id | event_date | occurred | all valid | test rows | status | count | integer | additive | Target not defined | increase | fct | report | proofs/vol.sql | 100 | 100 | 0 | APPROVED | PASS | Matches source |
| KPI-002 | Completion rate KPI | kpi | process | What share completed? | Process health | Review failures | analytics | completed/total | event | event_id | event_date | completed | non-cancelled | cancelled | status | ratio | percent | ratio | Target not defined | increase | fct | report | proofs/rate.sql | 0.8 | 0.8 | 0 | APPROVED | PASS | Definition approved |
""",
    )

    # Presentation readability surface
    matplotlib = base / "reports" / "agent" / "10_presentation" / "matplotlib"
    write(
        base / "reports" / "agent" / "10_presentation" / "report_page_contracts.md",
        f"""
# Report Page Contracts (TEST FIXTURE)

| Page Name | Audience | Business Purpose | Decisions Supported | Primary KPIs | Time Period | Exceptions | Recommended Actions | Status |
|---|---|---|---|---|---|---|---|---|
| Executive Overview | leadership | Summarize {process} | Prioritize interventions | Volume KPI, Completion rate KPI | Current month | Open exceptions listed | Act on failure spike | PASS |
| Exceptions and Data Quality | data engineering | Separate DQ from business KPIs | Fix pipeline issues | Orphan rate | All time | Source/transform issues | Repair orphans | PASS |
| Pipeline Health | platform | Monitor delivery | Restore SLA | Build success rate | Current week | Failed tests | Rerun failed models | PASS |
| Metric Dictionary | analysts | Explore definitions | Trace metrics | n/a | n/a | n/a | Use contracts | PASS |
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
    write(
        matplotlib / "data_access.py",
        """
# TEST FIXTURE ONLY — illustrates required board payload shape
MEASURE_BOARD = [
    {"id": "event_count", "display_name": "Event count", "value": 100, "formatted_value": "100", "group": "Volume", "format": "integer"},
]
METRIC_BOARD = [
    {"id": "completion_rate", "display_name": "Completion rate", "value": 0.8, "formatted_value": "80.0%", "group": "Performance", "format": "percent"},
]

def format_value(value, fmt):
    if fmt == "percent":
        return f"{value * 100:.1f}%"
    return str(value)
""",
    )
    write(
        matplotlib / "report_builder.py",
        """
# TEST FIXTURE ONLY
TABS = ["Executive Overview", "Exceptions and Data Quality", "Pipeline Health", "All Measures", "All Metrics", "Dimensions"]
""",
    )
    write(
        matplotlib / "report.html",
        """
<html><body>
<h1>Executive Overview</h1>
<table><tr><th>Display name</th><th>Formatted value</th></tr>
<tr><td>Event count</td><td>100</td></tr>
<tr><td>Completion rate</td><td>80.0%</td></tr>
</table>
<section id="dimensions"><h2>Dimensions</h2><table><tr><th>Status</th></tr><tr><td>Completed</td></tr></table></section>
<section id="quality"><h2>Data Quality</h2></section>
<section id="pipeline"><h2>Pipeline Health</h2></section>
</body></html>
""",
    )
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

| Item | Proof | Status |
|---|---|---|
| Volume KPI measure | 010_volume.sql | PASS |
| Completion rate metric | 020_rate.sql | PASS |
| Orphan rate | 030_dq.sql | PASS |
""",
    )
    write(
        base / "reports" / "agent" / "10_presentation" / "presentation_report.md",
        """
# Presentation Report (TEST FIXTURE)

Live SQL verification completed for RENDERED KPIs. Refresh path exercised in fixture mode.
""",
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

    # Run validators against each fixture
    checks = [
        "check_analytics_coverage.py",
        "check_analytics_product_completeness.py",
        "check_fact_analytical_coverage.py",
        "check_model_classification_coverage.py",
        "check_metric_contract_completeness.py",
        "check_time_intelligence_coverage.py",
        "check_data_observability_coverage.py",
        "check_presentation_coverage.py",
        "check_report_page_contracts.py",
        "check_report_business_readability.py",
        "check_exposure_coverage.py",
    ]
    failures = 0
    for slug, _, _, _ in fixtures:
        root = FIX / slug
        for script in checks:
            cmd = [sys.executable, str(SCRIPTS / script), "--root", str(root)]
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
