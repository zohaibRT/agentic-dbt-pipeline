#!/usr/bin/env python3
"""Shared helpers for enterprise report handoff readiness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib_llm_playwright_review import compute_report_bundle_hash, is_under_fixtures

HANDOFF_JSON = Path("reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json")
HANDOFF_MD = Path("reports/agent/10_presentation/REPORT_HANDOFF_READINESS.md")

PRESENTATION_STATES = {
    "PRESENTATION_GENERATED",
    "RUNTIME_PREFLIGHT_PENDING",
    "RUNTIME_PREFLIGHT_FAILED",
    "BROWSER_VALIDATION_PENDING",
    "BROWSER_VALIDATION_FAILED",
    "MCP_REVIEW_PENDING",
    "MCP_REVIEW_FAILED",
    "FINAL_VERIFICATION_PENDING",
    "VERIFIED_FOR_HANDOFF",
    "BLOCKED",
}

REQUIRED_GATE_IDS = (
    "manifest_relation_resolution",
    "runtime_preflight",
    "initial_data_load",
    "refresh_validation",
    "deterministic_playwright",
    "playwright_mcp_review",
    "llm_review_artifact_validation",
    "independent_verification",
    "final_acceptance",
)

PASSING_GATE_STATUSES = {"PASS", "NOT_APPLICABLE"}
BLOCKING_GATE_STATUSES = {"FAIL", "WARN", "BLOCKED", "SKIPPED", "NOT_RUN", "MISSING", "STALE"}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def validator_result_path(root: Path, stem: str) -> Path:
    return root / "reports" / "agent" / "_validator_results" / f"{stem}.json"


def load_validator_status(root: Path, stem: str) -> tuple[str, dict[str, Any]]:
    path = validator_result_path(root, stem)
    data = load_json(path)
    if not data:
        return "NOT_RUN", {}
    status = str(data.get("status") or "").strip().upper() or "NOT_RUN"
    return status, data


def interactive_report_exists(root: Path) -> bool:
    base = root / "reports" / "agent" / "10_presentation"
    return (base / "matplotlib" / "report.html").exists() or (base / "report.html").exists()


def write_handoff_markdown(path: Path, payload: dict[str, Any]) -> None:
    gates = payload.get("gates") or []
    lines = [
        "# Report Handoff Readiness",
        "",
        f"- Status: {payload.get('status')}",
        f"- Presentation state: {payload.get('presentation_state')}",
        f"- Open allowed: {payload.get('open_allowed')}",
        f"- Report bundle hash: {payload.get('report_bundle_hash')}",
        f"- Reviewed at: {payload.get('checked_at')}",
        "",
        "## Gates",
        "",
        "| Gate | Status | Evidence | Notes |",
        "|---|---|---|---|",
    ]
    for gate in gates:
        lines.append(
            f"| {gate.get('gate_id')} | {gate.get('status')} | "
            f"{gate.get('evidence') or ''} | {gate.get('notes') or ''} |"
        )
    lines.extend(
        [
            "",
            "## Verified report handoff",
            "",
            "Opening instructions are released only when status is PASS and open_allowed is true.",
            "",
        ]
    )
    if payload.get("open_allowed"):
        lines.extend(
            [
                "Open instructions may be shown to the user.",
                f"- Suggested launcher: `{payload.get('open_command') or 'open_report.bat / open_report.sh'}`",
                f"- Verified URL: `{payload.get('report_url') or 'http://127.0.0.1:<port>/'}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Report artifacts were generated, but the report is not ready to open.",
                "Runtime and browser verification are still pending.",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def fixture_handoff_exempt(root: Path, policy: dict[str, Any]) -> bool:
    applicability = str(policy.get("report_handoff_applicability") or "required").strip().lower()
    if applicability != "not_applicable_fixture":
        return False
    return is_under_fixtures(root)


__all__ = [
    "BLOCKING_GATE_STATUSES",
    "HANDOFF_JSON",
    "HANDOFF_MD",
    "PASSING_GATE_STATUSES",
    "PRESENTATION_STATES",
    "REQUIRED_GATE_IDS",
    "compute_report_bundle_hash",
    "fixture_handoff_exempt",
    "interactive_report_exists",
    "is_under_fixtures",
    "load_json",
    "load_validator_status",
    "validator_result_path",
    "write_handoff_markdown",
]
