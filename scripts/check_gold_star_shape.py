#!/usr/bin/env python3
"""Check that gold/marts is not silently fact-only without a dimension register."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FACT_RE = re.compile(r"(?i)\bfct_[a-z0-9_]+\b|\bfact_[a-z0-9_]+\b")
DIM_RE = re.compile(r"(?i)\bdim_[a-z0-9_]+\b")
BRIDGE_RE = re.compile(r"(?i)\bbridge_[a-z0-9_]+\b")


def list_models(models_root: Path) -> tuple[list[str], list[str], list[str]]:
    facts: list[str] = []
    dims: list[str] = []
    bridges: list[str] = []
    if not models_root.exists():
        return facts, dims, bridges
    for path in models_root.rglob("*.sql"):
        name = path.stem
        lower = name.lower()
        if lower.startswith("dim_"):
            dims.append(name)
        elif lower.startswith("fct_") or lower.startswith("fact_"):
            facts.append(name)
        elif lower.startswith("bridge_"):
            bridges.append(name)
    return sorted(facts), sorted(dims), sorted(bridges)


def report_has_dimension_inventory(text: str) -> bool:
    lower = text.lower()
    markers = (
        "dimension inventory",
        "dimension and bridge decisions",
        "candidate dimension",
        "dimensions built",
        "dimensions recommended",
    )
    if not any(marker in lower for marker in markers):
        return False
    decision_markers = ("blocked", "deferred", "build", "not_needed", "privacy")
    return any(marker in lower for marker in decision_markers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    gold_models = root / "models" / "gold"
    marts_models = root / "models" / "marts"
    models_root = gold_models if gold_models.exists() else marts_models

    facts, dims, bridges = list_models(models_root)
    report_paths = [
        root / "reports" / "agent" / "05_gold" / "gold_report.md",
        root / "reports" / "agent" / "05_gold" / "gold_discovery.md",
        root / "reports" / "agent" / "marts_report.md",
    ]
    report_text = ""
    for path in report_paths:
        if path.exists():
            report_text += "\n" + path.read_text(encoding="utf-8", errors="replace")

    print(f"Models root: {models_root if models_root.exists() else '(missing)'}")
    print(f"Facts: {len(facts)} | Dimensions: {len(dims)} | Bridges: {len(bridges)}")
    if facts:
        print("Fact models: " + ", ".join(facts))
    if dims:
        print("Dimension models: " + ", ".join(dims))
    if bridges:
        print("Bridge models: " + ", ".join(bridges))

    if not facts and not dims:
        print("SKIPPED | no gold/marts fact or dimension models found yet")
        return 0

    if facts and dims:
        print("PASS | gold/marts has both facts and dimensions")
        return 0

    if facts and not dims:
        has_register = report_has_dimension_inventory(report_text)
        if has_register:
            print(
                "WARN | facts exist with zero dimensions, but a dimension inventory/"
                "blocked-deferred register was found in gold reports. "
                "Treat star schema as incomplete until dimensions are built or explicitly approved as deferred."
            )
            return 0
        print(
            "FAIL | facts exist with zero dim_ models and no dimension inventory/"
            "blocked-deferred register in gold_report.md or gold_discovery.md. "
            "Read references/gold-dimension-completeness.md. "
            "Build privacy-safe dimensions where possible, or document each missing dimension as BLOCKED/DEFERRED with proof."
        )
        return 1

    print("WARN | dimensions exist without facts; confirm this is intentional")
    return 0


if __name__ == "__main__":
    sys.exit(main())
