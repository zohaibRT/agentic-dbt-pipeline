#!/usr/bin/env python3
"""Create the managed reports/agent folder skeleton for this dbt pipeline skill."""

from __future__ import annotations

import argparse
from pathlib import Path


PROOF_FOLDERS = {
    "00_discovery/sql_proofs": "Source discovery proofs: table inventory, row counts, candidate keys, business-state counts, date coverage, numeric summaries, and relationship or cardinality checks.",
    "02_sources/sql_proofs": "Sources phase proofs: generated source YAML evidence, source profiling, freshness evidence, source tests, and source metadata checks.",
    "03_bronze/sql_proofs": "Bronze or staging proofs: source-to-staging row counts, grain checks, relationship checks, status distributions, date coverage, and raw measure summaries.",
    "04_silver/sql_proofs": "Silver or intermediate proofs: join safety, row loss or multiplication, mapping coverage, derived flags, relationship integrity, and intermediate measure checks.",
    "05_gold/sql_proofs": "Gold or marts proofs: fact and dimension row counts, grain checks, relationship checks, privacy exposure checks, reporting mart checks, and metric component summaries.",
    "06_semantic/sql_proofs": "Semantic layer proofs: gold SQL versus semantic metric checks, metric grain checks, denominator checks, and semantic validation evidence.",
    "07_evaluator/sql_proofs": "Project evaluator proofs: evaluator table-shape checks, finding queries, accepted warning evidence, and evaluator schema isolation checks.",
    "09_analytics_insights/kpis/sql_proofs": "Analytics insight proofs: measure, metric, key performance indicator, reconciliation, variance, and source-to-final lineage checks.",
}

PLAIN_FOLDERS = [
    "01_setup",
    "08_documentation",
    "09_analytics_insights/kpis",
    "10_presentation",
    "10_presentation/matplotlib",
    "10_presentation/matplotlib/report_pages",
    "10_presentation/matplotlib/sql_verification",
    "10_presentation/report_pages",
    "10_presentation/figures",
    "11_operations",
]

ROOT_FILES = {
    "REPORT_INDEX.md": "# Report Index\n\nUse this file to list each report, status, purpose, and what the data engineer should verify.\n",
    "PIPELINE_STATUS.md": "# Pipeline Status\n\nUse this file to track the current pipeline checkpoint, status, validation, and next action.\n",
    "CONTEXT_TREE.md": "# Context Tree\n\nUse this file to track reusable project context, decisions, open questions, and deferred scope.\n",
    "NEXT_PHASE_PROMPT.md": "# Next Phase Prompt\n\nUse this file to store the exact next checkpoint prompt after a phase completes.\n",
    "HUMAN_VERIFICATION_GUIDE.md": "# Human Verification Guide\n\nUse this file to explain how to re-run SQL proofs, review validation results, and confirm blocked or deferred items.\n",
    "REQUIREMENTS_TRACEABILITY_MATRIX.md": """# Requirements Traceability Matrix

| Requirement ID | Requirement / Rule | Source | Business Area | Layer Impact | Implementation Artifact | Verification Artifact | Presentation / Output Artifact | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|
| TODO | Add approved discovery requirement | reports/agent/00_discovery/requirements.md | TODO | TODO | TODO | TODO | TODO | OPEN | Replace this starter row after discovery approval |
""",
    "LAYER_VERIFICATION_LEDGER.md": """# Layer Verification Ledger

| Phase | Layer | Model / Artifact | Expected Grain | Row Count | Upstream Comparison | Key / Grain Proof | Relationship Proof | Measure / KPI Proof | Privacy Check | Proof Files | dbt Command Result | Overall Status | Notes |
|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | 0 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | OPEN | Replace this starter row after the first verified layer |
""",
    "KPI_DEFINITION_CONTRACTS.md": """# Key Performance Indicator Definition Contracts

| KPI ID | Key Performance Indicator | Business Meaning | Formula | Grain | Date Basis | Included Rows | Excluded Rows | Source Tables / Models | Built In | Verified By SQL Proof | Expected Result | Actual Result | Difference / Tolerance | Approval Status | Verification Status | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---:|---:|---|---|---|---|
| TODO | Add approved or proposed key performance indicator | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | 0 | 0 | TODO | PROPOSED | BLOCKED | Replace this starter row when analytics insight reporting begins |
""",
    "METRIC_VERIFICATION_MATRIX.md": """# Metric Verification Matrix

| Metric ID | Metric / Measure / KPI | Type | Definition Approved | Built In | Source Proof | Mart Proof | Semantic Proof | Presentation Proof | Expected Result | Actual Result | Difference / Tolerance | Status | Notes |
|---|---|---|---|---|---|---|---|---|---:|---:|---|---|---|
| TODO | Add verified measure, metric, or key performance indicator | measure / metric / key performance indicator | NO | TODO | TODO | TODO | N/A | N/A | 0 | 0 | TODO | BLOCKED | Replace this starter row when metric verification begins |
""",
}

def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def proof_index_content(relative_folder: str, purpose: str) -> str:
    return f"""# SQL Proof Index

Folder: `reports/agent/{relative_folder}/`

Purpose: {purpose}

Every proof file in this folder should include:

| Field | Meaning |
|---|---|
| Proof name | Business-friendly proof name |
| Phase | Pipeline phase that produced the proof |
| Purpose | What the query proves and why it matters |
| Source objects | Schemas, tables, models, or metrics checked |
| Expected result | Expected row count, zero duplicates, allowed statuses, or business rule |
| Captured result at run time | Small aggregate result copied from the command output |
| Status | PASS, WARN, FAIL, BLOCKED, or SKIPPED |
| Re-run notes | Profile, target, schema, and safe filters needed to re-run |

Use sortable filenames such as:

```text
001_source_table_inventory.sql
010_<table_or_model>_row_count.sql
020_<table_or_model>_key_check.sql
030_<relationship>_relationship_check.sql
040_<metric_or_measure>_summary.sql
```
"""


def create_skeleton(root: Path) -> list[Path]:
    reports_root = root / "reports" / "agent"
    skill_root = Path(__file__).resolve().parents[1]
    template_root = skill_root / "templates" / "reports"
    created: list[Path] = []

    reports_root.mkdir(parents=True, exist_ok=True)

    for relative_path, content in ROOT_FILES.items():
        path = reports_root / relative_path
        template_path = template_root / "root" / relative_path
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
        if write_if_missing(path, content):
            created.append(path)

    for relative_folder, purpose in PROOF_FOLDERS.items():
        folder = reports_root / relative_folder
        folder.mkdir(parents=True, exist_ok=True)
        index_path = folder / "_proof_index.md"
        template_path = template_root / relative_folder / "_proof_index.md"
        if template_path.exists():
            index_content = template_path.read_text(encoding="utf-8")
        else:
            index_content = proof_index_content(relative_folder, purpose)
        if write_if_missing(index_path, index_content):
            created.append(index_path)

    for relative_folder in PLAIN_FOLDERS:
        folder = reports_root / relative_folder
        folder.mkdir(parents=True, exist_ok=True)
        keep_path = folder / ".gitkeep"
        if write_if_missing(keep_path, ""):
            created.append(keep_path)

    if template_root.exists():
        for template_path in template_root.rglob("*"):
            if not template_path.is_file() or "root" in template_path.relative_to(template_root).parts:
                continue
            relative_path = template_path.relative_to(template_root)
            output_path = reports_root / relative_path
            if write_if_missing(output_path, template_path.read_text(encoding="utf-8")):
                created.append(output_path)

    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Create reports/agent managed folder skeleton.")
    parser.add_argument("--root", default=".", help="Project or workspace root where reports/agent should be created.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    created = create_skeleton(root)
    print(f"Report skeleton ready under {root / 'reports' / 'agent'}")
    if created:
        print("Created files:")
        for path in created:
            print(f"- {path.relative_to(root)}")
    else:
        print("No new files were needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
