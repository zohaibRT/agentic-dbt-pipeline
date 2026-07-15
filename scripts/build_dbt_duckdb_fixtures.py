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
from lib_gate_common import REQUIRED_OBSERVABILITY_DOMAINS  # noqa: E402

TIME_INTEL_METRICS = [
    "KPI-001",
    "Volume KPI",
    "KPI-002",
    "Completion rate KPI",
    "volume_kpi",
    "completion_kpi",
    "completion_rate",
    "Completion rate",
    "failure_rate",
    "Failure rate",
    "avg_amount",
    "Average amount",
    "mom_volume_change",
    "Month-over-month volume change",
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
target-path: target
clean-targets:
  - target
  - dbt_packages
seeds:
  +schema: main
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
    description: TEST FIXTURE browser report for {process}
    depends_on:
{deps}
    owner:
      name: analytics
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
  fail_on_warning_at_final: true
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
            f"| {fact} | one row per event | event_id | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | volume and completion | PASS |"
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

| Fact | Grain | Counting Key | Volume | Value | Status | Time | Dimensions | Quality | Reconciliation | Business Questions | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
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
        f"""
# Key Performance Indicator Definition Contracts (TEST FIXTURE)

| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Unit/Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | Validation Type | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-001 | Volume KPI | kpi | {process} | How many events occurred? | Capacity planning | Investigate drop | analytics | count(*) | event | event_id | event_date | occurred | all valid | test rows | status | count | integer | additive | Target not defined | increase | {primary_fact} | report | numeric_tolerance | reports/agent/sql_proofs/010_volume.sql | 5 | 5 | 0 | APPROVED | PASS | Matches source |
| KPI-002 | Completion rate KPI | kpi | {process} | What share completed? | Process health | Review failures | analytics | completed/total | event | event_id | event_date | completed | non-cancelled | cancelled | status | ratio | percent | ratio | Target not defined | increase | {primary_fact} | report | numeric_tolerance | reports/agent/sql_proofs/020_rate.sql | 0.4 | 0.4 | 0 | APPROVED | PASS | Definition approved |
""",
    )
    write(
        base / "reports" / "agent" / "METRIC_VERIFICATION_MATRIX.md",
        """
# Metric Verification Matrix (TEST FIXTURE)

| Metric | Source Proof | Current Model Proof | Expected Result | Actual Result | Diff | Status | Notes |
|---|---|---|---|---|---|---|---|
| Volume KPI | reports/agent/sql_proofs/010_volume.sql | reports/agent/sql_proofs/010_volume.sql | 5 | 5 | 0 | PASS | Matches |
| Completion rate KPI | reports/agent/sql_proofs/020_rate.sql | reports/agent/sql_proofs/020_rate.sql | 0.4 | 0.4 | 0 | PASS | Matches |
""",
    )
    write(
        base / "reports" / "agent" / "sql_proofs" / "010_volume.sql",
        """
-- purpose: volume KPI
-- expected result: 5
-- captured result: 5
-- status: PASS
select count(*) as volume from {{ ref('"""
        + primary_fact
        + """') }};
""",
    )
    write(
        base / "reports" / "agent" / "sql_proofs" / "020_rate.sql",
        """
-- purpose: completion rate KPI
-- expected result: 0.4
-- captured result: 0.4
-- status: PASS
select 0.4 as rate;
""",
    )

    matplotlib = base / "reports" / "agent" / "10_presentation" / "matplotlib"
    write(
        base / "reports" / "agent" / "10_presentation" / "report_page_contracts.md",
        f"""
# Report Page Contracts (TEST FIXTURE)

| Page ID | Page Name | Audience | Business Purpose | Decisions Supported | Primary KPIs | Time Period | Exceptions | Recommended Actions | Status |
|---|---|---|---|---|---|---|---|---|---|
| executive_overview | Executive Overview | leadership | Summarize {process} | Prioritize interventions | Volume KPI, Completion rate KPI | Current month | Open exceptions listed | Act on failure spike | PASS |
| exceptions_and_data_quality | Exceptions and Data Quality | data engineering | Separate DQ from business KPIs | Fix pipeline issues | Orphan rate | All time | Source/transform issues | Repair orphans | PASS |
| pipeline_health | Pipeline Health | platform | Monitor delivery | Restore SLA | Build success rate | Current week | Failed tests | Rerun failed models | PASS |
| all_measures | All Measures | analysts | Browse measures | Trace definitions | n/a | All time | none | Use dictionary | PASS |
| all_metrics | All Metrics | analysts | Browse metrics | Trace definitions | n/a | All time | none | Use dictionary | PASS |
| all_dimensions | Dimensions | analysts | Browse dimension values | Understand segments | n/a | All time | none | Filter reports | PASS |
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
    write(
        matplotlib / "data_access.py",
        """
# TEST FIXTURE ONLY — illustrates required board payload shape
MEASURE_BOARD = [
    {"id": "event_count", "display_name": "Event count", "value": 5, "formatted_value": "5", "group": "Volume", "format": "integer"},
]
METRIC_BOARD = [
    {"id": "completion_rate", "display_name": "Completion rate", "value": 0.4, "formatted_value": "40.0%", "group": "Performance", "format": "percent"},
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
<tr><td>Event count</td><td>5</td></tr>
<tr><td>Completion rate</td><td>40.0%</td></tr>
</table>
<section id="all_dimensions"><h2>Dimensions</h2><table><tr><th>Status</th></tr><tr><td>Closed</td></tr></table></section>
<section id="exceptions_and_data_quality"><h2>Data Quality</h2></section>
<section id="pipeline_health"><h2>Pipeline Health</h2></section>
</body></html>
""",
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

| Item | Proof | Status |
|---|---|---|
| Volume KPI | 010_volume.sql | PASS |
| Completion rate KPI | 020_rate.sql | PASS |
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
        )
        print(f"Wrote dbt fixture {base}")

        ok, dbt_output = run_dbt(base)
        if ok:
            print(f"[PASS] dbt build :: {slug}")
        else:
            failures += 1
            print(f"[FAIL] dbt build :: {slug}")
            print(dbt_output)

    fixture_checks = [
        "check_fact_analytical_coverage.py",
        "check_metric_contract_completeness.py",
        "check_model_classification_coverage.py",
        "verify_metric_reconciliation.py",
        "validate_rendered_report_content.py",
    ]
    for domain in DOMAINS:
        root = FIX / domain["slug"]
        for script in fixture_checks:
            cmd = [sys.executable, str(SCRIPTS / script), "--root", str(root)]
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

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
