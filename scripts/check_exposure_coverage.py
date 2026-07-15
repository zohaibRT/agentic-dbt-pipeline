#!/usr/bin/env python3
"""Check downstream exposure coverage documentation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import markdown_table_rows, print_results, read_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    insights = root / "reports" / "agent" / "09_analytics_insights"
    presentation = root / "reports" / "agent" / "10_presentation"
    exposures_yml = list((root / "models").rglob("**/exposures*.yml")) if (root / "models").exists() else []
    coverage = insights / "exposure_coverage.md"

    if not insights.exists() and not presentation.exists() and not exposures_yml:
        print("SKIPPED: no analytics/presentation/exposures yet")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if presentation.exists() and not coverage.exists() and not exposures_yml:
        warnings.append(
            "presentation exists but no exposure_coverage.md or models/**/exposures*.yml found"
        )
        return print_results("Exposure coverage check", errors, warnings)

    if coverage.exists():
        rows = markdown_table_rows(coverage)
        text = read_text(coverage).lower()
        print(f"Exposure coverage: rows~{len(rows)}")
        if len(rows) == 0:
            warnings.append("exposure_coverage.md has no data rows")
        for hint in ("owner", "dependent", "business purpose", "criticality", "validation"):
            if hint not in text:
                warnings.append(f"exposure_coverage.md missing hint: {hint}")
    else:
        print(f"Exposure YAML files found: {len(exposures_yml)}")
        if not exposures_yml:
            warnings.append("no exposure coverage artifact found")

    return print_results("Exposure coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
