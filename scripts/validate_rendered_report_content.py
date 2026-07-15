#!/usr/bin/env python3
"""Static scan of rendered presentation HTML/JSON for business-readability issues."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from lib_gate_common import print_results, read_text

SNAKE_CASE_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
PREFIX_LABEL_RE = re.compile(r"\b(?:dim|fct|stg)_[a-z0-9_]+\b", re.I)
HIGH_PRECISION_RE = re.compile(r"\b\d+\.\d{5,}\b")
RAW_RATIO_RE = re.compile(r">\s*0\.\d{3,}\s*<")
TODO_RE = re.compile(r"\b(?:TODO|TBD)\b", re.I)
STACK_TRACE_RE = re.compile(
    r"(Traceback \(most recent call last\)|File \"[^\"]+\", line \d+|Exception:|Error:)",
    re.I,
)


def scan_text(text: str, source: str, errors: list[str]) -> None:
    for match in PREFIX_LABEL_RE.finditer(text):
        errors.append(f"{source}: visible technical model label '{match.group(0)}'")
    for match in HIGH_PRECISION_RE.finditer(text):
        errors.append(f"{source}: high-precision float '{match.group(0)}'")
    for match in RAW_RATIO_RE.finditer(text):
        token = match.group(0).strip(">< ").strip()
        errors.append(f"{source}: raw ratio value '{token}' (format as percent)")
    for match in TODO_RE.finditer(text):
        errors.append(f"{source}: placeholder token '{match.group(0)}'")
    if STACK_TRACE_RE.search(text):
        errors.append(f"{source}: stack trace or exception text visible in report")

    # Table/header cells and prominent labels
    for cell_match in re.finditer(r"<t[hd][^>]*>([^<]{3,})</t[hd]>", text, re.I):
        label = cell_match.group(1).strip()
        if SNAKE_CASE_RE.fullmatch(label) and "_" in label:
            errors.append(f"{source}: snake_case table label '{label}'")
    for heading in re.finditer(r"<h[1-6][^>]*>([^<]{3,})</h[1-6]>", text, re.I):
        label = heading.group(1).strip()
        if SNAKE_CASE_RE.fullmatch(label) and "_" in label:
            errors.append(f"{source}: snake_case heading '{label}'")


def scan_json_payload(path: Path, errors: list[str]) -> None:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        errors.append(f"{path.name}: invalid JSON payload")
        return

    def walk(node: object, prefix: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and SNAKE_CASE_RE.fullmatch(key) and key.startswith(
                    ("dim_", "fct_", "stg_")
                ):
                    errors.append(f"{path.name}: technical key '{key}' in {prefix}")
                walk(value, f"{prefix}.{key}")
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, f"{prefix}[{idx}]")
        elif isinstance(node, str):
            if PREFIX_LABEL_RE.search(node):
                errors.append(f"{path.name}: technical label text '{node}' in {prefix}")
            if HIGH_PRECISION_RE.search(node):
                errors.append(f"{path.name}: high-precision value '{node}' in {prefix}")

    walk(data, "root")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Presentation output directory containing report.html",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    matplotlib = args.report_dir.resolve() if args.report_dir else root / "reports" / "agent" / "10_presentation" / "matplotlib"
    report_html = matplotlib / "report.html"
    if not report_html.exists():
        print("SKIPPED: no report.html")
        return 0

    errors: list[str] = []
    warnings: list[str] = []

    scan_text(read_text(report_html), "report.html", errors)

    for json_path in sorted(matplotlib.glob("*.json")):
        scan_json_payload(json_path, errors)

    print(f"Rendered report content scan: errors={len(errors)}")
    return print_results("Rendered report content validation", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
