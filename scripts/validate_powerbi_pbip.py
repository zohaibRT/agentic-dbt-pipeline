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
LINEAGE_TAG_RE = re.compile(r"\blineageTag\s*:\s*([0-9a-fA-F-]{8,})\b")
UUID_LIKE_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


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


def report_artifact_reference_path(artifact: dict, pbip_path: Path, errors: list[str], index: int) -> Path | None:
    report = artifact.get("report")
    if isinstance(report, str):
        report_path = report
    elif isinstance(report, dict):
        report_path = report.get("path") or report.get("relativePath")
    else:
        fail(errors, pbip_path, f"artifacts[{index}].report must be a path string or object with path")
        return None

    if not isinstance(report_path, str) or not report_path.strip():
        fail(errors, pbip_path, f"artifacts[{index}].report.path must be a non-empty string")
        return None

    return (pbip_path.parent / report_path).resolve()


def validate_definition_pbir(report_dir: Path, errors: list[str]) -> None:
    definition_dir = report_dir / "definition"
    pbir_path = report_dir / "definition.pbir"
    legacy_pbir_path = definition_dir / "definition.pbir"
    if legacy_pbir_path.exists():
        fail(errors, legacy_pbir_path, "legacy nested definition.pbir is not allowed for enhanced PBIR; use Report/definition.pbir")
    if not pbir_path.exists():
        fail(errors, report_dir, "Report/definition.pbir is required for enhanced PBIR")
        return
    if pbir_path.stat().st_size == 0:
        fail(errors, pbir_path, "definition.pbir must not be empty")
        return

    data = load_json(pbir_path, errors)
    if not isinstance(data, dict):
        return
    if not data:
        fail(errors, pbir_path, "definition.pbir must contain a non-empty ReportDefinition object")
        return

    dataset_reference = data.get("datasetReference")
    by_path = dataset_reference.get("byPath") if isinstance(dataset_reference, dict) else None
    semantic_path = by_path.get("path") if isinstance(by_path, dict) else None
    if not isinstance(semantic_path, str) or ".SemanticModel" not in semantic_path:
        fail(errors, pbir_path, "datasetReference.byPath.path must point to the SemanticModel artifact")
        return

    semantic_candidates = [
        (report_dir / semantic_path).resolve(),
        (definition_dir / semantic_path).resolve(),
        (report_dir.parent / semantic_path).resolve(),
    ]
    if not any(candidate.exists() and candidate.is_dir() for candidate in semantic_candidates):
        fail(errors, pbir_path, f"datasetReference.byPath.path does not resolve to an existing SemanticModel folder: {semantic_path}")


def validate_report_pages(report_dir: Path, errors: list[str]) -> None:
    pages_dir = report_dir / "definition" / "pages"
    pages_json = pages_dir / "pages.json"
    if not pages_json.exists():
        fail(errors, pages_json, "definition/pages/pages.json is required for enhanced PBIR report pages")
        return

    data = load_json(pages_json, errors)
    if not isinstance(data, dict):
        return

    page_order = data.get("pageOrder")
    if not isinstance(page_order, list) or not page_order:
        fail(errors, pages_json, "pageOrder must be a non-empty list")
        return
    active_page_name = data.get("activePageName")
    if isinstance(active_page_name, str) and active_page_name and active_page_name not in page_order:
        fail(errors, pages_json, "activePageName must refer to a page listed in pageOrder")

    for page_name in page_order:
        if not isinstance(page_name, str) or not page_name.strip():
            fail(errors, pages_json, "pageOrder entries must be non-empty strings")
            continue
        page_dir = pages_dir / page_name
        if not page_dir.exists() or not page_dir.is_dir():
            fail(errors, page_dir, "page folder from pageOrder is missing")
            continue
        page_json = page_dir / "page.json"
        if not page_json.exists():
            fail(errors, page_json, "page.json is required for every page in pageOrder")
        visual_count = sum(1 for path in page_dir.rglob("visual.json") if path.is_file())
        if visual_count == 0:
            fail(errors, page_dir, "page has no visual.json files; shell-only or blank pages are not allowed")


def validate_single_report_artifact(report_dir: Path, errors: list[str]) -> None:
    if not report_dir.exists() or not report_dir.is_dir():
        fail(errors, report_dir, "Referenced Report artifact folder is missing")
        return
    if report_dir.suffix != ".Report":
        fail(errors, report_dir, "Referenced report artifact folder must end with .Report")

    definition_dir = report_dir / "definition"
    if not definition_dir.exists() or not definition_dir.is_dir():
        fail(errors, report_dir, "Report/definition folder is required")
        return

    validate_definition_pbir(report_dir, errors)
    validate_report_pages(report_dir, errors)

    root_report_json = report_dir / "report.json"
    if root_report_json.exists():
        fail(errors, root_report_json, "legacy root report.json is not allowed for enhanced PBIR; use Report/definition/report.json")

    report_json = definition_dir / "report.json"
    if not report_json.exists():
        fail(errors, report_json, "Report/definition/report.json is required")

    version_path = definition_dir / "version.json"
    if not version_path.exists():
        fail(errors, report_dir, "Report/definition/version.json is required")
    else:
        data = load_json(version_path, errors)
        if isinstance(data, dict):
            schema = data.get("$schema")
            version = data.get("version")
            if not isinstance(schema, str) or "report/definition/versionMetadata" not in schema:
                fail(errors, version_path, "$schema must be the Power BI report definition version metadata schema")
            if not isinstance(version, str) or not version.strip():
                fail(errors, version_path, "version must be a non-empty string")


def validate_pbip_shortcut(root: Path, errors: list[str], report_dirs_from_shortcuts: set[Path]) -> None:
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
                continue
            report_dir = report_artifact_reference_path(artifact, path, errors, index)
            if report_dir is None:
                continue
            report_dirs_from_shortcuts.add(report_dir)
            validate_single_report_artifact(report_dir, errors)


def validate_report_artifact(root: Path, errors: list[str], report_dirs_from_shortcuts: set[Path]) -> None:
    report_dirs = [path for path in root.rglob("*.Report") if path.is_dir()]
    if not report_dirs:
        fail(errors, root, "No .Report artifact folder found")
    for report_dir in report_dirs:
        resolved = report_dir.resolve()
        if resolved in report_dirs_from_shortcuts:
            continue
        validate_single_report_artifact(resolved, errors)


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
        config = data.get("config")
        if not isinstance(config, dict) or not config:
            fail(errors, path, "config object is required and must not be empty")
            continue
        version = config.get("version")
        logical_id = config.get("logicalId")
        if version != "2.0":
            fail(errors, path, 'config.version must be "2.0"')
        if not isinstance(logical_id, str) or not UUID_LIKE_RE.match(logical_id):
            fail(errors, path, "config.logicalId must be a stable UUID string")


def validate_tmdl_keywords_and_keys(root: Path, errors: list[str]) -> None:
    key_patterns = [
        re.compile(r"^\s*isKey\s*:\s*true\s*$", re.IGNORECASE),
        re.compile(r"^\s*IsKey\s*=\s*True\s*$"),
        re.compile(r"^\s*isKey\s*=\s*true\s*$", re.IGNORECASE),
    ]
    unindented_m_patterns = [
        re.compile(r"^\s*let\s*$", re.IGNORECASE),
        re.compile(r"^\s*in\s*$", re.IGNORECASE),
    ]

    for path in root.rglob("*.tmdl"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        key_count = 0
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "```" in line:
                fail(errors, path, f"Markdown code fence is not valid TMDL at line {line_number}")
            if line and not line[0].isspace() and any(pattern.match(line) for pattern in unindented_m_patterns):
                fail(errors, path, f"Unindented loose Power Query keyword at line {line_number}: {line.strip()}")
            if any(pattern.match(line) for pattern in key_patterns):
                key_count += 1
        if key_count > 1:
            fail(errors, path, f"More than one column has IsKey=true ({key_count} found)")


def validate_tmdl_lineage_tags(root: Path, errors: list[str]) -> None:
    seen: dict[str, Path] = {}
    for path in root.rglob("*.tmdl"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for tag in LINEAGE_TAG_RE.findall(text):
            normalized = tag.lower()
            if normalized in seen:
                fail(errors, path, f"Duplicate lineageTag {tag}; first seen in {seen[normalized]}")
            else:
                seen[normalized] = path


def validate_postgres_tmdl_patterns(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*.tmdl"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if re.search(r"\bPgSchema\b", text):
            fail(errors, path, "PgSchema expression is not allowed; hardcode schema in each partition source record")
        if re.search(r"PostgreSQL\.Database\(\s*PgServer\s*,\s*PgDatabase\s*\)", text):
            fail(errors, path, 'PostgreSQL.Database parameters must be quoted as #"PgServer", #"PgDatabase"')

        if "PostgreSQL.Database(" not in text:
            continue
        if not re.search(r'PostgreSQL\.Database\(\s*#"[A-Za-z0-9_ ]+"\s*,\s*#"[A-Za-z0-9_ ]+"\s*\)', text):
            fail(errors, path, 'PostgreSQL.Database call must use quoted parameter references such as #"PgServer", #"PgDatabase"')
        if "Table.SelectColumns" not in text:
            fail(errors, path, "PostgreSQL import partitions must use Table.SelectColumns to load only modeled columns")
        if "Table.TransformColumnTypes" not in text:
            fail(errors, path, "PostgreSQL import partitions must use Table.TransformColumnTypes for dates and numeric columns")
        if "PBI_ResultType" not in text:
            fail(errors, path, "PostgreSQL import partitions must include annotation PBI_ResultType = Table")
        if re.search(r"Source\s*{\s*\[\s*Schema\s*=\s*#\"", text):
            fail(errors, path, "Partition schema must be hardcoded in Source{[Schema=\"...\", Item=\"...\"]}[Data], not a parameter expression")


def validate_metrics_table_partition(root: Path, errors: list[str]) -> None:
    for path in root.rglob("*.tmdl"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        if not re.search(r"^\s*table\s+'?_[^'\n]*\b(Metrics|Measures)\b", text, re.IGNORECASE | re.MULTILINE):
            continue
        if not re.search(r"\bpartition\b.*=\s*calculated\b", text, re.IGNORECASE):
            fail(errors, path, "Metrics or measures table must include a calculated partition")
        if 'ROW("MetricKey", 1)' not in text and "ROW('MetricKey', 1)" not in text:
            fail(errors, path, 'Metrics or measures table calculated partition must use ROW("MetricKey", 1)')


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

    report_dirs_from_shortcuts: set[Path] = set()
    validate_pbip_shortcut(root, errors, report_dirs_from_shortcuts)
    validate_report_artifact(root, errors, report_dirs_from_shortcuts)
    expected_report_version_at_import = None if args.allow_any_report_version_at_import else args.expected_report_version_at_import

    validate_json_files(
        root,
        errors,
        expected_report_version_at_import=expected_report_version_at_import,
        fix_report_version_at_import=args.fix_report_version_at_import,
    )
    validate_platform_files(root, errors)
    validate_tmdl_keywords_and_keys(root, errors)
    validate_tmdl_lineage_tags(root, errors)
    validate_postgres_tmdl_patterns(root, errors)
    validate_metrics_table_partition(root, errors)
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
