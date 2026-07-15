#!/usr/bin/env python3
"""Check data observability / quality catalog coverage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import catalog_item_count, print_results, read_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0

    dq = insights / "kpis" / "data_quality_metric_catalog.md"
    pipeline = insights / "kpis" / "pipeline_health_metric_catalog.md"
    obs = insights / "data_observability_report.md"
    measure = insights / "kpis" / "measure_catalog.md"

    errors: list[str] = []
    warnings: list[str] = []

    dq_count = catalog_item_count(dq)
    pipe_count = catalog_item_count(pipeline)
    print(f"Observability: quality_metrics~{dq_count}, pipeline_metrics~{pipe_count}, report={obs.exists()}")

    if not dq.exists() and not obs.exists():
        warnings.append(
            "missing data_quality_metric_catalog.md and data_observability_report.md"
        )
    if not pipeline.exists():
        warnings.append("missing pipeline_health_metric_catalog.md")

    if measure.exists() and "row_count" in read_text(measure).lower() and dq_count == 0:
        errors.append(
            "measure_catalog.md mixes row_count / engineering QA without a separate "
            "data_quality_metric_catalog.md — keep technical counts out of business measures"
        )

    if obs.exists():
        text = read_text(obs).lower()
        for section in ("completeness", "freshness", "reconcil", "integrity"):
            if section not in text:
                warnings.append(f"data_observability_report.md missing section hint: {section}")

    return print_results("Data observability coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
