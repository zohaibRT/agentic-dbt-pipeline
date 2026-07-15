#!/usr/bin/env python3
"""Check KPI / metric contract completeness for published metrics.

Looks for required decision-oriented fields in KPI_DEFINITION_CONTRACTS.md
and related analytics contract artifacts.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_FIELD_HINTS = (
    ("business_question", ("business question", "business_question")),
    ("decision_supported", ("decision supported", "decision_supported", "decisions supported")),
    ("action_when_bad", ("action when bad", "action_when_bad", "recommended action")),
    ("owner", ("owner",)),
    ("display_name", ("display name", "display_name")),
    ("aggregation_behavior", ("aggregation", "additive", "semi_additive", "non_additive", "aggregation_behavior")),
    ("desired_direction", ("desired direction", "desired_direction", "increase", "decrease")),
    ("target_or_not_defined", ("target", "target not defined", "target_source")),
    ("sql_proof", ("sql proof", "sql_proof", "verified by sql")),
    ("approval_status", ("approval", "approved", "proposed", "deferred", "blocked")),
)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not contracts.exists() and not insights.exists():
        print("SKIPPED: no KPI contracts or analytics folder")
        return 0
    if not contracts.exists():
        print("SKIPPED: KPI_DEFINITION_CONTRACTS.md not found yet")
        return 0

    text = read_text(contracts)
    lower = text.lower()
    data_rows = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or re.match(r"^\|\s*-+", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].lower()
        if first in {"kpi id", "id", "name", ""} or first.startswith("<"):
            continue
        data_rows += 1

    print(f"Metric contract completeness: contract_rows~{data_rows}")

    errors: list[str] = []
    warnings: list[str] = []

    if data_rows == 0:
        warnings.append("KPI_DEFINITION_CONTRACTS.md has no data rows yet")
    else:
        missing = []
        for label, hints in REQUIRED_FIELD_HINTS:
            if not any(h in lower for h in hints):
                missing.append(label)
        if missing:
            # Hard fail only for the strongest decision fields when contracts exist
            critical = {"business_question", "decision_supported", "action_when_bad", "sql_proof", "approval_status"}
            critical_missing = [m for m in missing if m in critical]
            other_missing = [m for m in missing if m not in critical]
            if critical_missing:
                errors.append(
                    "KPI contracts missing critical fields: " + ", ".join(critical_missing)
                )
            if other_missing:
                warnings.append(
                    "KPI contracts missing recommended fields: " + ", ".join(other_missing)
                )

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")

    if errors:
        print("Metric contract completeness check FAILED")
        return 1
    if warnings:
        print("Metric contract completeness check PASSED with warnings")
        return 0
    print("Metric contract completeness check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
