#!/usr/bin/env python3
"""Shared helpers for acceptance-gate validators.

Domain-neutral utilities only: markdown tables, path reads, and analytics_policy
loading from project.config.yml. No industry entity assumptions.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - PyYAML is a skill dependency
    yaml = None  # type: ignore


HEADER_SKIP = {
    "name",
    "measure",
    "metric",
    "kpi",
    "id",
    "kpi id",
    "measure name",
    "metric name",
    "business process",
    "facts",
    "fact",
    "fact/event models",
    "dimensions",
    "model",
    "model name",
    "page",
    "page name",
    "metric / kpi",
    "exposure",
    "none",
    "",
    "---",
}

STATUS_PASS_TOKENS = frozenset({"pass", "passed", "ok", "complete", "supported", "approved"})
STATUS_FAIL_TOKENS = frozenset({"fail", "failed", "blocked"})
STATUS_DEFER_TOKENS = frozenset({"deferred", "warn", "warning", "pending", "not_applicable", "n/a", "na"})


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def markdown_table_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    if not path.exists():
        return rows
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].lower()
        if first in HEADER_SKIP or first.startswith("<"):
            continue
        rows.append(cells)
    return rows


def catalog_item_count(path: Path) -> int:
    return len(markdown_table_rows(path))


def row_status(cells: list[str]) -> str:
    joined = " ".join(cells).lower()
    for cell in reversed(cells):
        token = cell.strip().lower().replace(" ", "_")
        if token in STATUS_PASS_TOKENS or token.upper() == "PASS":
            return "PASS"
        if token in STATUS_FAIL_TOKENS or token.upper() in {"FAIL", "BLOCKED"}:
            return "FAIL"
        if token in STATUS_DEFER_TOKENS or token.upper() in {"DEFERRED", "WARN", "SKIPPED", "NOT_APPLICABLE"}:
            return "WARN"
    if re.search(r"\bpass\b", joined) and not re.search(r"\b(fail|blocked)\b", joined):
        return "PASS"
    if re.search(r"\b(fail|blocked)\b", joined):
        return "FAIL"
    if re.search(r"\b(deferred|warn|not_applicable|n/a)\b", joined):
        return "WARN"
    return "UNKNOWN"


def count_status_rows(path: Path) -> tuple[int, int, int]:
    """Return (pass_count, total_data_rows, unknown_count)."""
    rows = markdown_table_rows(path)
    if not rows:
        return 0, 0, 0
    passes = 0
    unknowns = 0
    for cells in rows:
        status = row_status(cells)
        if status == "PASS":
            passes += 1
        elif status == "UNKNOWN":
            unknowns += 1
    return passes, len(rows), unknowns


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    data = yaml.safe_load(read_text(path)) or {}
    return data if isinstance(data, dict) else {}


def load_analytics_policy(root: Path) -> dict[str, Any]:
    """Load analytics_policy from project.config.yml with process-coverage defaults."""
    defaults: dict[str, Any] = {
        "completion_mode": "process_coverage",
        "advisory_measure_target": None,
        "advisory_metric_target": None,
        "critical_fact_coverage_required": 1.0,
        "critical_kpi_contract_coverage_required": 1.0,
        "critical_reconciliation_coverage_required": 1.0,
        "business_process_coverage_required": 0.9,
        "time_intelligence_coverage_required": 0.8,
        "model_classification_coverage_required": 1.0,
        "business_label_coverage_required": 1.0,
        "report_traceability_required": 1.0,
    }
    for candidate in (
        root / "project.config.yml",
        root / "analytics_policy.yml",
        Path(__file__).resolve().parent.parent / "project.config.yml",
    ):
        cfg = load_yaml(candidate)
        policy = cfg.get("analytics_policy") if isinstance(cfg.get("analytics_policy"), dict) else None
        if policy:
            merged = dict(defaults)
            merged.update(policy)
            return merged
    return defaults


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return numerator / denominator


def count_gold_facts(root: Path) -> int:
    fact_catalog = root / "reports" / "agent" / "09_analytics_insights" / "fact_catalog.md"
    rows = markdown_table_rows(fact_catalog)
    if rows:
        count = sum(
            1
            for cells in rows
            if cells and (cells[0].lower().startswith("fct_") or cells[0].lower().startswith("mart_"))
        )
        if count:
            return count
    gold = root / "models" / "gold"
    if not gold.exists():
        return 0
    return sum(1 for path in gold.rglob("*.sql") if path.name.startswith(("fct_", "mart_")))


def print_results(title: str, errors: list[str], warnings: list[str]) -> int:
    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    if errors:
        print(f"{title} FAILED")
        return 1
    if warnings:
        print(f"{title} PASSED with warnings")
        return 0
    print(f"{title} PASSED")
    return 0
