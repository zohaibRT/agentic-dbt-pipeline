#!/usr/bin/env python3
"""Shared helpers for acceptance-gate validators.

Domain-neutral utilities only: markdown tables, path reads, and analytics_policy
loading from project.config.yml. No industry entity assumptions.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
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
    "transaction_fact",
    "transaction fact",
    "periodic_snapshot_fact",
    "periodic snapshot fact",
    "accumulating_snapshot_fact",
    "accumulating snapshot fact",
    "reporting_fact",
    "reporting fact",
    "factless_fact",
    "factless fact",
    "measurable_event_model",
    "measurable event model",
    "measurable event",
    "event_fact",
    "event fact",
    "fact",
)

# Standalone "event"/"transaction"/"snapshot" tokens are not sufficient alone.
_FACT_EXPLICIT_CLASSES = frozenset(
    {
        "transaction_fact",
        "event_fact",
        "factless_fact",
        "periodic_snapshot_fact",
        "accumulating_snapshot_fact",
        "reporting_fact",
        "measurable_event_model",
        "fact",
        "fact/event",
        "fact event",
    }
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
    "saved_query",
    "analysis",
    "unit_test",
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
            first_norm = normalize_header(first_vals[0]) if first_vals else ""
            if first_norm in HEADER_SKIP:
                # Empty first cell is allowed for name-only identity rows (e.g. unique_id blank,
                # model/name populated) — those must still resolve and can be ambiguous.
                identity_keys = (
                    "model",
                    "model_name",
                    "name",
                    "resource_name",
                    "page_id",
                    "page_name",
                    "kpi_id",
                    "metric_id",
                    "exposure",
                )
                has_identity = any((record.get(k) or "").strip() for k in identity_keys)
                if not (first_norm == "" and has_identity):
                    continue
            if not any(str(v).strip() for v in record.values()):
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
        # completion_mode: process_coverage (ratio gates) | fixed_count (advisory targets become hard fails)
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
        # Warning fail-at-final is owned by acceptance_policy.final_fail_on_warning only.
    }
    cfg = _load_project_config(root)
    policy = cfg.get("analytics_policy") if isinstance(cfg.get("analytics_policy"), dict) else None
    if policy:
        merged = dict(defaults)
        merged.update(policy)
        return merged
    return defaults


def load_human_in_loop_policy(root: Path) -> dict[str, Any]:
    """Load human_in_loop_policy from project.config.yml."""
    defaults: dict[str, Any] = {
        "production_kpi_approval_required": 1.0,
        "require_named_owner": True,
        "require_named_approver": True,
        "require_approval_evidence": True,
        "require_approval_date": True,
        "stale_approval_blocks_final": True,
        "unresolved_critical_decisions_block_final": True,
        "conditional_approval_requires_review_condition": True,
        "allow_technical_work_without_business_approval": True,
        "allow_unapproved_kpis_in_draft_reports": True,
        "allow_unapproved_kpis_in_trusted_executive_reports": False,
    }
    cfg = _load_project_config(root)
    policy = cfg.get("human_in_loop_policy") if isinstance(cfg.get("human_in_loop_policy"), dict) else None
    if policy:
        merged = dict(defaults)
        merged.update(policy)
        return merged
    return defaults


def load_presentation_policy(root: Path) -> dict[str, Any]:
    """Load presentation_policy from project.config.yml."""
    defaults: dict[str, Any] = {
        "require_stable_visual_ids": True,
        "require_bidirectional_page_contract_mapping": True,
        "require_bidirectional_proof_mapping": True,
        "approved_kpis_required_for_trusted_executive_pages": True,
        "pending_kpis_allowed_in_draft_pages": True,
        "require_tooltip_contract": True,
        "require_static_fallback": True,
        "require_accessible_data_table": True,
        "require_offline_interactive_dependency": True,
        "interactive_renderer": "plotly",
        "static_renderer": "matplotlib",
        "require_live_browser_validation": True,
        "require_live_browser_at_final": True,
        "require_llm_playwright_review_at_final": True,
        "llm_playwright_review_required_for_release": True,
        "llm_playwright_review_required_in_ci": False,
        "require_llm_review_artifact_freshness": True,
        "require_llm_review_page_coverage": 1.0,
        "require_llm_review_visual_coverage": 1.0,
        "llm_review_block_on_critical_findings": True,
        "llm_review_block_on_high_findings": True,
        "llm_playwright_review_applicability": "required",
        "llm_review_viewports": ["desktop", "tablet", "mobile"],
        "live_browser_viewports": ["desktop", "tablet", "mobile"],
        "render_modes": ["auto", "interactive_html", "static_image"],
    }
    cfg = _load_project_config(root)
    policy = cfg.get("presentation_policy") if isinstance(cfg.get("presentation_policy"), dict) else None
    if policy:
        merged = dict(defaults)
        merged.update(policy)
        return merged
    return defaults


def normalize_stable_id(value: str) -> str:
    """Normalize a stable presentation identity (not a display label)."""
    return re.sub(r"[^a-zA-Z0-9._:-]+", "_", str(value).strip()).strip("_")


def compare_formatted_values(
    displayed: str,
    proven: str,
    *,
    format_rule: str = "",
    precision: int | None = None,
) -> tuple[bool, str]:
    """Compare displayed vs proven values allowing formatting-only differences.

    Returns (ok, reason). Formatting-only differences within precision pass.
    """
    disp = str(displayed or "").strip()
    proof = str(proven or "").strip()
    if not disp and not proof:
        return True, "both empty"
    if disp == proof:
        return True, "exact"

    def _numeric(text: str) -> float | None:
        cleaned = text.replace(",", "").replace("%", "").replace("$", "").strip()
        # strip currency codes
        cleaned = re.sub(r"\b[A-Z]{3}\b", "", cleaned).strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    d_num = _numeric(disp)
    p_num = _numeric(proof)
    if d_num is not None and p_num is not None:
        rule = (format_rule or "").lower()
        if precision is None:
            if "percent" in rule or "%" in disp or "%" in proof:
                precision = 1
            elif "currency" in rule or "money" in rule:
                precision = 2
            else:
                precision = 6
        # percent display may be 80.0 vs proof 0.8
        if ("%" in disp) != ("%" in proof):
            if abs(d_num) <= 1.5 and abs(p_num) > 1.5:
                d_num, p_num = d_num * 100.0, p_num
            elif abs(p_num) <= 1.5 and abs(d_num) > 1.5:
                d_num, p_num = d_num, p_num * 100.0
        if abs(d_num - p_num) <= (10 ** (-precision)):
            return True, f"numeric within precision={precision}"
        return False, f"numeric mismatch displayed={disp!r} proven={proof!r}"

    if normalize_header(disp) == normalize_header(proof):
        return True, "normalized text match"
    return False, f"text mismatch displayed={disp!r} proven={proof!r}"


def load_json_registry(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, (dict, list)) else None


def presentation_registry_paths(root: Path) -> dict[str, Path]:
    """Canonical presentation registry locations (prefer 10_presentation/, fall back to matplotlib/)."""
    presentation = root / "reports" / "agent" / "10_presentation"
    matplotlib = presentation / "matplotlib"
    names = (
        "page_registry.json",
        "chart_registry.json",
        "rendered_metric_manifest.json",
        "query_registry.json",
        "proof_registry.json",
    )
    paths: dict[str, Path] = {}
    for name in names:
        preferred = presentation / name
        fallback = matplotlib / name
        paths[name] = preferred if preferred.exists() else fallback
    return paths


KNOWN_VALIDATION_TYPES = frozenset(
    {
        "numeric_exact",
        "numeric_tolerance",
        "ratio_tolerance",
        "row_count_match",
        "set_match",
        "acceptance_rule",
        "sql_boolean",
        "numeric_comparison",
        "set_constraint",
        "regex_match",
        "row_count_constraint",
        "approved_human_decision",
        "artifact_presence",
        "custom_python_predicate",
        "blocked",
        "deferred",
    }
)

TECHNICAL_VERIFICATION_STATUSES = frozenset({"PASS", "WARN", "FAIL", "BLOCKED", "DEFERRED"})
BUSINESS_APPROVAL_STATUSES = frozenset(
    {
        "NOT_REQUESTED",
        "PENDING_REVIEW",
        "APPROVED",
        "APPROVED_WITH_CONDITIONS",
        "REJECTED",
        "BLOCKED",
        "DEFERRED",
        # Legacy aliases still parsed; mapped by callers
        "PROPOSED",
    }
)

CONTRACT_FINGERPRINT_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("business_definition", ("business_definition", "business definition")),
    ("formula", ("formula",)),
    ("numerator", ("numerator",)),
    ("denominator", ("denominator",)),
    ("source_models", ("source_models", "source models", "source_model")),
    ("source_columns", ("source_columns", "source columns")),
    ("grain", ("grain",)),
    ("counting_key", ("counting_key", "count_key")),
    ("date_field", ("date_field", "date field")),
    ("date_role", ("date_role", "date role")),
    ("included_records", ("included_records", "included_rows", "included rows")),
    ("excluded_records", ("excluded_records", "excluded_rows", "excluded rows")),
    ("status_logic", ("status_logic", "status logic")),
    ("aggregation_behavior", ("aggregation_behavior", "aggregation")),
    ("unit", ("unit", "unit_currency", "unit/currency")),
    ("currency", ("currency",)),
    ("target", ("target",)),
    ("warning_threshold", ("warning_threshold", "warning threshold")),
    ("critical_threshold", ("critical_threshold", "critical threshold")),
    ("tolerance", ("reconciliation_tolerance", "diff_tolerance", "tolerance", "diff_/_tolerance")),
)

GENERIC_BLOCKER_TOKENS = frozenset(
    {
        "todo",
        "tbd",
        "pending",
        "later",
        "unknown",
        "needs review",
        "discuss with business",
        "n/a",
        "na",
        "none",
    }
)

INVALID_APPROVAL_EVIDENCE_TOKENS = frozenset(
    {
        "",
        "pass",
        "approved",
        "business approved",
        "user agreed",
        "stakeholder confirmed",
        "looks correct",
        "agent approved",
        "inferred",
        "todo",
        "tbd",
        "n/a",
        "na",
        "none",
        "placeholder",
    }
)


def normalize_field_value(text: str | None) -> str:
    """Normalize a contract field for fingerprinting (trim, collapse whitespace, lower)."""
    if text is None:
        return ""
    collapsed = re.sub(r"\s+", " ", str(text).strip().lower())
    return collapsed


def compute_contract_fingerprint(row: dict[str, str]) -> str:
    """Deterministic fingerprint from business-significant KPI contract fields."""
    import hashlib

    parts: list[str] = []
    for canonical, aliases in CONTRACT_FINGERPRINT_FIELDS:
        value = cell(row, *aliases)
        parts.append(f"{canonical}={normalize_field_value(value)}")
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def parse_applicability(text: str | None) -> dict[str, Any]:
    """Parse a cell that may be a value or NOT_APPLICABLE with reason.

    Returns:
      status: VALUE | NOT_APPLICABLE | BLANK | BARE_NA
      value: original stripped text
      reason: reason when NOT_APPLICABLE
    """
    raw = (text or "").strip()
    if not raw:
        return {"status": "BLANK", "value": "", "reason": ""}
    upper = raw.upper()
    if upper in {"N/A", "NA", "NONE", "IRRELEVANT", "NULL", "-"}:
        return {"status": "BARE_NA", "value": raw, "reason": ""}
    na_match = re.match(
        r"^(?:NOT[_\s-]?APPLICABLE|N\/A)\s*[:\-–—]\s*(.+)$",
        raw,
        re.I,
    )
    if na_match:
        reason = na_match.group(1).strip()
        if not reason or reason.lower() in GENERIC_BLOCKER_TOKENS:
            return {"status": "BARE_NA", "value": raw, "reason": reason}
        return {"status": "NOT_APPLICABLE", "value": raw, "reason": reason}
    if upper.startswith("NOT_APPLICABLE") or upper.startswith("NOT APPLICABLE"):
        return {"status": "BARE_NA", "value": raw, "reason": ""}
    return {"status": "VALUE", "value": raw, "reason": ""}


def is_meaningful_text(text: str | None, *, allow_placeholders: frozenset[str] | None = None) -> bool:
    """True when text is non-blank and not a generic placeholder."""
    raw = (text or "").strip()
    if not raw:
        return False
    lower = raw.lower()
    if lower in GENERIC_BLOCKER_TOKENS:
        return False
    if allow_placeholders and lower in {p.lower() for p in allow_placeholders}:
        return True
    if lower in {"todo", "tbd", "<todo>", "unknown"}:
        return False
    return True


def is_generic_blocker_text(text: str | None) -> bool:
    """True when blocker text is empty or only a generic token without specifics."""
    raw = (text or "").strip()
    if not raw:
        return True
    lower = raw.lower()
    if lower in GENERIC_BLOCKER_TOKENS:
        return True
    # Generic token alone or followed by nothing useful
    for token in GENERIC_BLOCKER_TOKENS:
        if lower == token or lower.startswith(token + " ") and len(lower) < len(token) + 12:
            # Allow "pending business date confirmation from owner" style
            if len(raw.split()) < 4:
                return True
    return False


def business_approval_status(row: dict[str, str]) -> str:
    """Return business_approval_status; never confuse with technical verification."""
    raw = cell(
        row,
        "business_approval_status",
        "business approval status",
        "approval",
        "approval_status",
    ).upper()
    if raw in BUSINESS_APPROVAL_STATUSES or raw in {
        "APPROVED",
        "APPROVED_WITH_CONDITIONS",
        "PENDING_REVIEW",
        "NOT_REQUESTED",
        "REJECTED",
        "BLOCKED",
        "DEFERRED",
        "PROPOSED",
        "DRAFT",
        "PENDING",
    }:
        if raw in {"DRAFT", "PENDING", ""}:
            return "PENDING_REVIEW"
        if raw == "PROPOSED":
            return "PENDING_REVIEW"
        return raw
    return raw or "NOT_REQUESTED"


def technical_verification_status(row: dict[str, str]) -> str:
    """Return technical_verification_status separately from business approval."""
    raw = cell(
        row,
        "technical_verification_status",
        "technical verification status",
        "verification",
        "verification_status",
    ).upper()
    if raw in TECHNICAL_VERIFICATION_STATUSES:
        return raw
    # Do not fall back to generic Status when business_approval_status also uses Status
    # Only use Status when verification columns are absent.
    if not cell(row, "technical_verification_status", "verification", "verification_status"):
        status = cell(row, "status").upper()
        if status in TECHNICAL_VERIFICATION_STATUSES:
            return status
    return raw or "UNKNOWN"


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


def validate_sql_proof_file(
    root: Path,
    proof_ref: str | None,
    *,
    expected_kpi_id: str | None = None,
    require_validation_type: bool = False,
    require_tolerance: bool = False,
) -> dict[str, Any]:
    """Validate a referenced SQL proof file for runnable SQL and captured evidence."""
    path = resolve_proof_path(root, proof_ref)
    result: dict[str, Any] = {
        "exists": False,
        "path": str(path) if path else (proof_ref or ""),
        "has_sql": False,
        "has_expected": False,
        "has_captured": False,
        "has_status": False,
        "has_kpi_id": False,
        "has_validation_type": False,
        "kpi_id": "",
        "validation_type": "",
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
        r"(?:^|\n)\s*(?:--\s*)?(?:technical[_\s]+verification[_\s]+)?status\s*[:=|-]\s*"
        r"(PASS|WARN|FAIL|BLOCKED|SKIPPED|DEFERRED)\b",
        text,
        re.I,
    )
    if not status_match:
        status_match = re.search(
            r"\bstatus\s*\|\s*(PASS|WARN|FAIL|BLOCKED|SKIPPED|DEFERRED)\b", text, re.I
        )
    if status_match:
        result["has_status"] = True
        token = status_match.group(1).upper()
        if token == "BLOCKED":
            token = "FAIL"
        result["status"] = "WARN" if token == "DEFERRED" else token
    else:
        result["errors"].append("proof file missing PASS/WARN/FAIL status")

    kpi_match = re.search(
        r"(?:^|\n)\s*(?:--\s*)?(?:kpi[_\s-]*id|metric[_\s-]*id)\s*[:=|-]\s*([A-Za-z0-9._/-]+)",
        text,
        re.I,
    )
    if kpi_match:
        result["has_kpi_id"] = True
        result["kpi_id"] = kpi_match.group(1).strip()
    if expected_kpi_id:
        if not result["has_kpi_id"]:
            result["errors"].append("proof file missing KPI ID")
        elif normalize_field_value(result["kpi_id"]) != normalize_field_value(expected_kpi_id):
            result["errors"].append(
                f"proof KPI ID {result['kpi_id']!r} does not match contract {expected_kpi_id!r}"
            )

    vtype_match = re.search(
        r"(?:^|\n)\s*(?:--\s*)?validation[_\s-]*type\s*[:=|-]\s*([A-Za-z0-9_]+)",
        text,
        re.I,
    )
    if vtype_match:
        result["has_validation_type"] = True
        result["validation_type"] = vtype_match.group(1).strip().lower()
    if require_validation_type and not result["has_validation_type"]:
        result["errors"].append("proof file missing validation type")

    if require_tolerance:
        if not re.search(r"(?:^|\n)\s*(?:--\s*)?tolerance\s*[:=|-]", text, re.I):
            result["errors"].append("proof file missing tolerance")

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


def load_resource_classification_policy(root: Path) -> dict[str, Any]:
    """Load resource_classification_policy from project.config.yml."""
    defaults: dict[str, Any] = {
        "require_enabled_local_models": True,
        "require_sources": True,
        "require_seeds": True,
        "require_snapshots": True,
        "require_semantic_models": True,
        "require_metrics": True,
        "require_exposures": True,
        "require_tests_individually": False,
        "require_dependency_package_models": False,
        "local_resource_coverage_required": 1.0,
        "production_resource_coverage_required": 1.0,
    }
    cfg = _load_project_config(root)
    policy = cfg.get("resource_classification_policy")
    if isinstance(policy, dict):
        merged = dict(defaults)
        merged.update(policy)
        return merged
    return defaults


def empty_resource_record(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "unique_id": "",
        "name": "",
        "alias": None,
        "resource_type": "unknown",
        "package_name": "",
        "version": None,
        "latest_version": None,
        "original_file_path": "",
        "patch_path": None,
        "database": None,
        "schema": None,
        "relation_name": None,
        "enabled": True,
        "materialization": None,
        "access": None,
        "group": None,
        "tags": [],
        "meta": {},
        "depends_on_nodes": [],
        "depends_on_macros": [],
        "columns": [],
        "description": "",
        "config": {},
        "checksum": None,
        "unavailable_fields": [],
        "inventory_source": "unknown",
    }
    base.update(overrides)
    return base


def _node_to_resource_record(node_id: str, node: dict[str, Any], *, inventory_source: str) -> dict[str, Any]:
    config = node.get("config") if isinstance(node.get("config"), dict) else {}
    depends_on = node.get("depends_on") if isinstance(node.get("depends_on"), dict) else {}
    unavailable: list[str] = []
    for optional in (
        "alias",
        "version",
        "latest_version",
        "patch_path",
        "database",
        "schema",
        "relation_name",
        "access",
        "group",
        "checksum",
    ):
        if node.get(optional) is None and config.get(optional) is None:
            unavailable.append(optional)
    resource_type = str(node.get("resource_type") or node_id.split(".", 1)[0] or "unknown")
    columns_raw = node.get("columns")
    if isinstance(columns_raw, list):
        columns = columns_raw
    elif isinstance(columns_raw, dict):
        columns = list(columns_raw.keys())
    else:
        columns = []
    checksum = node.get("checksum")
    if isinstance(checksum, dict):
        checksum = checksum.get("checksum")
    return empty_resource_record(
        unique_id=node_id,
        name=str(node.get("name") or ""),
        alias=node.get("alias"),
        resource_type=resource_type,
        package_name=str(node.get("package_name") or ""),
        version=node.get("version"),
        latest_version=node.get("latest_version"),
        original_file_path=str(node.get("original_file_path") or ""),
        patch_path=node.get("patch_path"),
        database=node.get("database"),
        schema=node.get("schema"),
        relation_name=node.get("relation_name"),
        enabled=bool(config.get("enabled", True)),
        materialization=config.get("materialized") or config.get("materialization"),
        access=config.get("access") or node.get("access"),
        group=config.get("group") or node.get("group"),
        tags=list(node.get("tags") or []),
        meta=dict(node.get("meta") or {}),
        depends_on_nodes=list(depends_on.get("nodes") or []),
        depends_on_macros=list(depends_on.get("macros") or []),
        columns=columns,
        description=str(node.get("description") or ""),
        config=dict(config),
        checksum=checksum,
        unavailable_fields=unavailable,
        inventory_source=inventory_source,
    )


def inventory_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a resource inventory from dbt manifest (nodes, sources, exposures, metrics, ...)."""
    resources: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(node_id: str, node: dict[str, Any], source: str = "manifest") -> None:
        if node_id in seen:
            return
        seen.add(node_id)
        resources.append(_node_to_resource_record(node_id, node, inventory_source=source))

    for bucket in ("nodes", "sources", "exposures", "metrics", "semantic_models", "saved_queries"):
        section = manifest.get(bucket, {})
        if not isinstance(section, dict):
            continue
        for node_id, node in section.items():
            if not isinstance(node, dict):
                continue
            rtype = str(node.get("resource_type") or node_id.split(".", 1)[0])
            if rtype not in _MANIFEST_RESOURCE_TYPES:
                rec = _node_to_resource_record(node_id, node, inventory_source="manifest_unknown_type")
                rec["meta"] = {**rec["meta"], "inventory_note": "unsupported_or_informational"}
                resources.append(rec)
                seen.add(node_id)
                continue
            add(node_id, node)

    disabled = manifest.get("disabled", {})
    if isinstance(disabled, dict):
        for node_id, entries in disabled.items():
            items = entries if isinstance(entries, list) else [entries]
            for node in items:
                if isinstance(node, dict) and node_id not in seen:
                    rec = _node_to_resource_record(node_id, node, inventory_source="manifest_disabled")
                    rec["enabled"] = False
                    resources.append(rec)
                    seen.add(node_id)
    return resources


def filesystem_fallback_unique_id(resource_type: str, rel_path: str, package: str = "local") -> str:
    """Stable fallback ID including path context (not stem alone)."""
    cleaned = rel_path.replace("\\", "/").strip("/")
    stem_path = Path(cleaned).with_suffix("").as_posix().replace("/", ".")
    return f"{resource_type}.{package}.{stem_path}"


def _project_package_name(root: Path) -> str:
    cfg = load_yaml(root / "dbt_project.yml")
    name = cfg.get("name") if isinstance(cfg, dict) else None
    return str(name).strip() if name else "local"


def inventory_from_filesystem(root: Path) -> list[dict[str, Any]]:
    """Fallback inventory with path-aware unique_ids when manifest is unavailable."""
    resources: list[dict[str, Any]] = []
    package = _project_package_name(root)
    scans = (
        ("models", "model", ("*.sql", "*.py")),
        ("seeds", "seed", ("*.csv", "*.CSV")),
        ("snapshots", "snapshot", ("*.sql",)),
        ("analyses", "analysis", ("*.sql",)),
    )
    for folder, rtype, patterns in scans:
        base = root / folder
        if not base.exists():
            continue
        for pattern in patterns:
            for path in sorted(base.rglob(pattern)):
                if not path.is_file():
                    continue
                rel = path.relative_to(root).as_posix()
                resources.append(
                    empty_resource_record(
                        unique_id=filesystem_fallback_unique_id(rtype, rel, package=package),
                        name=path.stem.lower(),
                        resource_type=rtype,
                        package_name=package,
                        original_file_path=rel,
                        enabled=True,
                        inventory_source="filesystem",
                        unavailable_fields=[
                            "database",
                            "schema",
                            "relation_name",
                            "version",
                            "checksum",
                            "depends_on_nodes",
                        ],
                    )
                )
    return resources


def build_resource_inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    """Return (inventory, source) preferring manifest when present."""
    manifest = load_manifest(root)
    if manifest:
        return inventory_from_manifest(manifest), "manifest"
    return inventory_from_filesystem(root), "filesystem"


def resources_by_name(inventory: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    needle = name.strip().lower().replace("`", "")
    return [r for r in inventory if str(r.get("name", "")).lower() == needle]


def resolve_named_resource(
    inventory: list[dict[str, Any]],
    *,
    unique_id: str = "",
    name: str = "",
    package_name: str = "",
    version: str = "",
    path_hint: str = "",
) -> tuple[dict[str, Any] | None, str]:
    """Resolve a resource. status: ok | missing | ambiguous | name_only_ok."""
    if unique_id:
        for resource in inventory:
            if resource.get("unique_id") == unique_id:
                return resource, "ok"
        return None, "missing"
    candidates = resources_by_name(inventory, name)
    if package_name:
        candidates = [c for c in candidates if str(c.get("package_name")) == package_name]
    if version != "":
        candidates = [c for c in candidates if str(c.get("version")) == str(version)]
    if path_hint:
        hint = path_hint.replace("\\", "/")
        candidates = [
            c
            for c in candidates
            if hint in str(c.get("original_file_path", "")).replace("\\", "/")
        ]
    if not candidates:
        return None, "missing"
    if len(candidates) > 1:
        return None, "ambiguous"
    # Disambiguators make the match canonical (not legacy name-only)
    if package_name or version != "" or path_hint:
        return candidates[0], "ok"
    return candidates[0], "name_only_ok"


def _class_is_analytical_fact(class_text: str) -> bool:
    """True for explicit fact-like structural classes — not bare event/transaction names."""
    token = class_text.lower().replace("_", " ").replace("/", " ").strip()
    if not token:
        return False
    compact = token.replace(" ", "_")
    for pattern in _FACT_CLASS_TOKENS:
        p = pattern.replace("_", " ").replace("/", " ")
        if p == token or p in token or compact == pattern.replace(" ", "_").replace("/", "_"):
            # Reject bare single-token event/transaction/snapshot matches that are not fact-qualified
            if token in {"event", "transaction", "snapshot", "mart"}:
                return False
            return True
    return False


def _normalize_model_name(name: str) -> str:
    return name.strip().lower().replace("`", "")


def _facts_from_classification(root: Path, inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    path = root / "reports" / "agent" / "09_analytics_insights" / "model_classification.md"
    facts: list[dict[str, str]] = []
    for row in table_dicts(path):
        class_text = cell(row, "class", "model_class", "classification", "structural_class")
        if not _class_is_analytical_fact(class_text):
            continue
        # reporting_mart alone is not a fact
        if "reporting mart" in class_text.lower() and "fact" not in class_text.lower():
            continue
        unique_id = cell(row, "unique_id", "unique id", "node_id")
        model = _normalize_model_name(cell(row, "model", "model_name", "name", "resource_name"))
        package = cell(row, "package_name", "package")
        version = cell(row, "version")
        if unique_id:
            facts.append(
                {
                    "name": model or unique_id.rsplit(".", 1)[-1],
                    "unique_id": unique_id,
                    "package_name": package,
                    "version": version,
                    "structural_class": class_text,
                    "source_of_classification": "model_classification",
                    "confidence": cell(row, "confidence") or "HIGH",
                    "grain": cell(row, "grain"),
                    "business_process": cell(row, "business_process", "process"),
                    "source": "model_classification",
                }
            )
            continue
        if not model:
            continue
        resolved, status = resolve_named_resource(
            inventory, name=model, package_name=package, version=version
        )
        if status == "ambiguous":
            facts.append(
                {
                    "name": model,
                    "unique_id": "",
                    "package_name": package,
                    "structural_class": class_text,
                    "source_of_classification": "model_classification",
                    "confidence": "LOW",
                    "source": "model_classification_ambiguous",
                    "ambiguous": "true",
                }
            )
            continue
        uid = str(resolved.get("unique_id")) if resolved else f"model.local.{model}"
        facts.append(
            {
                "name": model,
                "unique_id": uid,
                "package_name": str(resolved.get("package_name")) if resolved else package,
                "version": str(resolved.get("version") or version),
                "structural_class": class_text,
                "source_of_classification": "model_classification",
                "confidence": cell(row, "confidence") or ("MEDIUM" if status == "name_only_ok" else "HIGH"),
                "grain": cell(row, "grain"),
                "business_process": cell(row, "business_process", "process"),
                "source": "model_classification",
            }
        )
    return facts


def _facts_from_fact_catalog(root: Path, inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    path = root / "reports" / "agent" / "09_analytics_insights" / "fact_catalog.md"
    facts: list[dict[str, str]] = []
    for row in table_dicts(path):
        unique_id = cell(row, "unique_id", "unique id", "fact_id")
        name = _normalize_model_name(
            cell(row, "fact", "fact_model", "model", "name", "resource_name")
        )
        package = cell(row, "package_name", "package")
        if unique_id:
            facts.append(
                {
                    "name": name or unique_id.rsplit(".", 1)[-1],
                    "unique_id": unique_id,
                    "package_name": package,
                    "structural_class": cell(row, "fact_class", "class") or "fact",
                    "source_of_classification": "fact_catalog",
                    "confidence": cell(row, "machine_confidence", "confidence") or "HIGH",
                    "grain": cell(row, "grain"),
                    "business_process": cell(row, "business_process", "process"),
                    "source": "fact_catalog",
                }
            )
            continue
        if not name:
            continue
        resolved, status = resolve_named_resource(inventory, name=name, package_name=package)
        if status == "ambiguous":
            facts.append(
                {
                    "name": name,
                    "unique_id": "",
                    "source": "fact_catalog_ambiguous",
                    "ambiguous": "true",
                }
            )
            continue
        uid = str(resolved.get("unique_id")) if resolved else f"model.local.{name}"
        facts.append(
            {
                "name": name,
                "unique_id": uid,
                "package_name": str(resolved.get("package_name")) if resolved else package,
                "structural_class": cell(row, "fact_class", "class") or "fact",
                "source_of_classification": "fact_catalog",
                "confidence": "MEDIUM",
                "grain": cell(row, "grain"),
                "source": "fact_catalog",
            }
        )
    return facts


def _facts_from_manifest_meta(root: Path, inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    facts: list[dict[str, str]] = []
    for resource in inventory:
        if resource.get("resource_type") != "model":
            continue
        meta = resource.get("meta") or {}
        class_text = str(
            meta.get("model_class")
            or meta.get("structural_class")
            or meta.get("class")
            or meta.get("classification")
            or ""
        )
        tags = {str(tag).lower() for tag in resource.get("tags") or []}
        tag_fact = bool(tags.intersection({"transaction_fact", "event_fact", "fact", "reporting_fact"}))
        if _class_is_analytical_fact(class_text) or tag_fact:
            name = _normalize_model_name(str(resource.get("name", "")))
            if name:
                facts.append(
                    {
                        "name": name,
                        "unique_id": str(resource.get("unique_id")),
                        "package_name": str(resource.get("package_name") or ""),
                        "version": str(resource.get("version") or ""),
                        "structural_class": class_text or "fact",
                        "source_of_classification": "manifest_meta",
                        "confidence": "MEDIUM",
                        "source": "manifest_meta",
                    }
                )
    return facts


def _facts_from_prefix_fallback(root: Path, inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Naming convention is last-resort only; never sole signal when classification exists."""
    facts: list[dict[str, str]] = []
    for resource in inventory:
        if resource.get("resource_type") != "model":
            continue
        name = _normalize_model_name(str(resource.get("name", "")))
        if name.startswith("fct_"):
            facts.append(
                {
                    "name": name,
                    "unique_id": str(resource.get("unique_id")),
                    "package_name": str(resource.get("package_name") or ""),
                    "structural_class": "fact",
                    "source_of_classification": "prefix_fallback",
                    "confidence": "LOW",
                    "source": "prefix_fallback",
                }
            )
    return facts


def list_analytical_facts(root: Path) -> list[dict[str, str]]:
    """Return fact resource records keyed by unique_id (canonical).

    Discovery order:
    1. approved model_classification by unique_id
    2. fact_catalog by unique_id
    3. manifest meta/tags
    4. naming prefix fallback (fct_ only — mart_ is not automatic)
    """
    inventory, _source = build_resource_inventory(root)
    merged: dict[str, dict[str, str]] = {}
    ambiguous: list[dict[str, str]] = []
    for source_fn in (
        _facts_from_classification,
        _facts_from_fact_catalog,
        _facts_from_manifest_meta,
        _facts_from_prefix_fallback,
    ):
        for item in source_fn(root, inventory):
            if item.get("ambiguous") == "true":
                ambiguous.append(item)
                continue
            uid = item.get("unique_id") or ""
            if not uid:
                continue
            if uid not in merged:
                merged[uid] = item
    # Attach ambiguous markers for callers that inspect them
    result = list(merged.values())
    for item in ambiguous:
        item["unique_id"] = item.get("unique_id") or f"ambiguous:{item.get('name')}"
        result.append(item)
    return result


def list_gold_fact_names(root: Path) -> list[str]:
    """Return distinct fact names (legacy helper). Prefer list_analytical_facts."""
    names: list[str] = []
    seen: set[str] = set()
    for item in list_analytical_facts(root):
        if item.get("ambiguous") == "true":
            continue
        name = item.get("name") or ""
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return sorted(names)


def list_analytical_fact_unique_ids(root: Path) -> list[str]:
    return sorted(
        item["unique_id"]
        for item in list_analytical_facts(root)
        if item.get("unique_id") and item.get("ambiguous") != "true"
    )


def count_gold_facts(root: Path) -> int:
    return len(list_analytical_fact_unique_ids(root))


def _class_is_dimension(class_text: str, model_name: str) -> bool:
    token = class_text.lower()
    if "dimension" in token or "conformed_entity" in token or "core_entity" in token:
        return True
    # Prefix is fallback hint only when class empty
    if not token and model_name.startswith("dim_"):
        return True
    return False


def _dims_from_classification(root: Path, inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    path = root / "reports" / "agent" / "09_analytics_insights" / "model_classification.md"
    dims: list[dict[str, str]] = []
    for row in table_dicts(path):
        model = _normalize_model_name(cell(row, "model", "model_name", "name", "resource_name"))
        class_text = cell(row, "class", "model_class", "classification", "structural_class")
        unique_id = cell(row, "unique_id", "unique id")
        if not _class_is_dimension(class_text, model):
            continue
        if unique_id:
            dims.append({"name": model or unique_id.rsplit(".", 1)[-1], "unique_id": unique_id, "source": "model_classification"})
            continue
        if model:
            resolved, _status = resolve_named_resource(inventory, name=model)
            uid = str(resolved.get("unique_id")) if resolved else f"model.local.{model}"
            dims.append({"name": model, "unique_id": uid, "source": "model_classification"})
    return dims


def _dims_from_prefix_fallback(root: Path, inventory: list[dict[str, Any]]) -> list[dict[str, str]]:
    dims: list[dict[str, str]] = []
    for resource in inventory:
        if resource.get("resource_type") != "model":
            continue
        name = _normalize_model_name(str(resource.get("name", "")))
        if name.startswith("dim_"):
            dims.append(
                {
                    "name": name,
                    "unique_id": str(resource.get("unique_id")),
                    "source": "prefix_fallback",
                }
            )
    return dims


def list_gold_dimension_names(root: Path) -> list[str]:
    """Return gold dimension models via classification-first discovery."""
    inventory, _ = build_resource_inventory(root)
    merged: dict[str, dict[str, str]] = {}
    for item in _dims_from_classification(root, inventory) + _dims_from_prefix_fallback(root, inventory):
        uid = item.get("unique_id") or item["name"]
        if uid not in merged:
            merged[uid] = item
    return sorted({item["name"] for item in merged.values() if item.get("name")})


def compute_exposure_fingerprint(fields: dict[str, Any]) -> str:
    import hashlib

    keys = (
        "type",
        "business_purpose",
        "audience",
        "depends_on_models",
        "depends_on_sources",
        "depends_on_metrics",
        "url",
        "delivery_location",
        "refresh_expectation",
        "criticality",
        "sensitive_data_classification",
    )
    parts: list[str] = []
    for key in keys:
        value = fields.get(key, "")
        if isinstance(value, (list, tuple, set)):
            value = ",".join(sorted(str(v) for v in value))
        parts.append(f"{key}={normalize_field_value(str(value))}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def parse_set_details(text: str | None, *, rules: str | None = None) -> dict[str, Any]:
    """Parse set text into members, normalized set, and duplicate report."""
    rules_lower = (rules or "").lower()
    case_sensitive = "case_sensitive" in rules_lower or "preserve_case" in rules_lower
    lowercase = (not case_sensitive) or ("lowercase" in rules_lower)
    if "preserve_case" in rules_lower:
        lowercase = False
    trim = "no_trim" not in rules_lower
    dedupe = "keep_duplicates" not in rules_lower

    raw = (text or "").strip()
    members: list[str] = []
    if not raw or _blankish(raw):
        return {"members": [], "normalized_set": set(), "duplicates": [], "raw": raw}

    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                members = [str(item) for item in parsed]
            else:
                members = [str(parsed)]
        except json.JSONDecodeError:
            members = re.split(r"[,;|\n]+", raw)
    else:
        members = re.split(r"[,;|\n]+", raw)

    cleaned: list[str] = []
    for token in members:
        value = token.strip() if trim else token
        if not value:
            continue
        if lowercase:
            value = value.lower()
        cleaned.append(value)

    duplicates = sorted({m for m in cleaned if cleaned.count(m) > 1})
    if dedupe:
        ordered: list[str] = []
        seen: set[str] = set()
        for item in cleaned:
            if item in seen:
                continue
            seen.add(item)
            ordered.append(item)
        cleaned = ordered
    return {
        "members": cleaned,
        "normalized_set": set(cleaned),
        "duplicates": duplicates,
        "raw": raw,
    }


def parse_set(text: str | None, *, rules: str | None = None) -> set[str]:
    """Parse comma/semicolon/pipe/JSON tokens into a normalized set."""
    return parse_set_details(text, rules=rules)["normalized_set"]


def reconcile_set_match(
    expected: str | None,
    actual: str | None,
    rules: str | None = None,
) -> dict[str, Any]:
    """Independently compare expected vs actual categorical sets."""
    expected_parsed = parse_set_details(expected, rules=rules)
    actual_parsed = parse_set_details(actual, rules=rules)
    expected_set = expected_parsed["normalized_set"]
    actual_set = actual_parsed["normalized_set"]
    missing = expected_set - actual_set
    unexpected = actual_set - expected_set
    duplicates = sorted(set(expected_parsed["duplicates"]) | set(actual_parsed["duplicates"]))
    calculated = "PASS" if expected_set == actual_set else "FAIL"
    return {
        "expected_set": expected_set,
        "actual_set": actual_set,
        "normalized_expected_set": expected_set,
        "normalized_actual_set": actual_set,
        "missing": missing,
        "missing_members": missing,
        "unexpected": unexpected,
        "unexpected_members": unexpected,
        "duplicate_members": duplicates,
        "rules": (rules or "").strip(),
        "calculated_status": calculated,
    }


def reconcile_row_count(
    expected: str | None,
    actual: str | None,
    tolerance_text: str | None = None,
) -> dict[str, Any]:
    """Row-count reconciliation: integers only; default tolerance exact."""
    result: dict[str, Any] = {
        "expected": None,
        "actual": None,
        "abs_diff": None,
        "calculated_status": "FAIL",
        "within_tolerance": False,
        "errors": [],
    }
    exp = parse_number(expected)
    act = parse_number(actual)
    if exp is None or act is None:
        result["errors"].append("row_count_match requires integer expected and actual")
        return result
    if exp != exp.to_integral_value() or act != act.to_integral_value():
        result["errors"].append("row_count_match rejects fractional counts")
        return result
    if exp < 0 or act < 0:
        result["errors"].append("row_count_match rejects negative counts")
        return result
    result["expected"] = exp
    result["actual"] = act
    abs_diff = abs(act - exp)
    result["abs_diff"] = abs_diff
    tol_raw = (tolerance_text or "").strip()
    if not tol_raw or _blankish(tol_raw):
        tol = parse_tolerance("exact")
    else:
        tol = parse_tolerance(tol_raw)
    if tol["kind"] == "acceptance_rule":
        result["errors"].append("row_count_match requires explicit numeric or exact tolerance")
        return result
    within = False
    if tol["kind"] == "exact":
        within = abs_diff == 0
    elif tol["kind"] == "absolute" and tol["value"] is not None:
        within = abs_diff <= tol["value"]
    elif tol["kind"] == "relative" and tol["value"] is not None and exp != 0:
        within = (abs_diff / abs(exp)) <= tol["value"]
    result["within_tolerance"] = within
    result["calculated_status"] = "PASS" if within else "FAIL"
    result["tolerance"] = tol
    return result


def reconcile_acceptance_rule(row: dict[str, str]) -> dict[str, Any]:
    """Require named acceptance rule metadata — free-text PASS is insufficient."""
    rule_id = cell(row, "acceptance_rule_id", "rule_id")
    description = cell(
        row,
        "acceptance_rule_description",
        "rule_description",
        "acceptance_rule",
    )
    proof = cell(
        row,
        "proof_artifact",
        "sql_proof",
        "proof",
        "verified_by_sql_proof",
        "validation_source",
    )
    evaluated = cell(row, "evaluated_result", "actual", "actual_result")
    technical = technical_verification_status(row)

    invalid_rule_tokens = {
        "",
        "PASS",
        "WARN",
        "FAIL",
        "TODO",
        "TBD",
        "N/A",
        "NA",
        "NONE",
        "APPROVED",
        "BUSINESS APPROVED",
        "LOOKS CORRECT",
    }
    rule_token = rule_id.strip().upper() if rule_id else ""
    has_named_rule = bool(rule_id) and rule_token not in invalid_rule_tokens
    desc_token = description.strip().upper() if description else ""
    has_description = is_meaningful_text(description) and desc_token not in invalid_rule_tokens
    has_proof = bool(proof) and proof.strip().upper() not in {"N/A", "TODO", "NONE", ""}
    has_evaluated = is_meaningful_text(evaluated)
    has_technical = technical in TECHNICAL_VERIFICATION_STATUSES

    errors: list[str] = []
    if not has_named_rule:
        errors.append("missing acceptance_rule_id")
    if not has_description:
        errors.append("missing acceptance_rule_description")
    if not has_proof:
        errors.append("missing proof_artifact / validation_source")
    if not has_evaluated:
        errors.append("missing evaluated_result")
    if not has_technical:
        errors.append("missing technical_verification_status")

    calculated = "PASS" if not errors else "FAIL"
    return {
        "rule_id": rule_id,
        "has_named_rule": has_named_rule,
        "has_description": has_description,
        "has_proof": has_proof,
        "has_evaluated": has_evaluated,
        "errors": errors,
        "calculated_status": calculated,
    }

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


VALIDATOR_RESULT_SCHEMA_VERSION = "1.0"
VALIDATOR_RESULT_SCHEMA_VERSIONS = frozenset({"1", "1.0"})


@dataclass
class ValidatorWarning:
    warning_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"warning_id": self.warning_id, "message": self.message}


@dataclass
class ValidatorResult:
    """Machine-readable validator outcome (schema_version=1.0)."""

    validator_id: str
    status: str  # PASS | WARN | FAIL | BLOCKED | SKIPPED
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: str = ""
    schema_version: str = VALIDATOR_RESULT_SCHEMA_VERSION
    warning_ids: list[str] = field(default_factory=list)
    applicability: str = ""

    def structured_warnings(self) -> list[ValidatorWarning]:
        items: list[ValidatorWarning] = []
        ids = list(self.warning_ids)
        for index, message in enumerate(self.warnings):
            wid = ids[index] if index < len(ids) else stable_warning_id(self.validator_id, message, index)
            items.append(ValidatorWarning(warning_id=wid, message=message))
        return items

    def to_dict(self) -> dict[str, Any]:
        structured = self.structured_warnings()
        return {
            "schema_version": self.schema_version,
            "validator_id": self.validator_id,
            "status": self.status,
            "errors": list(self.errors),
            "warnings": [item.to_dict() for item in structured],
            "details": dict(self.details),
            "checked_at": self.checked_at,
            "warning_ids": [item.warning_id for item in structured],
            "applicability": self.applicability,
        }


def stable_warning_id(validator_id: str, message: str, index: int) -> str:
    """Stable warning id for acceptance matching (not full-message substring)."""
    import hashlib

    digest = hashlib.sha1(f"{validator_id}|{message.strip()}".encode("utf-8")).hexdigest()[:12]
    return f"{validator_id}:w{index}:{digest}"


def build_validator_result(
    validator_id: str,
    errors: list[str],
    warnings: list[str],
    *,
    details: dict[str, Any] | None = None,
    skipped: bool = False,
    skip_reason: str = "",
    blocked: bool = False,
) -> ValidatorResult:
    from datetime import datetime, timezone

    warning_ids = [stable_warning_id(validator_id, w, i) for i, w in enumerate(warnings)]
    checked_at = datetime.now(timezone.utc).isoformat()
    if skipped:
        status = "SKIPPED"
    elif blocked or any("BLOCKED" in e.upper() for e in errors):
        status = "BLOCKED" if blocked else "FAIL"
    elif errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"
    return ValidatorResult(
        validator_id=validator_id,
        status=status,
        errors=list(errors),
        warnings=list(warnings),
        details=dict(details or {}),
        checked_at=checked_at,
        warning_ids=warning_ids,
        applicability=skip_reason if skipped else "",
    )


def write_validator_result_json(path: Path | str | None, result: ValidatorResult) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")


def write_validator_result(path: Path | str | None, result: ValidatorResult) -> None:
    """Alias for write_validator_result_json."""
    write_validator_result_json(path, result)


def validate_validator_result_schema(data: dict[str, Any]) -> None:
    """Raise ValueError when ValidatorResult JSON is invalid or contradictory."""
    from datetime import datetime

    if not isinstance(data, dict):
        raise ValueError("validator result must be a JSON object")
    schema = str(data.get("schema_version") or "")
    if schema not in VALIDATOR_RESULT_SCHEMA_VERSIONS:
        raise ValueError(f"unknown or missing schema_version: {schema!r}")
    validator_id = str(data.get("validator_id") or "").strip()
    if not validator_id:
        raise ValueError("missing validator_id")
    status = str(data.get("status") or "").upper()
    if status not in {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED"}:
        raise ValueError(f"invalid status: {status!r}")
    errors = data.get("errors") or []
    warnings = data.get("warnings") or []
    if not isinstance(errors, list):
        raise ValueError("errors must be a list")
    if not isinstance(warnings, list):
        raise ValueError("warnings must be a list")
    details = data.get("details")
    if details is None:
        details = {}
    if not isinstance(details, dict):
        raise ValueError("details must be an object")
    checked_at = str(data.get("checked_at") or "").strip()
    if not checked_at:
        raise ValueError("missing checked_at")
    # Accept ISO-8601 with optional Z / offset
    parsed_ok = False
    for candidate in (checked_at, checked_at.replace("Z", "+00:00")):
        try:
            datetime.fromisoformat(candidate)
            parsed_ok = True
            break
        except ValueError:
            continue
    if not parsed_ok:
        raise ValueError(f"checked_at is not a valid ISO-8601 timestamp: {checked_at!r}")
    # Unique warning IDs (prefer structured warning objects; fall back to warning_ids)
    warning_ids: list[str] = []
    structured_ids = False
    for item in warnings:
        if isinstance(item, dict):
            structured_ids = True
            wid = str(item.get("warning_id") or "").strip()
            if wid:
                warning_ids.append(wid)
    if not structured_ids:
        for wid in data.get("warning_ids") or []:
            token = str(wid).strip()
            if token:
                warning_ids.append(token)
    if warning_ids and len(warning_ids) != len(set(warning_ids)):
        raise ValueError("warning_ids must be unique")
    # Contradictions in payload itself
    if status == "PASS" and warnings:
        raise ValueError("JSON status PASS must not contain warnings")
    if status == "WARN" and errors:
        raise ValueError("JSON status WARN must not contain errors")
    if status == "PASS" and errors:
        raise ValueError("JSON status PASS must not contain errors")
    if status == "WARN" and not warnings:
        raise ValueError("JSON status WARN requires at least one warning")
    if status == "FAIL" and not errors:
        raise ValueError("JSON status FAIL requires errors")
    if status == "BLOCKED":
        has_blocker = bool(errors) or bool(
            details.get("blocker") or details.get("blocking_reason") or details.get("blocked_reason")
        )
        if not has_blocker:
            raise ValueError(
                "JSON status BLOCKED requires errors or details.blocker/blocking_reason"
            )


def _normalize_warning_entries(raw_warnings: list[Any], warning_ids: list[str], validator_id: str) -> tuple[list[str], list[str]]:
    messages: list[str] = []
    ids: list[str] = []
    for index, item in enumerate(raw_warnings):
        if isinstance(item, dict):
            message = str(item.get("message") or item.get("warning") or "").strip()
            wid = str(item.get("warning_id") or "").strip()
            if not message and not wid:
                continue
            if not message:
                message = wid
            if not wid:
                wid = warning_ids[index] if index < len(warning_ids) else stable_warning_id(validator_id, message, index)
            messages.append(message)
            ids.append(wid)
        else:
            message = str(item).strip()
            if not message:
                continue
            wid = warning_ids[index] if index < len(warning_ids) else stable_warning_id(validator_id, message, index)
            messages.append(message)
            ids.append(wid)
    if not ids and warning_ids:
        ids = [str(x) for x in warning_ids]
    return messages, ids


def load_validator_result_json(path: Path | str) -> ValidatorResult:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_validator_result_schema(data)
    validator_id = str(data.get("validator_id") or Path(path).stem)
    status = str(data.get("status") or "").upper()
    raw_warnings = list(data.get("warnings") or [])
    warning_ids_raw = [str(x) for x in (data.get("warning_ids") or [])]
    messages, warning_ids = _normalize_warning_entries(raw_warnings, warning_ids_raw, validator_id)
    return ValidatorResult(
        validator_id=validator_id,
        status=status,
        errors=[str(x) for x in (data.get("errors") or [])],
        warnings=messages,
        details=dict(data.get("details") or {}),
        checked_at=str(data.get("checked_at") or ""),
        schema_version=str(data.get("schema_version") or VALIDATOR_RESULT_SCHEMA_VERSION),
        warning_ids=warning_ids,
        applicability=str(data.get("applicability") or ""),
    )


def read_validator_result(path: Path | str) -> ValidatorResult:
    """Alias for load_validator_result_json."""
    return load_validator_result_json(path)


def finalize_validator_result(
    validator_id: str,
    errors: list[str],
    warnings: list[str],
    *,
    output_json: Path | str | None = None,
    details: dict[str, Any] | None = None,
    skipped: bool = False,
    skip_reason: str = "",
) -> ValidatorResult:
    """Build, optionally write, and return a ValidatorResult."""
    result = build_validator_result(
        validator_id,
        errors,
        warnings,
        details=details,
        skipped=skipped,
        skip_reason=skip_reason,
    )
    write_validator_result_json(output_json, result)
    return result


def add_output_json_arg(parser: Any) -> None:
    """Attach --output-json to an ArgumentParser."""
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Write machine-readable ValidatorResult JSON to this path",
    )


def add_result_output_argument(parser: Any) -> None:
    """Alias for add_output_json_arg (shared result protocol)."""
    add_output_json_arg(parser)


def print_results(
    title: str,
    errors: list[str],
    warnings: list[str],
    *,
    output_json: Path | str | None = None,
    validator_id: str | None = None,
    details: dict[str, Any] | None = None,
    skipped: bool = False,
    skip_reason: str = "",
) -> int:
    """Print human-readable results and optionally write ValidatorResult JSON.

    Exit codes (direct CLI usage preserved):
      FAIL/BLOCKED -> 1
      PASS/WARN/SKIPPED -> 0
    JSON status always reflects WARN when warnings exist without errors.
    """
    vid = validator_id or re.sub(r"[^a-z0-9_]+", "_", title.lower()).strip("_") or "validator"
    result = build_validator_result(
        vid,
        errors,
        warnings,
        details=details,
        skipped=skipped,
        skip_reason=skip_reason,
    )
    write_validator_result_json(output_json, result)

    if skipped:
        reason = skip_reason or title
        print(f"SKIPPED: {reason}")
        print(f"STATUS: SKIPPED")
        return 0

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    print(f"STATUS: {result.status}")
    if result.warning_ids:
        print("WARNING_IDS: " + ", ".join(result.warning_ids))
    if errors:
        print(f"{title} FAILED")
        return 1
    if warnings:
        print(f"{title} PASSED with warnings")
        return 0
    print(f"{title} PASSED")
    return 0


def project_package_name(root: Path) -> str:
    """Public local package name from dbt_project.yml (not inventory order)."""
    return _project_package_name(root)


# ---------------------------------------------------------------------------
# Production KPI obligation inventory (human-approval denominator)
# ---------------------------------------------------------------------------

PRODUCTION_KPI_INTENT_TOKENS = frozenset(
    {
        "production",
        "trusted",
        "rendered",
        "executive",
        "approved",
        "proposed",
        "conditionally approved",
        "approved_with_conditions",
        "pending_review",
        "not_requested",
    }
)

PENDING_BUSINESS_STATUSES = frozenset(
    {
        "PENDING_REVIEW",
        "NOT_REQUESTED",
        "PROPOSED",
        "REJECTED",
        "BLOCKED",
        "DEFERRED",
        "",
    }
)

APPROVED_BUSINESS_STATUSES = frozenset({"APPROVED", "APPROVED_WITH_CONDITIONS"})


@dataclass
class ProductionKpiObligation:
    kpi_id: str
    source_artifacts: list[str] = field(default_factory=list)
    technical_status: str = ""
    business_approval_status: str = ""
    owner: str = ""
    approver: str = ""
    approval_evidence: str = ""
    approval_date: str = ""
    contract_version: str = ""
    contract_fingerprint: str = ""
    trusted_or_executive: bool = False
    resolution_state: str = "OPEN"


def _load_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _table_rows_any(path: Path, required_any: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    for headers, data in parse_markdown_tables(read_text(path)):
        norm = [normalize_header(h) for h in headers]
        if not (set(norm) & required_any):
            continue
        for cells in data:
            row = {
                norm[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm))
                if norm[i]
            }
            first = next(iter(row.values()), "")
            if first.lower() in {"none", "n/a", "na", "<d-01>", "todo"}:
                continue
            rows.append(row)
    return rows


def _add_obligation(
    bag: dict[str, ProductionKpiObligation],
    kpi_id: str,
    artifact: str,
    *,
    trusted: bool = False,
) -> ProductionKpiObligation:
    kid = (kpi_id or "").strip()
    if not kid or kid.lower() in {"n/a", "na", "none", "todo", "tbd"}:
        raise ValueError("empty kpi_id")
    # Prefer stable IDs — reject pure display-name tokens when they look like sentences
    obl = bag.get(kid)
    if obl is None:
        obl = ProductionKpiObligation(kpi_id=kid)
        bag[kid] = obl
    if artifact not in obl.source_artifacts:
        obl.source_artifacts.append(artifact)
    if trusted:
        obl.trusted_or_executive = True
    return obl


def discover_production_kpi_obligations(root: Path) -> list[ProductionKpiObligation]:
    """Discover all production KPIs requiring business approval (canonical kpi_id).

    Sources:
      1. KPI_DEFINITION_CONTRACTS.md
      2. Strategic KPI catalog rows
      3. rendered_metric_manifest.json
      4. page_registry.json primary_kpi_ids
      5. report_page_contracts.md primary KPI fields
      6. trusted/executive presentation items
    """
    root = Path(root)
    bag: dict[str, ProductionKpiObligation] = {}

    contracts_path = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    contract_rows = _table_rows_any(
        contracts_path,
        {"kpi_id", "kpi", "sql_proof", "business_approval_status", "approval"},
    )
    for index, row in enumerate(contract_rows, start=1):
        kpi_id = cell(row, "kpi_id", "id") or ""
        display = cell(row, "kpi", "display_name")
        # Canonical ID preferred; fall back to display only when no kpi_id column value
        canonical = kpi_id or display
        if not canonical:
            continue
        if not kpi_id and display:
            # Display-only rows are still tracked but flagged in resolution_state
            pass
        intent = " ".join(
            [
                cell(row, "trust_level", "trust"),
                cell(row, "production_status", "production"),
                cell(row, "audience"),
                cell(row, "notes"),
                business_approval_status(row),
                cell(row, "approval", "approval_status"),
            ]
        ).lower()
        biz = business_approval_status(row)
        legacy = cell(row, "approval", "approval_status").upper()
        # Production intent: approved/proposed/conditionally approved, or explicit production markers.
        # Pending/not_requested alone does NOT imply production obligation unless other artifacts
        # (trusted/executive/rendered) pull the KPI in later.
        is_production_intent = (
            biz in APPROVED_BUSINESS_STATUSES
            or legacy in {"APPROVED", "APPROVED_WITH_CONDITIONS", "PROPOSED"}
            or any(
                tok in intent
                for tok in (
                    "production",
                    "trusted",
                    "executive",
                    "conditionally approved",
                    "approved_with_conditions",
                )
            )
        )
        if not is_production_intent:
            continue
        try:
            obl = _add_obligation(bag, canonical, "KPI_DEFINITION_CONTRACTS.md")
        except ValueError:
            continue
        obl.technical_status = technical_verification_status(row)
        obl.business_approval_status = biz or legacy or "NOT_REQUESTED"
        obl.owner = cell(row, "business_owner", "owner")
        obl.approver = cell(row, "approver", "approved_by")
        obl.approval_evidence = cell(row, "approval_evidence", "approval evidence", "evidence_path")
        obl.approval_date = cell(row, "approval_date", "approval date", "approved_at")
        obl.contract_version = cell(row, "contract_version", "version")
        obl.contract_fingerprint = cell(row, "contract_fingerprint", "fingerprint") or compute_contract_fingerprint(row)

    # Strategic catalog
    for rel in (
        Path("reports/agent/09_analytics_insights/strategic_kpi_catalog.md"),
        Path("reports/agent/09_analytics_insights/kpi_catalog.md"),
        Path("reports/agent/STRATEGIC_KPI_CATALOG.md"),
    ):
        path = root / rel
        for row in _table_rows_any(path, {"kpi_id", "metric_id", "strategic"}):
            kid = cell(row, "kpi_id", "metric_id", "id")
            if not kid:
                continue
            try:
                _add_obligation(bag, kid, rel.as_posix())
            except ValueError:
                continue

    # Rendered metric manifest
    for manifest_rel in (
        Path("reports/agent/10_presentation/rendered_metric_manifest.json"),
        Path("reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json"),
    ):
        data = _load_json_file(root / manifest_rel)
        if not data:
            continue
        metrics = data.get("metrics") if isinstance(data, dict) else data
        if isinstance(metrics, dict):
            metrics = list(metrics.values())
        if not isinstance(metrics, list):
            continue
        for item in metrics:
            if not isinstance(item, dict):
                continue
            kid = str(item.get("kpi_id") or item.get("metric_id") or "").strip()
            if not kid:
                continue
            trust = str(item.get("trust_level") or item.get("trust") or "").upper()
            # DRAFT / PENDING / PROPOSED rendered items are not production obligations
            if trust in {"DRAFT", "PENDING", "PENDING_REVIEW", "PROPOSED", "NOT_REQUESTED"}:
                continue
            trusted = trust in {"TRUSTED", "PRODUCTION", "EXECUTIVE"} or bool(
                item.get("executive") or item.get("trusted")
            )
            # Only production obligations from manifest when trusted/production or explicitly approved
            biz = str(item.get("business_approval_status") or item.get("approval_status") or "").upper()
            if not trusted and biz not in APPROVED_BUSINESS_STATUSES:
                continue
            try:
                obl = _add_obligation(bag, kid, manifest_rel.as_posix(), trusted=trusted)
            except ValueError:
                continue
            if not obl.technical_status:
                obl.technical_status = str(item.get("technical_status") or item.get("status") or "")
            if biz and not obl.business_approval_status:
                obl.business_approval_status = biz

    # page_registry.json
    for preg_rel in (
        Path("reports/agent/10_presentation/page_registry.json"),
        Path("reports/agent/10_presentation/matplotlib/page_registry.json"),
    ):
        data = _load_json_file(root / preg_rel)
        if not data:
            continue
        pages = data.get("pages") if isinstance(data, dict) else data
        if isinstance(pages, dict):
            pages = list(pages.values())
        if not isinstance(pages, list):
            continue
        for page in pages:
            if not isinstance(page, dict):
                continue
            page_class = str(page.get("page_class") or page.get("page_type") or "").lower()
            audience = str(page.get("audience") or "").lower()
            # Executive/leadership trusted pages create production KPI obligations for primary KPIs.
            # Operational DQ/pipeline pages may be marked trusted for ops but are not executive KPIs
            # unless they are also primary on an executive page.
            page_trusted = (
                "executive" in page_class
                or "leadership" in audience
                or (
                    bool(page.get("trusted"))
                    and any(t in audience for t in ("executive", "leadership", "c-suite"))
                )
            )
            if not page_trusted:
                continue
            primary = page.get("primary_kpi_ids") or page.get("primary_kpis") or []
            if isinstance(primary, str):
                primary = [p.strip() for p in primary.split(",") if p.strip()]
            for kid in primary:
                token = str(kid).strip()
                if not token or token.upper().startswith("NOT_APPLICABLE"):
                    continue
                try:
                    _add_obligation(bag, token, preg_rel.as_posix(), trusted=True)
                except ValueError:
                    continue

    # report_page_contracts.md
    rpc = root / "reports" / "agent" / "10_presentation" / "report_page_contracts.md"
    for row in _table_rows_any(rpc, {"page_id", "page", "primary_kpi", "primary_kpi_ids"}):
        kids = cell(row, "primary_kpi_ids", "primary_kpi", "kpi_id", "primary kpis")
        page_label = cell(row, "page_type", "audience", "trust", "notes", "page_class", "page").lower()
        is_exec = any(t in page_label for t in ("executive", "trusted", "production", "leadership"))
        if not is_exec:
            continue
        for part in re.split(r"[,;|]", kids):
            kid = part.strip()
            if not kid or kid.upper().startswith("NOT_APPLICABLE"):
                continue
            try:
                _add_obligation(bag, kid, "report_page_contracts.md", trusted=True)
            except ValueError:
                continue

    # HTML: only mark trusted when element has explicit trust/executive attributes
    report_html = root / "reports" / "agent" / "10_presentation" / "matplotlib" / "report.html"
    if report_html.exists():
        html = read_text(report_html)
        for match in re.finditer(
            r'data-kpi-id=["\']([^"\']+)["\'][^>]*(?:data-trust-level|data-trust|trust_level)=["\']([^"\']+)["\']',
            html,
            re.I,
        ):
            kid, trust = match.group(1), match.group(2).upper()
            if trust in {"TRUSTED", "PRODUCTION", "EXECUTIVE"}:
                try:
                    _add_obligation(bag, kid, "report.html", trusted=True)
                except ValueError:
                    continue
        for match in re.finditer(
            r'(?:data-trust-level|data-trust)=["\'](TRUSTED|PRODUCTION|EXECUTIVE)["\'][^>]*data-kpi-id=["\']([^"\']+)["\']',
            html,
            re.I,
        ):
            try:
                _add_obligation(bag, match.group(2), "report.html", trusted=True)
            except ValueError:
                continue

    # Fill resolution_state
    for obl in bag.values():
        if obl.business_approval_status in APPROVED_BUSINESS_STATUSES:
            obl.resolution_state = "APPROVED"
        elif obl.business_approval_status in {"BLOCKED", "DEFERRED", "REJECTED"}:
            obl.resolution_state = obl.business_approval_status
        elif obl.trusted_or_executive and not obl.business_approval_status:
            obl.business_approval_status = "NOT_REQUESTED"
            obl.resolution_state = "OPEN"
        else:
            obl.resolution_state = "OPEN"

    return sorted(bag.values(), key=lambda o: o.kpi_id.lower())


def has_production_presentation_artifacts(root: Path) -> bool:
    """True when trusted/executive/production presentation artifacts exist."""
    root = Path(root)
    html = root / "reports" / "agent" / "10_presentation" / "matplotlib" / "report.html"
    if html.exists():
        text = read_text(html)
        if re.search(r"\b(trusted|executive|production)\b", text, re.I):
            return True
    for rel in (
        "reports/agent/10_presentation/page_registry.json",
        "reports/agent/10_presentation/rendered_metric_manifest.json",
        "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json",
    ):
        data = _load_json_file(root / rel)
        if not data:
            continue
        blob = json.dumps(data).lower()
        if any(tok in blob for tok in ("trusted", "executive", "production")):
            return True
    return False


# ---------------------------------------------------------------------------
# Reconciliation waiver register
# ---------------------------------------------------------------------------

RECONCILIATION_WAIVER_REGISTER = Path("reports/agent/RECONCILIATION_WAIVER_REGISTER.md")


@dataclass
class ReconciliationWaiver:
    waiver_id: str
    kpi_id: str
    validation_type: str = ""
    calculated_result: str = ""
    calculated_difference: str = ""
    tolerance: str = ""
    reason: str = ""
    business_impact: str = ""
    risk_owner: str = ""
    approver: str = ""
    approval_evidence: str = ""
    approval_date: str = ""
    expiry_or_review: str = ""
    current_status: str = ""
    fingerprint: str = ""
    raw: dict[str, str] = field(default_factory=dict)


def load_reconciliation_waivers(root: Path) -> list[ReconciliationWaiver]:
    path = Path(root) / RECONCILIATION_WAIVER_REGISTER
    rows = _table_rows_any(
        path,
        {"waiver_id", "kpi_id", "metric_id", "object_id", "approver", "risk_owner"},
    )
    waivers: list[ReconciliationWaiver] = []
    for row in rows:
        wid = cell(row, "waiver_id", "id")
        kid = cell(row, "object_id", "kpi_id", "metric_id", "object id")
        if not wid or not kid:
            continue
        disposition = cell(
            row,
            "governance_disposition",
            "disposition",
            "current_status",
            "status",
            "waiver_status",
        ).upper()
        waivers.append(
            ReconciliationWaiver(
                waiver_id=wid,
                kpi_id=kid,
                validation_type=cell(row, "validation_type"),
                calculated_result=cell(row, "calculated_result", "calculated_status"),
                calculated_difference=cell(row, "calculated_difference", "difference"),
                tolerance=cell(row, "tolerance"),
                reason=cell(row, "reason"),
                business_impact=cell(row, "business_impact", "impact"),
                risk_owner=cell(row, "risk_owner", "owner"),
                approver=cell(row, "approver", "approved_by"),
                approval_evidence=cell(row, "approval_evidence", "evidence"),
                approval_date=cell(row, "approval_date", "approved_at"),
                expiry_or_review=cell(
                    row,
                    "expiry_or_review_condition",
                    "expiry",
                    "review_condition",
                    "approval_expiry_or_review_condition",
                ),
                current_status=disposition,
                fingerprint=cell(
                    row,
                    "reconciliation_fingerprint",
                    "contract_fingerprint",
                    "fingerprint",
                ),
                raw=row,
            )
        )
    return waivers


def validate_reconciliation_waiver(
    root: Path,
    waiver: ReconciliationWaiver,
    *,
    expected_kpi_id: str,
    expected_fingerprint: str = "",
    expected_validation_type: str = "",
    expected_calculated_status: str = "FAIL",
    expected_difference: str | float | None = None,
    expected_tolerance: str = "",
    today: Any = None,
) -> tuple[bool, list[str], str]:
    """Return (ok, errors, governance_disposition).

    Does not convert calculated FAIL into technical PASS.
    Binds waiver fields to live reconciliation result.
    """
    from datetime import date as date_cls, datetime

    errors: list[str] = []
    if today is None:
        today = date_cls.today()

    if normalize_field_value(waiver.kpi_id) != normalize_field_value(expected_kpi_id):
        errors.append(f"waiver {waiver.waiver_id}: kpi_id mismatch ({waiver.kpi_id} vs {expected_kpi_id})")

    if expected_validation_type:
        wtype = normalize_field_value(waiver.validation_type).replace(" ", "_")
        etype = normalize_field_value(expected_validation_type).replace(" ", "_")
        if wtype and etype and wtype != etype:
            errors.append(
                f"waiver {waiver.waiver_id}: validation_type mismatch "
                f"({waiver.validation_type} vs {expected_validation_type})"
            )
        elif not wtype:
            errors.append(f"waiver {waiver.waiver_id}: missing validation_type")

    if expected_calculated_status:
        wcalc = normalize_field_value(waiver.calculated_result).upper()
        ecalc = normalize_field_value(expected_calculated_status).upper()
        if wcalc and ecalc and wcalc != ecalc and wcalc not in {ecalc, "FAIL"}:
            # Allow waiver to record FAIL when calculated is FAIL
            if not (ecalc == "FAIL" and wcalc in {"FAIL", "FAILED"}):
                errors.append(
                    f"waiver {waiver.waiver_id}: calculated_result mismatch "
                    f"({waiver.calculated_result} vs {expected_calculated_status})"
                )
        elif not wcalc:
            errors.append(f"waiver {waiver.waiver_id}: missing calculated_result")

    if expected_tolerance:
        wt = normalize_field_value(waiver.tolerance)
        et = normalize_field_value(expected_tolerance)
        if wt and et and wt != et:
            errors.append(
                f"waiver {waiver.waiver_id}: tolerance mismatch ({waiver.tolerance} vs {expected_tolerance})"
            )

    if expected_difference is not None and str(expected_difference).strip() != "":
        wdiff = parse_number(str(waiver.calculated_difference or "").replace("±", "").split()[0])
        ediff = parse_number(str(expected_difference).replace("±", "").split()[0])
        if ediff is not None:
            if wdiff is None:
                errors.append(f"waiver {waiver.waiver_id}: missing/invalid calculated_difference")
            elif abs(wdiff - ediff) > Decimal("0.01"):
                errors.append(
                    f"waiver {waiver.waiver_id}: calculated_difference mismatch "
                    f"({waiver.calculated_difference} vs {expected_difference})"
                )

    if waiver.current_status not in APPROVED_BUSINESS_STATUSES | {
        "APPROVED_WAIVER",
        "APPROVED_WITH_CONDITIONS",
    }:
        errors.append(
            f"waiver {waiver.waiver_id}: status {waiver.current_status or '(blank)'} "
            "must be APPROVED_WAIVER, APPROVED, or APPROVED_WITH_CONDITIONS"
        )
    if not is_meaningful_text(waiver.risk_owner):
        errors.append(f"waiver {waiver.waiver_id}: missing risk_owner")
    if not is_meaningful_text(waiver.approver):
        errors.append(f"waiver {waiver.waiver_id}: missing approver")
    if not is_meaningful_text(waiver.reason):
        errors.append(f"waiver {waiver.waiver_id}: missing reason")
    if not is_meaningful_text(waiver.approval_evidence):
        errors.append(f"waiver {waiver.waiver_id}: missing approval_evidence")
    else:
        evidence = waiver.approval_evidence.strip()
        lower = evidence.lower()
        if lower in INVALID_APPROVAL_EVIDENCE_TOKENS:
            errors.append(f"waiver {waiver.waiver_id}: invalid approval evidence token")
        if re.search(r"\b(agent[- ]?(generated|approved)|auto[- ]?approved)\b", evidence, re.I):
            errors.append(f"waiver {waiver.waiver_id}: agent-generated approval invalid")
        if "/" in evidence or "\\" in evidence or evidence.endswith((".md", ".txt", ".pdf")):
            cleaned = evidence.strip("`").split("#", 1)[0]
            candidates = [Path(root) / cleaned, Path(root) / "reports" / "agent" / Path(cleaned).name]
            if cleaned and not any(c.exists() for c in candidates):
                errors.append(f"waiver {waiver.waiver_id}: evidence path not found: {evidence}")

    # approval date
    parsed_date = None
    raw_date = (waiver.approval_date or "").strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            parsed_date = datetime.strptime(raw_date[:10], fmt).date()
            break
        except ValueError:
            continue
    if not parsed_date:
        errors.append(f"waiver {waiver.waiver_id}: missing/invalid approval_date")

    # expiry / review condition required
    expiry_raw = (waiver.expiry_or_review or "").strip()
    if not expiry_raw:
        errors.append(f"waiver {waiver.waiver_id}: missing expiry/review condition")
    else:
        parsed_expiry = False
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                expiry = datetime.strptime(expiry_raw[:10], fmt).date()
                parsed_expiry = True
                if expiry < today:
                    errors.append(f"waiver {waiver.waiver_id}: expired on {expiry.isoformat()}")
                break
            except ValueError:
                continue
        if not parsed_expiry and len(expiry_raw) < 3:
            errors.append(f"waiver {waiver.waiver_id}: expiry/review condition too short")

    if expected_fingerprint:
        if not waiver.fingerprint:
            errors.append(f"waiver {waiver.waiver_id}: missing reconciliation fingerprint")
        elif waiver.fingerprint != expected_fingerprint:
            errors.append(
                f"waiver {waiver.waiver_id}: stale fingerprint "
                f"({waiver.fingerprint} != {expected_fingerprint})"
            )

    ok = not errors
    disposition = "APPROVED_WAIVER" if ok else "INVALID_WAIVER"
    return ok, errors, disposition


def find_valid_waiver_for_kpi(
    root: Path,
    kpi_id: str,
    *,
    fingerprint: str = "",
    validation_type: str = "",
    calculated_status: str = "FAIL",
    calculated_difference: str | float | None = None,
    tolerance: str = "",
) -> tuple[ReconciliationWaiver | None, list[str], str]:
    """Find a currently valid waiver for kpi_id. Returns (waiver|None, errors, disposition)."""
    candidates = [
        w
        for w in load_reconciliation_waivers(root)
        if normalize_field_value(w.kpi_id) == normalize_field_value(kpi_id)
    ]
    if not candidates:
        return None, [f"{kpi_id}: reconciliation FAIL/WARN requires formal waiver"], "MISSING_WAIVER"
    errors_all: list[str] = []
    for waiver in candidates:
        ok, errs, disposition = validate_reconciliation_waiver(
            root,
            waiver,
            expected_kpi_id=kpi_id,
            expected_fingerprint=fingerprint,
            expected_validation_type=validation_type,
            expected_calculated_status=calculated_status,
            expected_difference=calculated_difference,
            expected_tolerance=tolerance,
        )
        if ok:
            return waiver, [], disposition
        errors_all.extend(errs)
    return None, errors_all or [f"{kpi_id}: no valid reconciliation waiver"], "INVALID_WAIVER"


# ---------------------------------------------------------------------------
# Typed executable acceptance rules
# ---------------------------------------------------------------------------

EXECUTABLE_ACCEPTANCE_RULE_TYPES = frozenset(
    {
        "sql_boolean",
        "numeric_comparison",
        "set_constraint",
        "regex_match",
        "row_count_constraint",
        "approved_human_decision",
        "artifact_presence",
        "custom_python_predicate",
    }
)


def evaluate_typed_acceptance_rule(
    root: Path,
    row: dict[str, str],
    *,
    allowlisted_predicates: set[str] | None = None,
) -> dict[str, Any]:
    """Independently calculate PASS/FAIL for typed acceptance rules.

    Free-text PASS / APPROVED / looks correct is never sufficient.
    """
    rule_id = cell(row, "acceptance_rule_id", "rule_id")
    rule_type = cell(row, "acceptance_rule_type", "rule_type", "validation_type").lower().strip()
    description = cell(row, "acceptance_rule_description", "rule_description", "acceptance_rule")
    evaluated_input = cell(row, "evaluated_input", "evaluated_result", "actual", "actual_result")
    expected_condition = cell(row, "expected_condition", "expected", "expected_result")
    proof = cell(row, "proof_artifact", "sql_proof", "proof", "validation_source")

    errors: list[str] = []
    if not rule_id or rule_id.strip().upper() in {"PASS", "APPROVED", "LOOKS CORRECT", "TODO"}:
        errors.append("missing or free-text acceptance_rule_id")
    if not rule_type:
        errors.append("missing acceptance_rule_type")
    elif rule_type not in EXECUTABLE_ACCEPTANCE_RULE_TYPES and rule_type != "acceptance_rule":
        # unknown typed rule
        if rule_type not in KNOWN_VALIDATION_TYPES:
            errors.append(f"unknown acceptance_rule_type {rule_type!r}")
    if not is_meaningful_text(description) or description.strip().upper() in {"PASS", "APPROVED", "LOOKS CORRECT"}:
        errors.append("missing acceptance_rule_description")
    if not proof or proof.strip().upper() in {"N/A", "TODO", "NONE"}:
        errors.append("missing proof_artifact")

    calculated = "FAIL"
    actual_result = evaluated_input

    if errors and rule_type not in EXECUTABLE_ACCEPTANCE_RULE_TYPES:
        return {
            "acceptance_rule_id": rule_id,
            "acceptance_rule_type": rule_type,
            "acceptance_rule_description": description,
            "evaluated_input": evaluated_input,
            "expected_condition": expected_condition,
            "actual_result": actual_result,
            "proof_artifact": proof,
            "calculated_status": "FAIL",
            "errors": errors,
        }

    if rule_type in {"numeric_comparison", "numeric_tolerance", "numeric_exact", "ratio_tolerance"}:
        tol = cell(row, "tolerance", "diff_tolerance") or ("exact" if rule_type == "numeric_exact" else "0")
        result = reconcile_numeric(expected_condition, evaluated_input, tol)
        calculated = result["calculated_status"]
        if result["expected"] is None or result["actual"] is None:
            errors.append("numeric_comparison requires parseable expected and actual")
            calculated = "FAIL"
    elif rule_type in {"set_constraint", "set_match"}:
        result = reconcile_set_match(expected_condition, evaluated_input, cell(row, "normalization_rules", "tolerance"))
        calculated = result["calculated_status"]
    elif rule_type in {"row_count_constraint", "row_count_match"}:
        result = reconcile_row_count(expected_condition, evaluated_input, cell(row, "tolerance"))
        calculated = result["calculated_status"]
        errors.extend(result.get("errors") or [])
    elif rule_type == "regex_match":
        pattern = expected_condition
        if not pattern:
            errors.append("regex_match missing expected_condition pattern")
            calculated = "FAIL"
        else:
            try:
                calculated = "PASS" if re.search(pattern, evaluated_input or "") else "FAIL"
            except re.error as exc:
                errors.append(f"invalid regex: {exc}")
                calculated = "FAIL"
            if calculated == "FAIL" and not errors:
                errors.append("regex_match did not match evaluated_input")
    elif rule_type == "sql_boolean":
        token = (evaluated_input or "").strip().upper()
        if token in {"TRUE", "PASS", "1", "YES"}:
            calculated = "PASS"
        elif token in {"FALSE", "FAIL", "0", "NO"}:
            calculated = "FAIL"
            errors.append("sql_boolean evaluated false")
        else:
            calculated = "FAIL"
            errors.append("sql_boolean requires TRUE/FALSE (or PASS/FAIL) evaluated_input")
    elif rule_type == "artifact_presence":
        target = expected_condition or proof
        path = Path(root) / target if target else None
        if path and path.exists():
            calculated = "PASS"
        else:
            calculated = "FAIL"
            errors.append(f"artifact not present: {target}")
    elif rule_type == "approved_human_decision":
        biz = business_approval_status(row)
        evidence = cell(row, "approval_evidence", "evidence")
        if biz in APPROVED_BUSINESS_STATUSES and is_meaningful_text(evidence):
            if evidence.strip().lower() not in INVALID_APPROVAL_EVIDENCE_TOKENS:
                calculated = "PASS"
            else:
                errors.append("approved_human_decision: invalid evidence")
        else:
            errors.append("approved_human_decision requires APPROVED status and valid evidence")
            calculated = "FAIL"
    elif rule_type == "custom_python_predicate":
        pred = cell(row, "predicate_name", "custom_predicate", "expected_condition")
        allow = allowlisted_predicates or set()
        if pred not in allow:
            errors.append(f"custom_python_predicate {pred!r} not allowlisted")
            calculated = "FAIL"
        else:
            # Deterministic allowlisted predicates only — no arbitrary code from Markdown
            if pred == "nonempty":
                calculated = "PASS" if is_meaningful_text(evaluated_input) else "FAIL"
            elif pred == "equals_expected":
                calculated = "PASS" if (evaluated_input or "").strip() == (expected_condition or "").strip() else "FAIL"
            else:
                errors.append(f"allowlisted predicate {pred!r} has no implementation")
                calculated = "FAIL"
    elif rule_type == "acceptance_rule":
        # Legacy metadata path — still require named rule fields
        meta = reconcile_acceptance_rule(row)
        calculated = meta["calculated_status"]
        errors.extend(meta.get("errors") or [])
    else:
        if rule_type:
            errors.append(f"unknown acceptance_rule_type {rule_type!r}")
        calculated = "FAIL"

    if errors and calculated == "PASS":
        calculated = "FAIL"

    return {
        "acceptance_rule_id": rule_id,
        "acceptance_rule_type": rule_type,
        "acceptance_rule_description": description,
        "evaluated_input": evaluated_input,
        "expected_condition": expected_condition,
        "actual_result": actual_result,
        "proof_artifact": proof,
        "calculated_status": calculated,
        "errors": errors,
    }


def resolve_source_reference(
    inventory: list[dict[str, Any]],
    source_name: str,
    table_name: str,
    *,
    package_name: str = "",
) -> tuple[dict[str, Any] | None, str]:
    """Resolve source(source_name, table_name) using both names (+ package when given)."""
    sname = source_name.strip().lower()
    tname = table_name.strip().lower()
    candidates = []
    for resource in inventory:
        if resource.get("resource_type") != "source":
            continue
        uid = str(resource.get("unique_id") or "")
        # unique_id form: source.package.source_name.table_name
        parts = uid.split(".")
        uid_source = parts[2].lower() if len(parts) >= 4 else ""
        uid_table = parts[3].lower() if len(parts) >= 4 else str(resource.get("name") or "").lower()
        name_ok = str(resource.get("name") or "").lower() == tname or uid_table == tname
        source_ok = uid_source == sname or sname in uid.lower()
        # Also check meta / fqn
        fqn = str(resource.get("meta", {}).get("source_name") or resource.get("source_name") or "").lower()
        if fqn:
            source_ok = source_ok or fqn == sname
        if not (name_ok and source_ok):
            # Fallback: unique_id contains source_name.table
            if f"{sname}.{tname}" in uid.lower():
                candidates.append(resource)
            continue
        if package_name and str(resource.get("package_name") or "").lower() != package_name.lower():
            continue
        candidates.append(resource)
    if len(candidates) == 1:
        return candidates[0], "ok"
    if len(candidates) > 1:
        return None, "ambiguous"
    return None, "missing"
