#!/usr/bin/env python3
"""Compare first-pass inclusion scope between two discovery_raw.json files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_tables(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tables = data.get("tables")
    if not isinstance(tables, list):
        raise ValueError(f"{path}: tables must be a list")
    out: dict[str, dict[str, Any]] = {}
    for item in tables:
        if not isinstance(item, dict):
            continue
        name = str(item.get("table_name") or item.get("name") or "").strip()
        if not name:
            continue
        status = str(item.get("inclusion_status") or "").strip().lower()
        out[name] = {
            "inclusion_status": status,
            "inclusion_reason": item.get("inclusion_reason") or "",
            "row_count": item.get("row_count"),
        }
    return out


def by_status(tables: dict[str, dict[str, Any]], status: str) -> set[str]:
    return {name for name, meta in tables.items() if meta["inclusion_status"] == status}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--left",
        type=Path,
        required=True,
        help="Path to first discovery_raw.json (often the approved run)",
    )
    parser.add_argument(
        "--right",
        type=Path,
        required=True,
        help="Path to second discovery_raw.json (often the new run)",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit 1 when included sets differ",
    )
    args = parser.parse_args()

    left = load_tables(args.left.resolve())
    right = load_tables(args.right.resolve())

    left_inc = by_status(left, "included")
    right_inc = by_status(right, "included")
    left_def = by_status(left, "deferred")
    right_def = by_status(right, "deferred")

    only_left = sorted(left_inc - right_inc)
    only_right = sorted(right_inc - left_inc)
    common = sorted(left_inc & right_inc)

    print(f"Left:  {args.left} | included={len(left_inc)} deferred={len(left_def)} total={len(left)}")
    print(f"Right: {args.right} | included={len(right_inc)} deferred={len(right_def)} total={len(right)}")
    print(f"Common included: {len(common)}")
    print(f"Only in left included ({len(only_left)}): {only_left}")
    print(f"Only in right included ({len(only_right)}): {only_right}")

    moved_left_to_deferred = sorted(name for name in only_left if name in right_def)
    moved_right_to_deferred = sorted(name for name in only_right if name in left_def)
    if moved_left_to_deferred:
        print(f"Left-included now deferred on right: {moved_left_to_deferred}")
    if moved_right_to_deferred:
        print(f"Right-included deferred on left: {moved_right_to_deferred}")

    if only_left or only_right:
        print(
            "RESULT: DIFF — same source can still disagree on borderline tables. "
            "Reuse the approved first_pass_scope.json / approved discovery, or ask the user to re-scope."
        )
        return 1 if args.fail_on_diff else 0

    print("RESULT: MATCH — included table sets are identical.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
