#!/usr/bin/env python3
"""Fail when executable skill logic hardcodes industry-specific entities.

Scans scripts, templates, prompts, YAML, SKILL/AGENTS, and requirement
references. Documentation examples are allowed; executable required lists and
hardcoded gates are not.

See AGENTS.md Domain neutrality and the upgrade acceptance criteria.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


FORBIDDEN_ENTITY_RES = (
    re.compile(r"\bhospital\b", re.I),
    re.compile(r"\bpatient\b", re.I),
    re.compile(r"\bsubscription\b", re.I),
    re.compile(r"\bjarir\b", re.I),
    re.compile(r"\bzaam\b", re.I),
    re.compile(r"\bimei\b", re.I),
    re.compile(r"\bcrm_tos\b", re.I),
)

CONTEXT_SENSITIVE = (
    "customer",
    "partner",
    "device",
    "order",
    "sku",
    "payment",
    "invoice",
    "employee",
    "program",
    "product",
)

REQUIRED_LIST_RES = (
    re.compile(r"\brequired\b.{0,80}\b(partner|program|product/sku|sku|subscription|hospital|patient)\b", re.I),
    re.compile(r"\bmust build\b.{0,80}\b(partner|program|product|sku|subscription|hospital|patient|dim_customer|fct_orders)\b", re.I),
    re.compile(r"\bmandatory\b.{0,80}\b(partner|program|sku|subscription|hospital|patient)\b", re.I),
    re.compile(r"\bdim_customer\b.*\bmust\b|\bmust\b.*\bdim_customer\b", re.I),
    re.compile(r"\bfct_orders\b.*\brequired\b|\brequired\b.*\bfct_orders\b", re.I),
)

HARDCODED_MODEL_REQUIREMENT = re.compile(
    r"(must build|required model|mandatory model|always create).{0,60}\b(dim_|fct_|mart_)[a-z0-9_]+\b",
    re.I,
)

KPI_FORMULA_PATTERNS = (
    re.compile(r"required.*count\s*\(\s*\*\s*\)\s*from\s+orders", re.I),
    re.compile(r"must\s+use\s+revenue\s*=", re.I),
    re.compile(r"mandatory\s+page.*sales\s+dashboard", re.I),
)

REQUIRED_SOURCES_LIST = re.compile(r"required_sources\s*=\s*\[", re.I)

SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "target",
    "dbt_packages",
    "logs",
    "fixtures",
    ".cursor",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def is_allowed_path(path: Path, skill_root: Path) -> bool:
    rel = path.relative_to(skill_root).as_posix().lower()
    parts = set(rel.split("/"))
    if parts & SKIP_DIR_PARTS:
        return True
    if rel.startswith("tests/") or "/tests/" in rel:
        return True
    if "example" in rel or "illustrative" in rel:
        return True
    if rel.startswith("docs/analytics-gate-p1-migration") or rel.startswith(
        "docs/analytics-product-completeness-migration"
    ) or rel.startswith(
        "docs/production_analytics_upgrade_summary"
    ):
        # Historical migration prose may mention removed 50+ behavior.
        return True
    return False


def python_executable_strings(path: Path) -> list[tuple[int, str]]:
    text = read_text(path)
    out: list[tuple[int, str]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((getattr(node, "lineno", 0), node.value))
    return out


def scan_python(path: Path, skill_root: Path) -> list[str]:
    if is_allowed_path(path, skill_root):
        return []
    if path.name == "check_domain_neutrality.py":
        return []
    finding: list[str] = []
    rel = path.relative_to(skill_root).as_posix()
    text = read_text(path)
    lower = text.lower()

    for lineno, value in python_executable_strings(path):
        vlower = value.lower()
        for pattern in FORBIDDEN_ENTITY_RES:
            if pattern.search(vlower):
                if any(
                    token in vlower
                    for token in (
                        "domain-neutral",
                        "do not hardcode",
                        "industry",
                        "illustrative",
                        "example",
                        "forbidden",
                        "must not",
                        "fixture",
                        "test",
                    )
                ):
                    continue
                finding.append(f"{rel}:{lineno}: forbidden entity token in executable string: {value!r}")

    for pattern in REQUIRED_LIST_RES:
        if pattern.search(text):
            finding.append(f"{rel}: suspicious industry required-list regex match: {pattern.pattern}")

    if re.search(r"default\s*=\s*50", text) and "min_measures" in lower:
        if "advisory" not in lower:
            finding.append(f"{rel}: fixed default min_measures=50 is not allowed as hard completion gate")
    if re.search(r"metric_count\s*<\s*50", text) and "coverage" in path.name:
        finding.append(f"{rel}: hard-coded metric_count < 50 gate is not allowed")
    if HARDCODED_MODEL_REQUIREMENT.search(text):
        finding.append(f"{rel}: hardcoded model name requirement detected")
    for pattern in KPI_FORMULA_PATTERNS:
        if pattern.search(text):
            finding.append(f"{rel}: hardcoded KPI formula/page pattern: {pattern.pattern}")
    if REQUIRED_SOURCES_LIST.search(text):
        finding.append(f"{rel}: hardcoded required_sources list detected")

    return finding


def scan_text_requirements(path: Path, skill_root: Path) -> list[str]:
    if is_allowed_path(path, skill_root):
        return []
    rel = path.relative_to(skill_root).as_posix()
    text = read_text(path)
    findings: list[str] = []
    for i, line in enumerate(text.splitlines(), start=1):
        lower = line.lower().strip()
        if any(token in lower for token in ("illustrative", "example", "for example", "advisory only")):
            continue
        if lower.startswith("|") and "when evidence" in lower:
            continue
        # Historical "removed 50+" discussion is fine in migration docs; skip pure history lines
        if "no longer" in lower or "removed" in lower or "not a" in lower and "gate" in lower:
            continue
        for pattern in REQUIRED_LIST_RES:
            if pattern.search(line):
                findings.append(f"{rel}:{i}: requirement hardcodes industry entity: {line.strip()}")
                break
        if HARDCODED_MODEL_REQUIREMENT.search(line):
            findings.append(f"{rel}:{i}: hardcoded model name requirement: {line.strip()}")
        for pattern in KPI_FORMULA_PATTERNS:
            if pattern.search(line):
                findings.append(f"{rel}:{i}: hardcoded KPI formula/page pattern: {line.strip()}")
                break
        if REQUIRED_SOURCES_LIST.search(line):
            findings.append(f"{rel}:{i}: hardcoded required_sources list: {line.strip()}")
        if re.search(r"\bhard\s+fail\b.{0,40}\b(50|30)\b|\bfail\b.{0,40}\bbelow\s+50", lower):
            findings.append(f"{rel}:{i}: fixed-count hard fail rule must not remain: {line.strip()}")
    return findings


def iter_scan_files(skill_root: Path) -> list[Path]:
    patterns = (
        "scripts/**/*.py",
        "templates/**/*.*",
        "references/**/*.md",
        "agents/**/*.md",
        "docs/**/*.md",
    )
    files: list[Path] = []
    for pattern in patterns:
        files.extend(skill_root.glob(pattern))
    for name in ("SKILL.md", "AGENTS.md", "prompt.md", "project.config.yml", "README.md"):
        candidate = skill_root / name
        if candidate.exists():
            files.append(candidate)
    # Deduplicate
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return sorted(unique)


def main() -> int:
    # Prefer shared ValidatorResult helpers when available (acceptance-gate protocol).
    try:
        from lib_gate_common import add_output_json_arg, print_results
    except ImportError:  # pragma: no cover
        add_output_json_arg = None  # type: ignore[assignment]
        print_results = None  # type: ignore[assignment]

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Skill repository root (default: parent of scripts/)",
    )
    if add_output_json_arg is not None:
        add_output_json_arg(parser)
    args = parser.parse_args()
    skill_root = args.root.resolve()

    errors: list[str] = []
    warnings: list[str] = []
    scanned = 0

    for path in iter_scan_files(skill_root):
        scanned += 1
        suffix = path.suffix.lower()
        if suffix == ".py":
            errors.extend(scan_python(path, skill_root))
        elif suffix in {".md", ".yml", ".yaml", ".sql", ".html", ".js", ".ts", ".json"}:
            errors.extend(scan_text_requirements(path, skill_root))

    print(f"Domain neutrality scan: root={skill_root}, files={scanned}")
    if print_results is not None:
        return print_results(
            "Domain neutrality check",
            errors,
            warnings,
            output_json=getattr(args, "output_json", None),
            validator_id=Path(__file__).stem,
            details={"files_scanned": scanned, "root": str(skill_root)},
        )

    for item in warnings:
        print(f"WARN: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    if errors:
        print("Domain neutrality check FAILED")
        return 1
    print("Domain neutrality check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
