#!/usr/bin/env python3
"""Shared helpers for acceptance-gate validators.

Domain-neutral utilities only: markdown tables, path reads, and analytics_policy
loading from project.config.yml. No industry entity assumptions.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
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

# Quality domains from data-observability-standard.md (section 11 production task).
REQUIRED_OBSERVABILITY_DOMAINS = frozenset(
    {
        "completeness",
        "uniqueness",
        "validity",
        "consistency",
        "referential integrity",
        "reconciliation accuracy",
        "freshness",
        "timeliness",
        "row-count stability",
        "distribution stability",
        "pipeline reliability",
        "test reliability",
        "documentation coverage",
        "model ownership coverage",
        "lineage coverage",
        "incident history",
        "mean time to detect",
        "mean time to resolve",
    }
)

_FACT_CLASS_TOKENS = (
    "fact/event",
    "fact event",
    "transaction fact",
    "periodic snapshot fact",
    "accumulating snapshot fact",
    "reporting fact mart",
    "reporting fact",
    "measurable event model",
    "measurable event",
    "event fact",
    "fact",
    "event",
    "transaction",
    "snapshot",
)

_MANIFEST_RESOURCE_TYPES = (
    "model",
    "seed",
    "snapshot",
    "source",
    "test",
    "exposure",
    "metric",
    "semantic_model",
    "analysis",
)

_CURRENCY_SYMBOLS_RE = re.compile(r"[$€£¥₹]|SAR|USD|EUR|GBP|AED|CAD|AUD|CHF|JPY|CNY", re.I)
_PERCENT_RE = re.compile(r"%")
_PARENS_NEGATIVE_RE = re.compile(r"^\(\s*(.+?)\s*\)$")
_NUMERIC_TOKEN_RE = re.compile(r"[-+]?\d[\d,]*\.?\d*")
_PROOF_REF_DIRS = (
    "reports/agent/sql_proofs",
    "reports/agent/09_analytics_insights/kpis/sql_proofs",
    "reports/agent/10_presentation/matplotlib/sql_verification",
)

_PROJECT_CONFIG_CANDIDATES = (
    lambda root: root / "project.config.yml",
    lambda root: root / "analytics_policy.yml",
    lambda _root: Path(__file__).resolve().parent.parent / "project.config.yml",
)


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


def _load_project_config(root: Path) -> dict[str, Any]:
    for candidate_fn in _PROJECT_CONFIG_CANDIDATES:
        cfg = load_yaml(candidate_fn(root))
        if cfg:
            return cfg
    return {}


def load_acceptance_policy(root: Path) -> dict[str, Any]:
    """Load acceptance_policy from project.config.yml with production defaults."""
    defaults: dict[str, Any] = {
        "final_fail_on_warning": True,
        "require_explicit_warning_acceptance": True,
    }
    cfg = _load_project_config(root)
    policy = cfg.get("acceptance_policy") if isinstance(cfg.get("acceptance_policy"), dict) else None
    if policy:
        merged = dict(defaults)
        merged.update(policy)
        return merged
    return defaults


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
        "rendered_proof_coverage_required": 1.0,
        "report_page_contract_coverage_required": 1.0,
        "observability_domain_coverage_required": 1.0,
        "critical_data_quality_coverage_required": 1.0,
        "critical_process_module_coverage_required": 1.0,
        "production_exposure_coverage_required": 1.0,
        "fail_on_warning_at_final": True,
    }
    cfg = _load_project_config(root)
    policy = cfg.get("analytics_policy") if isinstance(cfg.get("analytics_policy"), dict) else None
    if policy:
        merged = dict(defaults)
        merged.update(policy)
        return merged
    return defaults


def _blankish(text: str | None) -> bool:
    if text is None:
        return True
    token = text.strip().lower()
    return token in {"", "null", "none", "n/a", "na", "not_applicable", "not applicable", "-", "—"}


def _decimal_from_token(token: str) -> Decimal | None:
    cleaned = token.replace(",", "").strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_number(text: str | None) -> Decimal | None:
    """Parse a numeric string into Decimal, or None when blank/unparseable.

    Handles commas, currency symbols/codes, percentages (as fractions),
    and parentheses for negatives.
    """
    if _blankish(text):
        return None
    raw = str(text).strip()
    is_percent = bool(_PERCENT_RE.search(raw))
    normalized = raw
    if _PARENS_NEGATIVE_RE.match(normalized):
        normalized = "-" + _PARENS_NEGATIVE_RE.match(normalized).group(1)  # type: ignore[union-attr]
    normalized = _CURRENCY_SYMBOLS_RE.sub("", normalized)
    normalized = normalized.replace("%", "").strip()
    match = _NUMERIC_TOKEN_RE.search(normalized)
    if not match:
        return None
    value = _decimal_from_token(match.group(0))
    if value is None:
        return None
    if is_percent:
        return value / Decimal("100")
    return value


def parse_tolerance(text: str | None) -> dict[str, Any]:
    """Parse tolerance text into kind, numeric value, and raw string."""
    raw = (text or "").strip()
    lowered = raw.lower()
    if not raw or _blankish(raw):
        return {"kind": "exact", "value": Decimal("0"), "raw": raw}
    if "acceptance rule" in lowered or lowered in {"approved", "approved acceptance rule", "rule"}:
        return {"kind": "acceptance_rule", "value": None, "raw": raw}
    if lowered in {"exact", "zero", "0"}:
        return {"kind": "exact", "value": Decimal("0"), "raw": raw}
    relative_match = re.match(r"^relative\s*[:=]\s*(.+)$", lowered)
    if relative_match:
        value = parse_number(relative_match.group(1))
        return {"kind": "relative", "value": value, "raw": raw}
    absolute_match = re.match(r"^absolute\s*[:=]\s*(.+)$", lowered)
    if absolute_match:
        value = parse_number(absolute_match.group(1))
        return {"kind": "absolute", "value": value, "raw": raw}
    plus_minus_match = re.match(r"^[±+\-]\s*(.+)$", raw)
    if plus_minus_match:
        value = parse_number(plus_minus_match.group(1))
        return {"kind": "absolute", "value": value, "raw": raw}
    if raw.endswith("%") or re.search(r"\d\s*%", raw):
        value = parse_number(raw)
        return {"kind": "relative", "value": value, "raw": raw}
    numeric = parse_number(raw)
    if numeric is not None:
        return {"kind": "absolute", "value": numeric, "raw": raw}
    return {"kind": "acceptance_rule", "value": None, "raw": raw}


def _parse_number_with_percent_mode(text: str | None, *, as_percent_points: bool) -> Decimal | None:
    if _blankish(text):
        return None
    raw = str(text).strip()
    if as_percent_points and _PERCENT_RE.search(raw):
        normalized = _CURRENCY_SYMBOLS_RE.sub("", raw).replace("%", "").strip()
        if _PARENS_NEGATIVE_RE.match(normalized):
            normalized = "-" + _PARENS_NEGATIVE_RE.match(normalized).group(1)  # type: ignore[union-attr]
        match = _NUMERIC_TOKEN_RE.search(normalized)
        return _decimal_from_token(match.group(0)) if match else None
    return parse_number(text)


def reconcile_numeric(expected: str | None, actual: str | None, tolerance_text: str | None) -> dict[str, Any]:
    """Compare expected vs actual with tolerance; return calculated status metadata."""
    both_percent = bool(
        expected and actual and _PERCENT_RE.search(str(expected)) and _PERCENT_RE.search(str(actual))
    )
    expected_val = _parse_number_with_percent_mode(expected, as_percent_points=both_percent)
    actual_val = _parse_number_with_percent_mode(actual, as_percent_points=both_percent)
    tolerance = parse_tolerance(tolerance_text)

    result: dict[str, Any] = {
        "expected": expected_val,
        "actual": actual_val,
        "abs_diff": None,
        "rel_diff": None,
        "calculated_status": "FAIL",
        "within_tolerance": False,
        "tolerance": tolerance,
    }

    if tolerance["kind"] == "acceptance_rule":
        result["calculated_status"] = "PASS"
        result["within_tolerance"] = True
        return result

    if expected_val is None or actual_val is None:
        return result

    abs_diff = abs(actual_val - expected_val)
    result["abs_diff"] = abs_diff
    base = abs(expected_val)
    if base != 0:
        result["rel_diff"] = abs_diff / base
    else:
        result["rel_diff"] = Decimal("0") if abs_diff == 0 else None

    tol_value = tolerance.get("value")
    within = False
    kind = tolerance["kind"]
    if kind == "exact":
        within = abs_diff == 0
    elif kind == "absolute":
        within = tol_value is not None and abs_diff <= tol_value
    elif kind == "relative":
        if tol_value is None:
            within = False
        elif base == 0:
            within = abs_diff == 0
        else:
            within = result["rel_diff"] is not None and result["rel_diff"] <= tol_value

    result["within_tolerance"] = within
    result["calculated_status"] = "PASS" if within else "FAIL"
    return result


def resolve_proof_path(root: Path, ref: str | None) -> Path | None:
    """Resolve a SQL proof reference to an on-disk path."""
    if not ref or _blankish(ref):
        return None
    cleaned = ref.strip().strip("`").replace("\\", "/")
    candidates: list[Path] = []
    ref_path = Path(cleaned)
    if ref_path.is_absolute():
        candidates.append(ref_path)
    else:
        candidates.append(root / cleaned)
        if cleaned.startswith("reports/"):
            candidates.append(root / cleaned)
        else:
            for base in _PROOF_REF_DIRS:
                candidates.append(root / base / Path(cleaned).name)
                candidates.append(root / base / cleaned)
            candidates.append(root / "reports" / "agent" / cleaned)
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def validate_sql_proof_file(root: Path, proof_ref: str | None) -> dict[str, Any]:
    """Validate a referenced SQL proof file for runnable SQL and captured evidence."""
    path = resolve_proof_path(root, proof_ref)
    result: dict[str, Any] = {
        "exists": False,
        "path": str(path) if path else (proof_ref or ""),
        "has_sql": False,
        "has_expected": False,
        "has_captured": False,
        "has_status": False,
        "status": "UNKNOWN",
        "errors": [],
    }
    if path is None:
        result["errors"].append(f"proof file not found: {proof_ref}")
        return result
    result["exists"] = True
    result["path"] = str(path)
    text = read_text(path)
    lower = text.lower()
    if not text.strip():
        result["errors"].append("proof file is empty")
        return result

    sql_tokens = ("select", "with", "insert", "update", "delete", "merge", "create", "explain")
    result["has_sql"] = any(re.search(rf"\b{token}\b", lower) for token in sql_tokens)
    if not result["has_sql"]:
        result["errors"].append("proof file missing runnable SQL")

    expected_patterns = (
        r"expected\s*(?:result)?\s*[:=|-]",
        r"--\s*expected",
        r"acceptance\s+rule",
    )
    result["has_expected"] = any(re.search(pattern, lower) for pattern in expected_patterns)
    if not result["has_expected"]:
        result["errors"].append("proof file missing expected result or acceptance rule")

    captured_patterns = (
        r"captured\s+result",
        r"actual\s*(?:result)?\s*[:=|-]",
        r"--\s*actual",
    )
    result["has_captured"] = any(re.search(pattern, lower) for pattern in captured_patterns)
    if not result["has_captured"]:
        result["errors"].append("proof file missing captured/actual result")

    status_match = re.search(
        r"(?:^|\n)\s*(?:--\s*)?status\s*[:=|-]\s*(PASS|WARN|FAIL|BLOCKED|SKIPPED|DEFERRED)\b",
        text,
        re.I,
    )
    if not status_match:
        status_match = re.search(r"\bstatus\s*\|\s*(PASS|WARN|FAIL|BLOCKED|SKIPPED|DEFERRED)\b", text, re.I)
    if status_match:
        result["has_status"] = True
        token = status_match.group(1).upper()
        if token == "BLOCKED":
            token = "FAIL"
        result["status"] = "WARN" if token == "DEFERRED" else token
    else:
        result["errors"].append("proof file missing PASS/WARN/FAIL status")

    return result


def load_manifest(root: Path) -> dict[str, Any] | None:
    """Load dbt manifest.json when present."""
    manifest_path = root / "target" / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        data = json.loads(read_text(manifest_path))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def inventory_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a resource inventory from dbt manifest nodes."""
    nodes = manifest.get("nodes", {})
    sources = manifest.get("sources", {})
    resources: list[dict[str, Any]] = []

    def _append(node_id: str, node: dict[str, Any]) -> None:
        config = node.get("config") if isinstance(node.get("config"), dict) else {}
        depends_on = node.get("depends_on") if isinstance(node.get("depends_on"), dict) else {}
        resources.append(
            {
                "unique_id": node_id,
                "name": node.get("name", ""),
                "resource_type": node.get("resource_type", ""),
                "package_name": node.get("package_name", ""),
                "original_file_path": node.get("original_file_path", ""),
                "enabled": config.get("enabled", True),
                "materialization": config.get("materialization", node.get("config", {}).get("materialized")),
                "depends_on": depends_on.get("nodes", []) if depends_on else [],
                "tags": list(node.get("tags") or []),
                "meta": dict(node.get("meta") or {}),
            }
        )

    if isinstance(nodes, dict):
        for node_id, node in nodes.items():
            if isinstance(node, dict) and node.get("resource_type") in _MANIFEST_RESOURCE_TYPES:
                _append(node_id, node)
    if isinstance(sources, dict):
        for node_id, node in sources.items():
            if isinstance(node, dict):
                _append(node_id, node)
    return resources


def inventory_from_filesystem(root: Path) -> list[dict[str, Any]]:
    """Fallback inventory from SQL model files when manifest is unavailable."""
    resources: list[dict[str, Any]] = []
    models_dir = root / "models"
    if not models_dir.exists():
        return resources
    for path in sorted(models_dir.rglob("*.sql")):
        stem = path.stem.lower()
        rel = path.relative_to(root).as_posix()
        resources.append(
            {
                "unique_id": f"model.local.{stem}",
                "name": stem,
                "resource_type": "model",
                "package_name": "local",
                "original_file_path": rel,
                "enabled": True,
                "materialization": None,
                "depends_on": [],
                "tags": [],
                "meta": {},
            }
        )
    return resources


def _class_is_analytical_fact(class_text: str) -> bool:
    token = class_text.lower().replace("_", " ").replace("/", " ").strip()
    if not token:
        return False
    for pattern in _FACT_CLASS_TOKENS:
        if pattern.replace("/", " ") in token or token in pattern.replace("/", " "):
            return True
    return any(part in token for part in ("fact", "event", "transaction", "snapshot"))


def _normalize_model_name(name: str) -> str:
    return name.strip().lower().replace("`", "")


def _facts_from_classification(root: Path) -> list[dict[str, str]]:
    path = root / "reports" / "agent" / "09_analytics_insights" / "model_classification.md"
    facts: list[dict[str, str]] = []
    for row in table_dicts(path):
        model = _normalize_model_name(cell(row, "model", "model_name", "name"))
        class_text = cell(row, "class", "model_class", "classification")
        if model and _class_is_analytical_fact(class_text):
            facts.append({"name": model, "unique_id": f"model.local.{model}", "source": "model_classification"})
    return facts


def _facts_from_fact_catalog(root: Path) -> list[dict[str, str]]:
    path = root / "reports" / "agent" / "09_analytics_insights" / "fact_catalog.md"
    facts: list[dict[str, str]] = []
    for row in table_dicts(path):
        name = _normalize_model_name(cell(row, "fact", "fact_model", "model", "name"))
        if name:
            facts.append({"name": name, "unique_id": f"model.local.{name}", "source": "fact_catalog"})
    if facts:
        return facts
    for cells in markdown_table_rows(path):
        if not cells:
            continue
        name = _normalize_model_name(cells[0])
        if name and name not in HEADER_SKIP:
            facts.append({"name": name, "unique_id": f"model.local.{name}", "source": "fact_catalog"})
    return facts


def _facts_from_manifest_meta(root: Path) -> list[dict[str, str]]:
    manifest = load_manifest(root)
    if not manifest:
        return []
    facts: list[dict[str, str]] = []
    for resource in inventory_from_manifest(manifest):
        if resource.get("resource_type") != "model":
            continue
        meta = resource.get("meta") or {}
        class_text = str(meta.get("model_class") or meta.get("class") or meta.get("classification") or "")
        tags = {str(tag).lower() for tag in resource.get("tags") or []}
        if _class_is_analytical_fact(class_text) or tags.intersection({"fact", "event", "transaction", "snapshot"}):
            name = _normalize_model_name(str(resource.get("name", "")))
            if name:
                facts.append(
                    {
                        "name": name,
                        "unique_id": str(resource.get("unique_id", f"model.local.{name}")),
                        "source": "manifest_meta",
                    }
                )
    return facts


def _facts_from_prefix_fallback(root: Path) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    manifest = load_manifest(root)
    if manifest:
        for resource in inventory_from_manifest(manifest):
            if resource.get("resource_type") != "model":
                continue
            name = _normalize_model_name(str(resource.get("name", "")))
            if name.startswith(("fct_", "mart_")):
                facts.append(
                    {
                        "name": name,
                        "unique_id": str(resource.get("unique_id", f"model.local.{name}")),
                        "source": "prefix_manifest",
                    }
                )
        if facts:
            return facts
    gold = root / "models" / "gold"
    search_roots = [gold] if gold.exists() else [root / "models"]
    for base in search_roots:
        if not base.exists():
            continue
        for path in base.rglob("*.sql"):
            name = path.stem.lower()
            if name.startswith(("fct_", "mart_")):
                rel = path.relative_to(root).as_posix()
                facts.append(
                    {
                        "name": name,
                        "unique_id": f"model.local.{name}",
                        "source": "prefix_filesystem",
                        "path": rel,
                    }
                )
    return facts


def list_analytical_facts(root: Path) -> list[dict[str, str]]:
    """Return analytical fact models using classification-first discovery."""
    merged: dict[str, dict[str, str]] = {}
    for source_fn in (
        _facts_from_classification,
        _facts_from_fact_catalog,
        _facts_from_manifest_meta,
        _facts_from_prefix_fallback,
    ):
        for item in source_fn(root):
            name = item["name"]
            if name not in merged:
                merged[name] = item
    return sorted(merged.values(), key=lambda row: row["name"])


def list_gold_fact_names(root: Path) -> list[str]:
    return [item["name"] for item in list_analytical_facts(root)]


def count_gold_facts(root: Path) -> int:
    return len(list_analytical_facts(root))


def load_accepted_warnings(root: Path, path_optional: str | Path | None = None) -> set[str]:
    """Collect accepted/deferred warning id substrings from control-plane files."""
    accepted: set[str] = set()
    if path_optional:
        optional_path = Path(path_optional)
        if not optional_path.is_absolute():
            optional_path = root / optional_path
        if optional_path.exists():
            for line in read_text(optional_path).splitlines():
                token = line.strip().strip("-*").strip()
                if token and not token.startswith("#"):
                    accepted.add(token.lower())

    control_files = [
        root / "reports" / "agent" / "CONTEXT_TREE.md",
        root / "reports" / "agent" / "PIPELINE_STATUS.md",
        root / "reports" / "agent" / "HUMAN_ATTENTION_BOARD.md",
    ]
    warning_line_patterns = (
        re.compile(r"accepted\s+warning[s]?\s*[:=-]\s*(.+)$", re.I),
        re.compile(r"warning\s+id\s*[:=-]\s*(.+)$", re.I),
        re.compile(r"deferred\s+warning[s]?\s*[:=-]\s*(.+)$", re.I),
        re.compile(r"accepted\s+warn(?:ing)?\s*[:=-]\s*(.+)$", re.I),
    )
    bullet_id_pattern = re.compile(r"^\s*[-*]\s*(?:\[ACCEPTED\]|\[DEFERRED\])?\s*([A-Za-z0-9._/-]+)", re.I)

    for path in control_files:
        for line in read_text(path).splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for pattern in warning_line_patterns:
                match = pattern.search(stripped)
                if match:
                    for part in re.split(r"[,;|]", match.group(1)):
                        token = part.strip().lower()
                        if token:
                            accepted.add(token)
            bullet_match = bullet_id_pattern.match(stripped)
            if bullet_match and any(
                keyword in stripped.lower() for keyword in ("accepted", "deferred", "warning")
            ):
                accepted.add(bullet_match.group(1).lower())
    return accepted


def _slugify_page_id(value: str) -> str:
    slug = normalize_header(value)
    return slug or value.strip().lower()


def extract_page_ids_from_presentation(root: Path) -> set[str]:
    """Extract page/tab identifiers from presentation artifacts."""
    presentation = root / "reports" / "agent" / "10_presentation"
    matplotlib = presentation / "matplotlib"
    page_ids: set[str] = set()

    builder_path = matplotlib / "report_builder.py"
    builder_text = read_text(builder_path)
    if builder_text:
        for match in re.finditer(r"(?:TABS|tabs|PAGES|pages)\s*=\s*\[(.*?)\]", builder_text, re.S):
            for item in re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)):
                page_ids.add(_slugify_page_id(item))
                page_ids.add(item.strip())

    html_path = matplotlib / "report.html"
    html_text = read_text(html_path)
    if html_text:
        for match in re.finditer(r'data-tab=["\']([^"\']+)["\']', html_text, re.I):
            page_ids.add(_slugify_page_id(match.group(1)))
        for match in re.finditer(r'\bid=["\']([^"\']+)["\']', html_text, re.I):
            token = match.group(1).strip()
            if token and token not in {"app", "root", "main"}:
                page_ids.add(_slugify_page_id(token))
        for match in re.finditer(r"<h1[^>]*>([^<]+)</h1>", html_text, re.I):
            page_ids.add(_slugify_page_id(match.group(1)))

    spec_path = matplotlib / "report_spec.md"
    if not spec_path.exists():
        spec_path = presentation / "report_spec.md"
    for row in table_dicts(spec_path, required_any_headers=("page", "page_id", "page_name", "tab")):
        for alias in ("page_id", "page", "page_name", "tab", "tab_id", "tab_name"):
            value = cell(row, alias)
            if value:
                page_ids.add(_slugify_page_id(value))
                page_ids.add(value.strip())

    registry_paths = (
        matplotlib / "page_registry.json",
        presentation / "page_registry.json",
    )
    for registry_path in registry_paths:
        if not registry_path.exists():
            continue
        try:
            data = json.loads(read_text(registry_path))
        except json.JSONDecodeError:
            continue
        entries: list[Any]
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            entries = list(data.get("pages") or data.get("tabs") or [])
        else:
            entries = []
        for entry in entries:
            if isinstance(entry, str):
                page_ids.add(_slugify_page_id(entry))
            elif isinstance(entry, dict):
                for key in ("page_id", "id", "tab_id", "name", "page_name", "tab"):
                    value = entry.get(key)
                    if isinstance(value, str) and value.strip():
                        page_ids.add(_slugify_page_id(value))
                        page_ids.add(value.strip())

    return {token for token in page_ids if token}


def ratio(numerator: int, denominator: int) -> float | None:
    """Return coverage ratio, or None when denominator is empty (NOT complete by default)."""
    if denominator <= 0:
        return None
    return numerator / denominator


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
