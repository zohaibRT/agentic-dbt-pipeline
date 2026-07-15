#!/usr/bin/env python3
"""Check KPI / metric contract completeness for published metrics.

Validates every published KPI row individually against required headers.
Coverage = complete critical KPI contracts / total published critical KPIs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import (
    cell,
    load_analytics_policy,
    normalize_header,
    parse_markdown_tables,
    print_results,
    ratio,
    read_text,
)


CRITICAL_HEADER_GROUPS = (
    ("kpi_id", ("kpi_id", "kpi", "id", "key_performance_indicator")),
    ("display_name", ("display_name", "display")),
    ("business_question", ("business_question",)),
    ("decision_supported", ("decision_supported", "decisions_supported")),
    ("action_when_bad", ("action_when_bad", "recommended_action")),
    ("owner", ("owner",)),
    ("grain", ("grain",)),
    ("counting_key", ("counting_key", "count_key")),
    ("sql_proof", ("sql_proof", "verified_by_sql_proof", "proof")),
    ("approval", ("approval", "approval_status")),
    ("verification", ("verification", "verification_status", "status")),
)

RECOMMENDED_HEADER_GROUPS = (
    ("aggregation", ("aggregation", "aggregation_behavior")),
    ("desired_direction", ("desired_direction",)),
    ("target", ("target", "target_source")),
    ("format", ("format",)),
    ("expected", ("expected", "expected_result")),
    ("actual", ("actual", "actual_result")),
)

PUBLISHED_APPROVALS = {"APPROVED", "PROPOSED", "BLOCKED", "DEFERRED"}


def contract_rows(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    rows: list[dict[str, str]] = []
    for headers, data in parse_markdown_tables(text):
        norm = [normalize_header(h) for h in headers]
        header_set = set(norm)
        # Prefer expanded or legacy contract tables
        if not (
            {"sql_proof", "approval", "approval_status"} & header_set
            or ("kpi_id" in header_set and "grain" in header_set)
            or ("kpi" in header_set and "sql_proof" in header_set)
        ):
            continue
        for cells in data:
            row = {
                norm[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm))
                if norm[i]
            }
            rows.append(row)
        if rows:
            return rows
    return rows


def row_has(row: dict[str, str], aliases: tuple[str, ...]) -> bool:
    value = cell(row, *aliases)
    if not value:
        return False
    upper = value.strip().upper()
    return upper not in {"TODO", "N/A", "TBD", "<TODO>", ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required_ratio = float(policy.get("critical_kpi_contract_coverage_required", 1.0))

    contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    insights = root / "reports" / "agent" / "09_analytics_insights"
    errors: list[str] = []
    warnings: list[str] = []

    if not contracts.exists() and not insights.exists():
        print("SKIPPED: no KPI contracts or analytics folder")
        return 0
    if not contracts.exists():
        # Analytics started without contracts is incomplete for critical KPI coverage
        errors.append(
            "KPI_DEFINITION_CONTRACTS.md missing while analytics insights exist — "
            "critical KPI contract coverage cannot be verified"
        )
        return print_results("Metric contract completeness check", errors, warnings)

    rows = contract_rows(contracts)
    print(f"Metric contract completeness: contract_rows={len(rows)}")

    if not rows:
        errors.append("KPI_DEFINITION_CONTRACTS.md has no data rows")
        return print_results("Metric contract completeness check", errors, warnings)

    published = 0
    complete = 0
    for index, row in enumerate(rows, start=1):
        kpi_id = cell(row, "kpi_id", "kpi", "id", "display_name") or f"row {index}"
        approval = cell(row, "approval", "approval_status").upper()
        if approval and approval not in PUBLISHED_APPROVALS and approval not in {"DRAFT", "PENDING", ""}:
            warnings.append(f"{kpi_id}: unusual approval status {approval}")

        # Count rows that look like published/critical KPIs (exclude pure drafts without proof intent)
        is_critical = approval in {"APPROVED", "PROPOSED", "BLOCKED", ""} or not approval
        if not is_critical:
            continue

        published += 1
        missing_critical: list[str] = []
        for label, aliases in CRITICAL_HEADER_GROUPS:
            if not row_has(row, aliases):
                missing_critical.append(label)
        missing_recommended: list[str] = []
        for label, aliases in RECOMMENDED_HEADER_GROUPS:
            if not row_has(row, aliases):
                missing_recommended.append(label)

        if missing_critical:
            errors.append(f"{kpi_id}: missing critical contract fields: {', '.join(missing_critical)}")
        else:
            complete += 1
        if missing_recommended:
            warnings.append(
                f"{kpi_id}: missing recommended contract fields: {', '.join(missing_recommended)}"
            )

    cov = ratio(complete, published)
    if cov is None:
        errors.append("no published critical KPI rows to score (empty applicable set is NOT_APPLICABLE, not 100%)")
    else:
        print(f"Critical KPI contract coverage: {complete}/{published} ({cov:.0%})")
        if cov < required_ratio:
            errors.append(
                f"critical KPI contract coverage {cov:.0%} below required {required_ratio:.0%}"
            )

    return print_results("Metric contract completeness check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
