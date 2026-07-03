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
    "HUMAN_VERIFICATION_GUIDE.md": "# Human Verification Guide\n\nUse this file to explain how to re-run SQL proofs, review validation results, and confirm blocked or deferred items.\n",
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
    created: list[Path] = []

    reports_root.mkdir(parents=True, exist_ok=True)

    for relative_path, content in ROOT_FILES.items():
        path = reports_root / relative_path
        if write_if_missing(path, content):
            created.append(path)

    for relative_folder, purpose in PROOF_FOLDERS.items():
        folder = reports_root / relative_folder
        folder.mkdir(parents=True, exist_ok=True)
        index_path = folder / "_proof_index.md"
        if write_if_missing(index_path, proof_index_content(relative_folder, purpose)):
            created.append(index_path)

    for relative_folder in PLAIN_FOLDERS:
        folder = reports_root / relative_folder
        folder.mkdir(parents=True, exist_ok=True)
        keep_path = folder / ".gitkeep"
        if write_if_missing(keep_path, ""):
            created.append(keep_path)

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
