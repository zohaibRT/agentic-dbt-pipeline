#!/usr/bin/env python3
"""Build four runnable DuckDB dbt fixtures and run gate validators.

Each fixture is a small dbt project with seeds, staging, intermediate, and gold
models plus minimal reports/agent control files for analytics validators.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "dbt_duckdb"
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
from build_analytics_fixtures import (  # noqa: E402
    observability_coverage_table,
    time_intelligence_table,
    write,
)
from fixture_kpi_contracts import (  # noqa: E402
    approval_register_markdown,
    attention_board_markdown,
    decision_log_markdown,
    kpi_contracts_markdown,
    matrix_markdown,
    rate_sql,
    volume_sql,
)
from lib_fixture_control_plane import write_control_plane_files  # noqa: E402
from lib_gate_common import REQUIRED_OBSERVABILITY_DOMAINS  # noqa: E402
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


def write_dbt_project(base: Path, slug: str) -> None:
    write(
        base / "dbt_project.yml",
        f"""
name: {slug}
version: '1.0.0'
config-version: 2
profile: fixture_duckdb
model-paths: ["models"]
seed-paths: ["seeds"]
snapshot-paths: ["snapshots"]
target-path: target
clean-targets:
  - target
  - dbt_packages
seeds:
  +schema: main
snapshots:
  {slug}:
    +target_schema: snapshots
models:
  {slug}:
    staging:
      +materialized: view
    intermediate:
      +materialized: view
    gold:
      +materialized: table
""",
    )
    write(
        base / "profiles.yml",
        """
fixture_duckdb:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "./target/fixture.duckdb"
      schema: main
""",
    )


def write_sources(base: Path, seed_names: list[str]) -> None:
    tables = "\n".join(
        f"      - name: {name}\n        description: TEST FIXTURE seed table" for name in seed_names
    )
    write(
        base / "models" / "sources" / "raw.yml",
        f"""
version: 2
sources:
  - name: raw
    description: TEST FIXTURE raw source tables (loaded from seeds)
    schema: main
    tables:
{tables}
""",
    )


def write_schema_tests(base: Path, facts: list[str], dims: list[str]) -> None:
    dim_keys = {
        "dim_entities": "entity_id",
        "dim_catalog_items": "item_id",
        "dim_statuses": "status_code",
        "dim_providers": "provider_id",
        "dim_locations": "location_id",
        "dim_assets": "asset_id",
        "dim_people": "person_id",
        "dim_organizations": "organization_id",
    }
    model_blocks = []
    for fact in facts:
        model_blocks.append(
            f"""
  - name: {fact}
    description: TEST FIXTURE fact model
    columns:
      - name: event_id
        tests: [not_null, unique]
"""
        )
    for dim in dims:
        key = dim_keys.get(dim, f"{dim.replace('dim_', '')}_id")
        model_blocks.append(
            f"""
  - name: {dim}
    description: TEST FIXTURE dimension model
    columns:
      - name: {key}
        tests: [not_null, unique]
"""
        )
    write(
        base / "models" / "gold" / "schema.yml",
        f"""
version: 2
models:
{"".join(model_blocks)}
""",
    )


def write_exposures(base: Path, facts: list[str], process: str) -> None:
    deps = "\n".join(f"      - ref('{fact}')" for fact in facts)
    write(
        base / "models" / "exposures.yml",
        f"""
version: 2
exposures:
  - name: browser_report
    type: dashboard
    maturity: high
    label: Browser Report
    description: "TEST FIXTURE browser report for {process} | purpose: {process} overview for analysts | criticality: high | refresh: daily | audience: analysts | approval: APPROVED | evidence: SYNTHETIC_FIXTURE_APPROVAL:exposure_coverage#browser_report"
    depends_on:
{deps}
    owner:
      name: fixture-owner
      email: fixture-owner@example.test
""",
    )


def stamp_manifest_identities(base: Path) -> None:
    """Rewrite classification/fact/exposure docs with manifest unique_ids after dbt parse."""
    from lib_gate_common import (  # noqa: WPS433
        build_resource_inventory,
        compute_exposure_fingerprint,
    )

    inventory, source = build_resource_inventory(base)
    if source != "manifest":
        return
    models = [r for r in inventory if r.get("resource_type") == "model" and r.get("enabled") is not False]
    sources = [r for r in inventory if r.get("resource_type") == "source"]
    seeds = [r for r in inventory if r.get("resource_type") == "seed"]
    snapshots = [r for r in inventory if r.get("resource_type") == "snapshot"]
    exposures = [r for r in inventory if r.get("resource_type") == "exposure"]

    insights = base / "reports" / "agent" / "09_analytics_insights"
    class_rows: list[str] = [
        "| Unique ID | Model | Package | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Human Approval Status | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for resource in models:
        name = str(resource.get("name"))
        uid = str(resource.get("unique_id"))
        package = str(resource.get("package_name") or "")
        path = str(resource.get("original_file_path") or "")
        if "stg_" in name or "/staging" in path or "bronze" in path:
            klass = "staging"
            meaning = "cleaned source-aligned layer"
        elif "int_" in name or "intermediate" in path or "silver" in path:
            klass = "intermediate"
            meaning = "enriched business logic layer"
        elif name.startswith("dim_") or "dimension" in path:
            klass = "dimension"
            meaning = "descriptive entity"
        else:
            klass = "event_fact"
            meaning = "primary measurable event"
        class_rows.append(
            f"| {uid} | {name} | {package} | {klass} | {meaning} | event | event_id | event_date | "
            f"count | n/a | not_null | PASS | table | HIGH | APPROVED | PASS |"
        )
    for resource in sources:
        class_rows.append(
            f"| {resource.get('unique_id')} | {resource.get('name')} | {resource.get('package_name')} | "
            f"source | inventoried source | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |"
        )
    for resource in seeds:
        class_rows.append(
            f"| {resource.get('unique_id')} | {resource.get('name')} | {resource.get('package_name')} | "
            f"seed | inventoried seed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |"
        )
    for resource in snapshots:
        class_rows.append(
            f"| {resource.get('unique_id')} | {resource.get('name')} | {resource.get('package_name')} | "
            f"snapshot | SCD snapshot resource | entity | id | updated_at | n/a | n/a | n/a | n/a | table | HIGH | APPROVED | PASS |"
        )
    for resource in exposures:
        class_rows.append(
            f"| {resource.get('unique_id')} | {resource.get('name')} | {resource.get('package_name')} | "
            f"exposure | production presentation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | HIGH | APPROVED | PASS |"
        )

    write(
        insights / "model_classification.md",
        "# Model Classification (TEST FIXTURE — unique_id stamped after dbt parse)\n\n"
        + "\n".join(class_rows)
        + "\n",
    )

    fact_models = [
        r
        for r in models
        if str(r.get("name", "")).startswith("fct_") or str(r.get("name")) == "activity_events"
    ]
    fact_lines = [
        "| Fact ID | Unique ID | Resource Name | Package Name | Version | Fact Class | Business Process | Grain | Status |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for resource in fact_models:
        fact_lines.append(
            f"| {resource.get('name')} | {resource.get('unique_id')} | {resource.get('name')} | "
            f"{resource.get('package_name')} |  | event_fact | fixture process | event | PASS |"
        )
    write(insights / "fact_catalog.md", "# Fact Catalog (TEST FIXTURE)\n\n" + "\n".join(fact_lines) + "\n")

    contracts = insights / "fact_coverage_contracts.md"
    if contracts.exists() and fact_models:
        contract_lines = [
            "| Unique ID | Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for resource in fact_models:
            name = resource.get("name")
            contract_lines.append(
                f"| {resource.get('unique_id')} | {name} | one row per event | event_id | event_date | "
                f"SUPPORTED: sql_proofs/{name}_volume.sql | "
                f"SUPPORTED: sql_proofs/{name}_amount.sql | "
                f"NOT_APPLICABLE: no duration measures at this grain | "
                f"SUPPORTED: sql_proofs/{name}_status.sql | "
                f"SUPPORTED: sql_proofs/{name}_lifecycle.sql | "
                f"SUPPORTED: sql_proofs/{name}_dims.sql | "
                f"SUPPORTED: sql_proofs/{name}_trends.sql | "
                f"SUPPORTED: sql_proofs/{name}_period.sql | "
                f"SUPPORTED: sql_proofs/{name}_quality.sql | "
                f"SUPPORTED: sql_proofs/{name}_exceptions.sql | "
                f"NOT_APPLICABLE: aging not in first-pass scope | "
                f"SUPPORTED: sql_proofs/{name}_recon.sql | "
                f"volume and completion | Fixture notes | PASS |"
            )
        write(contracts, "# Fact Coverage Contracts (TEST FIXTURE)\n\n" + "\n".join(contract_lines) + "\n")

    if exposures:
        exp = exposures[0]
        deps = list(exp.get("depends_on_nodes") or [])
        meta = exp.get("meta") if isinstance(exp.get("meta"), dict) else {}
        purpose = str(meta.get("business_purpose") or "overview for analysts")
        audience = str(meta.get("audience") or "analysts")
        criticality = str(meta.get("criticality") or "high")
        refresh = str(meta.get("refresh_expectation") or "daily")
        sensitive = str(meta.get("sensitive_data_classification") or "")
        evidence = "SYNTHETIC_FIXTURE_APPROVAL:exposure_coverage#browser_report"
        fp = compute_exposure_fingerprint(
            {
                "type": exp.get("type") or "dashboard",
                "business_purpose": purpose,
                "audience": audience,
                "depends_on_models": deps,
                "depends_on_sources": [],
                "depends_on_metrics": "",
                "url": "",
                "delivery_location": "",
                "refresh_expectation": refresh,
                "criticality": criticality,
                "sensitive_data_classification": sensitive,
            }
        )
        write(
            insights / "exposure_coverage.md",
            f"""
# Exposure Coverage (TEST FIXTURE — SYNTHETIC approval evidence)

| Exposure ID | Unique ID | Exposure | Type | Owner | Approver | Dependent Models | Dependent Metrics | Refresh Expectation | Business Purpose | Audience | Criticality | Technical Validation Status | Business Approval Status | Approval Evidence | Exposure Fingerprint | Validation Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-browser_report | {exp.get('unique_id')} | browser_report | dashboard | fixture-owner | fixture-approver | {', '.join(deps)} | Volume KPI | {refresh} | {purpose} | {audience} | {criticality} | PASS | APPROVED | {evidence} | {fp} | PASS |
""",
        )


def write_agent_reports(
    base: Path,
    slug: str,
    process: str,
    facts: list[str],
    dims: list[str],
    staging_models: list[str],
    intermediate_models: list[str],
    seeds: list[str],
) -> None:
    primary_fact = facts[0]
    fact_list = ", ".join(facts)
    dim_list = ", ".join(dims)

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
resource_classification_policy:
  require_enabled_local_models: true
  require_sources: true
  require_seeds: true
  require_snapshots: true
  require_semantic_models: true
  require_metrics: true
  require_exposures: true
  require_tests_individually: false
  require_dependency_package_models: false
  local_resource_coverage_required: 1.0
  production_resource_coverage_required: 1.0
acceptance_policy:
  final_fail_on_warning: true
  require_explicit_warning_acceptance: true
""",
    )

    insights = base / "reports" / "agent" / "09_analytics_insights"
    kpis = insights / "kpis"

    classification_rows = []
    for model in staging_models:
        classification_rows.append(
            f"| {model} | staging | cleaned source-aligned layer | source | source_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |"
        )
    for model in intermediate_models:
        classification_rows.append(
            f"| {model} | intermediate | enriched business logic layer | logic | logic_id | n/a | n/a | n/a | not_null | n/a | view | HIGH | PASS |"
        )
    for fact in facts:
        classification_rows.append(
            f"| {fact} | fact/event | primary measurable event | event | event_id | event_date | count, amount | {dim_list} | not_null | PASS | table | HIGH | PASS |"
        )
    for dim in dims:
        classification_rows.append(
            f"| {dim} | dimension | descriptive entity | entity | entity_id | n/a | n/a | self | unique | n/a | table | HIGH | PASS |"
        )

    fact_contract_rows = []
    fact_catalog_rows = []
    for fact in facts:
        fact_contract_rows.append(
            f"| {fact} | one row per event | event_id | event_date | "
            f"SUPPORTED: sql_proofs/{fact}_volume.sql | "
            f"SUPPORTED: sql_proofs/{fact}_amount.sql | "
            f"NOT_APPLICABLE: no duration measures at this grain | "
            f"SUPPORTED: sql_proofs/{fact}_status.sql | "
            f"SUPPORTED: sql_proofs/{fact}_lifecycle.sql | "
            f"SUPPORTED: sql_proofs/{fact}_dims.sql | "
            f"SUPPORTED: sql_proofs/{fact}_trends.sql | "
            f"SUPPORTED: sql_proofs/{fact}_period.sql | "
            f"SUPPORTED: sql_proofs/{fact}_quality.sql | "
            f"SUPPORTED: sql_proofs/{fact}_exceptions.sql | "
            f"NOT_APPLICABLE: aging not in first-pass scope | "
            f"SUPPORTED: sql_proofs/{fact}_recon.sql | "
            f"volume and completion | Fixture notes | PASS |"
        )
        fact_catalog_rows.append(f"| {fact} | event | PASS |")

    write(
        insights / "business_process_catalog.md",
        f"""
# Business Process Catalog (TEST FIXTURE — illustrative only)

| Process | Event | Grain | Status Fields | Dates | Dimensions | Business Questions | Confidence | Approval | Status |
|---|---|---|---|---|---|---|---|---|---|
| {process} | primary event | one row per event | status | event_date | {dim_list} | What is volume and completion rate? | HIGH | APPROVED | PASS |
""",
    )
    write(
        insights / "analytics_coverage_matrix.md",
        f"""
# Analytics Coverage Matrix (TEST FIXTURE)

| Business Process | Fact/Event Models | Dimensions | Grain Proven | Measures | Contextual Metrics | Strategic KPIs | Time Intelligence | Segmentation | Exceptions | Data Quality | Reconciliation | Report Page | Owner/Approval | Status | Missing Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {process} | {fact_list} | {dim_list} | yes | 6 | 4 | 2 | current+prior | yes | yes | yes | yes | Executive Overview | owner | PASS | none |
""",
    )
    write(
        insights / "fact_coverage_contracts.md",
        f"""
# Fact Coverage Contracts (TEST FIXTURE)

| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(fact_contract_rows)}
""",
    )
    write(
        insights / "model_classification.md",
        f"""
# Model Classification (TEST FIXTURE)

| Model | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(classification_rows)}
""",
    )
    write(insights / "time_intelligence_coverage.md", time_intelligence_table())
    write(
        insights / "exposure_coverage.md",
        f"""
# Exposure Coverage (TEST FIXTURE)

| Exposure | Type | Owner | Dependent Models | Dependent Metrics | Refresh | Business Purpose | Criticality | Validation Status |
|---|---|---|---|---|---|---|---|---|
| browser_report | browser report | analytics | {primary_fact} | Volume KPI | daily | {process} overview | high | PASS |
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
{chr(10).join(fact_catalog_rows)}
""",
    )
    write(
        insights / "dimension_catalog.md",
        f"""
# Dimension Catalog (TEST FIXTURE)

| Dimension | Grain | Status |
|---|---|---|
{chr(10).join(f"| {dim} | entity | PASS |" for dim in dims)}
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
        kpi_contracts_markdown(process=process, fact=primary_fact, volume_expected="5"),
    )
    write(
        base / "reports" / "agent" / "BUSINESS_APPROVAL_REGISTER.md",
        approval_register_markdown(process=process, fact=primary_fact, volume_expected="5"),
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
        matrix_markdown(volume_expected="5"),
    )
    write(
        base / "reports" / "agent" / "sql_proofs" / "010_volume.sql",
        f"""
-- purpose: volume KPI proof for KPI-001
-- kpi_id: KPI-001
-- validation_type: numeric_tolerance
-- expected result: 5
-- captured result: 5
-- tolerance: 0
-- technical_verification_status: PASS
-- status: PASS
select count(*) as volume from {{{{ ref('{primary_fact}') }}}};
""",
    )
    write(
        base / "reports" / "agent" / "sql_proofs" / "020_rate.sql",
        f"""
-- purpose: rate KPI proof for KPI-002
-- kpi_id: KPI-002
-- validation_type: ratio_tolerance
-- expected result: 0.4
-- captured result: 0.4
-- tolerance: 0
-- technical_verification_status: PASS
-- status: PASS
select 0.4 as rate;
""",
    )

    matplotlib = base / "reports" / "agent" / "10_presentation" / "matplotlib"
    write(
        base / "reports" / "agent" / "10_presentation" / "report_page_contracts.md",
        f"""
# Report Page Contracts (TEST FIXTURE)

| Page ID | Page Name | Page Class | Audience | Business Processes | Business Questions | Decisions Supported | Primary KPIs | Driver Metrics | Guardrail Metrics | Dimensions | Filters | Reporting Period | Visuals | Exceptions | Insight Narrative | Recommended Actions | Caveats | Technical Validation Status | Business Approval Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| executive_overview | Executive Overview | executive_overview | leadership | {process} | What is volume and completion? | Prioritize interventions | KPI-001, KPI-002 | KPI-002 | NOT_APPLICABLE: no DQ guardrails on executive | {dim_list} | period | Current month | visual_volume_trend, visual_completion_rate_trend, card_volume, card_completion | Open exceptions listed | Volume stable; completion on target | Act on failure spike | SYNTHETIC_FIXTURE | PASS | APPROVED |
| exceptions_and_data_quality | Exceptions and Data Quality | exceptions_quality | data engineering | {process} | Where is quality failing? | Fix pipeline issues | DQ-001 | NOT_APPLICABLE: DQ page | orphan_rate | NOT_APPLICABLE: quality page | status | All time | NOT_APPLICABLE: table view | Source/transform issues | Orphans within tolerance | Repair orphans | SYNTHETIC_FIXTURE | PASS | APPROVED |
| pipeline_health | Pipeline Health | pipeline_health | platform | {process} | Is delivery healthy? | Restore SLA | PIPE-001 | NOT_APPLICABLE: pipeline page | build_success_rate | NOT_APPLICABLE: pipeline page | run_date | Current week | NOT_APPLICABLE: status cards | Failed tests | Builds succeeding | Rerun failed models | SYNTHETIC_FIXTURE | PASS | APPROVED |
| all_measures | All Measures | metric_dictionary | analysts | {process} | Which measures exist? | Trace definitions | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | {dim_list} | NOT_APPLICABLE: no filters on dictionary | All time | measure_board | NOT_APPLICABLE: no exceptions on dictionary | Browse measures with display names | Use dictionary | SYNTHETIC_FIXTURE | PASS | APPROVED |
| all_metrics | All Metrics | metric_dictionary | analysts | {process} | Which metrics exist? | Trace definitions | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | NOT_APPLICABLE: dictionary browse | {dim_list} | NOT_APPLICABLE: no filters on dictionary | All time | metric_board | NOT_APPLICABLE: no exceptions on dictionary | Browse metrics with display names | Use dictionary | SYNTHETIC_FIXTURE | PASS | APPROVED |
| all_dimensions | Dimensions | dimension_explorer | analysts | {process} | Which segments exist? | Understand segments | NOT_APPLICABLE: dimension browse | NOT_APPLICABLE: dimension browse | NOT_APPLICABLE: dimension browse | {dim_list} | dim filters | All time | dimension_board | NOT_APPLICABLE: no exceptions on dimension browse | Browse dimension labels | Filter reports | SYNTHETIC_FIXTURE | PASS | APPROVED |
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
| status_code | O | Open | seed | HIGH |
| status_code | C | Closed | seed | HIGH |
""",
    )
    write_interactive_presentation(
        matplotlib,
        volume_total=5,
        completion_rate=0.4,
        source_resource_id=f"model.{slug}.{primary_fact}",
    )
    write(
        matplotlib / "sql_verification" / "010_volume.sql",
        """
-- purpose: volume
-- expected result: 5
-- captured result: 5
-- status: PASS
select count(*) from main.""" + primary_fact + """;
""",
    )
    write(
        matplotlib / "sql_verification" / "020_rate.sql",
        """
-- purpose: completion rate
-- expected result: 0.4
-- captured result: 0.4
-- status: PASS
select 0.4;
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
    write_control_plane_files(
        write,
        base,
        slug=slug,
        process=process,
        seeds=seeds,
        staging_models=staging_models,
        intermediate_models=intermediate_models,
        facts=facts,
        dims=dims,
    )


def write_domain_a(base: Path) -> None:
    write(base / "seeds" / "raw_statuses.csv", "status_code,status_name\nO,Open\nC,Closed\n")
    write(
        base / "seeds" / "raw_entities.csv",
        "entity_id,entity_name\nE1,Entity One\nE2,Entity Two\nE3,Entity Three\n",
    )
    write(
        base / "seeds" / "raw_catalog_items.csv",
        "item_id,item_name\nI1,Item Alpha\nI2,Item Beta\n",
    )
    write(
        base / "seeds" / "raw_events.csv",
        "event_id,entity_id,item_id,status_code,event_date,amount\n"
        "1,E1,I1,O,2024-01-01,100.50\n"
        "2,E1,I1,C,2024-01-02,200.00\n"
        "3,E2,I2,O,2024-01-03,50.25\n"
        "4,E2,I2,C,2024-01-04,75.00\n"
        "5,E3,I1,O,2024-01-05,10.00\n",
    )
    write(
        base / "models" / "staging" / "stg_statuses.sql",
        "select status_code, status_name from {{ ref('raw_statuses') }}",
    )
    write(
        base / "models" / "staging" / "stg_entities.sql",
        "select entity_id, entity_name from {{ ref('raw_entities') }}",
    )
    write(
        base / "models" / "staging" / "stg_catalog_items.sql",
        "select item_id, item_name from {{ ref('raw_catalog_items') }}",
    )
    write(
        base / "models" / "staging" / "stg_events.sql",
        """
select
    event_id,
    entity_id,
    item_id,
    status_code,
    cast(event_date as date) as event_date,
    cast(amount as double) as amount
from {{ ref('raw_events') }}
""",
    )
    write(
        base / "models" / "intermediate" / "int_events_enriched.sql",
        """
select
    e.event_id,
    e.entity_id,
    e.item_id,
    e.status_code,
    s.status_name,
    e.event_date,
    e.amount
from {{ ref('stg_events') }} e
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
""",
    )
    write(
        base / "models" / "gold" / "fct_events.sql",
        """
select
    event_id,
    entity_id,
    item_id,
    status_code,
    status_name,
    event_date,
    amount,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_events_enriched') }}
""",
    )
    write(
        base / "models" / "gold" / "dim_entities.sql",
        "select entity_id, entity_name from {{ ref('stg_entities') }}",
    )
    write(
        base / "models" / "gold" / "dim_catalog_items.sql",
        "select item_id, item_name from {{ ref('stg_catalog_items') }}",
    )
    write(
        base / "models" / "gold" / "dim_statuses.sql",
        "select status_code, status_name from {{ ref('stg_statuses') }}",
    )


def write_domain_b(base: Path) -> None:
    write(base / "seeds" / "raw_statuses.csv", "status_code,status_name\nO,Open\nC,Closed\n")
    write(
        base / "seeds" / "raw_providers.csv",
        "provider_id,provider_name\nP1,Provider One\nP2,Provider Two\n",
    )
    write(
        base / "seeds" / "raw_locations.csv",
        "location_id,location_name\nL1,Location Alpha\nL2,Location Beta\n",
    )
    write(
        base / "seeds" / "raw_encounters.csv",
        "encounter_id,provider_id,location_id,status_code,encounter_date\n"
        "1,P1,L1,O,2024-02-01\n"
        "2,P1,L2,C,2024-02-02\n"
        "3,P2,L1,O,2024-02-03\n"
        "4,P2,L2,C,2024-02-04\n"
        "5,P1,L1,O,2024-02-05\n",
    )
    write(
        base / "seeds" / "raw_activities.csv",
        "activity_id,encounter_id,provider_id,location_id,activity_type,activity_date\n"
        "1,1,P1,L1,check-in,2024-02-01\n"
        "2,1,P1,L1,review,2024-02-01\n"
        "3,2,P1,L2,check-out,2024-02-02\n"
        "4,3,P2,L1,check-in,2024-02-03\n"
        "5,4,P2,L2,review,2024-02-04\n",
    )
    write(
        base / "models" / "staging" / "stg_statuses.sql",
        "select status_code, status_name from {{ ref('raw_statuses') }}",
    )
    write(
        base / "models" / "staging" / "stg_providers.sql",
        "select provider_id, provider_name from {{ ref('raw_providers') }}",
    )
    write(
        base / "models" / "staging" / "stg_locations.sql",
        "select location_id, location_name from {{ ref('raw_locations') }}",
    )
    write(
        base / "models" / "staging" / "stg_encounters.sql",
        """
select
    encounter_id,
    provider_id,
    location_id,
    status_code,
    cast(encounter_date as date) as encounter_date
from {{ ref('raw_encounters') }}
""",
    )
    write(
        base / "models" / "staging" / "stg_activities.sql",
        """
select
    activity_id,
    encounter_id,
    provider_id,
    location_id,
    activity_type,
    cast(activity_date as date) as activity_date
from {{ ref('raw_activities') }}
""",
    )
    write(
        base / "models" / "intermediate" / "int_encounters_enriched.sql",
        """
select
    e.encounter_id,
    e.provider_id,
    e.location_id,
    e.status_code,
    s.status_name,
    e.encounter_date
from {{ ref('stg_encounters') }} e
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
""",
    )
    write(
        base / "models" / "intermediate" / "int_activities_enriched.sql",
        """
select
    a.activity_id,
    a.encounter_id,
    a.provider_id,
    a.location_id,
    a.activity_type,
    a.activity_date,
    s.status_name
from {{ ref('stg_activities') }} a
left join {{ ref('stg_encounters') }} e on a.encounter_id = e.encounter_id
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
""",
    )
    write(
        base / "models" / "gold" / "fct_encounters.sql",
        """
select
    encounter_id as event_id,
    provider_id,
    location_id,
    status_code,
    status_name,
    encounter_date as event_date,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_encounters_enriched') }}
""",
    )
    write(
        base / "models" / "gold" / "activity_events.sql",
        """
select
    activity_id as event_id,
    encounter_id,
    provider_id,
    location_id,
    activity_type,
    activity_date as event_date
from {{ ref('int_activities_enriched') }}
""",
    )
    write(
        base / "models" / "gold" / "dim_providers.sql",
        "select provider_id, provider_name from {{ ref('stg_providers') }}",
    )
    write(
        base / "models" / "gold" / "dim_locations.sql",
        "select location_id, location_name from {{ ref('stg_locations') }}",
    )
    write(
        base / "models" / "gold" / "dim_statuses.sql",
        "select status_code, status_name from {{ ref('stg_statuses') }}",
    )
    # Remove legacy same-named snapshot that collides with gold model refs under dbt-fusion.
    legacy_snap = base / "snapshots" / "activity_events.sql"
    if legacy_snap.exists():
        legacy_snap.unlink()
    # Snapshot resource for SCD coverage (distinct name — same-name collisions are proven in unit tests).
    write(
        base / "snapshots" / "activity_events_scd.sql",
        """
{% snapshot activity_events_scd %}
{{
  config(
    target_schema='snapshots',
    unique_key='activity_id',
    strategy='check',
    check_cols=['activity_type', 'activity_date']
  )
}}
select
    activity_id,
    encounter_id,
    activity_type,
    activity_date
from {{ ref('stg_activities') }}
{% endsnapshot %}
""",
    )


def write_domain_c(base: Path) -> None:
    write(base / "seeds" / "raw_statuses.csv", "status_code,status_name\nO,Open\nC,Closed\n")
    write(
        base / "seeds" / "raw_assets.csv",
        "asset_id,asset_name\nA1,Asset One\nA2,Asset Two\n",
    )
    write(
        base / "seeds" / "raw_asset_events.csv",
        "event_id,asset_id,status_code,event_date,signal_value\n"
        "1,A1,O,2024-03-01,10.1\n"
        "2,A1,C,2024-03-02,20.2\n"
        "3,A2,O,2024-03-03,5.5\n"
        "4,A2,C,2024-03-04,8.8\n"
        "5,A1,O,2024-03-05,1.1\n",
    )
    write(
        base / "models" / "staging" / "stg_statuses.sql",
        "select status_code, status_name from {{ ref('raw_statuses') }}",
    )
    write(
        base / "models" / "staging" / "stg_assets.sql",
        "select asset_id, asset_name from {{ ref('raw_assets') }}",
    )
    write(
        base / "models" / "staging" / "stg_asset_events.sql",
        """
select
    event_id,
    asset_id,
    status_code,
    cast(event_date as date) as event_date,
    cast(signal_value as double) as signal_value
from {{ ref('raw_asset_events') }}
""",
    )
    write(
        base / "models" / "intermediate" / "int_asset_events_enriched.sql",
        """
select
    e.event_id,
    e.asset_id,
    e.status_code,
    s.status_name,
    e.event_date,
    e.signal_value
from {{ ref('stg_asset_events') }} e
left join {{ ref('stg_statuses') }} s on e.status_code = s.status_code
""",
    )
    write(
        base / "models" / "gold" / "fct_asset_events.sql",
        """
select
    event_id,
    asset_id,
    status_code,
    status_name,
    event_date,
    signal_value,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_asset_events_enriched') }}
""",
    )
    write(
        base / "models" / "gold" / "dim_assets.sql",
        "select asset_id, asset_name from {{ ref('stg_assets') }}",
    )
    write(
        base / "models" / "gold" / "dim_statuses.sql",
        "select status_code, status_name from {{ ref('stg_statuses') }}",
    )


def write_domain_d(base: Path) -> None:
    write(base / "seeds" / "raw_statuses.csv", "status_code,status_name\nO,Open\nC,Closed\n")
    write(
        base / "seeds" / "raw_people.csv",
        "person_id,person_name\nN1,Person One\nN2,Person Two\n",
    )
    write(
        base / "seeds" / "raw_organizations.csv",
        "organization_id,organization_name\nO1,Org Alpha\nO2,Org Beta\n",
    )
    write(
        base / "seeds" / "raw_case_activities.csv",
        "activity_id,person_id,organization_id,status_code,activity_date,amount\n"
        "1,N1,O1,O,2024-04-01,100\n"
        "2,N1,O1,C,2024-04-02,200\n"
        "3,N2,O2,O,2024-04-03,50\n"
        "4,N2,O2,C,2024-04-04,75\n"
        "5,N1,O2,O,2024-04-05,10\n",
    )
    write(
        base / "models" / "staging" / "stg_statuses.sql",
        "select status_code, status_name from {{ ref('raw_statuses') }}",
    )
    write(
        base / "models" / "staging" / "stg_people.sql",
        "select person_id, person_name from {{ ref('raw_people') }}",
    )
    write(
        base / "models" / "staging" / "stg_organizations.sql",
        "select organization_id, organization_name from {{ ref('raw_organizations') }}",
    )
    write(
        base / "models" / "staging" / "stg_case_activities.sql",
        """
select
    activity_id,
    person_id,
    organization_id,
    status_code,
    cast(activity_date as date) as activity_date,
    cast(amount as double) as amount
from {{ ref('raw_case_activities') }}
""",
    )
    write(
        base / "models" / "intermediate" / "int_case_activities_enriched.sql",
        """
select
    a.activity_id,
    a.person_id,
    a.organization_id,
    a.status_code,
    s.status_name,
    a.activity_date,
    a.amount
from {{ ref('stg_case_activities') }} a
left join {{ ref('stg_statuses') }} s on a.status_code = s.status_code
""",
    )
    write(
        base / "models" / "gold" / "fct_case_activities.sql",
        """
select
    activity_id as event_id,
    person_id,
    organization_id,
    status_code,
    status_name,
    activity_date as event_date,
    amount,
    case when status_code = 'C' then 1 else 0 end as is_completed
from {{ ref('int_case_activities_enriched') }}
""",
    )
    write(
        base / "models" / "gold" / "dim_people.sql",
        "select person_id, person_name from {{ ref('stg_people') }}",
    )
    write(
        base / "models" / "gold" / "dim_organizations.sql",
        "select organization_id, organization_name from {{ ref('stg_organizations') }}",
    )
    write(
        base / "models" / "gold" / "dim_statuses.sql",
        "select status_code, status_name from {{ ref('stg_statuses') }}",
    )


DOMAINS = [
    {
        "slug": "domain_a_transactional",
        "process": "Transactional lifecycle",
        "facts": ["fct_events"],
        "dims": ["dim_entities", "dim_catalog_items", "dim_statuses"],
        "staging": ["stg_statuses", "stg_entities", "stg_catalog_items", "stg_events"],
        "intermediate": ["int_events_enriched"],
        "seeds": ["raw_statuses", "raw_entities", "raw_catalog_items", "raw_events"],
        "writer": write_domain_a,
    },
    {
        "slug": "domain_b_encounter",
        "process": "Encounter lifecycle",
        "facts": ["fct_encounters", "activity_events"],
        "dims": ["dim_providers", "dim_locations", "dim_statuses"],
        "staging": ["stg_statuses", "stg_providers", "stg_locations", "stg_encounters", "stg_activities"],
        "intermediate": ["int_encounters_enriched", "int_activities_enriched"],
        "seeds": ["raw_statuses", "raw_providers", "raw_locations", "raw_encounters", "raw_activities"],
        "writer": write_domain_b,
    },
    {
        "slug": "domain_c_asset_events",
        "process": "Asset event monitoring",
        "facts": ["fct_asset_events"],
        "dims": ["dim_assets", "dim_statuses"],
        "staging": ["stg_statuses", "stg_assets", "stg_asset_events"],
        "intermediate": ["int_asset_events_enriched"],
        "seeds": ["raw_statuses", "raw_assets", "raw_asset_events"],
        "writer": write_domain_c,
    },
    {
        "slug": "domain_d_case_activity",
        "process": "Case activity lifecycle",
        "facts": ["fct_case_activities"],
        "dims": ["dim_people", "dim_organizations", "dim_statuses"],
        "staging": ["stg_statuses", "stg_people", "stg_organizations", "stg_case_activities"],
        "intermediate": ["int_case_activities_enriched"],
        "seeds": ["raw_statuses", "raw_people", "raw_organizations", "raw_case_activities"],
        "writer": write_domain_d,
    },
]


def run_dbt(project_dir: Path) -> tuple[bool, str]:
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(project_dir)
    commands = [
        ["dbt", "parse", "--no-partial-parse", "--project-dir", str(project_dir)],
        ["dbt", "seed", "--project-dir", str(project_dir)],
        ["dbt", "build", "--project-dir", str(project_dir)],
    ]
    output_parts: list[str] = []
    for command in commands:
        proc = subprocess.run(
            command,
            cwd=str(project_dir),
            env=env,
            capture_output=True,
            text=True,
        )
        output_parts.append(f"$ {' '.join(command)}\n{proc.stdout}\n{proc.stderr}")
        if proc.returncode != 0:
            return False, "\n".join(output_parts)
    return True, "\n".join(output_parts)


def main() -> int:
    FIX.mkdir(parents=True, exist_ok=True)
    failures = 0

    for domain in DOMAINS:
        slug = domain["slug"]
        base = FIX / slug
        write_dbt_project(base, slug)
        write_sources(base, domain["seeds"])
        domain["writer"](base)
        write_schema_tests(base, domain["facts"], domain["dims"])
        write_exposures(base, domain["facts"], domain["process"])
        write_agent_reports(
            base,
            slug,
            domain["process"],
            domain["facts"],
            domain["dims"],
            domain["staging"],
            domain["intermediate"],
            domain["seeds"],
        )
        print(f"Wrote dbt fixture {base}")

        ok, dbt_output = run_dbt(base)
        if ok:
            stamp_manifest_identities(base)
            print(f"[PASS] dbt build :: {slug}")
        else:
            failures += 1
            print(f"[FAIL] dbt build :: {slug}")
            print(dbt_output)

    fixture_checks = [
        "check_fact_analytical_coverage.py",
        "check_metric_contract_completeness.py",
        "check_model_classification_coverage.py",
        "check_exposure_coverage.py",
        "verify_metric_reconciliation.py",
        "validate_rendered_report_content.py",
        "validate_chart_registry.py",
        "check_presentation_traceability.py",
        "validate_live_report_dom.py",
    ]
    for domain in DOMAINS:
        root = FIX / domain["slug"]
        for script in fixture_checks:
            cmd = [sys.executable, str(SCRIPTS / script), "--root", str(root)]
            if script == "validate_live_report_dom.py":
                cmd.append("--allow-skip")
            if script in {
                "check_model_classification_coverage.py",
                "check_exposure_coverage.py",
            }:
                cmd.extend(["--phase", "final"])
            proc = subprocess.run(cmd, cwd=str(SCRIPTS), capture_output=True, text=True)
            status = "PASS" if proc.returncode == 0 else "FAIL"
            if proc.returncode != 0:
                failures += 1
            print(f"[{status}] {domain['slug']} :: {script}")
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_domain_neutrality.py"), "--root", str(ROOT)],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        failures += 1
        print("[FAIL] check_domain_neutrality.py")
        print(proc.stdout)
        print(proc.stderr)
    else:
        print("[PASS] check_domain_neutrality.py")

    for domain in DOMAINS:
        root = FIX / domain["slug"]
        for script_name, extra_args in (
            ("run_acceptance_gate.py", ["--phase", "final", "--strict", "--skip-dbt"]),
            ("run_independent_verifier.py", ["--phase", "final"]),
        ):
            cmd = [sys.executable, str(SCRIPTS / script_name), "--root", str(root), *extra_args]
            proc = subprocess.run(cmd, cwd=str(SCRIPTS), capture_output=True, text=True)
            status = "PASS" if proc.returncode == 0 else "FAIL"
            if proc.returncode != 0:
                failures += 1
            print(f"[{status}] {domain['slug']} :: {script_name}")
            if proc.returncode != 0:
                print(proc.stdout)
                print(proc.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
