#!/usr/bin/env python3
"""Verify KPI contracts and metric reconciliation matrix evidence."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


KPI_CONTRACTS = Path("reports/agent/KPI_DEFINITION_CONTRACTS.md")
METRIC_MATRIX = Path("reports/agent/METRIC_VERIFICATION_MATRIX.md")
BAD_STATUSES = {"FAIL", "BLOCKED"}
VALID_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "DEFERRED", "SKIPPED"}


def table_rows(text: str, min_columns: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < min_columns:
            continue
        first = cells[0].lower()
        if first in {"kpi id", "metric id"}:
            continue
        rows.append(cells)
    return rows


def check_refs(root: Path, label: str, text: str, warnings: list[str]) -> None:
    for proof_ref in re.findall(r"reports/agent/[^\s`|,)]+\.sql", text):
        proof_path = root / Path(proof_ref)
        if not proof_path.exists():
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

    if not contracts_path.exists():
        errors.append(f"Missing {KPI_CONTRACTS}")
        contract_rows: list[list[str]] = []
    else:
        contract_rows = table_rows(contracts_path.read_text(encoding="utf-8", errors="replace"), 16)

    if not matrix_path.exists():
        errors.append(f"Missing {METRIC_MATRIX}")
        matrix_rows: list[list[str]] = []
    else:
        matrix_rows = table_rows(matrix_path.read_text(encoding="utf-8", errors="replace"), 13)

    if contracts_path.exists() and not contract_rows:
        errors.append("KPI definition contracts file has no contract rows")
    if matrix_path.exists() and not matrix_rows:
        errors.append("Metric verification matrix has no metric rows")

    for index, row in enumerate(contract_rows, start=1):
        kpi_id = row[0] or f"KPI row {index}"
        approval_status = row[14].upper() if len(row) > 14 else ""
        verification_status = row[15].upper() if len(row) > 15 else ""
        proof = row[10] if len(row) > 10 else ""
        expected = row[11] if len(row) > 11 else ""
        actual = row[12] if len(row) > 12 else ""

        if verification_status not in VALID_STATUSES:
            errors.append(f"{kpi_id}: invalid or missing verification status '{verification_status}'")
        elif verification_status in BAD_STATUSES:
            errors.append(f"{kpi_id}: unresolved verification status {verification_status}")

        if verification_status in {"PASS", "WARN"}:
            if approval_status not in {"APPROVED", "PROPOSED", "DEFERRED", "BLOCKED"}:
                errors.append(f"{kpi_id}: invalid or missing approval status '{approval_status}'")
            if not proof or proof.upper() in {"N/A", "TODO"}:
                errors.append(f"{kpi_id}: missing SQL proof reference")
            if not expected or not actual:
                errors.append(f"{kpi_id}: missing expected or actual result")

        check_refs(root, kpi_id, proof, warnings)

    for index, row in enumerate(matrix_rows, start=1):
        metric_id = row[0] or f"Metric row {index}"
        status = row[12].upper() if len(row) > 12 else ""
        source_proof = row[5] if len(row) > 5 else ""
        mart_proof = row[6] if len(row) > 6 else ""
        expected = row[9] if len(row) > 9 else ""
        actual = row[10] if len(row) > 10 else ""

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

        check_refs(root, metric_id, " ".join(row), warnings)

    print("Metric reconciliation summary:")
    print(f"  KPI contracts checked: {len(contract_rows)}")
    print(f"  metric matrix rows checked: {len(matrix_rows)}")
    print(f"  warnings: {len(warnings)}")
    print(f"  errors: {len(errors)}")
    for warning in warnings[:20]:
        print(f"  WARN: {warning}")
    for error in errors[:20]:
        print(f"  ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
