#!/usr/bin/env python3
"""Fail when executable skill logic hardcodes industry-specific entities.

Inspects scripts/validators for required industry tokens outside allowed
contexts (comments/docstrings/tests/fixtures/examples). Documentation examples
are allowed; executable required lists and hardcoded gates are not.

See AGENTS.md Domain neutrality and the upgrade acceptance criteria.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


# Tokens that must not appear as required executable expectations.
FORBIDDEN_ENTITY_RES = (
    re.compile(r"\bhospital\b", re.I),
    re.compile(r"\bpatient\b", re.I),
    re.compile(r"\bsubscription\b", re.I),
    re.compile(r"\bjarir\b", re.I),
    re.compile(r"\bzaam\b", re.I),
    re.compile(r"\bimei\b", re.I),
    re.compile(r"\bcrm_tos\b", re.I),
)

# Broader tokens only flagged in required-list / gate contexts.
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

REQUIRED_LIST_HINTS = (
    "required",
    "must build",
    "mandatory",
    "min_measures",
    "default=50",
    "default = 50",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def is_allowed_path(path: Path, skill_root: Path) -> bool:
    rel = path.relative_to(skill_root).as_posix().lower()
    if rel.startswith("fixtures/") or "/fixtures/" in rel:
        return True
    if rel.startswith("tests/") or "/tests/" in rel:
        return True
    if "example" in rel or "illustrative" in rel:
        return True
    return False


def python_executable_strings(path: Path) -> list[tuple[int, str]]:
    """Extract string constants likely used in executable comparisons/gates."""
    text = read_text(path)
    out: list[tuple[int, str]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((getattr(node, "lineno", 0), node.value))
        # Astroid-free fallback for joined lists used as token gates
    return out


def scan_python(path: Path, skill_root: Path) -> list[str]:
    if is_allowed_path(path, skill_root):
        return []
    # This checker necessarily embeds industry tokens inside detection regexes.
    if path.name == "check_domain_neutrality.py":
        return []
    finding: list[str] = []
    rel = path.relative_to(skill_root).as_posix()
    text = read_text(path)
    lower = text.lower()

    # Hard fail: forbidden entities in non-comment default args / token tuples for gates
    for lineno, value in python_executable_strings(path):
        vlower = value.lower()
        for pattern in FORBIDDEN_ENTITY_RES:
            if pattern.search(vlower):
                # Allow clear instructional error messages about domain neutrality
                if "domain-neutral" in vlower or "do not hardcode" in vlower or "industry" in vlower:
                    continue
                if "illustrative" in vlower or "example" in vlower:
                    continue
                # Allow detector pattern strings that mention entities only as forbidden markers
                if "forbidden" in vlower or "must not" in vlower:
                    continue
                finding.append(f"{rel}:{lineno}: forbidden entity token in executable string: {value!r}")

    # Soft-to-hard: required dimension lists that bake CONTEXT_SENSITIVE nouns
    for hint in REQUIRED_LIST_HINTS:
        if hint in lower and any(f"required.*{tok}" in lower or f"{tok}.*," in lower for tok in CONTEXT_SENSITIVE):
            # Heuristic: partner/program/product required lists
            if re.search(r"partner.?program.?product|required.*\b(partner|sku|subscription)\b", lower):
                finding.append(f"{rel}: suspicious industry required-list context near {hint!r}")

    # Default 50+ catalog count gates are forbidden as hard completion mode
    if re.search(r"default\s*=\s*50", text) and "min_measures" in lower:
        if "advisory" not in lower and path.name == "check_presentation_coverage.py":
            finding.append(
                f"{rel}: fixed default min_measures=50 is not allowed as hard completion gate"
            )
    if re.search(r"metric_count\s*<\s*50", text) and path.name.endswith("coverage.py"):
        finding.append(f"{rel}: hard-coded metric_count < 50 gate is not allowed")

    return finding


def scan_markdown_requirements(path: Path, skill_root: Path) -> list[str]:
    """Flag executable-requirement prose that mandates industry entities."""
    if is_allowed_path(path, skill_root):
        return []
    rel = path.relative_to(skill_root).as_posix()
    text = read_text(path)
    findings: list[str] = []
    # Only scan lines that look like hard requirements, not examples
    for i, line in enumerate(text.splitlines(), start=1):
        lower = line.lower().strip()
        if "illustrative" in lower or "example" in lower or "for example" in lower:
            continue
        if lower.startswith("|") and "when evidence" in lower:
            continue
        if re.search(r"must build.*\b(partner|program|product/sku|subscription|hospital|patient)\b", lower):
            findings.append(f"{rel}:{i}: requirement hardcodes industry entity: {line.strip()}")
        if re.search(r"required reporting classes.*\b(partner|program|product/sku)\b", lower):
            findings.append(f"{rel}:{i}: required reporting classes still industry-locked")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Skill repository root (default: parent of scripts/)",
    )
    args = parser.parse_args()
    skill_root = args.root.resolve()

    errors: list[str] = []
    warnings: list[str] = []

    scripts_dir = skill_root / "scripts"
    for path in sorted(scripts_dir.glob("*.py")):
        errors.extend(scan_python(path, skill_root))

    refs = skill_root / "references"
    for path in sorted(refs.glob("*.md")):
        hits = scan_markdown_requirements(path, skill_root)
        # Requirements docs may still be migrating; elevate clear must-build lines to errors
        errors.extend(hits)

    print(f"Domain neutrality scan: root={skill_root}")
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
