#!/usr/bin/env python3
"""Check time-intelligence coverage for published metrics/KPIs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import count_status_rows, load_analytics_policy, print_results, ratio, read_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required = float(policy.get("time_intelligence_coverage_required", 0.8))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    coverage = insights / "time_intelligence_coverage.md"
    contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"

    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0
    if not coverage.exists() and not contracts.exists():
        print("SKIPPED: no time-intelligence coverage or KPI contracts yet")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if not coverage.exists():
        warnings.append(
            "missing time_intelligence_coverage.md — evaluate current/prior/trend support per important metric"
        )
        return print_results("Time intelligence coverage check", errors, warnings)

    passes, total, unknowns = count_status_rows(coverage)
    cov = ratio(passes, total) if total else 0.0
    print(f"Time intelligence coverage: PASS-like={passes}/{total} ({cov:.0%}), unknown={unknowns}")

    if total == 0:
        warnings.append("time_intelligence_coverage.md has no data rows")
    elif cov < required:
        # Insufficient history should be DEFERRED/WARN rows, not silent omission
        errors.append(
            f"applicable time-intelligence coverage {cov:.0%} below required {required:.0%}"
        )

    text = read_text(coverage).lower()
    for hint in ("reporting period", "prior", "date role", "target"):
        if hint not in text:
            warnings.append(f"time_intelligence_coverage.md should discuss {hint}")

    return print_results("Time intelligence coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
