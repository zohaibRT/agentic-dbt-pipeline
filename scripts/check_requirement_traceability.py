#!/usr/bin/env python3
"""Check that approved requirements are traceable to artifacts and proofs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MATRIX_PATH = Path("reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md")
BAD_STATUSES = {"OPEN", "IN_PROGRESS", "FAIL", "BLOCKED"}
VALID_STATUSES = {"OPEN", "IN_PROGRESS", "PASS", "WARN", "FAIL", "BLOCKED", "DEFERRED"}


def table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 9:
            continue
        if cells[0].lower() in {"requirement id", "id"}:
            continue
        rows.append(cells)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="dbt project root")
    args = parser.parse_args()

    root = args.root.resolve()
    matrix = root / MATRIX_PATH
    errors: list[str] = []
    warnings: list[str] = []

    if not matrix.exists():
        print(f"Missing {MATRIX_PATH}")
        return 1

    rows = table_rows(matrix.read_text(encoding="utf-8", errors="replace"))
    if not rows:
        errors.append("Requirements traceability matrix has no requirement rows")

    for index, row in enumerate(rows, start=1):
        requirement_id = row[0] or f"row {index}"
        status = row[8].upper() if len(row) > 8 else ""
        implementation = row[5] if len(row) > 5 else ""
        verification = row[6] if len(row) > 6 else ""

        if status not in VALID_STATUSES:
            errors.append(f"{requirement_id}: invalid or missing status '{status}'")
        elif status in BAD_STATUSES:
            errors.append(f"{requirement_id}: unresolved status {status}")

        if status in {"PASS", "WARN"}:
            if not implementation or implementation.upper() in {"N/A", "TODO"}:
                errors.append(f"{requirement_id}: {status} row missing implementation artifact")
            if not verification or verification.upper() in {"N/A", "TODO"}:
                errors.append(f"{requirement_id}: {status} row missing verification artifact")

        for proof_ref in re.findall(r"reports/agent/[^\s`|)]+", verification):
            proof_path = root / Path(proof_ref)
            if not proof_path.exists():
                warnings.append(f"{requirement_id}: referenced verification artifact not found: {proof_ref}")

    print("Requirement traceability summary:")
    print(f"  requirements checked: {len(rows)}")
    print(f"  warnings: {len(warnings)}")
    print(f"  errors: {len(errors)}")
    for warning in warnings[:20]:
        print(f"  WARN: {warning}")
    for error in errors[:20]:
        print(f"  ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
