#!/usr/bin/env python3
"""Check per-fact analytical coverage contracts.

Maps each detected gold fact/event model to an exact contract row and requires
applicable analytical families to be evaluated with an explicit Status column.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib_gate_common import (
    cell,
    list_gold_fact_names,
    load_analytics_policy,
    named_status,
    print_results,
    ratio,
    table_dicts,
)


REQUIRED_EVAL_FIELDS = (
    ("grain", ("grain",)),
    ("volume", ("volume",)),
    ("status_family", ("status", "status_mix", "status_distribution")),
    ("time", ("time", "time_intelligence", "date_coverage")),
    ("quality", ("quality", "data_quality")),
    ("reconciliation", ("reconciliation", "reconcile")),
    ("dimensions", ("dimensions", "dimension", "segmentation")),
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
    gold_facts = list_gold_fact_names(root)

    if not insights.exists():
        print("SKIPPED: no analytics insight folder")
        return 0
    if not gold_facts and not contracts.exists():
        print("SKIPPED: no gold facts / fact contracts yet")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    if not contracts.exists():
        errors.append("missing reports/agent/09_analytics_insights/fact_coverage_contracts.md")
        return print_results("Fact analytical coverage check", errors, warnings)

    rows = table_dicts(
        contracts,
        required_any_headers=("fact", "fact_model", "model", "name", "status"),
    )
    by_fact: dict[str, dict[str, str]] = {}
    for row in rows:
        name = cell(row, "fact", "fact_model", "model", "name").lower().replace("`", "")
        if not name:
            continue
        by_fact[name] = row

    print(f"Fact coverage contracts: rows={len(by_fact)}, gold_facts={len(gold_facts)}")

    if gold_facts:
        missing = [f for f in gold_facts if f not in by_fact]
        if missing:
            errors.append(
                "fact_coverage_contracts missing rows for gold facts: " + ", ".join(missing)
            )
        extra = [f for f in by_fact if f not in gold_facts and (f.startswith("fct_") or f.startswith("mart_"))]
        if extra:
            warnings.append("contract rows without matching gold SQL model: " + ", ".join(sorted(extra)))

    complete = 0
    applicable = 0
    for fact_name in gold_facts or sorted(by_fact):
        row = by_fact.get(fact_name)
        if not row:
            continue
        applicable += 1
        status = named_status(row)
        row_missing = []
        for label, aliases in REQUIRED_EVAL_FIELDS:
            value = cell(row, *aliases)
            if not value or value.strip().upper() in {"TODO", "TBD"}:
                row_missing.append(label)
        if status == "UNKNOWN":
            errors.append(f"{fact_name}: missing explicit Status column value")
        elif status == "FAIL":
            errors.append(f"{fact_name}: fact coverage Status is FAIL/BLOCKED")
        elif row_missing:
            errors.append(f"{fact_name}: incomplete analytical evaluation for: {', '.join(row_missing)}")
        elif status == "PASS":
            complete += 1
        elif status == "WARN":
            warnings.append(f"{fact_name}: fact coverage Status is WARN/DEFERRED")
            complete += 0
        elif status == "NOT_APPLICABLE":
            applicable -= 1

    cov = ratio(complete, applicable)
    if cov is None:
        if gold_facts:
            errors.append("no applicable fact coverage rows (empty set is NOT_APPLICABLE, not 100%)")
        else:
            warnings.append("no fact coverage rows to score yet")
    else:
        print(f"Critical fact coverage: {complete}/{applicable} ({cov:.0%})")
        if cov < required:
            errors.append(f"critical fact coverage {cov:.0%} below required {required:.0%}")

    return print_results("Fact analytical coverage check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
