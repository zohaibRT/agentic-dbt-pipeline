#!/usr/bin/env python3
"""Check report page contracts exist and cover required decision fields."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import markdown_table_rows, print_results, read_text


REQUIRED_HINTS = (
    ("audience", ("audience",)),
    ("business_purpose", ("business purpose", "purpose", "business_process")),
    ("decisions_supported", ("decision", "decisions_supported")),
    ("primary_kpis", ("primary kpi", "primary_kpis", "kpi")),
    ("time_period", ("time_period", "reporting period", "period")),
    ("exceptions", ("exception",)),
    ("recommended_actions", ("recommended action", "action")),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    presentation = root / "reports" / "agent" / "10_presentation"
    if not presentation.exists():
        print("SKIPPED: no presentation folder")
        return 0

    contracts = presentation / "report_page_contracts.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not contracts.exists():
        # Soft when only early presentation scaffolding exists
        if (presentation / "matplotlib").exists():
            warnings.append("missing report_page_contracts.md for Matplotlib presentation pages")
        else:
            print("SKIPPED: report_page_contracts.md not found yet")
            return 0
        return print_results("Report page contracts check", errors, warnings)

    rows = markdown_table_rows(contracts)
    text = read_text(contracts).lower()
    print(f"Report page contracts: rows~{len(rows)}")

    if len(rows) == 0 and "page_name:" not in text and "page_name" not in text:
        errors.append("report_page_contracts.md has no page rows or YAML page_name entries")

    missing = []
    for label, hints in REQUIRED_HINTS:
        if not any(h in text for h in hints):
            missing.append(label)
    if missing:
        # Critical decision fields are hard errors when contracts file exists
        critical = {"audience", "business_purpose", "decisions_supported", "primary_kpis"}
        hard = [m for m in missing if m in critical]
        soft = [m for m in missing if m not in critical]
        if hard:
            errors.append("report page contracts missing required fields: " + ", ".join(hard))
        if soft:
            warnings.append("report page contracts missing optional fields: " + ", ".join(soft))

    return print_results("Report page contracts check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
