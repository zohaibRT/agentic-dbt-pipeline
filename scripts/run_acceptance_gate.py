#!/usr/bin/env python3
"""Run an evidence-based acceptance gate for an agentic dbt project.

This script is intended to run from the dbt project root after the agent has
built one or more phases. It checks required control-plane files, phase reports,
SQL proof files, KPI proof coverage, dbt commands, and common production gaps.

Exit code:
- 0 when overall status is PASS or WARN
- 1 when overall status is FAIL
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

STATUS_VALUES = {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED", "DEFERRED"}
FAIL_STATUSES = {"FAIL", "BLOCKED"}

REQUIRED_CONTROL_FILES = [
    "AGENT_PLAN.md",
    "reports/agent/00_discovery/core_profile.json",
    "reports/agent/00_discovery/discovery_raw.json",
    "reports/agent/00_discovery/requirements.md",
    "reports/agent/PIPELINE_STATUS.md",
    "reports/agent/CONTEXT_TREE.md",
    "reports/agent/REPORT_INDEX.md",
    "reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "reports/agent/LAYER_VERIFICATION_LEDGER.md",
    "reports/agent/KPI_DEFINITION_CONTRACTS.md",
    "reports/agent/METRIC_VERIFICATION_MATRIX.md",
]

LAYER_REPORT_REQUIREMENTS = {
    "03_bronze": ["Data Verification Results", "SQL Proof Files"],
    "04_silver": ["Data Verification Results", "SQL Proof Files"],
    "05_gold": ["Data Verification Results", "SQL Proof Files"],
}

PROJECT_VALIDATION_SCRIPTS = [
    ("check_discovery_artifacts.py", ["--root", "{root}"]),
    ("validate_kpi_proofs.py", ["--root", "{root}"]),
    ("check_requirement_traceability.py", ["--root", "{root}"]),
    ("check_layer_proof_coverage.py", ["--root", "{root}"]),
    ("verify_metric_reconciliation.py", ["--root", "{root}"]),
    ("validate_powerbi_pbip.py", []),
    ("validate_local_web_report.py", []),
]

DBT_COMMANDS = [
    ["dbt", "deps"],
    ["dbt", "parse", "--no-partial-parse"],
    ["dbt", "build"],
]

PROOF_STATUS_RE = re.compile(r"\bstatus\s*[:=|-]\s*(PASS|WARN|FAIL|BLOCKED|SKIPPED|DEFERRED)\b", re.I)
ANY_BAD_STATUS_RE = re.compile(r"\b(FAIL|BLOCKED)\b", re.I)


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str = ""
    command: str | None = None
    return_code: int | None = None


@dataclass
class GateReport:
    overall_status: str = "PASS"
    checks: list[CheckResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.checks.append(result)
        if result.status in FAIL_STATUSES:
            self.failures.append(f"{result.name}: {result.detail}")
        elif result.status == "WARN":
            self.warnings.append(f"{result.name}: {result.detail}")

    def finalize(self) -> None:
        if self.failures:
            self.overall_status = "FAIL"
        elif self.warnings:
            self.overall_status = "WARN"
        else:
            self.overall_status = "PASS"


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def run_command(command: list[str], root: Path, timeout: int) -> CheckResult:
    command_text = " ".join(command)
    executable = Path(command[0])
    if not executable.exists() and shutil.which(command[0]) is None:
        return CheckResult(command_text, "WARN", f"Executable not found: {command[0]}", command_text)
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(command_text, "FAIL", f"Timed out after {timeout}s", command_text)

    output = (completed.stdout + "\n" + completed.stderr).strip()
    detail = output[-1500:] if output else "No output"
    status = "PASS" if completed.returncode == 0 else "FAIL"
    return CheckResult(command_text, status, detail, command_text, completed.returncode)


def check_required_files(root: Path, report: GateReport) -> None:
    for item in REQUIRED_CONTROL_FILES:
        path = root / item
        if path.exists():
            report.add(CheckResult(f"Required file: {item}", "PASS", "exists"))
        else:
            report.add(CheckResult(f"Required file: {item}", "FAIL", "missing"))


def find_phase_report(root: Path, phase: str) -> Path | None:
    folder = root / "reports" / "agent" / phase
    if not folder.exists():
        return None
    candidates = sorted(p for p in folder.glob("*.md") if "proof_index" not in p.name.lower())
    if not candidates:
        return None
    preferred = [p for p in candidates if "report" in p.name.lower()]
    return preferred[0] if preferred else candidates[0]


def check_phase_reports(root: Path, report: GateReport) -> None:
    for phase, required_sections in LAYER_REPORT_REQUIREMENTS.items():
        phase_report = find_phase_report(root, phase)
        if phase_report is None:
            report.add(CheckResult(f"Phase report: {phase}", "WARN", "phase report not found"))
            continue
        text = read_text(phase_report)
        missing = [section for section in required_sections if section.lower() not in text.lower()]
        if missing:
            report.add(CheckResult(f"Phase report: {rel(root, phase_report)}", "FAIL", "missing sections: " + ", ".join(missing)))
        elif ANY_BAD_STATUS_RE.search(text):
            report.add(CheckResult(f"Phase report: {rel(root, phase_report)}", "FAIL", "contains FAIL or BLOCKED"))
        else:
            report.add(CheckResult(f"Phase report: {rel(root, phase_report)}", "PASS", "required sections present"))


def iter_proofs(root: Path) -> Iterable[Path]:
    proof_root = root / "reports" / "agent"
    if not proof_root.exists():
        return []
    return proof_root.glob("**/sql_proofs/*.sql")


def check_sql_proofs(root: Path, report: GateReport) -> None:
    proofs = sorted(iter_proofs(root))
    if not proofs:
        report.add(CheckResult("SQL proof files", "FAIL", "no reports/agent/**/sql_proofs/*.sql files found"))
        return

    missing_status: list[str] = []
    bad_status: list[str] = []
    missing_header_fields: list[str] = []
    required_words = ["purpose", "expected", "captured"]

    for proof in proofs:
        text = read_text(proof)
        lower = text.lower()
        status_match = PROOF_STATUS_RE.search(text)
        if not status_match:
            missing_status.append(rel(root, proof))
        elif status_match.group(1).upper() in FAIL_STATUSES:
            bad_status.append(f"{rel(root, proof)} ({status_match.group(1).upper()})")
        if any(word not in lower for word in required_words):
            missing_header_fields.append(rel(root, proof))

    if bad_status:
        report.add(CheckResult("SQL proof statuses", "FAIL", "bad proofs: " + ", ".join(bad_status[:20])))
    elif missing_status:
        report.add(CheckResult("SQL proof statuses", "FAIL", "proofs missing explicit status: " + ", ".join(missing_status[:20])))
    elif missing_header_fields:
        report.add(CheckResult("SQL proof headers", "WARN", "proofs may be missing purpose/expected/captured fields: " + ", ".join(missing_header_fields[:20])))
    else:
        report.add(CheckResult("SQL proof files", "PASS", f"{len(proofs)} proof files have usable status/header evidence"))


def check_pipeline_status(root: Path, report: GateReport) -> None:
    path = root / "reports" / "agent" / "PIPELINE_STATUS.md"
    if not path.exists():
        return
    text = read_text(path)
    if ANY_BAD_STATUS_RE.search(text):
        report.add(CheckResult("PIPELINE_STATUS.md", "FAIL", "contains FAIL or BLOCKED"))
    else:
        report.add(CheckResult("PIPELINE_STATUS.md", "PASS", "no FAIL/BLOCKED status found"))


def check_traceability_files(root: Path, report: GateReport) -> None:
    matrix = root / "reports" / "agent" / "REQUIREMENTS_TRACEABILITY_MATRIX.md"
    ledger = root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md"
    kpi_contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    metric_matrix = root / "reports" / "agent" / "METRIC_VERIFICATION_MATRIX.md"
    report.add(CheckResult("Requirements traceability matrix", "PASS" if matrix.exists() else "WARN", "exists" if matrix.exists() else "recommended but missing"))
    report.add(CheckResult("Layer verification ledger", "PASS" if ledger.exists() else "WARN", "exists" if ledger.exists() else "recommended but missing"))
    report.add(CheckResult("KPI definition contracts", "PASS" if kpi_contracts.exists() else "WARN", "exists" if kpi_contracts.exists() else "recommended but missing"))
    report.add(CheckResult("Metric verification matrix", "PASS" if metric_matrix.exists() else "WARN", "exists" if metric_matrix.exists() else "recommended but missing"))


def check_operational_gaps(root: Path, report: GateReport) -> None:
    all_text = "\n".join(read_text(p) for p in root.glob("**/*") if p.is_file() and p.suffix.lower() in {".yml", ".yaml", ".md", ".sql", ".py"} and "target" not in p.parts and p.stat().st_size < 500_000)
    lowered = all_text.lower()
    if "freshness:" not in lowered and "loaded_at_field" not in lowered:
        report.add(CheckResult("Source freshness", "WARN", "no dbt source freshness configuration detected"))
    if "elementary" not in lowered:
        report.add(CheckResult("Data observability", "WARN", "no Elementary/observability package or monitoring evidence detected"))
    if not any((root / p).exists() for p in [".github/workflows/dbt.yml", ".github/workflows/ci.yml", "airflow", "dags"]):
        report.add(CheckResult("Production schedule / CI", "WARN", "no obvious CI or scheduled production orchestration found"))
    if not (root / "reports" / "agent" / "HUMAN_VERIFICATION_GUIDE.md").exists():
        report.add(CheckResult("Human verification guide", "WARN", "missing reports/agent/HUMAN_VERIFICATION_GUIDE.md"))


def run_validation_scripts(root: Path, report: GateReport, timeout: int) -> None:
    script_dir = Path(__file__).resolve().parent
    for script_name, script_args in PROJECT_VALIDATION_SCRIPTS:
        script_path = script_dir / script_name
        if not script_path.exists():
            report.add(CheckResult("Validation script: " + script_name, "FAIL", f"skill script not found at {script_path}"))
            continue
        if script_name == "validate_powerbi_pbip.py" and not list((root / "reports" / "agent" / "10_presentation").glob("**/*.pbip")):
            report.add(CheckResult("Validation script: " + script_name, "SKIPPED", "no PBIP found"))
            continue
        if script_name == "validate_local_web_report.py" and not (root / "reports" / "agent" / "10_presentation" / "matplotlib" / "serve_report.py").exists():
            report.add(CheckResult("Validation script: " + script_name, "SKIPPED", "no local web report server found"))
            continue
        resolved_args = [str(root) if item == "{root}" else item for item in script_args]
        command = [sys.executable, str(script_path), *resolved_args]
        report.add(run_command(command, root, timeout))


def run_dbt(root: Path, report: GateReport, timeout: int, skip_dbt: bool) -> None:
    if skip_dbt:
        report.add(CheckResult("dbt commands", "SKIPPED", "--skip-dbt was used"))
        return
    if not (root / "dbt_project.yml").exists():
        report.add(CheckResult("dbt commands", "WARN", "dbt_project.yml not found"))
        return
    for command in DBT_COMMANDS:
        report.add(run_command(command, root, timeout))


def write_reports(root: Path, gate: GateReport) -> None:
    output_dir = root / "reports" / "agent"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "ACCEPTANCE_GATE_REPORT.json"
    md_path = output_dir / "ACCEPTANCE_GATE_REPORT.md"

    json_path.write_text(json.dumps(asdict(gate), indent=2), encoding="utf-8")

    rows = ["| Check | Status | Detail |", "|---|---|---|"]
    for check in gate.checks:
        detail = (check.detail or "").replace("\n", " ").replace("|", "\\|")
        if len(detail) > 500:
            detail = detail[:500] + "..."
        rows.append(f"| {check.name} | {check.status} | {detail} |")

    md = [
        "# Acceptance Gate Report",
        "",
        f"Overall status: **{gate.overall_status}**",
        "",
        "## Check Results",
        "",
        *rows,
        "",
        "## Failures",
        "",
    ]
    md.extend([f"- {item}" for item in gate.failures] or ["- None"])
    md.extend(["", "## Warnings", ""])
    md.extend([f"- {item}" for item in gate.warnings] or ["- None"])
    md.extend(["", "## Recommended next action", ""])
    if gate.overall_status == "FAIL":
        md.append("Fix all FAIL/BLOCKED items before final delivery.")
    elif gate.overall_status == "WARN":
        md.append("Review warnings with the data engineer, then either fix them or explicitly accept/defer them in CONTEXT_TREE.md and PIPELINE_STATUS.md.")
    else:
        md.append("Gate passed. Proceed to human sign-off and final delivery.")

    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="dbt project root")
    parser.add_argument("--timeout", type=int, default=900, help="timeout per command in seconds")
    parser.add_argument("--skip-dbt", action="store_true", help="skip dbt deps/parse/build commands")
    args = parser.parse_args()

    root = args.root.resolve()
    gate = GateReport()

    check_required_files(root, gate)
    check_pipeline_status(root, gate)
    check_phase_reports(root, gate)
    check_sql_proofs(root, gate)
    check_traceability_files(root, gate)
    run_validation_scripts(root, gate, args.timeout)
    run_dbt(root, gate, args.timeout, args.skip_dbt)
    check_operational_gaps(root, gate)

    gate.finalize()
    write_reports(root, gate)

    print(f"Acceptance gate overall status: {gate.overall_status}")
    print("Wrote reports/agent/ACCEPTANCE_GATE_REPORT.md")
    print("Wrote reports/agent/ACCEPTANCE_GATE_REPORT.json")

    return 1 if gate.overall_status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
