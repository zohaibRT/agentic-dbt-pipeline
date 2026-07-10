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
    errors.extend(validate_status_review_sections(root))

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
