#!/usr/bin/env python3
"""Verify KPI contracts with numeric reconciliation and proof existence.

Parses columns by header. Independently calculates numeric variance and fails
when recorded PASS contradicts calculated results. Missing referenced proofs
are hard errors for APPROVED/PROPOSED KPIs.
"""

from __future__ import annotations

import argparse
import re
import sys
from decimal import Decimal
from pathlib import Path

from lib_gate_common import (
    cell,
    load_analytics_policy,
    normalize_header,
    parse_markdown_tables,
    parse_number,
    ratio,
    read_text,
    reconcile_numeric,
    resolve_proof_path,
    validate_sql_proof_file,
)


KPI_CONTRACTS = Path("reports/agent/KPI_DEFINITION_CONTRACTS.md")
METRIC_MATRIX = Path("reports/agent/METRIC_VERIFICATION_MATRIX.md")
BAD_STATUSES = {"FAIL", "BLOCKED"}
VALID_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "DEFERRED", "SKIPPED"}
VALID_APPROVALS = {"APPROVED", "PROPOSED", "DEFERRED", "BLOCKED", "DRAFT", "PENDING"}
NUMERIC_TYPES = {
    "numeric_exact",
    "numeric_tolerance",
    "ratio_tolerance",
    "row_count_match",
}


def detect_contract_schema(headers: list[str]) -> str:
    norm = {normalize_header(h) for h in headers}
    if {"display_name", "business_question", "counting_key", "decision_supported"} & norm:
        return "expanded"
    if "sql_proof" in norm or "approval_status" in norm or "approval" in norm:
        if {"verification", "verification_status", "expected", "expected_result"} & norm:
            return "legacy_with_verification"
        return "legacy"
    return "unknown"


def rows_from_first_matching_table(path: Path, matcher) -> tuple[str, list[dict[str, str]]]:
    text = read_text(path)
    for headers, data in parse_markdown_tables(text):
        schema = matcher(headers)
        if schema == "unknown":
            continue
        norm_headers = [normalize_header(h) for h in headers]
        rows: list[dict[str, str]] = []
        for cells in data:
            if not cells or cells[0].upper() == "TODO":
                continue
            row = {
                norm_headers[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm_headers))
                if norm_headers[i]
            }
            rows.append(row)
        return schema, rows
    return "unknown", []


def proof_hard_check(root: Path, label: str, proof_ref: str, errors: list[str]) -> bool:
    result = validate_sql_proof_file(root, proof_ref)
    if not result.get("exists"):
        errors.append(f"{label}: referenced SQL proof not found: {proof_ref}")
        return False
    for err in result.get("errors") or []:
        errors.append(f"{label}: {err}")
    ok = bool(result.get("has_sql") and result.get("has_expected") and result.get("has_captured") and result.get("has_status"))
    if not ok and not result.get("errors"):
        errors.append(f"{label}: SQL proof incomplete at {result.get('path')}")
    return ok and not result.get("errors")


def numeric_reconcile_row(
    label: str,
    expected: str,
    actual: str,
    tolerance: str,
    recorded_status: str,
    recorded_diff: str,
    errors: list[str],
    warnings: list[str],
) -> bool:
    """Return True when reconciliation succeeds within tolerance."""
    result = reconcile_numeric(expected, actual, tolerance or "0")
    calc = result["calculated_status"]
    if result["expected"] is None or result["actual"] is None:
        # Nonnumeric
        if not expected or not actual:
            errors.append(f"{label}: missing expected or actual for numeric reconciliation")
            return False
        warnings.append(f"{label}: nonnumeric expected/actual — require explicit validation_type")
        return recorded_status in {"PASS", "WARN"}

    if recorded_diff and recorded_diff.upper() not in {"N/A", "TODO", "NONE", ""}:
        parsed_diff = parse_number(recorded_diff.replace("±", "").split()[0])
        if parsed_diff is not None and result["abs_diff"] is not None:
            if abs(parsed_diff - result["abs_diff"]) > Decimal("0.0001") and "relative" not in (
                tolerance or ""
            ).lower():
                # Allow relative/tolerance cell formatting differences softly
                if abs(parsed_diff - result["abs_diff"]) > Decimal("0.01"):
                    errors.append(
                        f"{label}: recorded Diff {recorded_diff!r} does not match "
                        f"calculated abs_diff {result['abs_diff']}"
                    )

    if recorded_status == "PASS" and calc == "FAIL":
        errors.append(
            f"{label}: recorded Verification PASS contradicts calculated variance "
            f"(expected={expected!r}, actual={actual!r}, abs_diff={result['abs_diff']}, "
            f"tolerance={tolerance!r})"
        )
        return False
    if calc == "FAIL" and recorded_status not in {"FAIL", "BLOCKED", "WARN"}:
        errors.append(f"{label}: calculated reconciliation FAIL but status is {recorded_status}")
        return False
    if calc == "PASS":
        return True
    if recorded_status == "WARN":
        warnings.append(f"{label}: reconciliation WARN accepted with variance {result['abs_diff']}")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    root = args.root.resolve()
    policy = load_analytics_policy(root)
    recon_required = float(policy.get("critical_reconciliation_coverage_required", 1.0))
    errors: list[str] = []
    warnings: list[str] = []

    contracts_path = root / KPI_CONTRACTS
    matrix_path = root / METRIC_MATRIX

    schema = "unknown"
    contracts: list[dict[str, str]] = []
    if not contracts_path.exists():
        errors.append(f"Missing {KPI_CONTRACTS}")
    else:
        schema, contracts = rows_from_first_matching_table(contracts_path, detect_contract_schema)
        if schema == "unknown":
            errors.append("KPI_DEFINITION_CONTRACTS.md has no recognizable contract table headers")
        elif not contracts:
            errors.append("KPI definition contracts file has no contract rows")
        else:
            print(f"Detected KPI contract schema: {schema}")
            if schema.startswith("legacy"):
                warnings.append("legacy KPI contract schema detected — migrate to expanded schema")

    matrix: list[dict[str, str]] = []
    if not matrix_path.exists():
        errors.append(f"Missing {METRIC_MATRIX}")
    else:
        _schema, matrix = rows_from_first_matching_table(
            matrix_path,
            lambda headers: "legacy" if "status" in {normalize_header(h) for h in headers} else "unknown",
        )
        if not matrix:
            errors.append("Metric verification matrix has no metric rows")

    critical_total = 0
    critical_reconciled = 0
    blocked_or_deferred = 0

    for index, row in enumerate(contracts, start=1):
        kpi_id = (
            cell(row, "kpi_id", "kpi", "id", "key_performance_indicator", "display_name")
            or f"KPI row {index}"
        )
        approval = cell(row, "approval", "approval_status", "business_approval_status").upper()
        verification = cell(row, "verification", "verification_status").upper()
        if not verification:
            status_fallback = cell(row, "status").upper()
            if status_fallback in VALID_STATUSES:
                verification = status_fallback
        proof = cell(row, "sql_proof", "verified_by_sql_proof", "proof")
        expected = cell(row, "expected", "expected_result", "acceptance_rule")
        actual = cell(row, "actual", "actual_result")
        tolerance = cell(row, "diff_tolerance", "diff_/_tolerance", "tolerance", "reconciliation_tolerance", "diff")
        validation_type = cell(row, "validation_type", "recon_type", "contract_validation_type").lower()
        recorded_diff = cell(row, "diff", "difference", "abs_diff")

        if approval in {"BLOCKED", "DEFERRED"}:
            blocked_or_deferred += 1
            reason = cell(row, "reason", "why_correct_/_open_question", "why_correct_open_question", "caveats")
            if not reason:
                errors.append(f"{kpi_id}: BLOCKED/DEFERRED requires reason / missing evidence")
            if proof:
                if resolve_proof_path(root, proof) is None:
                    errors.append(f"{kpi_id}: blocker/deferred proof artifact not found: {proof}")
            continue

        if approval in {"APPROVED", "PROPOSED"} or (not approval and verification in {"PASS", "WARN"}):
            critical_total += 1
            if verification not in VALID_STATUSES:
                errors.append(f"{kpi_id}: invalid or missing verification status '{verification}'")
                continue
            if verification in BAD_STATUSES:
                errors.append(f"{kpi_id}: unresolved verification status {verification}")
                continue
            if not proof or proof.upper() in {"N/A", "TODO"}:
                errors.append(f"{kpi_id}: missing SQL proof reference")
                continue
            proof_ok = proof_hard_check(root, kpi_id, proof, errors)
            if not expected or not actual:
                errors.append(f"{kpi_id}: missing expected or actual result")
                continue

            vtype = validation_type or "numeric_tolerance"
            reconciled = False
            if vtype in NUMERIC_TYPES or parse_number(expected) is not None:
                reconciled = numeric_reconcile_row(
                    kpi_id, expected, actual, tolerance or "0", verification, recorded_diff, errors, warnings
                )
            elif vtype in {"acceptance_rule", "set_match", "blocked", "deferred"}:
                if not expected:
                    errors.append(f"{kpi_id}: nonnumeric validation requires acceptance rule")
                else:
                    reconciled = verification in {"PASS", "WARN"}
            else:
                warnings.append(f"{kpi_id}: unknown validation_type {vtype!r}; treating as acceptance_rule")
                reconciled = verification in {"PASS", "WARN"} and proof_ok

            if reconciled and proof_ok and verification in {"PASS", "WARN"}:
                critical_reconciled += 1

        elif verification in {"PASS", "WARN"}:
            # Untagged but verified rows still need proof existence
            if proof:
                proof_hard_check(root, kpi_id, proof, errors)

    matrix_ok = 0
    matrix_critical = 0
    for index, row in enumerate(matrix, start=1):
        metric_id = cell(row, "metric", "metric_id", "id", "kpi") or f"Metric row {index}"
        status = cell(row, "status", "verification_status").upper()
        source_proof = cell(row, "source_proof")
        mart_proof = cell(row, "current_model_proof", "mart_proof", "current_proof")
        expected = cell(row, "expected_result", "expected")
        actual = cell(row, "actual_result", "actual")
        tolerance = cell(row, "diff", "tolerance", "diff_tolerance")

        if status in {"DEFERRED", "SKIPPED"}:
            continue
        if status in BAD_STATUSES:
            errors.append(f"{metric_id}: unresolved status {status}")
            continue
        matrix_critical += 1
        if status not in VALID_STATUSES:
            errors.append(f"{metric_id}: invalid or missing status '{status}'")
            continue
        if not source_proof or source_proof.upper() in {"N/A", "TODO"}:
            errors.append(f"{metric_id}: missing source proof")
            continue
        if not mart_proof or mart_proof.upper() in {"N/A", "TODO"}:
            errors.append(f"{metric_id}: missing mart proof")
            continue
        proof_hard_check(root, f"{metric_id} source", source_proof, errors)
        proof_hard_check(root, f"{metric_id} mart", mart_proof, errors)
        if not expected or not actual:
            errors.append(f"{metric_id}: missing expected or actual result")
            continue
        if numeric_reconcile_row(metric_id, expected, actual, tolerance or "0", status, "", errors, warnings):
            matrix_ok += 1

    cov = ratio(critical_reconciled, critical_total)
    print("Metric reconciliation summary:")
    print(f"  KPI contract schema: {schema}")
    print(f"  KPI contracts checked: {len(contracts)}")
    print(f"  metric matrix rows checked: {len(matrix)}")
    print(f"  blocked/deferred KPIs: {blocked_or_deferred}")
    if cov is None:
        print("  critical reconciliation coverage: N/A (no APPROVED/PROPOSED KPIs)")
        if contracts:
            warnings.append("no APPROVED/PROPOSED KPIs to reconcile (empty set is not 100%)")
    else:
        print(f"  critical reconciliation coverage: {critical_reconciled}/{critical_total} ({cov:.0%})")
        if cov < recon_required:
            errors.append(
                f"critical reconciliation coverage {cov:.0%} below required {recon_required:.0%}"
            )
    if matrix_critical:
        print(f"  matrix reconciled: {matrix_ok}/{matrix_critical}")

    print(f"  warnings: {len(warnings)}")
    print(f"  errors: {len(errors)}")
    for warning in warnings[:30]:
        print(f"  WARN: {warning}")
    for error in errors[:40]:
        print(f"  ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
