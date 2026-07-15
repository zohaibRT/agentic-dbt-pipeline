#!/usr/bin/env python3
"""Fail when business report pages leak technical SQL-style names or raw floats.

Enforces reporting-coverage-requirements.md Rule 5c and report-page-contract.md
hard presentation failures for readability.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SNAKE_TECH_RE = re.compile(
    r"\b(?:dim|fct|mart|stg|int)_[a-z0-9_]+\b"
    r"|\b[a-z]+(?:_[a-z0-9]+){3,}\b"
)
RAW_FLOAT_RE = re.compile(r"\b0\.\d{6,}\b|\b\d+\.\d{6,}\b")
DISPLAY_HINTS = (
    "display_name",
    "display name",
    "formatted_value",
    "formatted value",
    "business_label",
)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def collect_presentation_text(root: Path) -> tuple[str, list[Path]]:
    presentation = root / "reports" / "agent" / "10_presentation"
    paths: list[Path] = []
    chunks: list[str] = []
    if not presentation.exists():
        return "", paths
    for path in presentation.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".py", ".md", ".js"}:
            continue
        if "sql_verification" in path.parts:
            continue
        paths.append(path)
        chunks.append(read_text(path))
    return "\n".join(chunks), paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    text, paths = collect_presentation_text(root)
    if not text:
        print("SKIPPED: no presentation artifacts found")
        return 0

    lower = text.lower()
    errors: list[str] = []
    warnings: list[str] = []

    # Focus on business page surfaces when identifiable
    business_markers = (
        "all measures",
        "all metrics",
        "executive",
        "overview",
        "measure_board",
        "metric_board",
    )
    business_focus = any(m in lower for m in business_markers)

    tech_hits = SNAKE_TECH_RE.findall(lower)
    dim_row_counts = [h for h in tech_hits if h.startswith("dim_") and "row_count" in h]
    raw_floats = RAW_FLOAT_RE.findall(text)
    has_display = any(h in lower for h in DISPLAY_HINTS)

    print(
        f"Business readability: files={len(paths)}, tech_name_hits~{len(tech_hits)}, "
        f"dim_row_count_hits~{len(dim_row_counts)}, raw_float_hits~{len(raw_floats)}, "
        f"display_hints={has_display}"
    )

    if business_focus and not has_display:
        errors.append(
            "business pages lack display_name/formatted_value fields — "
            "do not show snake_case warehouse ids as primary labels"
        )

    if len(dim_row_counts) >= 5 and "dimensions" not in lower:
        warnings.append(
            "many dim_*_row_count labels found without a Dimensions browse surface — "
            "move QA counts off executive/business measure pages"
        )

    if business_focus and len(raw_floats) >= 8 and not has_display:
        errors.append(
            "business pages expose many high-precision raw floats without formatting helpers"
        )
    elif business_focus and len(raw_floats) >= 8:
        warnings.append(
            "high-precision raw floats present — ensure UI shows formatted_value (%, currency, rounded decimals)"
        )

    if "reporting period" not in lower and "all time" not in lower and "period" not in lower:
        warnings.append(
            "no explicit reporting period / All time labeling detected on presentation pages"
        )

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")

    if errors:
        print("Report business readability check FAILED")
        return 1
    if warnings:
        print("Report business readability check PASSED with warnings")
        return 0
    print("Report business readability check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
