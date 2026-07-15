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

STATUS_PASS_EXACT = frozenset({"pass", "passed"})
STATUS_FAIL_EXACT = frozenset({"fail", "failed", "blocked"})
STATUS_WARN_EXACT = frozenset({"warn", "warning", "deferred", "skipped", "pending"})
STATUS_NA_EXACT = frozenset({"not_applicable", "n/a", "na", "not-applicable"})


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def parse_markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return list of (headers, data_rows) for every markdown table in text."""
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("|"):
            i += 1
            continue
        header_cells = [c.strip() for c in line.strip("|").split("|")]
        if i + 1 >= len(lines):
            break
        sep = lines[i + 1].strip()
        if not re.match(r"^\|\s*-+", sep):
            i += 1
            continue
        data: list[list[str]] = []
        i += 2
        while i < len(lines) and lines[i].strip().startswith("|"):
            row_line = lines[i].strip()
            if re.match(r"^\|\s*-+", row_line):
                i += 1
                continue
            cells = [c.strip() for c in row_line.strip("|").split("|")]
            if cells and not cells[0].startswith("<") and cells[0].upper() != "TODO":
                data.append(cells)
            i += 1
        tables.append((header_cells, data))
    return tables


def table_dicts_from_text(text: str, required_any_headers: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    """Parse markdown tables into dict rows keyed by normalized headers."""
    rows: list[dict[str, str]] = []
    for headers, data in parse_markdown_tables(text):
        norm_headers = [normalize_header(h) for h in headers]
        if required_any_headers:
            wanted = {normalize_header(h) for h in required_any_headers}
            if not wanted.intersection(norm_headers):
                continue
        for cells in data:
            record: dict[str, str] = {}
            for idx, header in enumerate(norm_headers):
                if not header:
                    continue
                record[header] = cells[idx].strip() if idx < len(cells) else ""
            # Skip pure header-echo rows
            first_vals = [record.get(h, "") for h in norm_headers[:1]]
            if first_vals and normalize_header(first_vals[0]) in HEADER_SKIP:
                continue
            rows.append(record)
    return rows


def table_dicts(path: Path, required_any_headers: tuple[str, ...] | None = None) -> list[dict[str, str]]:
    return table_dicts_from_text(read_text(path), required_any_headers=required_any_headers)


def cell(row: dict[str, str], *aliases: str, default: str = "") -> str:
    for alias in aliases:
        key = normalize_header(alias)
        if key in row and row[key] != "":
            return row[key]
    return default


def markdown_table_rows(path: Path) -> list[list[str]]:
    """Legacy cell-list helper; prefers first table with data rows."""
    rows: list[list[str]] = []
    for _headers, data in parse_markdown_tables(read_text(path)):
        rows.extend(data)
    filtered: list[list[str]] = []
    for cells in rows:
        if not cells:
            continue
        first = cells[0].lower()
        if first in HEADER_SKIP or first.startswith("<") or first.upper() == "TODO":
            continue
        filtered.append(cells)
    return filtered


def catalog_item_count(path: Path) -> int:
    return len(markdown_table_rows(path))


def named_status(row: dict[str, str]) -> str:
    """Read status only from an explicit Status / Verification Status column."""
    raw = cell(row, "status", "verification_status", "verification", "validation_status")
    token = normalize_header(raw)
    if not token:
        return "UNKNOWN"
    if token in STATUS_PASS_EXACT:
        return "PASS"
    if token in STATUS_FAIL_EXACT:
        return "FAIL"
    if token in STATUS_NA_EXACT:
        return "NOT_APPLICABLE"
    if token in STATUS_WARN_EXACT:
        return "WARN"
    upper = raw.strip().upper()
    if upper in {"PASS", "FAIL", "BLOCKED", "WARN", "DEFERRED", "SKIPPED", "NOT_APPLICABLE"}:
        if upper == "BLOCKED":
            return "FAIL"
        if upper == "NOT_APPLICABLE":
            return "NOT_APPLICABLE"
        return upper if upper != "DEFERRED" else "WARN"
    return "UNKNOWN"


def row_status(cells: list[str]) -> str:
    """Backward-compatible status helper; prefer last cell when it looks like a status token."""
    if not cells:
        return "UNKNOWN"
    last = cells[-1].strip()
    token = normalize_header(last)
    if token in STATUS_PASS_EXACT:
        return "PASS"
    if token in STATUS_FAIL_EXACT:
        return "FAIL"
    if token in STATUS_NA_EXACT:
        return "NOT_APPLICABLE"
    if token in STATUS_WARN_EXACT:
        return "WARN"
    upper = last.upper()
    if upper in {"PASS", "FAIL", "BLOCKED", "WARN", "DEFERRED", "SKIPPED"}:
        return "FAIL" if upper == "BLOCKED" else ("WARN" if upper == "DEFERRED" else upper)
    # Do not treat APPROVED/SUPPORTED elsewhere in the row as PASS
    return "UNKNOWN"


def count_status_rows(path: Path) -> tuple[int, int, int]:
    """Return (pass_count, applicable_total, unknown_count).

    NOT_APPLICABLE rows are excluded from the denominator.
    """
    dict_rows = table_dicts(path)
    if dict_rows and any("status" in r or "verification_status" in r or "verification" in r for r in dict_rows):
        passes = 0
        applicable = 0
        unknowns = 0
        for row in dict_rows:
            status = named_status(row)
            if status == "NOT_APPLICABLE":
                continue
            applicable += 1
            if status == "PASS":
                passes += 1
            elif status == "UNKNOWN":
                unknowns += 1
        return passes, applicable, unknowns

    rows = markdown_table_rows(path)
    if not rows:
        return 0, 0, 0
    passes = 0
    unknowns = 0
    applicable = 0
    for cells in rows:
        status = row_status(cells)
        if status == "NOT_APPLICABLE":
            continue
        applicable += 1
        if status == "PASS":
            passes += 1
        elif status == "UNKNOWN":
            unknowns += 1
    return passes, applicable, unknowns


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
        "fail_on_warning_at_final": False,
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


def ratio(numerator: int, denominator: int) -> float | None:
    """Return coverage ratio, or None when denominator is empty (NOT complete by default)."""
    if denominator <= 0:
        return None
    return numerator / denominator


def count_gold_facts(root: Path) -> int:
    fact_catalog = root / "reports" / "agent" / "09_analytics_insights" / "fact_catalog.md"
    rows = table_dicts(fact_catalog)
    if rows:
        count = 0
        for row in rows:
            name = cell(row, "fact", "fact_model", "model", "name").lower().replace("`", "")
            if name.startswith("fct_") or name.startswith("mart_"):
                count += 1
        if count:
            return count
    # Fallback list parser
    for cells in markdown_table_rows(fact_catalog):
        name = cells[0].lower().replace("`", "")
        if name.startswith("fct_") or name.startswith("mart_"):
            return sum(
                1
                for c in markdown_table_rows(fact_catalog)
                if c and (c[0].lower().startswith("fct_") or c[0].lower().startswith("mart_"))
            )
    gold = root / "models" / "gold"
    if not gold.exists():
        return 0
    return sum(1 for path in gold.rglob("*.sql") if path.name.startswith(("fct_", "mart_")))


def list_gold_fact_names(root: Path) -> list[str]:
    names: list[str] = []
    for row in table_dicts(root / "reports" / "agent" / "09_analytics_insights" / "fact_catalog.md"):
        name = cell(row, "fact", "fact_model", "model", "name").lower().replace("`", "")
        if name.startswith("fct_") or name.startswith("mart_"):
            names.append(name)
    if names:
        return sorted(set(names))
    gold = root / "models" / "gold"
    if not gold.exists():
        return []
    return sorted({p.stem.lower() for p in gold.rglob("*.sql") if p.name.startswith(("fct_", "mart_"))})


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
