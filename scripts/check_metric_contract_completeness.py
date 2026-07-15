#!/usr/bin/env python3
"""Check KPI / metric contract completeness for published metrics.

Validates every published KPI row independently against required headers.
Coverage = complete critical KPI contracts / total published critical KPIs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    cell,
    load_analytics_policy,
    normalize_header,
    parse_markdown_tables,
    print_results,
    ratio,
    read_text,
    validate_sql_proof_file,
)

PUBLISHED_APPROVALS = {"APPROVED", "PROPOSED"}
BLOCKED_APPROVALS = {"BLOCKED", "DEFERRED"}

ALLOWED_PLACEHOLDERS: dict[str, frozenset[str]] = {
    "owner": frozenset({"owner not assigned"}),
    "target": frozenset({"target not defined"}),
    "reason": frozenset({"none"}),
    "caveats": frozenset({"none"}),
}

APPROVED_REQUIRED = (
    ("kpi_id", ("kpi_id", "kpi", "id")),
    ("display_name", ("display_name", "display")),
    ("metric_class", ("metric_class", "class")),
    ("business_process", ("business_process", "process")),
    ("business_question", ("business_question",)),
    ("decision_supported", ("decision_supported", "decisions_supported")),
    ("action_when_bad", ("action_when_bad", "action when bad", "recommended_action")),
    ("owner", ("owner",)),
    ("formula", ("formula", "business_definition", "business definition")),
    ("grain", ("grain",)),
    ("counting_key", ("counting_key", "count_key")),
    ("source_models", ("source_models", "source models", "source_model", "source model")),
    ("date_field", ("date_field", "date field")),
    ("date_role", ("date_role", "date role")),
    ("included_rows", ("included_rows", "included rows")),
    ("excluded_rows", ("excluded_rows", "excluded rows")),
    ("dimensions", ("dimensions",)),
    ("unit_currency", ("unit_currency", "unit/currency", "unit")),
    ("format", ("format",)),
    ("aggregation", ("aggregation", "aggregation_behavior")),
    ("target", ("target", "target_source")),
    ("desired_direction", ("desired_direction", "desired direction")),
    ("sql_proof", ("sql_proof", "sql proof", "proof", "verified_by_sql_proof")),
    ("expected", ("expected", "expected_result")),
    ("actual", ("actual", "actual_result")),
    ("approval", ("approval", "approval_status")),
    ("verification", ("verification", "verification_status", "status")),
)

BLOCKED_REQUIRED = (
    ("kpi_id", ("kpi_id", "kpi", "id")),
    ("display_name", ("display_name", "display")),
    ("business_process", ("business_process", "process")),
    ("business_question", ("business_question",)),
    ("reason", ("reason", "caveats", "reason/caveats", "why correct / open question")),
    ("approval", ("approval", "approval_status")),
    ("verification", ("verification", "verification_status", "status")),
)

BLOCKED_PREFERRED = (
    ("missing_evidence", ("missing evidence", "missing_evidence")),
    ("next_action", ("next action", "recommended next action", "recommended_action")),
    ("owner", ("owner",)),
)


def contract_rows(path: Path) -> list[dict[str, str]]:
    text = read_text(path)
    rows: list[dict[str, str]] = []
    for headers, data in parse_markdown_tables(text):
        norm = [normalize_header(h) for h in headers]
        header_set = set(norm)
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


def row_has(row: dict[str, str], aliases: tuple[str, ...], field_key: str | None = None) -> bool:
    value = cell(row, *aliases)
    if not value:
        return False
    token = value.strip()
    upper = token.upper()
    if upper in {"TODO", "N/A", "TBD", "<TODO>", ""}:
        return False
    placeholders = ALLOWED_PLACEHOLDERS.get(field_key or "", frozenset())
    if token.lower() in placeholders:
        return True
    return bool(token)


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

    has_validation_type = any("validation_type" in row for row in rows)

    published = 0
    complete = 0
    for index, row in enumerate(rows, start=1):
        kpi_id = cell(row, "kpi_id", "kpi", "id", "display_name") or f"row {index}"
        approval = cell(row, "approval", "approval_status").upper()

        if approval in BLOCKED_APPROVALS:
            published += 1
            missing = [
                label
                for label, aliases in BLOCKED_REQUIRED
                if not row_has(row, aliases, field_key=label)
            ]
            if missing:
                errors.append(f"{kpi_id}: BLOCKED/DEFERRED missing fields: {', '.join(missing)}")
            else:
                complete += 1
            for label, aliases in BLOCKED_PREFERRED:
                if not row_has(row, aliases, field_key=label):
                    warnings.append(f"{kpi_id}: missing preferred BLOCKED/DEFERRED field: {label}")
            continue

        if approval not in PUBLISHED_APPROVALS and approval not in {"", "DRAFT", "PENDING"}:
            warnings.append(f"{kpi_id}: unusual approval status {approval}")
            continue
        if approval in {"", "DRAFT", "PENDING"}:
            continue

        published += 1
        missing_critical = [
            label
            for label, aliases in APPROVED_REQUIRED
            if not row_has(row, aliases, field_key=label)
        ]
        if has_validation_type and not row_has(row, ("validation_type", "validation type")):
            missing_critical.append("validation_type")

        if missing_critical:
            errors.append(f"{kpi_id}: missing critical contract fields: {', '.join(missing_critical)}")
        else:
            proof_ref = cell(row, "sql_proof", "sql proof", "proof")
            proof_result = validate_sql_proof_file(root, proof_ref)
            if proof_result.get("errors"):
                errors.append(
                    f"{kpi_id}: SQL proof issues: {'; '.join(proof_result['errors'])}"
                )
            else:
                complete += 1

    cov = ratio(complete, published)
    if cov is None:
        errors.append(
            "no published critical KPI rows to score (empty applicable set is NOT_APPLICABLE, not 100%)"
        )
    else:
        print(f"Critical KPI contract coverage: {complete}/{published} ({cov:.0%})")
        if cov < required_ratio:
            errors.append(
                f"critical KPI contract coverage {cov:.0%} below required {required_ratio:.0%}"
            )

    return print_results("Metric contract completeness check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
