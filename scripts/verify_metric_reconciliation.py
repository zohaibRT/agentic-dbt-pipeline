#!/usr/bin/env python3
"""Verify KPI contracts and metric reconciliation matrix evidence.

Parses Markdown tables by header name. Supports:
- Legacy contract schema (older templates)
- Expanded production contract schema from kpi-definition-contract.md

Fixed column positions are intentionally not used.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lib_gate_common import cell, normalize_header, parse_markdown_tables, read_text


KPI_CONTRACTS = Path("reports/agent/KPI_DEFINITION_CONTRACTS.md")
METRIC_MATRIX = Path("reports/agent/METRIC_VERIFICATION_MATRIX.md")
BAD_STATUSES = {"FAIL", "BLOCKED"}
VALID_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "DEFERRED", "SKIPPED"}
VALID_APPROVALS = {"APPROVED", "PROPOSED", "DEFERRED", "BLOCKED", "DRAFT", "PENDING"}


def detect_contract_schema(headers: list[str]) -> str:
    norm = {normalize_header(h) for h in headers}
    if {"display_name", "business_question", "counting_key", "decision_supported"} & norm:
        return "expanded"
    if "sql_proof" in norm or "approval_status" in norm or "approval" in norm:
        if "verification" in norm or "verification_status" in norm or "expected" in norm or "expected_result" in norm:
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


def check_refs(root: Path, label: str, text: str, warnings: list[str]) -> None:
    for proof_ref in re.findall(r"reports/agent/[^\s`|,)]+\.sql", text):
        if not (root / Path(proof_ref)).exists():
            warnings.append(f"{label}: referenced SQL proof not found: {proof_ref}")
    for proof_ref in re.findall(r"(?<![A-Za-z0-9_./-])([\w./-]*sql_proofs/[\w./-]+\.sql)", text):
        candidates = [root / proof_ref, root / "reports" / "agent" / proof_ref]
        if not any(p.exists() for p in candidates):
            warnings.append(f"{label}: referenced SQL proof not found: {proof_ref}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="dbt project root")
    args = parser.parse_args()

    root = args.root.resolve()
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
            errors.append(
                "KPI_DEFINITION_CONTRACTS.md has no recognizable contract table headers "
                "(need SQL Proof / Approval columns at minimum)"
            )
        elif not contracts:
            errors.append("KPI definition contracts file has no contract rows")
        else:
            print(f"Detected KPI contract schema: {schema}")

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

    for index, row in enumerate(contracts, start=1):
        kpi_id = (
            cell(row, "kpi_id", "kpi", "id", "key_performance_indicator", "display_name")
            or f"KPI row {index}"
        )
        approval = cell(row, "approval", "approval_status", "business_approval_status").upper()
        verification = cell(row, "verification", "verification_status").upper()
        # Expanded schema uses Verification; legacy may only have Approval Status
        if not verification:
            status_fallback = cell(row, "status").upper()
            if status_fallback in VALID_STATUSES:
                verification = status_fallback
        proof = cell(row, "sql_proof", "verified_by_sql_proof", "proof")
        expected = cell(row, "expected", "expected_result")
        actual = cell(row, "actual", "actual_result")

        if not verification and approval:
            if approval in {"APPROVED", "PROPOSED"}:
                verification = "PASS" if expected and actual and proof else "WARN"
            elif approval in {"DEFERRED", "BLOCKED", "DRAFT", "PENDING"}:
                verification = approval if approval in VALID_STATUSES else "DEFERRED"

        if verification not in VALID_STATUSES:
            errors.append(f"{kpi_id}: invalid or missing verification status '{verification}'")
        elif verification in BAD_STATUSES:
            errors.append(f"{kpi_id}: unresolved verification status {verification}")

        if verification in {"PASS", "WARN"}:
            if approval and approval not in VALID_APPROVALS:
                errors.append(f"{kpi_id}: invalid approval status '{approval}'")
            if not approval:
                errors.append(f"{kpi_id}: missing approval status")
            if not proof or proof.upper() in {"N/A", "TODO"}:
                errors.append(f"{kpi_id}: missing SQL proof reference")
            if schema == "expanded" and (not expected or not actual):
                errors.append(f"{kpi_id}: missing expected or actual result")
            elif schema != "expanded" and (not expected or not actual):
                warnings.append(f"{kpi_id}: legacy contract missing expected/actual — add columns when migrating")

        check_refs(root, kpi_id, proof, warnings)

    for index, row in enumerate(matrix, start=1):
        metric_id = cell(row, "metric", "metric_id", "id", "kpi") or f"Metric row {index}"
        status = cell(row, "status", "verification_status").upper()
        source_proof = cell(row, "source_proof")
        mart_proof = cell(row, "current_model_proof", "mart_proof", "current_proof")
        expected = cell(row, "expected_result", "expected")
        actual = cell(row, "actual_result", "actual")

        if status not in VALID_STATUSES:
            errors.append(f"{metric_id}: invalid or missing status '{status}'")
        elif status in BAD_STATUSES:
            errors.append(f"{metric_id}: unresolved status {status}")

        if status in {"PASS", "WARN"}:
            if not source_proof or source_proof.upper() in {"N/A", "TODO"}:
                errors.append(f"{metric_id}: missing source proof")
            if not mart_proof or mart_proof.upper() in {"N/A", "TODO"}:
                errors.append(f"{metric_id}: missing mart proof")
            if not expected or not actual:
                errors.append(f"{metric_id}: missing expected or actual result")

        check_refs(root, metric_id, " ".join(row.values()), warnings)

    print("Metric reconciliation summary:")
    print(f"  KPI contract schema: {schema}")
    print(f"  KPI contracts checked: {len(contracts)}")
    print(f"  metric matrix rows checked: {len(matrix)}")
    print(f"  warnings: {len(warnings)}")
    print(f"  errors: {len(errors)}")
    for warning in warnings[:20]:
        print(f"  WARN: {warning}")
    for error in errors[:20]:
        print(f"  ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
