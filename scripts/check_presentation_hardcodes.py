#!/usr/bin/env python3
"""Fail when presentation Python hardcodes credentials or foreign project paths.

Presentation must resolve warehouse connection from the project's dbt profile
and non-secret env / project config — never from copied passwords or machine paths.
"""

from __future__ import annotations

from pathlib import Path
from lib_gate_common import add_output_json_arg, print_results

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
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    presentation = root / "reports" / "agent" / "10_presentation"
    if not presentation.exists():
        return print_results(
            "Presentation hardcode check",
            [],
            [],
            output_json=getattr(args, "output_json", None),
            validator_id=Path(__file__).stem,
            skipped=True,
            skip_reason="no presentation folder",
        )

    errors: list[str] = []
    py_files = [p for p in presentation.rglob("*.py") if "__pycache__" not in p.parts]
    if not py_files:
        return print_results(
            "Presentation hardcode check",
            [],
            [],
            output_json=getattr(args, "output_json", None),
            validator_id=Path(__file__).stem,
            skipped=True,
            skip_reason="no presentation Python files",
        )

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
    return print_results(
        "Presentation hardcode check",
        errors,
        [],
        output_json=getattr(args, "output_json", None),
        validator_id=Path(__file__).stem,
    )


if __name__ == "__main__":
    raise SystemExit(main())
