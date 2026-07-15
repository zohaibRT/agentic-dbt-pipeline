#!/usr/bin/env python3
"""Fail when presentation Python hardcodes credentials or foreign project paths.

Presentation must resolve warehouse connection from the project's dbt profile
and non-secret env / project config — never from copied passwords or machine paths.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PASSWORD_LITERAL_RE = re.compile(r"""\bpassword\s*=\s*['\"][^'\"]+['\"]""", re.I)
PASS_LITERAL_RE = re.compile(r"""\bpass\s*=\s*['\"][^'\"]+['\"]""", re.I)
FOREIGN_PROJECT_RE = re.compile(r"\bagentic_dbt_\d+\b", re.I)
ABSOLUTE_CODEBASE_RE = re.compile(
    r"""['\"](?:[A-Za-z]:[\\/]+codebase|[A-Za-z]:[\\/]+Users|/Users/|/home/)[^'\"]*['\"]""",
    re.I,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    presentation = root / "reports" / "agent" / "10_presentation"
    if not presentation.exists():
        print("SKIPPED: no presentation folder")
        return 0

    errors: list[str] = []
    py_files = [p for p in presentation.rglob("*.py") if "__pycache__" not in p.parts]
    if not py_files:
        print("SKIPPED: no presentation Python files")
        return 0

    for path in py_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        if PASSWORD_LITERAL_RE.search(text) or PASS_LITERAL_RE.search(text):
            errors.append(f"{rel}: hardcoded password/pass string literal — use dbt profiles.yml")
        if ABSOLUTE_CODEBASE_RE.search(text):
            errors.append(f"{rel}: absolute machine path — use Path(__file__) / project-relative paths")
        if FOREIGN_PROJECT_RE.search(text):
            errors.append(f"{rel}: references another agentic_dbt_* project id")

    print(f"Checked {len(py_files)} presentation Python file(s)")
    for item in errors:
        print(f"ERROR: {item}")
    if errors:
        print("Presentation hardcode check FAILED")
        return 1
    print("Presentation hardcode check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
