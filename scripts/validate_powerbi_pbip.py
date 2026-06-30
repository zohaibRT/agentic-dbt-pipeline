#!/usr/bin/env python3
"""Static validation for generated Power BI PBIP/TMDL projects.

This intentionally checks the fragile failures the skill has seen in real
Power BI Desktop open attempts. It is not a full TMDL compiler; agents must
still run Power BI MCP/Desktop validation when available.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


PLATFORM_SCHEMA_RE = re.compile(
    r"^https://developer\.microsoft\.com/json-schemas/fabric/gitIntegration/"
    r"platformProperties/2\.[0-9]+\.[0-9]+/schema\.json$"
)
DEFAULT_REPORT_VERSION_AT_IMPORT = "5.55"


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path}: {message}")


def load_json(path: Path, errors: list[str]) -> object | None:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception as exc:  # noqa: BLE001 - report parse failures directly
        fail(errors, path, f"JSON parse failed: {exc}")
        return None


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_pbip_shortcut(root: Path, errors: list[str]) -> None:
    pbips = list(root.rglob("*.pbip"))
    if not pbips:
        fail(errors, root, "No .pbip file found")
        return

    for path in pbips:
        data = load_json(path, errors)
        if not isinstance(data, dict):
            continue
        artifacts = data.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            fail(errors, path, "Missing non-empty artifacts list")
            continue
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                fail(errors, path, f"artifacts[{index}] is not an object")
                continue
            if "dataset" in artifact:
                fail(errors, path, f"artifacts[{index}].dataset is not allowed for report PBIP shortcuts")
            if "report" not in artifact:
                fail(errors, path, f"artifacts[{index}].report is required for report PBIP shortcuts")


def validate_json_files(
    root: Path,
    errors: list[str],
    *,
    expected_report_version_at_import: str | None,
    fix_report_version_at_import: bool,
) -> None:
    for path in root.rglob("*.json"):
        data = load_json(path, errors)
        if path.name == "report.json" and isinstance(data, dict):
            theme_collection = data.setdefault("themeCollection", {}) if fix_report_version_at_import else data.get("themeCollection", {})
            if fix_report_version_at_import and not isinstance(theme_collection, dict):
                data["themeCollection"] = {}
                theme_collection = data["themeCollection"]

            base_theme = (
                theme_collection.setdefault("baseTheme", {})
                if fix_report_version_at_import and isinstance(theme_collection, dict)
                else theme_collection.get("baseTheme") if isinstance(theme_collection, dict) else None
            )
            if fix_report_version_at_import and not isinstance(base_theme, dict) and isinstance(theme_collection, dict):
                theme_collection["baseTheme"] = {}
                base_theme = theme_collection["baseTheme"]

            if not isinstance(base_theme, dict):
                fail(errors, path, "themeCollection.baseTheme is missing or not an object")
                continue
            value = base_theme.get("reportVersionAtImport")
            if fix_report_version_at_import and expected_report_version_at_import:
                if not isinstance(value, str) or value != expected_report_version_at_import:
                    base_theme["reportVersionAtImport"] = expected_report_version_at_import
                    write_json(path, data)
                    value = expected_report_version_at_import
            if value is None:
                fail(errors, path, "themeCollection.baseTheme.reportVersionAtImport is missing")
            elif not isinstance(value, str):
                fail(errors, path, "themeCollection.baseTheme.reportVersionAtImport must be a string")
            elif not value.strip():
                fail(errors, path, "themeCollection.baseTheme.reportVersionAtImport must not be empty")
            elif expected_report_version_at_import and value != expected_report_version_at_import:
                fail(
                    errors,
                    path,
                    "themeCollection.baseTheme.reportVersionAtImport must be "
                    f'"{expected_report_version_at_import}" unless a known-good project reference proves another value',
                )


def validate_platform_files(root: Path, errors: list[str]) -> None:
    for path in root.rglob(".platform"):
        data = load_json(path, errors)
        if not isinstance(data, dict):
            continue
        schema = data.get("$schema")
        if not isinstance(schema, str) or not PLATFORM_SCHEMA_RE.match(schema):
            fail(errors, path, "$schema does not match Fabric gitIntegration platformProperties 2.x.y pattern")


def validate_tmdl_keywords_and_keys(root: Path, errors: list[str]) -> None:
    key_patterns = [
        re.compile(r"^\s*isKey\s*:\s*true\s*$", re.IGNORECASE),
        re.compile(r"^\s*IsKey\s*=\s*True\s*$"),
        re.compile(r"^\s*isKey\s*=\s*true\s*$", re.IGNORECASE),
    ]
    loose_m_patterns = [
        re.compile(r"^\s*let\s*$", re.IGNORECASE),
        re.compile(r"^\s*in\s*$", re.IGNORECASE),
    ]

    for path in root.rglob("*.tmdl"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        key_count = 0
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.match(line) for pattern in loose_m_patterns):
                fail(errors, path, f"Loose Power Query keyword at line {line_number}: {line.strip()}")
            if any(pattern.match(line) for pattern in key_patterns):
                key_count += 1
        if key_count > 1:
            fail(errors, path, f"More than one column has IsKey=true ({key_count} found)")


def relationship_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_relationship = False

    for line in text.splitlines():
        if re.match(r"^\s*relationship\b", line, re.IGNORECASE):
            if current:
                blocks.append("\n".join(current))
            current = [line]
            in_relationship = True
            continue
        if in_relationship:
            if re.match(r"^\S", line) and current and not line.lower().startswith(("relationship", "\t", " ")):
                blocks.append("\n".join(current))
                current = []
                in_relationship = False
            else:
                current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def extract_table(block: str, field_prefix: str) -> str | None:
    patterns = [
        rf"{field_prefix}Column\s*:\s*'([^']+)'\[",
        rf"{field_prefix}Column\s*:\s*([A-Za-z_][\w]*)\[",
        rf"{field_prefix}Column\s*:\s*([A-Za-z_][\w]*)\.",
        rf"{field_prefix}Table\s*:\s*'?([A-Za-z_][\w]*)'?",
    ]
    for pattern in patterns:
        match = re.search(pattern, block, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_active_edges(root: Path) -> list[tuple[str, str, Path]]:
    edges: list[tuple[str, str, Path]] = []
    for path in root.rglob("*.tmdl"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for block in relationship_blocks(text):
            if re.search(r"\b(isActive|active)\s*:\s*false\b", block, re.IGNORECASE):
                continue
            left = extract_table(block, "from")
            right = extract_table(block, "to")
            if left and right and left != right:
                edges.append((left, right, path))
    return edges


def count_paths(graph: dict[str, set[str]], start: str, end: str, max_paths: int = 2) -> int:
    count = 0
    stack: list[tuple[str, set[str]]] = [(start, {start})]
    while stack:
        node, seen = stack.pop()
        for neighbor in graph[node]:
            if neighbor == end:
                count += 1
                if count >= max_paths:
                    return count
            elif neighbor not in seen:
                stack.append((neighbor, seen | {neighbor}))
    return count


def validate_relationship_ambiguity(root: Path, errors: list[str]) -> None:
    edges = extract_active_edges(root)
    graph: dict[str, set[str]] = defaultdict(set)
    for left, right, _path in edges:
        graph[left].add(right)
        graph[right].add(left)

    tables = sorted(graph)
    for index, left in enumerate(tables):
        for right in tables[index + 1 :]:
            if count_paths(graph, left, right) > 1:
                fail(errors, root, f"Multiple active relationship paths between {left} and {right}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a generated Power BI PBIP/TMDL project")
    parser.add_argument("path", type=Path, help="PBIP project root or folder containing the .pbip file")
    parser.add_argument(
        "--expected-report-version-at-import",
        default=DEFAULT_REPORT_VERSION_AT_IMPORT,
        help=(
            "Expected report.json themeCollection.baseTheme.reportVersionAtImport string. "
            "Use an empty value only when a validated reference project requires another version."
        ),
    )
    parser.add_argument(
        "--allow-any-report-version-at-import",
        action="store_true",
        help="Allow any non-empty string for reportVersionAtImport.",
    )
    parser.add_argument(
        "--fix-report-version-at-import",
        action="store_true",
        help="Repair missing, non-string, or wrong reportVersionAtImport to the expected string before validation.",
    )
    args = parser.parse_args()

    root = args.path.resolve()
    errors: list[str] = []
    if not root.exists():
        print(f"ERROR: {root} does not exist", file=sys.stderr)
        return 2

    validate_pbip_shortcut(root, errors)
    expected_report_version_at_import = None if args.allow_any_report_version_at_import else args.expected_report_version_at_import

    validate_json_files(
        root,
        errors,
        expected_report_version_at_import=expected_report_version_at_import,
        fix_report_version_at_import=args.fix_report_version_at_import,
    )
    validate_platform_files(root, errors)
    validate_tmdl_keywords_and_keys(root, errors)
    validate_relationship_ambiguity(root, errors)

    if errors:
        print("Power BI PBIP static validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Power BI PBIP static validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
