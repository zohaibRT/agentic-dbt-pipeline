#!/usr/bin/env python3
"""Check model classification coverage for in-scope models."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import load_analytics_policy, markdown_table_rows, print_results, ratio, read_text


def list_built_models(root: Path) -> set[str]:
    models: set[str] = set()
    models_dir = root / "models"
    if not models_dir.exists():
        return models
    for path in models_dir.rglob("*.sql"):
        if any(part.startswith(".") for part in path.parts):
            continue
        models.add(path.stem.lower())
    return models


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required = float(policy.get("model_classification_coverage_required", 1.0))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    classification = insights / "model_classification.md"
    built = list_built_models(root)

    if not insights.exists() and not built:
        print("SKIPPED: no analytics insights or models yet")
        return 0
    if not built:
        print("SKIPPED: no SQL models under models/")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if not classification.exists():
        errors.append("missing reports/agent/09_analytics_insights/model_classification.md")
        return print_results("Model classification coverage check", errors, warnings)

    rows = markdown_table_rows(classification)
    classified = {cells[0].lower().replace("`", "") for cells in rows if cells}
    missing = sorted(built - classified)
    coverage = ratio(len(built) - len(missing), len(built))
    if coverage is None:
        errors.append("no built models to classify (empty inventory is NOT_APPLICABLE, not 100%)")
    else:
        print(f"Model classification: classified={len(classified & built)}/{len(built)} ({coverage:.0%})")
        if coverage < required:
            errors.append(
                f"model classification coverage {coverage:.0%} below required {required:.0%}; "
                f"missing examples: {', '.join(missing[:8])}"
            )
        elif missing:
            warnings.append(f"unclassified models remain: {', '.join(missing[:8])}")

    text = read_text(classification).lower()
    if "class" not in text and "model class" not in text:
        warnings.append("model_classification.md should include a model class column")

    return print_results("Model classification coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
