#!/usr/bin/env python3
"""Check layer verification ledger coverage and referenced proof files.

Parses the ledger table by normalized header names (not fixed column positions).
Final phase requires the expanded canonical schema.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from lib_gate_common import add_output_json_arg, print_results

LEDGER_PATH = Path("reports/agent/LAYER_VERIFICATION_LEDGER.md")
BAD_STATUSES = {"FAIL", "BLOCKED"}
VALID_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED", "DEFERRED", "OPEN"}
PLACEHOLDER_TOKENS = {"TODO", "TBD", "REPLACE", "N/A", "NA", ""}

# Canonical logical fields required at final / for expanded schema
CANONICAL_FIELDS = (
    "phase",
    "layer",
    "model_or_artifact",
    "expected_grain",
    "row_count",
    "upstream_comparison",
    "key_or_grain_proof",
    "relationship_proof",
    "measure_or_kpi_proof",
    "privacy_check",
    "proof_files",
    "dbt_command_result",
    "overall_status",
    "notes",
)

# Unambiguous legacy aliases → canonical field
HEADER_ALIASES: dict[str, str] = {
    "phase": "phase",
    "layer": "layer",
    "model / artifact": "model_or_artifact",
    "model/artifact": "model_or_artifact",
    "model": "model_or_artifact",
    "artifact": "model_or_artifact",
    "expected grain": "expected_grain",
    "grain": "expected_grain",
    "row count": "row_count",
    "rows": "row_count",
    "upstream comparison": "upstream_comparison",
    "upstream": "upstream_comparison",
    "key / grain proof": "key_or_grain_proof",
    "key/grain proof": "key_or_grain_proof",
    "key proof": "key_or_grain_proof",
    "relationship proof": "relationship_proof",
    "measure / kpi proof": "measure_or_kpi_proof",
    "measure/kpi proof": "measure_or_kpi_proof",
    "measure proof": "measure_or_kpi_proof",
    "privacy check": "privacy_check",
    "privacy proof": "privacy_check",
    "proof files": "proof_files",
    "proof file": "proof_files",
    "dbt command result": "dbt_command_result",
    "dbt result": "dbt_command_result",
    "overall status": "overall_status",
    "status": "overall_status",
    "notes": "notes",
}

LEGACY_MIN_FIELDS = {
    "phase",
    "model_or_artifact",
    "expected_grain",
    "row_count",
    "overall_status",
}


def _norm_header(cell: str) -> str:
    return re.sub(r"\s+", " ", (cell or "").strip().lower())


def _parse_markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Return list of (headers, data_rows) for each markdown table."""
    tables: list[tuple[list[str], list[list[str]]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("|"):
            i += 1
            continue
        header_cells = [c.strip() for c in line.strip("|").split("|")]
        if i + 1 >= len(lines) or "---" not in lines[i + 1]:
            i += 1
            continue
        i += 2
        rows: list[list[str]] = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            if "---" in lines[i]:
                i += 1
                continue
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows.append(cells)
            i += 1
        tables.append((header_cells, rows))
    return tables


def map_headers(headers: list[str]) -> dict[str, int]:
    """Map canonical field → column index. Raises ValueError on ambiguous aliases."""
    mapping: dict[str, int] = {}
    for idx, header in enumerate(headers):
        key = _norm_header(header)
        if not key or key.startswith("---"):
            continue
        canonical = HEADER_ALIASES.get(key)
        if not canonical:
            continue
        if canonical in mapping and mapping[canonical] != idx:
            raise ValueError(f"ambiguous header mapping for {canonical!r}: {header!r}")
        mapping[canonical] = idx
    return mapping


def is_expanded_schema(field_map: dict[str, int]) -> bool:
    return all(field in field_map for field in CANONICAL_FIELDS)


def is_legacy_schema(field_map: dict[str, int]) -> bool:
    return (
        not is_expanded_schema(field_map)
        and LEGACY_MIN_FIELDS.issubset(set(field_map))
        and "proof_files" not in field_map
    )


def cell(row: list[str], field_map: dict[str, int], field: str, default: str = "") -> str:
    idx = field_map.get(field)
    if idx is None or idx >= len(row):
        return default
    return (row[idx] or "").strip()


def split_proof_paths(proof_files: str) -> list[str]:
    """Split a proof-files cell into individual path-like tokens."""
    if not proof_files:
        return []
    parts = re.split(r"[,;|\n]", proof_files)
    paths: list[str] = []
    for part in parts:
        token = part.strip().strip("`").strip()
        if not token:
            continue
        # Also capture embedded reports/agent/...sql paths
        embedded = re.findall(r"(?:reports/agent/[^\s`|,)]+\.(?:sql|md|json)|[A-Za-z0-9_./\\-]+\.sql)", token)
        if embedded:
            paths.extend(embedded)
        elif "/" in token or "\\" in token or token.endswith((".sql", ".md", ".json")):
            paths.append(token)
    # de-dupe preserve order
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def is_todo_row(row_values: dict[str, str]) -> bool:
    model = (row_values.get("model_or_artifact") or "").strip().upper()
    phase = (row_values.get("phase") or "").strip().upper()
    status = (row_values.get("overall_status") or "").strip().upper()
    if model in PLACEHOLDER_TOKENS and phase in PLACEHOLDER_TOKENS:
        return True
    if status == "TODO":
        return True
    return False


def project_has_models(root: Path) -> bool:
    models = root / "models"
    if not models.exists():
        return False
    return any(models.rglob("*.sql"))


def validate_ledger(
    root: Path,
    *,
    phase: str = "analytics",
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"schema": None, "row_count": 0, "phase": phase}
    ledger = root / LEDGER_PATH
    if not ledger.exists():
        errors.append(f"Missing {LEDGER_PATH.as_posix()}")
        return errors, warnings, details

    text = ledger.read_text(encoding="utf-8", errors="replace")
    tables = _parse_markdown_tables(text)
    if not tables:
        errors.append("Layer verification ledger has no markdown tables")
        return errors, warnings, details

    # Prefer the first table that maps to ledger fields
    field_map: dict[str, int] | None = None
    data_rows: list[list[str]] = []
    headers: list[str] = []
    for hdrs, rows in tables:
        try:
            mapping = map_headers(hdrs)
        except ValueError as exc:
            errors.append(str(exc))
            return errors, warnings, details
        if "model_or_artifact" in mapping and "overall_status" in mapping:
            field_map = mapping
            data_rows = rows
            headers = hdrs
            break

    if field_map is None:
        errors.append("Layer verification ledger missing recognizable header row")
        return errors, warnings, details

    details["headers"] = headers
    final_like = phase in {"final", "presentation"}
    expanded = is_expanded_schema(field_map)
    legacy = is_legacy_schema(field_map)
    details["schema"] = "expanded" if expanded else ("legacy" if legacy else "partial")

    if final_like and not expanded:
        errors.append(
            "final phase requires expanded Layer Verification Ledger schema "
            f"(missing fields: {', '.join(f for f in CANONICAL_FIELDS if f not in field_map)})"
        )
    elif legacy and not final_like:
        warnings.append(
            "[layer_ledger_legacy_schema] legacy Layer Verification Ledger schema detected — "
            "migrate to expanded canonical columns before final"
        )
    elif not expanded and not legacy:
        msg = (
            "Layer Verification Ledger schema incomplete for header-based parsing "
            f"(have: {sorted(field_map)})"
        )
        if final_like:
            errors.append(msg)
        else:
            warnings.append(f"[layer_ledger_partial_schema] {msg}")

    applicable_rows = 0
    for index, row in enumerate(data_rows, start=1):
        values = {field: cell(row, field_map, field) for field in CANONICAL_FIELDS if field in field_map}
        # Ensure status/model always present keys
        values.setdefault("model_or_artifact", cell(row, field_map, "model_or_artifact"))
        values.setdefault("overall_status", cell(row, field_map, "overall_status"))
        values.setdefault("proof_files", cell(row, field_map, "proof_files"))
        values.setdefault("phase", cell(row, field_map, "phase"))

        if is_todo_row(values):
            # Starter TODO rows are not completed evidence
            continue

        applicable_rows += 1
        model = values.get("model_or_artifact") or f"row {index}"
        overall_status = (values.get("overall_status") or "").upper()
        proof_files = values.get("proof_files") or ""

        if overall_status not in VALID_STATUSES:
            errors.append(f"{model}: invalid or missing overall status '{overall_status or 'MISSING'}'")
        elif overall_status in BAD_STATUSES:
            errors.append(f"{model}: unresolved overall status {overall_status}")

        if overall_status in {"PASS", "WARN"} and "proof_files" in field_map:
            if not proof_files or proof_files.strip().upper() in PLACEHOLDER_TOKENS:
                errors.append(f"{model}: {overall_status} row missing proof files")
            else:
                paths = split_proof_paths(proof_files)
                if not paths:
                    errors.append(f"{model}: {overall_status} row has no parseable proof file paths")
                for proof_ref in paths:
                    if proof_ref.upper() in PLACEHOLDER_TOKENS:
                        errors.append(f"{model}: {overall_status} row references placeholder proof {proof_ref!r}")
                        continue
                    proof_path = (root / proof_ref).resolve()
                    # Allow path relative to reports/agent
                    alt = (root / "reports" / "agent" / Path(proof_ref).name).resolve()
                    if not proof_path.exists() and not alt.exists():
                        errors.append(f"{model}: referenced proof not found: {proof_ref}")

    details["row_count"] = applicable_rows
    if applicable_rows == 0:
        if project_has_models(root) or final_like:
            errors.append("Layer verification ledger has no applicable model or artifact rows")
        else:
            warnings.append("[layer_ledger_empty] Layer verification ledger has no applicable rows")

    return errors, warnings, details


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."), help="dbt project root")
    parser.add_argument(
        "--phase",
        choices=["discovery", "analytics", "presentation", "final", "bronze", "silver", "gold"],
        default="analytics",
        help="Workflow phase (final requires expanded schema)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    errors, warnings, details = validate_ledger(root, phase=args.phase)
    return print_results(
        "Layer proof coverage",
        errors,
        warnings,
        details=details,
        output_json=getattr(args, "output_json", None),
        validator_id=Path(__file__).stem,
    )


if __name__ == "__main__":
    raise SystemExit(main())
