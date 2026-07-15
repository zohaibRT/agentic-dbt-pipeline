#!/usr/bin/env python3
"""Validate mandatory discovery artifacts in a generated dbt project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_DISCOVERY_FILES = [
    "reports/agent/00_discovery/README.md",
    "reports/agent/00_discovery/core_profile.json",
    "reports/agent/00_discovery/discovery_raw.json",
    "reports/agent/00_discovery/first_pass_scope.json",
    "reports/agent/00_discovery/discovery_report.md",
    "reports/agent/00_discovery/requirements.md",
    "reports/agent/00_discovery/cardinality_report.md",
    "reports/agent/00_discovery/relationship_profile.md",
    "reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md",
    "reports/agent/00_discovery/sql_proofs/_proof_index.md",
]

REQUIRED_JSON_KEYS = {
    "core_profile.json": ["_file_meta", "profile", "source", "workspace"],
    "discovery_raw.json": ["_file_meta", "run", "scope", "tables", "queries_executed"],
    "first_pass_scope.json": [
        "_file_meta",
        "lock_status",
        "fingerprint",
        "counts",
        "included_tables",
        "deferred_tables",
    ],
}


def validate_json(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.as_posix()}: invalid JSON ({exc.msg})"]

    for key in REQUIRED_JSON_KEYS.get(path.name, []):
        if key not in data:
            errors.append(f"{path.as_posix()}: missing required key '{key}'")

    meta = data.get("_file_meta")
    if not isinstance(meta, dict):
        errors.append(f"{path.as_posix()}: _file_meta must be an object")
    else:
        for field in ("purpose", "why", "required_on_every_discovery_run"):
            if field not in meta:
                errors.append(f"{path.as_posix()}: _file_meta missing '{field}'")

    if path.name == "discovery_raw.json":
        tables = data.get("tables")
        queries = data.get("queries_executed")
        if not isinstance(tables, list):
            errors.append(f"{path.name}: tables must be a list")
        elif not tables:
            errors.append(f"{path.name}: tables must not be empty after discovery")
        else:
            for index, table in enumerate(tables[:5]):
                if not isinstance(table, dict):
                    errors.append(f"{path.name}: tables[{index}] must be an object")
                    continue
                for field in ("table_name", "row_count", "inclusion_status"):
                    if field not in table:
                        errors.append(f"{path.name}: tables[{index}] missing '{field}'")
        if not isinstance(queries, list):
            errors.append(f"{path.name}: queries_executed must be a list")
        elif not queries:
            errors.append(f"{path.name}: queries_executed must not be empty after discovery")
        else:
            for index, query in enumerate(queries):
                if not isinstance(query, dict):
                    errors.append(f"{path.name}: queries_executed[{index}] must be an object")
                    continue
                proof_file = query.get("proof_file") or query.get("sql_proof_file") or query.get("path")
                if not proof_file:
                    errors.append(f"{path.name}: queries_executed[{index}] missing proof_file/sql_proof_file/path")

    if path.name == "core_profile.json":
        profile = data.get("profile", {})
        source = data.get("source", {})
        for label, value in (
            ("profile.dbt_profile_name", profile.get("dbt_profile_name")),
            ("profile.adapter", profile.get("adapter")),
            ("source.source_schema", source.get("source_schema")),
        ):
            if isinstance(value, str) and value.strip().startswith("<"):
                errors.append(f"{path.as_posix()}: placeholder value still present for {label}")

    if path.name == "first_pass_scope.json":
        lock_status = str(data.get("lock_status") or "").strip().lower()
        if lock_status not in ("proposed", "approved", "superseded"):
            errors.append(
                f"{path.as_posix()}: lock_status must be proposed, approved, or superseded"
            )
        fingerprint = data.get("fingerprint")
        if not isinstance(fingerprint, dict):
            errors.append(f"{path.as_posix()}: fingerprint must be an object")
        else:
            for field in ("profile", "database", "source_schema", "business_process"):
                value = fingerprint.get(field)
                if not value or (isinstance(value, str) and value.strip().startswith("<")):
                    errors.append(f"{path.as_posix()}: fingerprint.{field} must be filled")
        included = data.get("included_tables")
        deferred = data.get("deferred_tables")
        if not isinstance(included, list):
            errors.append(f"{path.as_posix()}: included_tables must be a list")
        if not isinstance(deferred, list):
            errors.append(f"{path.as_posix()}: deferred_tables must be a list")

    return errors


def validate_scope_lock_consistency(root: Path) -> list[str]:
    errors: list[str] = []
    discovery_dir = root / "reports" / "agent" / "00_discovery"
    raw_path = discovery_dir / "discovery_raw.json"
    scope_path = discovery_dir / "first_pass_scope.json"
    if not raw_path.exists() or not scope_path.exists():
        return errors

    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        scope = json.loads(scope_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return errors

    raw_included = {
        str(item.get("table_name") or "").strip()
        for item in raw.get("tables", [])
        if isinstance(item, dict)
        and str(item.get("inclusion_status") or "").strip().lower() == "included"
    }
    scope_included = {
        str(name).strip()
        for name in (scope.get("included_tables") or [])
        if str(name).strip()
    }
    if raw_included and scope_included and raw_included != scope_included:
        only_raw = sorted(raw_included - scope_included)
        only_scope = sorted(scope_included - raw_included)
        errors.append(
            "first_pass_scope.json included_tables does not match discovery_raw.json included set"
            + (f"; only in raw: {only_raw}" if only_raw else "")
            + (f"; only in scope lock: {only_scope}" if only_scope else "")
        )

    return errors


def validate_sql_proof_linkage(root: Path) -> list[str]:
    errors: list[str] = []
    discovery_dir = root / "reports" / "agent" / "00_discovery"
    raw_path = discovery_dir / "discovery_raw.json"
    proof_dir = discovery_dir / "sql_proofs"
    if not raw_path.exists():
        return errors

    try:
        data = json.loads(raw_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return errors
    queries = data.get("queries_executed", [])
    linked_files: set[str] = set()
    for index, query in enumerate(queries):
        if not isinstance(query, dict):
            continue
        proof_file = query.get("proof_file") or query.get("sql_proof_file") or query.get("path")
        if not proof_file:
            continue
        proof_path = Path(str(proof_file))
        if not proof_path.is_absolute():
            if proof_path.parts and proof_path.parts[0] == "reports":
                proof_path = root / proof_path
            else:
                proof_path = proof_dir / proof_path
        if not proof_path.exists():
            errors.append(f"discovery_raw.json: queries_executed[{index}] proof file does not exist: {proof_file}")
        else:
            linked_files.add(proof_path.resolve().as_posix())

    proof_files = [
        path for path in proof_dir.glob("*.sql")
        if path.name != "sql_proof_template.sql"
    ]
    if not proof_files:
        errors.append("Discovery sql_proofs folder has no concrete .sql proof files")
    unlinked = [
        path.relative_to(root).as_posix()
        for path in proof_files
        if path.resolve().as_posix() not in linked_files
    ]
    if unlinked:
        errors.append("SQL proof files not linked from discovery_raw.json queries_executed[]: " + ", ".join(unlinked[:20]))

    report_text = ""
    for relative in ("cardinality_report.md", "relationship_profile.md"):
        path = discovery_dir / relative
        if path.exists():
            report_text += "\n" + path.read_text(encoding="utf-8", errors="replace").lower()
    if proof_files and not any(token in report_text for token in ("sql_proofs/", ".sql")):
        errors.append("cardinality_report.md or relationship_profile.md should link the SQL proof files that support relationship claims")

    return errors


def validate_status_review_sections(root: Path) -> list[str]:
    errors: list[str] = []
    files = [
        root / "reports" / "agent" / "PIPELINE_STATUS.md",
        root / "reports" / "agent" / "00_discovery" / "discovery_report.md",
        root / "reports" / "agent" / "00_discovery" / "DISCOVERY_APPROVAL_CHECKLIST.md",
    ]
    status_tokens = ("WARN", "FAIL", "BLOCKED", "SKIPPED")
    required_terms = ("why", "evidence", "review", "action")
    # Exact template headers that agents must not drop when rewriting PIPELINE_STATUS.md
    pipeline_required_headers = (
        "why this status was used",
        "evidence",
        "what to review",
        "required action",
    )

    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        upper = text.upper()
        if not any(token in upper for token in status_tokens):
            continue
        lower = text.lower()
        has_review_section = "status review" in lower or "status review queue" in lower
        if not has_review_section:
            errors.append(f"{path.as_posix()}: contains non-PASS statuses but no Status Review section")
            continue
        missing_terms = [term for term in required_terms if term not in lower]
        if missing_terms:
            errors.append(
                f"{path.as_posix()}: Status Review section is missing expected terms: "
                + ", ".join(missing_terms)
            )
        if path.name == "PIPELINE_STATUS.md":
            missing_headers = [
                header for header in pipeline_required_headers if header not in lower
            ]
            if missing_headers:
                errors.append(
                    f"{path.as_posix()}: Status Review Queue must keep template columns: "
                    + ", ".join(missing_headers)
                    + ". Copy headers from templates/reports/root/PIPELINE_STATUS.md"
                )

    return errors


def validate_report_index_why(root: Path) -> list[str]:
    """REPORT_INDEX must explain why non-PASS statuses were used."""
    errors: list[str] = []
    path = root / "reports" / "agent" / "REPORT_INDEX.md"
    if not path.exists():
        return errors
    text = path.read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    upper = text.upper()
    if not any(token in upper for token in ("WARN", "FAIL", "BLOCKED", "SKIPPED")):
        return errors
    if "why this status was used" not in lower and "why this status" not in lower:
        errors.append(
            f"{path.as_posix()}: contains non-PASS statuses but no 'Why this status was used' column. "
            "Copy headers from templates/reports/root/REPORT_INDEX.md so WARN/FAIL have an answer."
        )
    return errors


def validate_discovery_folder_hygiene(root: Path) -> list[str]:
    """Keep helper scripts and scratch JSON out of reports/agent/00_discovery."""
    errors: list[str] = []
    discovery_dir = root / "reports" / "agent" / "00_discovery"
    if not discovery_dir.exists():
        return errors

    allowed_json = {"core_profile.json", "discovery_raw.json", "first_pass_scope.json"}
    for path in sorted(discovery_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".py":
            errors.append(
                f"{path.as_posix()}: Python helpers must live under "
                "scripts/discovery/, not reports/agent/00_discovery/"
            )
        elif path.suffix.lower() == ".json" and path.name not in allowed_json:
            errors.append(
                f"{path.as_posix()}: scratch/non-canonical JSON must live under "
                "scripts/discovery/working/; keep only core_profile.json, "
                "discovery_raw.json, and first_pass_scope.json in discovery reports"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    root = args.root.resolve()
    errors: list[str] = []

    for relative in REQUIRED_DISCOVERY_FILES:
        path = root / relative
        if not path.exists():
            errors.append(f"Missing required discovery file: {relative}")

    for name in REQUIRED_JSON_KEYS:
        path = root / "reports" / "agent" / "00_discovery" / name
        if path.exists():
            errors.extend(validate_json(path))
    errors.extend(validate_sql_proof_linkage(root))
    errors.extend(validate_discovery_folder_hygiene(root))
    errors.extend(validate_status_review_sections(root))
    errors.extend(validate_scope_lock_consistency(root))
    errors.extend(validate_report_index_why(root))

    inventory = root / "reports/agent/00_discovery/sql_proofs/001_source_table_inventory.sql"
    if not inventory.exists():
        errors.append("Missing required discovery proof: reports/agent/00_discovery/sql_proofs/001_source_table_inventory.sql")

    if errors:
        print("Discovery artifact validation FAILED")
        for item in errors:
            print(f"- {item}")
        return 1

    print("Discovery artifact validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
