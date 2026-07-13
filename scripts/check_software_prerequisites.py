#!/usr/bin/env python3
"""Detect software prerequisites for the agentic dbt pipeline.

Exit codes:
- 0: all required checks PASS or WARN
- 1: one or more required checks FAIL/BLOCKED
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ADAPTER_PACKAGES = {
    "postgres": "dbt-postgres",
    "redshift": "dbt-redshift",
    "snowflake": "dbt-snowflake",
    "bigquery": "dbt-bigquery",
    "databricks": "dbt-databricks",
}


@dataclass
class CheckResult:
    name: str
    required_for: str
    status: str
    detected: str
    action: str
    notes: str = ""


def run_cmd(command: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output.strip()


def which(name: str) -> str | None:
    return shutil.which(name)


def check_python() -> CheckResult:
    code, out = run_cmd([sys.executable, "--version"])
    if code == 0 and out:
        return CheckResult("Python", "scripts + dbt env", "PASS", out, "Use active interpreter", "")
    return CheckResult(
        "Python",
        "scripts + dbt env",
        "BLOCKED",
        "missing",
        "Install Python 3.12 and rerun",
        "Required for setup and later phases",
    )


def check_pip() -> CheckResult:
    code, out = run_cmd([sys.executable, "-m", "pip", "--version"])
    if code == 0 and out:
        return CheckResult("pip", "package install", "PASS", out.splitlines()[0], "Ready", "")
    return CheckResult(
        "pip",
        "package install",
        "BLOCKED",
        "missing",
        "Repair Python install or bootstrap pip",
        "",
    )


def check_venv(root: Path) -> CheckResult:
    venv_dir = root / ".venv"
    if venv_dir.exists():
        return CheckResult("venv", "isolated installs", "PASS", str(venv_dir), "Existing .venv found", "")
    return CheckResult(
        "venv",
        "isolated installs",
        "WARN",
        "not found",
        "Create with: py -3.12 -m venv .venv",
        "Create during project setup before installing dbt",
    )


def check_dbt() -> CheckResult:
    if which("dbt") is None:
        return CheckResult(
            "dbt-core",
            "build/test",
            "BLOCKED",
            "missing",
            'Install with: python -m pip install "dbt-core==1.10.15"',
            "Required before sources and layer builds",
        )
    code, out = run_cmd(["dbt", "--version"])
    if code != 0:
        return CheckResult("dbt-core", "build/test", "FAIL", out or "dbt failed", "Reinstall dbt-core in active venv", "")
    first = out.splitlines()[0] if out else "dbt present"
    return CheckResult("dbt-core", "build/test", "PASS", first, "Ready", "")


def check_adapter(adapter: str | None) -> CheckResult:
    if not adapter:
        return CheckResult(
            "dbt adapter",
            "warehouse connection",
            "WARN",
            "adapter not specified",
            "Pass --adapter after profile selection",
            "Install only the matching adapter package",
        )
    package = ADAPTER_PACKAGES.get(adapter.lower())
    if not package:
        return CheckResult(
            "dbt adapter",
            "warehouse connection",
            "WARN",
            adapter,
            "Install adapter package for this profile type manually",
            "Unknown adapter key",
        )
    code, out = run_cmd([sys.executable, "-m", "pip", "show", package])
    if code == 0 and out:
        version_line = next((line for line in out.splitlines() if line.lower().startswith("version:")), package)
        return CheckResult("dbt adapter", "warehouse connection", "PASS", f"{package} ({version_line})", "Ready", "")
    return CheckResult(
        "dbt adapter",
        "warehouse connection",
        "BLOCKED",
        f"{package} missing",
        f'Install with: python -m pip install "{package}"',
        out,
    )


def check_python_package(name: str, required_for: str, required: bool) -> CheckResult:
    code, out = run_cmd([sys.executable, "-c", f"import {name}; print(getattr({name}, '__version__', 'ok'))"])
    if code == 0 and out:
        return CheckResult(name, required_for, "PASS", out.splitlines()[0], "Ready", "")
    status = "BLOCKED" if required else "WARN"
    return CheckResult(
        name,
        required_for,
        status,
        "missing",
        f"Install with: python -m pip install {name}",
        "",
    )


def check_tool(name: str, required_for: str, required: bool, install_hint: str) -> CheckResult:
    path = which(name)
    if not path:
        return CheckResult(
            name,
            required_for,
            "BLOCKED" if required else "WARN",
            "missing",
            install_hint,
            "",
        )
    code, out = run_cmd([name, "--version"])
    detected = out.splitlines()[0] if out else path
    if code != 0 and not out:
        return CheckResult(name, required_for, "WARN", path, "Found executable but version check failed", "")
    return CheckResult(name, required_for, "PASS", detected, "Ready", "")


def write_markdown(path: Path, checks: list[CheckResult], overall: str) -> None:
    rows = [
        "# Software Prerequisites Check",
        "",
        f"Overall status: **{overall}**",
        "",
        "| Software | Required for | Detected | Action | Status | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for check in checks:
        notes = (check.notes or "").replace("|", "\\|")
        rows.append(
            f"| {check.name} | {check.required_for} | {check.detected} | {check.action} | {check.status} | {notes} |"
        )
    rows.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--adapter", default=None, help="Selected dbt profile adapter type")
    parser.add_argument("--require-git", action="store_true")
    parser.add_argument("--require-gh", action="store_true")
    parser.add_argument("--require-node", action="store_true")
    parser.add_argument("--require-presentation", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    checks: list[CheckResult] = [
        check_python(),
        check_pip(),
        check_venv(root),
        check_dbt(),
        check_adapter(args.adapter),
        check_python_package("yaml", "skill scripts / config validation", True),
        check_python_package("matplotlib", "Matplotlib presentation", args.require_presentation),
        check_python_package("numpy", "Matplotlib presentation", args.require_presentation),
        check_python_package("pandas", "Matplotlib presentation", args.require_presentation),
        check_tool("git", "commits / history", args.require_git, "Install Git for Windows / system git"),
        check_tool("node", "skill install via npx", args.require_node, "Install Node.js LTS"),
        check_tool("npx", "skill install via npx", args.require_node, "Install Node.js LTS (includes npx)"),
        check_tool("gh", "GitHub push / PR / API", args.require_gh, "Install GitHub CLI (gh)"),
    ]

    blocked_or_fail = [c for c in checks if c.status in {"FAIL", "BLOCKED"}]
    overall = "FAIL" if blocked_or_fail else ("WARN" if any(c.status == "WARN" for c in checks) else "PASS")

    print(f"Software prerequisites overall status: {overall}")
    for check in checks:
        print(f"- {check.name}: {check.status} | {check.detected} | {check.action}")

    if args.write_report:
        report_dir = root / "reports" / "agent" / "01_setup"
        write_markdown(report_dir / "SOFTWARE_PREREQUISITES.md", checks, overall)
        json_path = report_dir / "SOFTWARE_PREREQUISITES.json"
        json_path.write_text(
            json.dumps({"overall_status": overall, "checks": [asdict(c) for c in checks]}, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {report_dir / 'SOFTWARE_PREREQUISITES.md'}")
        print(f"Wrote {json_path}")

    return 1 if overall == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
