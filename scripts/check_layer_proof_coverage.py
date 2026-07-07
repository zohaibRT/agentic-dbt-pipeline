#!/usr/bin/env python3
"""Check layer verification ledger coverage and referenced proof files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


LEDGER_PATH = Path("reports/agent/LAYER_VERIFICATION_LEDGER.md")
BAD_STATUSES = {"FAIL", "BLOCKED"}
VALID_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED", "DEFERRED"}


def table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 13:
            continue
        if cells[0].lower() == "phase":
            continue
        rows.append(cells)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="dbt project root")
    args = parser.parse_args()

    root = args.root.resolve()
    ledger = root / LEDGER_PATH
    errors: list[str] = []
    warnings: list[str] = []

    if not ledger.exists():
        print(f"Missing {LEDGER_PATH}")
        return 1

    rows = table_rows(ledger.read_text(encoding="utf-8", errors="replace"))
    if not rows:
        errors.append("Layer verification ledger has no model or artifact rows")

    for index, row in enumerate(rows, start=1):
        model = row[2] or f"row {index}"
        proof_files = row[10] if len(row) > 10 else ""
        overall_status = row[12].upper() if len(row) > 12 else ""

        if overall_status not in VALID_STATUSES:
            errors.append(f"{model}: invalid or missing overall status '{overall_status}'")
        elif overall_status in BAD_STATUSES:
            errors.append(f"{model}: unresolved overall status {overall_status}")

        if overall_status in {"PASS", "WARN"}:
            if not proof_files or proof_files.upper() in {"N/A", "TODO"}:
                errors.append(f"{model}: {overall_status} row missing proof files")

        for proof_ref in re.findall(r"reports/agent/[^\s`|,)]+\.sql", proof_files):
            proof_path = root / Path(proof_ref)
            if not proof_path.exists():
                warnings.append(f"{model}: referenced SQL proof not found: {proof_ref}")

    print("Layer proof coverage summary:")
    print(f"  rows checked: {len(rows)}")
    print(f"  warnings: {len(warnings)}")
    print(f"  errors: {len(errors)}")
    for warning in warnings[:20]:
        print(f"  WARN: {warning}")
    for error in errors[:20]:
        print(f"  ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
