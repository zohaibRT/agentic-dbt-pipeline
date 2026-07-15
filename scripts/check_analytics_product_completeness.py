#!/usr/bin/env python3
"""Check analytics product completeness via coverage matrix modules."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import count_status_rows, load_analytics_policy, print_results, ratio, read_text


REQUIRED_MODULE_HINTS = (
    ("architecture", ("architecture", "staging", "fact", "dimension")),
    ("business_process", ("business process", "process catalog")),
    ("measures", ("measure",)),
    ("metrics", ("metric",)),
    ("kpis", ("kpi", "strategic")),
    ("time_intelligence", ("time", "trend", "period")),
    ("segmentation", ("segment", "dimension")),
    ("data_quality", ("quality", "orphan", "null")),
    ("reconciliation", ("reconcil",)),
    ("presentation", ("report page", "presentation")),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required = float(policy.get("business_process_coverage_required", 0.9))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0

    matrix = insights / "analytics_coverage_matrix.md"
    process_catalog = insights / "business_process_catalog.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not matrix.exists():
        errors.append("missing reports/agent/09_analytics_insights/analytics_coverage_matrix.md")
        return print_results("Analytics product completeness check", errors, warnings)

    passes, total, unknowns = count_status_rows(matrix)
    coverage = ratio(passes, total) if total else 0.0
    print(f"Analytics coverage matrix: PASS-like={passes}/{total} ({coverage:.0%}), unknown={unknowns}")

    if total == 0:
        errors.append("analytics_coverage_matrix.md has no data rows")
    elif coverage < required:
        errors.append(
            f"business-process analytical coverage {coverage:.0%} below required {required:.0%}"
        )

    if not process_catalog.exists():
        warnings.append("missing business_process_catalog.md — processes should drive metrics and pages")
    else:
        text = read_text(process_catalog).lower()
        if "business question" not in text and "question" not in text:
            warnings.append("business_process_catalog.md should document supported business questions")

    matrix_text = read_text(matrix).lower()
    missing_modules = []
    for label, hints in REQUIRED_MODULE_HINTS:
        if not any(h in matrix_text for h in hints):
            missing_modules.append(label)
    if missing_modules:
        warnings.append(
            "analytics_coverage_matrix.md may be missing modules: " + ", ".join(missing_modules)
        )

    return print_results("Analytics product completeness check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
