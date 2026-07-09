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
