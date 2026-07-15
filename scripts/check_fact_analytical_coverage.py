#!/usr/bin/env python3
"""Check per-fact analytical coverage contracts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import (
    count_gold_facts,
    count_status_rows,
    load_analytics_policy,
    markdown_table_rows,
    print_results,
    ratio,
    read_text,
)


COVERAGE_HINTS = (
    "grain",
    "volume",
    "status",
    "time",
    "quality",
    "reconcil",
    "dimension",
    "business question",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required = float(policy.get("critical_fact_coverage_required", 1.0))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    contracts = insights / "fact_coverage_contracts.md"
    gold_facts = count_gold_facts(root)

    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0
    if gold_facts == 0 and not contracts.exists():
        print("SKIPPED: no gold facts / fact contracts yet")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if not contracts.exists():
        errors.append("missing reports/agent/09_analytics_insights/fact_coverage_contracts.md")
        return print_results("Fact analytical coverage check", errors, warnings)

    passes, total, unknowns = count_status_rows(contracts)
    coverage = ratio(passes, total) if total else 0.0
    rows = markdown_table_rows(contracts)
    print(f"Fact coverage contracts: PASS-like={passes}/{total} ({coverage:.0%}), rows={len(rows)}")

    if total == 0:
        errors.append("fact_coverage_contracts.md has no data rows")
    elif coverage < required:
        errors.append(f"critical fact coverage {coverage:.0%} below required {required:.0%}")

    text = read_text(contracts).lower()
    missing = [h for h in COVERAGE_HINTS if h not in text]
    if missing:
        warnings.append("fact contracts missing evaluation hints: " + ", ".join(missing))

    if gold_facts and total < gold_facts:
        warnings.append(
            f"fact_coverage_contracts rows ({total}) < detected gold facts ({gold_facts})"
        )

    return print_results("Fact analytical coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
