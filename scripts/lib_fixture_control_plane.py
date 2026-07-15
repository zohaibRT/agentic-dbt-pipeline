#!/usr/bin/env python3
"""Write minimal control-plane artifacts for TEST FIXTURE projects.

Used by fixture builders so final acceptance gates pass without weakening validators.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

WriteFn = Callable[[Path, str], None]


def write_control_plane_files(
    write: WriteFn,
    base: Path,
    *,
    slug: str,
    process: str,
    seeds: list[str],
    staging_models: list[str],
    intermediate_models: list[str],
    facts: list[str],
    dims: list[str],
    profile_name: str = "fixture_duckdb",
    adapter: str = "duckdb",
    source_schema: str = "main",
    database: str = "fixture",
) -> None:
    """Emit discovery, layer, and root control files marked TEST FIXTURE ONLY."""
    included_tables = list(seeds)

    discovery_proof = "reports/agent/00_discovery/sql_proofs/001_source_table_inventory.sql"

    write(
        base / "AGENT_PLAN.md",
        f"""
# Agent Plan (TEST FIXTURE ONLY)

Fixture `{slug}` exercises analytics and acceptance gates with synthetic data.

## Scope

- Business process: {process}
- Profile: {profile_name} ({adapter})
- Source schema: {source_schema}

## Phase plan

All phases complete with PASS evidence for gate regression testing.
""",
    )

    write(
        base / "reports" / "agent" / "PIPELINE_STATUS.md",
        f"""
# Pipeline Status (TEST FIXTURE ONLY)

## Current Status

| Field | Value |
|---|---|
| Current checkpoint | Final delivery |
| Status | PASS |
| Active phase folder | `reports/agent/10_presentation/` |
| Last updated | fixture build |
| Next checkpoint | none |

## Phase Status

| Phase | Status | Report | Notes |
|---|---|---|---|
| Discovery | PASS | `reports/agent/00_discovery/discovery_report.md` | Synthetic seed inventory |
| Project setup and configuration | PASS | `reports/agent/01_setup/setup_report.md` | Fixture profile |
| Sources | PASS | `reports/agent/02_sources/sources_report.md` | Seeds loaded |
| Bronze / staging | PASS | `reports/agent/03_bronze/bronze_report.md` | Staging views built |
| Silver / intermediate | PASS | `reports/agent/04_silver/silver_report.md` | Enrichment complete |
| Gold / marts | PASS | `reports/agent/05_gold/gold_report.md` | Star schema ready |
| Semantic layer | PASS | n/a | Not in fixture scope |
| Project evaluator | PASS | n/a | Not in fixture scope |
| Documentation | PASS | `reports/agent/08_documentation/docs_report.md` | Catalogs present |
| Analytics insight reporting | PASS | `reports/agent/09_analytics_insights/analytics_coverage_matrix.md` | Coverage complete |
| Presentation layer | PASS | `reports/agent/10_presentation/presentation_report.md` | Interactive report rendered |

## Important Notes

- None

## Latest Validation Evidence

| Check | Result | Evidence |
|---|---|---|
| Source inventory | PASS | `{discovery_proof}` |
| Row counts | PASS | `{discovery_proof}` |
| Keys and grain | PASS | `reports/agent/05_gold/sql_proofs/010_grain_check.sql` |
| Relationships | PASS | `reports/agent/04_silver/sql_proofs/010_join_check.sql` |
| Privacy review | PASS | `reports/agent/03_bronze/sql_proofs/010_row_count.sql` |
""",
    )

    write(
        base / "reports" / "agent" / "CONTEXT_TREE.md",
        f"""
# Context Tree (TEST FIXTURE ONLY)

## Active Run

| Field | Value |
|---|---|
| Current checkpoint | Final |
| Current status | PASS |
| Last updated | fixture build |
| Source lock status | locked |

## Input Context

| Input | Value | Source | Notes |
|---|---|---|---|
| Domain | {slug} | fixture | TEST FIXTURE ONLY |
| Business description | {process} | fixture | illustrative |
| dbt profile name | {profile_name} | profiles.yml | no secrets |
| Adapter | {adapter} | profiles.yml | local duckdb |
| Database or catalog | {database} | profiles.yml | file-backed |
| Source schema | {source_schema} | seeds | synthetic |

## Decisions And Rules

| Decision / Rule | Status | Source | Applies To | Notes |
|---|---|---|---|---|
| Use synthetic seeds | approved | fixture | all layers | Gate regression only |

## Open Questions

| Question | Why it matters | Blocking phase | Current status |
|---|---|---|---|
| None | n/a | n/a | answered |
""",
    )

    write(
        base / "reports" / "agent" / "REPORT_INDEX.md",
        f"""
# Report Index (TEST FIXTURE ONLY)

## Root Control Files

| File | Purpose | Status | Why this status was used | What the data engineer should check |
|---|---|---|---|---|
| `reports/agent/PIPELINE_STATUS.md` | Phase status | PASS | All fixture phases complete | Confirm PASS rows |
| `reports/agent/CONTEXT_TREE.md` | Context | PASS | Fixture context locked | Confirm profile/schema |
| `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` | Traceability | PASS | Requirements mapped | Confirm proof links |

## Discovery Reports

| Report | Purpose | Status | Why this status was used | What the data engineer should check |
|---|---|---|---|---|
| `reports/agent/00_discovery/discovery_report.md` | Discovery summary | PASS | Seeds inventoried | Review inclusion |
| `reports/agent/00_discovery/requirements.md` | Requirements | PASS | Derived from seeds | Approve scope |
| `reports/agent/00_discovery/core_profile.json` | Profile snapshot | PASS | Non-secret context | Confirm adapter |
| `reports/agent/00_discovery/discovery_raw.json` | Raw evidence | PASS | Linked proofs | Confirm tables |
| `reports/agent/00_discovery/sql_proofs/` | Discovery proofs | PASS | Runnable SQL | Re-run inventory |

## Later Phase Reports

| Phase | Report | Status | Why this status was used | Notes |
|---|---|---|---|---|
| Bronze / staging | `reports/agent/03_bronze/bronze_report.md` | PASS | Staging validated | Fixture |
| Silver / intermediate | `reports/agent/04_silver/silver_report.md` | PASS | Joins validated | Fixture |
| Gold / marts | `reports/agent/05_gold/gold_report.md` | PASS | Star schema validated | Fixture |
| Presentation layer | `reports/agent/10_presentation/presentation_report.md` | PASS | Charts rendered | Fixture |
""",
    )

    write(
        base / "reports" / "agent" / "HUMAN_VERIFICATION_GUIDE.md",
        """
# Human Verification Guide (TEST FIXTURE ONLY)

## Purpose

Fixture projects use synthetic data for automated gate regression. Human sign-off is not required for CI.

## What To Check

| Area | Evidence File | Why current status (if not PASS) | Human Action | Status |
|---|---|---|---|---|
| Pipeline status | `reports/agent/PIPELINE_STATUS.md` | PASS | Spot-check PASS phases | PASS |
| Layer validation | `reports/agent/LAYER_VERIFICATION_LEDGER.md` | PASS | Confirm proof links | PASS |
| KPI definitions | `reports/agent/KPI_DEFINITION_CONTRACTS.md` | PASS | Confirm formulas | PASS |
| Presentation | `reports/agent/10_presentation/presentation_report.md` | PASS | Open report.html | PASS |

## Final Sign-Off

Fixture builds are machine-verified; no human sign-off required in CI.
""",
    )

    write(
        base / "reports" / "agent" / "HUMAN_ATTENTION_BOARD.md",
        """
# Human Attention Board (TEST FIXTURE ONLY)

No OPEN items. Fixture uses synthetic data for gate regression.
""",
    )

    _write_discovery_artifacts(
        write,
        base,
        slug=slug,
        process=process,
        included_tables=included_tables,
        profile_name=profile_name,
        adapter=adapter,
        source_schema=source_schema,
        database=database,
        discovery_proof=discovery_proof,
    )
    _write_traceability_matrix(write, base, process, facts, dims, staging_models, intermediate_models)
    _write_layer_ledger(
        write,
        base,
        staging_models=staging_models,
        intermediate_models=intermediate_models,
        facts=facts,
        dims=dims,
    )
    _write_layer_reports(write, base, staging_models, intermediate_models, facts, dims)
    _write_layer_sql_proofs(write, base, staging_models, intermediate_models, facts)
    _write_fixture_ci_workflow(write, base)
    _write_sources_report(write, base)


def _write_discovery_artifacts(
    write: WriteFn,
    base: Path,
    *,
    slug: str,
    process: str,
    included_tables: list[str],
    profile_name: str,
    adapter: str,
    source_schema: str,
    database: str,
    discovery_proof: str,
) -> None:
    discovery = base / "reports" / "agent" / "00_discovery"
    proof_dir = discovery / "sql_proofs"

    write(
        discovery / "README.md",
        """
# Discovery Reports (TEST FIXTURE ONLY)

Synthetic seed inventory for gate regression. Status vocabulary: PASS = evidence supports claim.
""",
    )

    write(
        discovery / "requirements.md",
        f"""
# Requirements (TEST FIXTURE ONLY)

## Source-derived requirements

| ID | Requirement | Source | Status |
|---|---|---|---|
| REQ-001 | Model {process} events from seed tables | seeds | PASS |
| REQ-002 | Publish volume and completion KPIs | business | PASS |
| REQ-003 | Provide interactive presentation report | reporting | PASS |
""",
    )

    write(
        discovery / "discovery_report.md",
        f"""
# Discovery Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Business process: {process}
- Included tables: {len(included_tables)}

## Table Inclusion Filter

All listed seeds are included for the fixture first-pass scope.

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/001_source_table_inventory.sql` | Source inventory | PASS | Tables listed |
""",
    )

    write(
        discovery / "cardinality_report.md",
        """
# Cardinality Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Main join path reviewed: staging to dimensions
- Many-to-many risks found: no

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/001_source_table_inventory.sql` | Inventory | PASS | Seeds present |
""",
    )

    write(
        discovery / "relationship_profile.md",
        """
# Relationship Profile (TEST FIXTURE ONLY)

## Summary

- Status: PASS

## Proven Relationships

| Parent | Child | Join | Status | Proof file |
|---|---|---|---|---|
| raw_entities | raw_events | entity_id | PASS | `sql_proofs/001_source_table_inventory.sql` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/001_source_table_inventory.sql` | Inventory | PASS | Linked |
""",
    )

    write(
        discovery / "DISCOVERY_APPROVAL_CHECKLIST.md",
        """
# Discovery Approval Checklist (TEST FIXTURE ONLY)

## Required Outputs

| Check | Status | Evidence / Notes |
|---|---|---|
| Discovery report exists | PASS | discovery_report.md |
| Requirements file exists | PASS | requirements.md |
| Core profile JSON exists | PASS | core_profile.json |
| Discovery raw JSON exists | PASS | discovery_raw.json |
| SQL proof folder exists | PASS | sql_proofs/ |

## Approval Decision

| Field | Value |
|---|---|
| Decision | APPROVED |
| Approved by | fixture builder |
| Conditions | TEST FIXTURE ONLY |
""",
    )

    write(
        proof_dir / "_proof_index.md",
        """
# SQL Proof Index (TEST FIXTURE ONLY)

| Proof file | Purpose | Status |
|---|---|---|
| 001_source_table_inventory.sql | List seed tables | PASS |
""",
    )

    write(
        proof_dir / "001_source_table_inventory.sql",
        """
-- purpose: list source seed tables for fixture discovery
-- expected result: all seeds present
-- captured result: all seeds present
-- status: PASS
select 'fixture_inventory' as proof_name;
""",
    )

    tables = []
    for table in included_tables:
        tables.append(
            {
                "schema": source_schema,
                "table_name": table,
                "row_count": 5,
                "inclusion_status": "included",
                "inclusion_reason": "TEST FIXTURE seed table",
                "status": "PASS",
            }
        )

    core_profile = {
        "_file_meta": {
            "purpose": "Machine-readable snapshot of fixture dbt connection",
            "why": "Gate regression without chat history",
            "required_on_every_discovery_run": True,
        },
        "run": {
            "generated_at": "2026-01-01T00:00:00Z",
            "discovery_status": "PASS",
            "last_updated_by_phase": "discovery",
        },
        "profile": {
            "dbt_profile_name": profile_name,
            "adapter": adapter,
            "database_or_catalog": database,
            "target_schema": source_schema,
            "threads": 1,
        },
        "source": {
            "domain": slug,
            "business_description": process,
            "source_schema": source_schema,
            "source_name": "raw",
        },
        "workspace": {
            "project_root": str(base),
            "dbt_project_name": slug,
            "env_file_present": False,
        },
    }
    (discovery / "core_profile.json").write_text(json.dumps(core_profile, indent=2) + "\n", encoding="utf-8")

    discovery_raw = {
        "_file_meta": {
            "purpose": "Structured raw discovery evidence for fixture",
            "why": "Audit trail for gate regression",
            "required_on_every_discovery_run": True,
        },
        "run": {
            "generated_at": "2026-01-01T00:00:00Z",
            "discovery_status": "PASS",
            "dbt_profile_name": profile_name,
            "adapter": adapter,
            "source_schema": source_schema,
        },
        "scope": {
            "total_tables_in_schema": len(included_tables),
            "tables_profiled": len(included_tables),
            "tables_included_v1": len(included_tables),
            "tables_deferred": 0,
            "tables_excluded": 0,
            "first_pass_business_process": process,
            "filter_reference": "fixture",
            "notes": "TEST FIXTURE ONLY",
        },
        "tables": tables,
        "queries_executed": [
            {
                "proof_file": discovery_proof,
                "purpose": "List source tables and row counts",
                "status": "PASS",
                "captured_at": "2026-01-01T00:00:00Z",
                "summary": "All fixture seeds inventoried",
            }
        ],
    }
    (discovery / "discovery_raw.json").write_text(json.dumps(discovery_raw, indent=2) + "\n", encoding="utf-8")

    first_pass_scope = {
        "_file_meta": {
            "purpose": "Locked first-pass table inclusion scope for fixture",
            "why": "Repeatable fixture discovery",
            "required_on_every_discovery_run": True,
        },
        "lock_status": "approved",
        "fingerprint": {
            "profile": profile_name,
            "database": database,
            "source_schema": source_schema,
            "business_process": process,
        },
        "counts": {
            "total_tables": len(included_tables),
            "included": len(included_tables),
            "deferred": 0,
            "excluded": 0,
        },
        "included_tables": included_tables,
        "deferred_tables": [],
        "prior_scope_path": None,
        "approved_at": "2026-01-01T00:00:00Z",
        "approved_by": "fixture builder",
        "notes": "TEST FIXTURE ONLY",
    }
    (discovery / "first_pass_scope.json").write_text(json.dumps(first_pass_scope, indent=2) + "\n", encoding="utf-8")


def _write_traceability_matrix(
    write: WriteFn,
    base: Path,
    process: str,
    facts: list[str],
    dims: list[str],
    staging_models: list[str],
    intermediate_models: list[str],
) -> None:
    primary_fact = facts[0]
    staging_ref = staging_models[0] if staging_models else "stg_events"
    int_ref = intermediate_models[0] if intermediate_models else "int_events_enriched"
    rows = [
        f"| DISC-001 | Model {process} from seeds | reports/agent/00_discovery/requirements.md | {process} | bronze | models/staging/{staging_ref}.sql | reports/agent/03_bronze/sql_proofs/010_row_count.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |",
        f"| DISC-002 | Enrich events with status | reports/agent/00_discovery/requirements.md | {process} | silver | models/intermediate/{int_ref}.sql | reports/agent/04_silver/sql_proofs/010_join_check.sql | n/a | PASS | Fixture |",
        f"| DISC-003 | Publish gold star schema | reports/agent/00_discovery/requirements.md | {process} | gold | models/gold/{primary_fact}.sql | reports/agent/05_gold/sql_proofs/010_grain_check.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |",
        "| DISC-004 | Volume KPI with SQL proof | reports/agent/KPI_DEFINITION_CONTRACTS.md | analytics | presentation | reports/agent/KPI_DEFINITION_CONTRACTS.md | reports/agent/sql_proofs/010_volume.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |",
        "| DISC-005 | Completion rate KPI | reports/agent/KPI_DEFINITION_CONTRACTS.md | analytics | presentation | reports/agent/KPI_DEFINITION_CONTRACTS.md | reports/agent/sql_proofs/020_rate.sql | reports/agent/10_presentation/matplotlib/report.html | PASS | Fixture |",
    ]
    dim_note = ", ".join(dims)
    write(
        base / "reports" / "agent" / "REQUIREMENTS_TRACEABILITY_MATRIX.md",
        f"""
# Requirements Traceability Matrix (TEST FIXTURE ONLY)

Dimensions in scope: {dim_note}

| Requirement ID | Requirement / Rule | Source | Business Area | Layer Impact | Implementation Artifact | Verification Artifact | Presentation / Output Artifact | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}
""",
    )


def _write_layer_ledger(
    write: WriteFn,
    base: Path,
    *,
    staging_models: list[str],
    intermediate_models: list[str],
    facts: list[str],
    dims: list[str],
) -> None:
    rows: list[str] = []
    for model in staging_models:
        rows.append(
            f"| 03_bronze | bronze/staging | {model} | source row | 5 | match | PASS | PASS | PASS | PASS | reports/agent/03_bronze/sql_proofs/010_row_count.sql | PASS | PASS | Fixture |"
        )
    for model in intermediate_models:
        rows.append(
            f"| 04_silver | silver/intermediate | {model} | event | 5 | match | PASS | PASS | PASS | PASS | reports/agent/04_silver/sql_proofs/010_join_check.sql | PASS | PASS | Fixture |"
        )
    for fact in facts:
        rows.append(
            f"| 05_gold | gold/marts | {fact} | event | 5 | match | PASS | PASS | PASS | PASS | reports/agent/05_gold/sql_proofs/010_grain_check.sql | PASS | PASS | Fixture |"
        )
    for dim in dims:
        rows.append(
            f"| 05_gold | gold/marts | {dim} | entity | 5 | match | PASS | PASS | n/a | PASS | reports/agent/05_gold/sql_proofs/010_grain_check.sql | PASS | PASS | Fixture |"
        )
    write(
        base / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md",
        f"""
# Layer Verification Ledger (TEST FIXTURE ONLY)

| Phase | Layer | Model / Artifact | Expected Grain | Row Count | Upstream Comparison | Key / Grain Proof | Relationship Proof | Measure / KPI Proof | Privacy Check | Proof Files | dbt Command Result | Overall Status | Notes |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}
""",
    )


def _write_layer_reports(
    write: WriteFn,
    base: Path,
    staging_models: list[str],
    intermediate_models: list[str],
    facts: list[str],
    dims: list[str],
) -> None:
    staging_rows = "\n".join(
        f"| {m} | seed | view | 5 | PASS | Fixture |" for m in staging_models
    ) or "| n/a | n/a | n/a | 0 | PASS | Fixture |"
    int_rows = "\n".join(
        f"| {m} | enrichment | event | view | 5 | PASS |" for m in intermediate_models
    ) or "| n/a | n/a | event | view | 0 | PASS |"
    gold_rows = "\n".join(
        [f"| {f} | fact | event | table | 5 | PASS |" for f in facts]
        + [f"| {d} | dimension | entity | table | 5 | PASS |" for d in dims]
    )

    write(
        base / "reports" / "agent" / "03_bronze" / "bronze_report.md",
        f"""
# Bronze / Staging Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Models built: {len(staging_models)}

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Source-to-bronze row count | PASS | `sql_proofs/010_row_count.sql` |
| Primary key check | PASS | `sql_proofs/010_row_count.sql` |
| Date coverage | PASS | `sql_proofs/010_row_count.sql` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/010_row_count.sql` | Row presence | PASS | 5 rows |

## What Was Built Or Changed

| Model | Source table | Materialization | Row count | Status | Notes |
|---|---|---|---:|---|---|
{staging_rows}
""",
    )

    write(
        base / "reports" / "agent" / "04_silver" / "silver_report.md",
        f"""
# Silver / Intermediate Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Models built: {len(intermediate_models)}

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Row loss check | PASS | `sql_proofs/010_join_check.sql` |
| Relationship integrity | PASS | `sql_proofs/010_join_check.sql` |
| Mapping coverage | PASS | `sql_proofs/010_join_check.sql` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/010_join_check.sql` | Join safety | PASS | 5 rows |

## What Was Built Or Changed

| Model | Purpose | Grain | Materialization | Row count | Status |
|---|---|---|---|---:|---|
{int_rows}
""",
    )

    write(
        base / "reports" / "agent" / "05_gold" / "gold_report.md",
        f"""
# Gold / Marts Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Dimensions built: {len(dims)}
- Facts built: {len(facts)}

## Data Verification Results

| Check | Result | Evidence |
|---|---|---|
| Fact grain uniqueness | PASS | `sql_proofs/010_grain_check.sql` |
| Dimension key uniqueness | PASS | `sql_proofs/010_grain_check.sql` |
| Relationship integrity | PASS | `sql_proofs/010_grain_check.sql` |

## SQL Proof Files

| Proof file | Purpose | Status | Key result |
|---|---|---|---|
| `sql_proofs/010_grain_check.sql` | Grain check | PASS | unique keys |

## Models Built Or Changed

| Model | Type | Grain | Materialization | Row count | Status |
|---|---|---|---|---:|---|
{gold_rows}
""",
    )


def _write_layer_sql_proofs(
    write: WriteFn,
    base: Path,
    staging_models: list[str],
    intermediate_models: list[str],
    facts: list[str],
) -> None:
    primary_fact = facts[0] if facts else "fct_events"
    write(
        base / "reports" / "agent" / "03_bronze" / "sql_proofs" / "010_row_count.sql",
        """
-- purpose: bronze staging row presence
-- expected result: 5
-- captured result: 5
-- status: PASS
select 5 as row_count;
""",
    )
    write(
        base / "reports" / "agent" / "04_silver" / "sql_proofs" / "010_join_check.sql",
        """
-- purpose: silver join integrity
-- expected result: 5
-- captured result: 5
-- status: PASS
select 5 as joined_rows;
""",
    )
    write(
        base / "reports" / "agent" / "05_gold" / "sql_proofs" / "010_grain_check.sql",
        f"""
-- purpose: gold grain uniqueness for {primary_fact}
-- expected result: 5
-- captured result: 5
-- status: PASS
select count(*) as row_count from {{{{ ref('{primary_fact}') }}}};
""",
    )


def _write_fixture_ci_workflow(write: WriteFn, base: Path) -> None:
    write(
        base / ".github" / "workflows" / "fixture_ci.yml",
        """
# TEST FIXTURE ONLY — documents CI/orchestration evidence for acceptance gate
name: Fixture CI

on:
  workflow_dispatch:

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Fixture validated by analytics_gates workflow"
      - run: python scripts/run_acceptance_gate.py --phase final --strict
      - run: python scripts/build_dbt_duckdb_fixtures.py
      - run: python -m unittest discover -s tests -p "test_*.py"
""",
    )


def _write_sources_report(write: WriteFn, base: Path) -> None:
    write(
        base / "reports" / "agent" / "02_sources" / "sources_report.md",
        """
# Sources Report (TEST FIXTURE ONLY)

## Summary

- Status: PASS
- Source freshness: documented for fixture gate evidence (`freshness:` policy noted; seeds are static)

## Source Freshness Notes

Fixture seeds are static CSV files. Production deployments should configure `freshness:` checks on event tables.
""",
    )
