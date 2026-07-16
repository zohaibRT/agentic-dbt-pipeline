#!/usr/bin/env python3
"""Run an evidence-based acceptance gate for an agentic dbt project.

This script is intended to run from the dbt project root after the agent has
built one or more phases. It checks required control-plane files, phase reports,
SQL proof files, KPI proof coverage, dbt commands, and common production gaps.

Exit code:
- 0 when overall status is PASS, or WARN with every warning explicitly accepted
- 1 when overall status is FAIL, or unaccepted WARN under strict/final policy
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from lib_gate_common import (
    load_acceptance_policy,
    load_accepted_warnings,
    load_analytics_policy,
    load_presentation_policy,
    load_validator_result_json,
    VALIDATOR_RESULT_SCHEMA_VERSION,
)

STATUS_VALUES = {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED", "DEFERRED"}
FAIL_STATUSES = {"FAIL", "BLOCKED"}

PHASES = (
    "discovery",
    "bronze",
    "silver",
    "gold",
    "semantic",
    "analytics",
    "presentation",
    "final",
)
PHASE_INDEX = {phase: index for index, phase in enumerate(PHASES)}

DISCOVERY_CONTROL_FILES = [
    "AGENT_PLAN.md",
    "reports/agent/00_discovery/core_profile.json",
    "reports/agent/00_discovery/discovery_raw.json",
    "reports/agent/00_discovery/requirements.md",
    "reports/agent/PIPELINE_STATUS.md",
    "reports/agent/CONTEXT_TREE.md",
    "reports/agent/REPORT_INDEX.md",
]

FINAL_CONTROL_FILES = [
    *DISCOVERY_CONTROL_FILES,
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

LAYER_PHASE_FOR_REPORT = {
    "bronze": "03_bronze",
    "silver": "04_silver",
    "gold": "05_gold",
}

PROJECT_VALIDATION_SCRIPTS = [
    ("check_discovery_artifacts.py", ["--root", "{root}"], "discovery"),
    ("check_gold_star_shape.py", ["--root", "{root}"], "gold"),
    ("validate_kpi_proofs.py", ["--root", "{root}"], "analytics"),
    ("check_requirement_traceability.py", ["--root", "{root}"], "bronze"),
    ("check_layer_proof_coverage.py", ["--root", "{root}"], "bronze"),
    ("verify_metric_reconciliation.py", ["--root", "{root}"], "analytics"),
    ("check_model_classification_coverage.py", ["--root", "{root}", "--phase", "{phase}"], "analytics"),
    ("check_analytics_coverage.py", ["--root", "{root}"], "analytics"),
    ("check_analytics_product_completeness.py", ["--root", "{root}"], "analytics"),
    ("check_fact_analytical_coverage.py", ["--root", "{root}", "--phase", "{phase}"], "analytics"),
    ("check_metric_contract_completeness.py", ["--root", "{root}"], "analytics"),
    (
        "check_human_approval_coverage.py",
        ["--root", "{root}", "--phase", "{phase}"],
        "analytics",
    ),
    ("check_time_intelligence_coverage.py", ["--root", "{root}"], "analytics"),
    ("check_data_observability_coverage.py", ["--root", "{root}"], "analytics"),
    ("check_presentation_coverage.py", ["--root", "{root}"], "presentation"),
    ("check_report_page_contracts.py", ["--root", "{root}", "--phase", "{phase}"], "presentation"),
    ("check_report_business_readability.py", ["--root", "{root}"], "presentation"),
    ("check_exposure_coverage.py", ["--root", "{root}", "--phase", "{phase}"], "analytics"),
    ("check_presentation_hardcodes.py", ["--root", "{root}"], "presentation"),
    ("check_privacy_opt_out.py", ["--root", "{root}"], "presentation"),
    ("check_domain_neutrality.py", ["--root", "{skill_root}"], "discovery"),
    ("validate_powerbi_pbip.py", [], "presentation"),
    (
        "validate_local_web_report.py",
        [
            "--report-dir",
            "{root}/reports/agent/10_presentation/matplotlib",
        ],
        "presentation",
    ),
    (
        "validate_rendered_report_content.py",
        [
            "--report-dir",
            "{root}/reports/agent/10_presentation/matplotlib",
        ],
        "presentation",
    ),
    ("validate_chart_registry.py", ["--root", "{root}"], "presentation"),
    ("check_presentation_traceability.py", ["--root", "{root}", "--phase", "{phase}"], "presentation"),
    ("validate_live_report_dom.py", ["--root", "{root}", "--desktop", "--tablet", "--mobile"], "presentation"),
    ("run_independent_verifier.py", ["--root", "{root}", "--phase", "{phase}"], "final"),
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
class WarningRecord:
    warning_id: str
    message: str
    accepted: bool = False


@dataclass
class GateReport:
    overall_status: str = "PASS"
    phase: str = "final"
    checks: list[CheckResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    warning_records: list[WarningRecord] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    enforce_warning_policy: bool = False

    def add(self, result: CheckResult) -> None:
        self.checks.append(result)
        if result.status in FAIL_STATUSES:
            self.failures.append(f"{result.name}: {result.detail}")
        elif result.status == "WARN":
            message = f"{result.name}: {result.detail}"
            self.warnings.append(message)
            # Prefer explicit warning_ids=... from validator JSON detail
            warning_ids: list[str] = []
            if "warning_ids=" in (result.detail or ""):
                token = (result.detail or "").split("warning_ids=", 1)[1]
                warning_ids = [part.strip() for part in token.split(",") if part.strip()]
            if warning_ids:
                for wid in warning_ids:
                    self.warning_records.append(WarningRecord(warning_id=wid, message=message))
            else:
                self.warning_records.append(WarningRecord(warning_id=result.name, message=message))
        elif result.status == "SKIPPED":
            # Recorded for visibility; required final SKIPPED handled by caller
            pass

    def finalize(
        self,
        accepted_tokens: set[str],
        *,
        require_explicit_warning_acceptance: bool = True,
    ) -> None:
        if self.enforce_warning_policy:
            remaining_warnings: list[str] = []
            accepted_visible: list[str] = []
            for record in self.warning_records:
                if require_explicit_warning_acceptance:
                    # Primary: stable warning_id match (exact or accepted token contained in id).
                    # Do not use full warning-message substring as primary acceptance.
                    wid = record.warning_id.lower()
                    noise = {"accepted", "deferred", "warning", "warnings"}
                    record.accepted = any(
                        token == wid
                        for token in accepted_tokens
                        if token and token not in noise
                    )
                else:
                    record.accepted = False
                if record.accepted:
                    accepted_visible.append(record.message)
                else:
                    self.failures.append(record.message)
                    remaining_warnings.append(record.message)
            # Accepted warnings remain visible but do not keep overall at WARN
            self.warnings = accepted_visible + remaining_warnings
        else:
            for record in self.warning_records:
                wid = record.warning_id.lower()
                noise = {"accepted", "deferred", "warning", "warnings"}
                record.accepted = any(
                    token == wid for token in accepted_tokens if token and token not in noise
                )

        if self.failures:
            self.overall_status = "FAIL"
        elif any(not r.accepted for r in self.warning_records):
            self.overall_status = "WARN"
        elif self.warning_records and all(r.accepted for r in self.warning_records):
            # Explicitly accepted warnings remain listed; overall PASS for completion
            self.overall_status = "PASS"
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


def phase_at_least(current: str, minimum: str) -> bool:
    return PHASE_INDEX[current] >= PHASE_INDEX[minimum]


def resolve_default_phase(root: Path) -> str:
    insights = root / "reports" / "agent" / "09_analytics_insights"
    return "analytics" if insights.exists() else "final"


def run_command(
    command: list[str],
    root: Path,
    timeout: int,
    *,
    result_json: Path | None = None,
) -> CheckResult:
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

    # Prefer machine-readable ValidatorResult when requested
    if result_json is not None:
        if not result_json.exists():
            return CheckResult(
                command_text,
                "FAIL",
                f"missing validator result JSON: {result_json}",
                command_text,
                completed.returncode,
            )
        try:
            payload = load_validator_result_json(result_json)
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                command_text,
                "FAIL",
                f"malformed validator result JSON ({result_json}): {exc}",
                command_text,
                completed.returncode,
            )
        status = payload.status
        # Exit code vs JSON contradiction
        if status in {"FAIL", "BLOCKED"} and completed.returncode == 0:
            return CheckResult(
                command_text,
                "FAIL",
                f"JSON status {status} contradicts exit 0",
                command_text,
                completed.returncode,
            )
        if status == "PASS" and completed.returncode != 0:
            return CheckResult(
                command_text,
                "FAIL",
                f"JSON status PASS contradicts exit {completed.returncode}",
                command_text,
                completed.returncode,
            )
        if status in {"WARN", "SKIPPED"} and completed.returncode != 0:
            return CheckResult(
                command_text,
                "FAIL",
                f"JSON status {status} contradicts exit {completed.returncode}",
                command_text,
                completed.returncode,
            )
        detail_bits = []
        if payload.errors:
            detail_bits.extend(payload.errors[:8])
        if payload.warnings:
            detail_bits.extend(payload.warnings[:8])
        if payload.warning_ids:
            detail_bits.append("warning_ids=" + ",".join(payload.warning_ids[:12]))
        if not detail_bits:
            detail_bits.append(detail or payload.status)
        return CheckResult(
            command_text,
            status,
            "; ".join(detail_bits),
            command_text,
            completed.returncode,
        )

    status = "PASS" if completed.returncode == 0 else "FAIL"
    return CheckResult(command_text, status, detail, command_text, completed.returncode)


def check_required_files(root: Path, report: GateReport, phase: str) -> None:
    required = FINAL_CONTROL_FILES if phase_at_least(phase, "final") else DISCOVERY_CONTROL_FILES
    for item in required:
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


def check_phase_reports(root: Path, report: GateReport, phase: str) -> None:
    for layer_phase, required_sections in LAYER_REPORT_REQUIREMENTS.items():
        layer_name = next(
            (name for name, folder in LAYER_PHASE_FOR_REPORT.items() if folder == layer_phase),
            None,
        )
        if layer_name is None or not phase_at_least(phase, layer_name):
            continue
        phase_report = find_phase_report(root, layer_phase)
        if phase_report is None:
            report.add(CheckResult(f"Phase report: {layer_phase}", "WARN", "phase report not found"))
            continue
        text = read_text(phase_report)
        missing = [section for section in required_sections if section.lower() not in text.lower()]
        if missing:
            report.add(
                CheckResult(
                    f"Phase report: {rel(root, phase_report)}",
                    "FAIL",
                    "missing sections: " + ", ".join(missing),
                )
            )
        elif ANY_BAD_STATUS_RE.search(text):
            report.add(
                CheckResult(
                    f"Phase report: {rel(root, phase_report)}",
                    "FAIL",
                    "contains FAIL or BLOCKED",
                )
            )
        else:
            report.add(
                CheckResult(
                    f"Phase report: {rel(root, phase_report)}",
                    "PASS",
                    "required sections present",
                )
            )


def iter_proofs(root: Path) -> Iterable[Path]:
    proof_root = root / "reports" / "agent"
    if not proof_root.exists():
        return []
    return proof_root.glob("**/sql_proofs/*.sql")


def check_sql_proofs(root: Path, report: GateReport, phase: str) -> None:
    if not phase_at_least(phase, "bronze"):
        return
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
        report.add(
            CheckResult(
                "SQL proof statuses",
                "FAIL",
                "proofs missing explicit status: " + ", ".join(missing_status[:20]),
            )
        )
    elif missing_header_fields:
        report.add(
            CheckResult(
                "SQL proof headers",
                "WARN",
                "proofs may be missing purpose/expected/captured fields: "
                + ", ".join(missing_header_fields[:20]),
            )
        )
    else:
        report.add(
            CheckResult(
                "SQL proof files",
                "PASS",
                f"{len(proofs)} proof files have usable status/header evidence",
            )
        )


def check_pipeline_status(root: Path, report: GateReport) -> None:
    path = root / "reports" / "agent" / "PIPELINE_STATUS.md"
    if not path.exists():
        return
    text = read_text(path)
    if ANY_BAD_STATUS_RE.search(text):
        report.add(CheckResult("PIPELINE_STATUS.md", "FAIL", "contains FAIL or BLOCKED"))
    else:
        report.add(CheckResult("PIPELINE_STATUS.md", "PASS", "no FAIL/BLOCKED status found"))


def check_traceability_files(root: Path, report: GateReport, phase: str) -> None:
    matrix = root / "reports" / "agent" / "REQUIREMENTS_TRACEABILITY_MATRIX.md"
    ledger = root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md"
    kpi_contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    metric_matrix = root / "reports" / "agent" / "METRIC_VERIFICATION_MATRIX.md"
    if phase_at_least(phase, "bronze"):
        report.add(
            CheckResult(
                "Requirements traceability matrix",
                "PASS" if matrix.exists() else "WARN",
                "exists" if matrix.exists() else "recommended but missing",
            )
        )
        report.add(
            CheckResult(
                "Layer verification ledger",
                "PASS" if ledger.exists() else "WARN",
                "exists" if ledger.exists() else "recommended but missing",
            )
        )
    if phase_at_least(phase, "analytics"):
        report.add(
            CheckResult(
                "KPI definition contracts",
                "PASS" if kpi_contracts.exists() else "WARN",
                "exists" if kpi_contracts.exists() else "recommended but missing",
            )
        )
        report.add(
            CheckResult(
                "Metric verification matrix",
                "PASS" if metric_matrix.exists() else "WARN",
                "exists" if metric_matrix.exists() else "recommended but missing",
            )
        )


def detect_ci_orchestration_evidence(root: Path) -> dict[str, object]:
    """Inspect .github/workflows/*.yml|*.yaml for relevant CI evidence.

    Filename alone is never sufficient. Empty workflows or workflows without
    jobs/steps that run tests, dbt, analytics gates, acceptance gates, or
    fixture builds do not count.
    """
    workflows_dir = root / ".github" / "workflows"
    command_patterns = (
        r"\bunittest\b",
        r"\bpytest\b",
        r"python\s+-m\s+unittest",
        r"\bdbt\s+parse\b",
        r"\bdbt\s+build\b",
        r"\bdbt\s+test\b",
        r"\bdbt\s+deps\b",
        r"run_acceptance_gate",
        r"acceptance_gate",
        r"analytics_gates",
        r"check_domain_neutrality",
        r"build_analytics_fixtures",
        r"build_dbt_duckdb",
        r"validate_live_report",
        r"independent_verifier",
        r"\bschedule\s*:",
        r"\bcron\s*:",
    )
    findings: list[str] = []
    if workflows_dir.exists():
        paths = sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml"))
        for path in paths:
            text = read_text(path)
            lower = text.lower().strip()
            if not lower:
                continue
            if "jobs:" not in lower:
                continue
            # Empty jobs block is not valid CI evidence
            if re.search(r"jobs:\s*\{\s*\}", lower):
                continue
            if "run:" not in lower and "uses:" not in lower and "schedule:" not in lower:
                continue
            # Normalize hit labels for reporting
            labels: list[str] = []
            for pattern in command_patterns:
                if not re.search(pattern, lower):
                    continue
                if "unittest" in pattern:
                    labels.append("unittest")
                elif "pytest" in pattern:
                    labels.append("pytest")
                elif r"dbt\s+parse" in pattern:
                    labels.append("dbt parse")
                elif r"dbt\s+build" in pattern:
                    labels.append("dbt build")
                elif r"dbt\s+test" in pattern:
                    labels.append("dbt test")
                elif r"dbt\s+deps" in pattern:
                    labels.append("dbt deps")
                elif "run_acceptance_gate" in pattern or pattern == r"acceptance_gate":
                    labels.append("acceptance_gate")
                elif "analytics_gates" in pattern:
                    labels.append("analytics_gates")
                elif "build_analytics_fixtures" in pattern:
                    labels.append("build_analytics_fixtures")
                elif "build_dbt_duckdb" in pattern:
                    labels.append("build_dbt_duckdb")
                elif "check_domain_neutrality" in pattern:
                    labels.append("check_domain_neutrality")
                elif "validate_live_report" in pattern:
                    labels.append("validate_live_report")
                elif "independent_verifier" in pattern:
                    labels.append("independent_verifier")
                elif "schedule" in pattern:
                    labels.append("schedule")
                elif "cron" in pattern:
                    labels.append("cron")
            labels = sorted(set(labels))
            if labels:
                findings.append(f"{path.name} ({', '.join(labels[:8])})")

    has_airflow = (root / "airflow").exists() or (root / "dags").exists()
    if has_airflow:
        findings.append("airflow/dags present")

    if findings:
        return {
            "has_relevant_ci": True,
            "detail": "relevant CI/orchestration evidence: " + "; ".join(findings[:8]),
            "workflows": findings,
        }
    return {
        "has_relevant_ci": False,
        "detail": (
            "no relevant CI/orchestration evidence under .github/workflows/ "
            "(need dbt/test/analytics-gate/acceptance/fixture/schedule steps)"
        ),
        "workflows": [],
    }


def check_operational_gaps(root: Path, report: GateReport, phase: str) -> None:
    if not phase_at_least(phase, "final"):
        return
    all_text = "\n".join(
        read_text(p)
        for p in root.glob("**/*")
        if p.is_file()
        and p.suffix.lower() in {".yml", ".yaml", ".md", ".sql", ".py"}
        and "target" not in p.parts
        and p.stat().st_size < 500_000
    )
    lowered = all_text.lower()
    if "freshness:" not in lowered and "loaded_at_field" not in lowered:
        report.add(CheckResult("Source freshness", "WARN", "no dbt source freshness configuration detected"))

    obs_cov = root / "reports" / "agent" / "09_analytics_insights" / "data_observability_coverage.md"
    obs_report = root / "reports" / "agent" / "09_analytics_insights" / "data_observability_report.md"
    has_obs_evidence = obs_cov.exists() or obs_report.exists()
    has_dq_tests = "unique" in lowered or "not_null" in lowered or "relationships" in lowered
    if not has_obs_evidence and not has_dq_tests:
        report.add(
            CheckResult(
                "Data observability",
                "WARN",
                "no observability coverage matrix, observability report, or dbt "
                "data-quality test / SQL-proof / telemetry / monitoring evidence detected "
                "(vendor-neutral)",
            )
        )

    ci_summary = detect_ci_orchestration_evidence(root)
    if not ci_summary["has_relevant_ci"]:
        report.add(
            CheckResult(
                "Production schedule / CI",
                "WARN",
                ci_summary["detail"],
            )
        )
    else:
        report.add(
            CheckResult(
                "Production schedule / CI",
                "PASS",
                ci_summary["detail"],
            )
        )
    if not (root / "reports" / "agent" / "HUMAN_VERIFICATION_GUIDE.md").exists():
        report.add(
            CheckResult(
                "Human verification guide",
                "WARN",
                "missing reports/agent/HUMAN_VERIFICATION_GUIDE.md",
            )
        )


def run_validation_scripts(
    root: Path,
    report: GateReport,
    timeout: int,
    phase: str,
    *,
    strict: bool = False,
) -> None:
    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    insights = root / "reports" / "agent" / "09_analytics_insights"
    presentation = root / "reports" / "agent" / "10_presentation"
    matplotlib_dir = presentation / "matplotlib"

    analytics_scripts = {
        "check_analytics_coverage.py",
        "check_analytics_product_completeness.py",
        "check_fact_analytical_coverage.py",
        "check_model_classification_coverage.py",
        "check_metric_contract_completeness.py",
        "check_time_intelligence_coverage.py",
        "check_data_observability_coverage.py",
        "check_exposure_coverage.py",
    }
    presentation_scripts = {
        "check_presentation_coverage.py",
        "check_report_page_contracts.py",
        "check_report_business_readability.py",
    }

    for script_name, script_args, minimum_phase in PROJECT_VALIDATION_SCRIPTS:
        if not phase_at_least(phase, minimum_phase):
            continue
        script_path = script_dir / script_name
        if not script_path.exists():
            report.add(
                CheckResult(
                    "Validation script: " + script_name,
                    "FAIL",
                    f"skill script not found at {script_path}",
                )
            )
            continue
        if script_name == "validate_powerbi_pbip.py" and not list(presentation.glob("**/*.pbip")):
            report.add(CheckResult("Validation script: " + script_name, "SKIPPED", "no PBIP found"))
            continue
        if script_name == "validate_local_web_report.py" and not (matplotlib_dir / "serve_report.py").exists():
            report.add(
                CheckResult(
                    "Validation script: " + script_name,
                    "SKIPPED",
                    "no local web report server found",
                )
            )
            continue
        if script_name == "validate_rendered_report_content.py" and not (matplotlib_dir / "report.html").exists():
            report.add(CheckResult("Validation script: " + script_name, "SKIPPED", "no report.html"))
            continue
        if script_name == "validate_chart_registry.py" and not matplotlib_dir.exists():
            report.add(CheckResult("Validation script: " + script_name, "SKIPPED", "no Matplotlib presentation folder"))
            continue
        if script_name == "check_presentation_traceability.py" and not matplotlib_dir.exists():
            report.add(CheckResult("Validation script: " + script_name, "SKIPPED", "no Matplotlib presentation folder"))
            continue
        if script_name == "run_independent_verifier.py" and os.environ.get("INDEPENDENT_VERIFIER_ACTIVE") == "1":
            report.add(
                CheckResult(
                    "Validation script: " + script_name,
                    "SKIPPED",
                    "already inside independent verifier",
                )
            )
            continue
        if script_name == "validate_live_report_dom.py" and not (matplotlib_dir / "report.html").exists():
            report.add(CheckResult("Validation script: " + script_name, "SKIPPED", "no report.html"))
            continue
        if script_name == "validate_live_report_dom.py":
            presentation_policy = load_presentation_policy(root)
            if not presentation_policy.get("require_live_browser_validation", True):
                report.add(
                    CheckResult(
                        "Validation script: " + script_name,
                        "SKIPPED",
                        "presentation_policy.require_live_browser_validation=false",
                    )
                )
                continue
            # Replace default viewport flags with policy viewports when provided
            viewports = presentation_policy.get("live_browser_viewports") or []
            if isinstance(viewports, list) and viewports:
                script_args = ["--root", "{root}"] + [f"--{str(v).strip().lower()}" for v in viewports]
        if script_name in analytics_scripts and not insights.exists():
            report.add(
                CheckResult(
                    "Validation script: " + script_name,
                    "SKIPPED",
                    "no analytics insight folder",
                )
            )
            continue
        if script_name == "check_presentation_coverage.py" and not matplotlib_dir.exists():
            report.add(
                CheckResult(
                    "Validation script: " + script_name,
                    "SKIPPED",
                    "no Matplotlib presentation folder",
                )
            )
            continue
        if script_name in presentation_scripts - {"check_presentation_coverage.py"} and not presentation.exists():
            report.add(
                CheckResult(
                    "Validation script: " + script_name,
                    "SKIPPED",
                    "no presentation folder",
                )
            )
            continue
        if script_name == "check_presentation_hardcodes.py" and not presentation.exists():
            report.add(
                CheckResult(
                    "Validation script: " + script_name,
                    "SKIPPED",
                    "no presentation folder",
                )
            )
            continue
        resolved_args = []
        for item in script_args:
            value = item
            if "{root}" in value:
                value = value.replace("{root}", str(root))
            if "{skill_root}" in value:
                value = value.replace("{skill_root}", str(skill_root))
            if "{phase}" in value:
                # Map gate phase onto human-approval enforcement phase
                hitl_phase = "analytics"
                if phase_at_least(phase, "final"):
                    hitl_phase = "final"
                elif phase_at_least(phase, "presentation"):
                    hitl_phase = "presentation"
                value = value.replace("{phase}", hitl_phase)
            resolved_args.append(value)

        # Final / interactive reports must not auto-skip Playwright
        interactive_report = (matplotlib_dir / "report.html").exists()
        if script_name == "validate_live_report_dom.py":
            presentation_policy = load_presentation_policy(root)
            require_live = bool(presentation_policy.get("require_live_browser_validation", True))
            require_at_final = bool(presentation_policy.get("require_live_browser_at_final", True))
            if phase_at_least(phase, "final"):
                require_live = require_live and require_at_final
            if phase_at_least(phase, "final") and interactive_report and require_live:
                # Strip any allow-skip that may have been passed
                resolved_args = [a for a in resolved_args if a != "--allow-skip"]
            elif (
                not phase_at_least(phase, "final")
                and not os.environ.get("CI", "").lower() in {"1", "true", "yes"}
            ):
                if "--allow-skip" not in resolved_args:
                    resolved_args.append("--allow-skip")

        # Independent verifier must not skip live in final/strict mode with interactive report
        if script_name == "run_independent_verifier.py":
            final_like = phase_at_least(phase, "final") or bool(strict)
            if final_like and interactive_report:
                resolved_args = [
                    a
                    for a in resolved_args
                    if a not in {"--skip-live", "--allow-skip-live", "--allow-skip"}
                ]
                if "--strict" not in resolved_args and strict:
                    resolved_args.append("--strict")
            elif "--skip-live" not in resolved_args and not final_like:
                # non-final may skip live for speed unless CI
                if not os.environ.get("CI", "").lower() in {"1", "true", "yes"}:
                    resolved_args.append("--skip-live")

        result_dir = root / "reports" / "agent" / "_validator_results"
        result_dir.mkdir(parents=True, exist_ok=True)
        result_json = result_dir / f"{Path(script_name).stem}.json"
        # Scripts that support --output-json (production validators)
        no_json_scripts = {
            "run_independent_verifier.py",
            "validate_powerbi_pbip.py",
        }
        supports_json = script_name.endswith(".py") and script_name not in no_json_scripts
        if supports_json:
            resolved_args.extend(["--output-json", str(result_json)])

        command = [sys.executable, str(script_path), *resolved_args]
        cwd = skill_root if script_name == "check_domain_neutrality.py" else root
        check = run_command(
            command,
            cwd,
            timeout,
            result_json=result_json if supports_json else None,
        )
        # Independent verifier: prefer overall_status from its report JSON
        if script_name == "run_independent_verifier.py":
            iv_report = root / "reports" / "agent" / "INDEPENDENT_VERIFICATION_REPORT.json"
            if iv_report.exists():
                try:
                    iv_payload = json.loads(iv_report.read_text(encoding="utf-8"))
                    iv_status = str(iv_payload.get("overall_status") or "").upper()
                    if iv_status in {"PASS", "WARN", "FAIL", "BLOCKED", "SKIPPED"}:
                        check = CheckResult(
                            check.name,
                            iv_status,
                            f"independent verifier overall_status={iv_status}",
                            check.command,
                            check.return_code,
                        )
                except Exception as exc:  # noqa: BLE001
                    check = CheckResult(
                        check.name,
                        "FAIL",
                        f"malformed INDEPENDENT_VERIFICATION_REPORT.json: {exc}",
                        check.command,
                        check.return_code,
                    )
            elif phase_at_least(phase, "final"):
                check = CheckResult(
                    check.name,
                    "FAIL",
                    "missing INDEPENDENT_VERIFICATION_REPORT.json after verifier run",
                    check.command,
                    check.return_code,
                )
        # Required final/strict SKIPPED is FAIL unless applicability evidence allows it
        final_like = phase_at_least(phase, "final") or bool(strict)
        if final_like and check.status == "SKIPPED":
            detail_lower = (check.detail or "").lower()
            allowed_skip = any(
                token in detail_lower
                for token in (
                    "no pbip found",
                    "no local web report server found",
                    "no report.html",
                    "no matplotlib presentation folder",
                    "no analytics insight folder",
                    "no presentation folder",
                    "already inside independent verifier",
                    "presentation_policy.require_live_browser_validation=false",
                    "not_applicable",
                    "applicability=",
                )
            )
            # Live browser is never an allowed skip when interactive report exists
            if script_name == "validate_live_report_dom.py" and interactive_report:
                allowed_skip = False
            # Core production validators must not be skipped at final when applicable
            core_required = {
                "check_human_approval_coverage.py",
                "verify_metric_reconciliation.py",
                "check_model_classification_coverage.py",
                "check_fact_analytical_coverage.py",
                "check_exposure_coverage.py",
                "check_presentation_traceability.py",
                "validate_live_report_dom.py",
                "run_independent_verifier.py",
            }
            if script_name in core_required and not allowed_skip:
                check = CheckResult(
                    check.name,
                    "FAIL",
                    f"required validator SKIPPED at final/strict: {check.detail}",
                    check.command,
                    check.return_code,
                )
            elif script_name == "validate_live_report_dom.py" and interactive_report:
                check = CheckResult(
                    check.name,
                    "FAIL",
                    f"live browser SKIPPED is not allowed at final with interactive report: {check.detail}",
                    check.command,
                    check.return_code,
                )
        report.add(check)

def run_dbt(root: Path, report: GateReport, timeout: int, skip_dbt: bool, phase: str) -> None:
    if skip_dbt:
        report.add(CheckResult("dbt commands", "SKIPPED", "--skip-dbt was used"))
        return
    if not phase_at_least(phase, "gold"):
        return
    if not (root / "dbt_project.yml").exists():
        report.add(CheckResult("dbt commands", "WARN", "dbt_project.yml not found"))
        return
    for command in DBT_COMMANDS:
        report.add(run_command(command, root, timeout))


def write_reports(root: Path, gate: GateReport, accepted_tokens: set[str]) -> None:
    output_dir = root / "reports" / "agent"
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "ACCEPTANCE_GATE_REPORT.json"
    md_path = output_dir / "ACCEPTANCE_GATE_REPORT.md"

    payload = asdict(gate)
    payload["accepted_warning_tokens"] = sorted(accepted_tokens)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    rows = ["| Check | Status | Detail |", "|---|---|---|"]
    for check in gate.checks:
        detail = (check.detail or "").replace("\n", " ").replace("|", "\\|")
        if len(detail) > 500:
            detail = detail[:500] + "..."
        rows.append(f"| {check.name} | {check.status} | {detail} |")

    warning_rows = ["| Warning ID | Accepted | Detail |", "|---|---|---|"]
    if gate.warning_records:
        for record in gate.warning_records:
            detail = record.message.replace("|", "\\|")
            if len(detail) > 500:
                detail = detail[:500] + "..."
            accepted = "Yes" if record.accepted else "No"
            warning_rows.append(f"| {record.warning_id} | {accepted} | {detail} |")
    else:
        warning_rows.append("| _none_ | — | — |")

    md = [
        "# Acceptance Gate Report",
        "",
        f"Overall status: **{gate.overall_status}**",
        f"Phase: **{gate.phase}**",
        f"Warning policy enforced: **{'yes' if gate.enforce_warning_policy else 'no'}**",
        "",
        "## Check Results",
        "",
        *rows,
        "",
        "## Warning acceptance",
        "",
        *warning_rows,
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
        md.append(
            "Review warnings with the data engineer, then either fix them or explicitly accept/defer them "
            "in CONTEXT_TREE.md, PIPELINE_STATUS.md, HUMAN_ATTENTION_BOARD.md, or --accepted-warning-file."
        )
    else:
        md.append("Gate passed. Proceed to human sign-off and final delivery.")

    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")


def resolve_enforce_warning_policy(
    *,
    phase: str,
    strict: bool,
    fail_on_warning: bool,
    acceptance_policy: dict,
) -> bool:
    """Return whether unaccepted warnings must fail this gate run.

    Normal discovery/bronze/silver/gold/semantic/analytics/presentation runs do
    not enforce warnings unless --strict or --fail-on-warning is passed.
    Final phase enforces when acceptance_policy.final_fail_on_warning is true.
    """
    return bool(
        strict
        or fail_on_warning
        or (phase == "final" and acceptance_policy.get("final_fail_on_warning", True))
    )


def compute_exit_code(gate: GateReport) -> int:
    return 1 if gate.overall_status == "FAIL" else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="dbt project root")
    parser.add_argument("--timeout", type=int, default=900, help="timeout per command in seconds")
    parser.add_argument("--skip-dbt", action="store_true", help="skip dbt deps/parse/build commands")
    parser.add_argument(
        "--phase",
        choices=PHASES,
        default=None,
        help="workflow phase gate scope (default: analytics when insights exist else final)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat unaccepted warnings as failures regardless of phase",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="alias for enforcing warning acceptance on this run",
    )
    parser.add_argument(
        "--accepted-warning-file",
        type=Path,
        default=None,
        help="optional file listing accepted warning id substrings (one per line)",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    phase = args.phase or resolve_default_phase(root)
    acceptance_policy = load_acceptance_policy(root)
    analytics_policy = load_analytics_policy(root)
    _ = analytics_policy  # loaded for policy coverage / future advisory reporting
    accepted_tokens = load_accepted_warnings(root, args.accepted_warning_file)

    # Final warning policy applies only on final phase when
    # acceptance_policy.final_fail_on_warning is true, or when the caller
    # explicitly requests --strict / --fail-on-warning.
    enforce_warning_policy = resolve_enforce_warning_policy(
        phase=phase,
        strict=bool(args.strict),
        fail_on_warning=bool(args.fail_on_warning),
        acceptance_policy=acceptance_policy,
    )
    require_explicit = bool(acceptance_policy.get("require_explicit_warning_acceptance", True))

    gate = GateReport(phase=phase, enforce_warning_policy=enforce_warning_policy)

    check_required_files(root, gate, phase)
    check_pipeline_status(root, gate)
    check_phase_reports(root, gate, phase)
    check_sql_proofs(root, gate, phase)
    check_traceability_files(root, gate, phase)
    run_validation_scripts(root, gate, args.timeout, phase, strict=bool(args.strict))
    run_dbt(root, gate, args.timeout, args.skip_dbt, phase)
    check_operational_gaps(root, gate, phase)

    gate.finalize(accepted_tokens, require_explicit_warning_acceptance=require_explicit)
    write_reports(root, gate, accepted_tokens)

    print(f"Acceptance gate overall status: {gate.overall_status}")
    print(f"Acceptance gate phase: {phase}")
    print("Wrote reports/agent/ACCEPTANCE_GATE_REPORT.md")
    print("Wrote reports/agent/ACCEPTANCE_GATE_REPORT.json")

    return compute_exit_code(gate)


if __name__ == "__main__":
    raise SystemExit(main())
