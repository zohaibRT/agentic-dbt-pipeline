#!/usr/bin/env python3
"""Check analytics product completeness via coverage matrix modules."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    cell,
    load_analytics_policy,
    named_status,
    print_results,
    ratio,
    read_text,
    table_dicts,
)

PROCESS_MODULES = (
    ("facts", ("fact/event models", "facts", "fact", "fact_event_models")),
    ("dimensions", ("dimensions",)),
    ("grain", ("grain proven", "grain", "grain_proven")),
    ("measures", ("measures",)),
    ("metrics", ("contextual metrics", "metrics", "contextual_metrics")),
    ("kpis", ("strategic kpis", "kpis", "strategic_kpis")),
    ("time", ("time intelligence", "time_intelligence", "time")),
    ("segmentation", ("segmentation",)),
    ("exceptions", ("exceptions", "exception")),
    ("quality", ("data quality", "quality", "data_quality")),
    ("reconciliation", ("reconciliation",)),
    ("report_page", ("report page", "report_page")),
    ("owner", ("owner/approval", "owner", "owner_approval")),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    process_required = float(policy.get("business_process_coverage_required", 0.9))
    module_required = float(policy.get("critical_process_module_coverage_required", 1.0))

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

    rows = table_dicts(
        matrix,
        required_any_headers=("business process", "status", "business_process"),
    )
    if not rows:
        errors.append("analytics_coverage_matrix.md has no process rows")
        return print_results("Analytics product completeness check", errors, warnings)

    pass_rows = 0
    applicable = 0
    module_complete = 0
    module_total = 0

    for index, row in enumerate(rows, start=1):
        process = cell(row, "business process", "business_process", "process") or f"row {index}"
        status = named_status(row)
        if status == "NOT_APPLICABLE":
            continue
        applicable += 1
        if status == "PASS":
            pass_rows += 1
        elif status == "UNKNOWN":
            warnings.append(f"{process}: unclear Status in analytics_coverage_matrix.md")

        if status != "PASS":
            continue

        missing_modules = [
            label
            for label, aliases in PROCESS_MODULES
            if not cell(row, *aliases)
        ]
        module_total += 1
        if missing_modules:
            errors.append(
                f"{process}: PASS row missing module cells: {', '.join(missing_modules)}"
            )
        else:
            module_complete += 1

    process_cov = ratio(pass_rows, applicable)
    if process_cov is None:
        errors.append(
            "analytics_coverage_matrix.md has no applicable data rows "
            "(empty applicable set is NOT_APPLICABLE, not 100%)"
        )
    else:
        print(f"Business-process coverage: PASS={pass_rows}/{applicable} ({process_cov:.0%})")
        if process_cov < process_required:
            errors.append(
                f"business-process analytical coverage {process_cov:.0%} below required {process_required:.0%}"
            )

    module_cov = ratio(module_complete, module_total)
    if module_total > 0 and module_cov is not None:
        print(f"Process module coverage: {module_complete}/{module_total} ({module_cov:.0%})")
        if module_cov < module_required:
            errors.append(
                f"critical process module coverage {module_cov:.0%} below required {module_required:.0%}"
            )

    if not process_catalog.exists():
        warnings.append("missing business_process_catalog.md — processes should drive metrics and pages")
    else:
        text = read_text(process_catalog).lower()
        if "business question" not in text and "question" not in text:
            warnings.append("business_process_catalog.md should document supported business questions")

    return print_results("Analytics product completeness check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
