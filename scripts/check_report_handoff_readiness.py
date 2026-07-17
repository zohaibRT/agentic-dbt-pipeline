#!/usr/bin/env python3
"""Enterprise report handoff readiness gate.

Independently evaluates canonical evidence artifacts. Does not trust a manually
recorded overall PASS. Sets open_allowed=true only when every applicable
required gate is PASS/NOT_APPLICABLE and evidence is fresh for the current
report bundle.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib_gate_common import add_output_json_arg, load_presentation_policy, print_results
from lib_llm_playwright_review import compute_report_bundle_hash, is_under_fixtures
from lib_manifest_relation import resolve_registered_relations
from lib_report_handoff import (
    HANDOFF_JSON,
    HANDOFF_MD,
    PASSING_GATE_STATUSES,
    REQUIRED_GATE_IDS,
    fixture_handoff_exempt,
    interactive_report_exists,
    load_json,
    load_validator_status,
    write_handoff_markdown,
)


def _gate(
    gate_id: str,
    status: str,
    *,
    evidence: str = "",
    notes: str = "",
    required: bool = True,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "status": str(status).strip().upper() or "NOT_RUN",
        "evidence": evidence,
        "notes": notes,
        "required": required,
    }


def _detail_flag(data: dict[str, Any], *keys: str) -> Any:
    details = data.get("details") if isinstance(data.get("details"), dict) else {}
    for key in keys:
        if key in details:
            return details.get(key)
        if key in data:
            return data.get(key)
    return None


def _truthy_pass(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().upper()
    return text in {"PASS", "TRUE", "1", "YES", "OK", "SUCCESS"}


def evaluate_gates(root: Path, *, phase: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build gate rows and evaluation details from canonical artifacts."""
    policy = load_presentation_policy(root)
    details: dict[str, Any] = {"phase": phase}
    gates: list[dict[str, Any]] = []

    if fixture_handoff_exempt(root, policy):
        for gate_id in REQUIRED_GATE_IDS:
            gates.append(
                _gate(
                    gate_id,
                    "NOT_APPLICABLE",
                    evidence="presentation_policy.report_handoff_applicability",
                    notes="fixture_only_handoff_exempt",
                    required=False,
                )
            )
        details["fixture_exempt"] = True
        return gates, details

    require_manifest = bool(policy.get("require_manifest_relation_resolution", True))
    require_preflight = bool(policy.get("require_report_runtime_preflight", True))
    require_initial = bool(policy.get("require_successful_initial_data_load", True))
    require_refresh = bool(policy.get("require_successful_refresh_validation", True))
    require_dom = bool(policy.get("require_deterministic_playwright_before_handoff", True))
    require_mcp = bool(policy.get("require_playwright_mcp_before_handoff", True))
    # Independent verification + final acceptance are only required at final phase.
    require_iv = bool(policy.get("require_independent_verification_before_handoff", True)) and phase == "final"
    require_final = bool(policy.get("require_final_acceptance_before_handoff", True)) and phase == "final"
    require_handoff = bool(policy.get("require_report_handoff_readiness", True))
    details["policy"] = {
        "require_manifest_relation_resolution": require_manifest,
        "require_report_runtime_preflight": require_preflight,
        "require_successful_initial_data_load": require_initial,
        "require_successful_refresh_validation": require_refresh,
        "require_deterministic_playwright_before_handoff": require_dom,
        "require_playwright_mcp_before_handoff": require_mcp,
        "require_independent_verification_before_handoff": require_iv,
        "require_final_acceptance_before_handoff": require_final,
        "require_report_handoff_readiness": require_handoff,
    }

    local_status, local_data = load_validator_status(root, "validate_local_web_report")
    live_status, live_data = load_validator_status(root, "validate_live_report_dom")
    llm_status, llm_data = load_validator_status(root, "check_llm_playwright_review")
    indep_path = root / "reports" / "agent" / "INDEPENDENT_VERIFICATION_REPORT.json"
    indep = load_json(indep_path)
    indep_status = str(indep.get("overall_status") or indep.get("status") or "").strip().upper() or "NOT_RUN"
    accept_path = root / "reports" / "agent" / "ACCEPTANCE_GATE_REPORT.json"
    accept = load_json(accept_path)
    accept_status = str(accept.get("overall_status") or accept.get("status") or "").strip().upper() or "NOT_RUN"

    preflight_path = root / "reports" / "agent" / "10_presentation" / "matplotlib" / "runtime_preflight.json"
    if not preflight_path.exists():
        preflight_path = root / "reports" / "agent" / "10_presentation" / "runtime_preflight.json"
    preflight = load_json(preflight_path)

    # 1) Manifest relation resolution — independent exact unique_id → relation check.
    relation_report = resolve_registered_relations(root, require_physical=True)
    details["relation_resolution"] = {
        "status": relation_report.get("status"),
        "manifest_checksum": relation_report.get("manifest_checksum"),
        "manifest_path": relation_report.get("manifest_path"),
        "profile_name": relation_report.get("profile_name"),
        "target": relation_report.get("target"),
        "adapter": relation_report.get("adapter"),
        "errors": list(relation_report.get("errors") or []),
        "resolved_relations": list(relation_report.get("resolved_relations") or []),
    }
    relation_ok = bool(relation_report.get("manifest_relation_resolution"))
    if not require_manifest:
        gates.append(_gate("manifest_relation_resolution", "NOT_APPLICABLE", required=False))
    elif relation_ok:
        gates.append(
            _gate(
                "manifest_relation_resolution",
                "PASS",
                evidence=str(relation_report.get("manifest_path") or preflight_path),
            )
        )
    else:
        notes = "; ".join(
            relation_report.get("errors")
            or (
                ["no exact unique_id registered on chart/query/metric payloads"]
                if not relation_report.get("unique_ids")
                else ["manifest relation resolution failed"]
            )
        )
        gates.append(
            _gate(
                "manifest_relation_resolution",
                "FAIL",
                evidence=str(relation_report.get("manifest_path") or preflight_path),
                notes=notes,
            )
        )

    # 2) Runtime preflight
    preflight_ok = (
        local_status == "PASS"
        and _truthy_pass(_detail_flag(local_data, "runtime_preflight") or preflight.get("status") or preflight.get("runtime_preflight"))
    ) or (preflight.get("status", "").upper() == "PASS")
    if not require_preflight:
        gates.append(_gate("runtime_preflight", "NOT_APPLICABLE", required=False))
    elif preflight_ok:
        gates.append(_gate("runtime_preflight", "PASS", evidence="validate_local_web_report.py / runtime_preflight.json"))
    else:
        status = local_status if local_status != "NOT_RUN" else ("FAIL" if preflight else "NOT_RUN")
        if local_status in {"FAIL", "BLOCKED", "WARN", "SKIPPED"}:
            status = local_status
        gates.append(_gate("runtime_preflight", status, evidence="validate_local_web_report.py"))

    # 3) Initial data load
    initial_ok = _truthy_pass(
        _detail_flag(local_data, "initial_data_load")
        or _detail_flag(live_data, "initial_data_load")
        or preflight.get("initial_data_load")
    ) or (
        local_status == "PASS"
        and bool(_detail_flag(local_data, "charts_payload_ok"))
        and bool(_detail_flag(local_data, "metrics_payload_ok"))
    ) or (live_status == "PASS")
    if not require_initial:
        gates.append(_gate("initial_data_load", "NOT_APPLICABLE", required=False))
    elif initial_ok:
        gates.append(_gate("initial_data_load", "PASS", evidence="live data endpoints"))
    else:
        gates.append(
            _gate(
                "initial_data_load",
                "FAIL" if local_data or live_data or preflight else "NOT_RUN",
                evidence="validate_local_web_report / validate_live_report_dom",
            )
        )

    # 4) Refresh validation — explicit False / local FAIL wins over sibling PASS.
    explicit_refresh = _detail_flag(local_data, "refresh_validation")
    explicit_refresh_ok = _detail_flag(local_data, "refresh_ok")
    if explicit_refresh is False or explicit_refresh_ok is False or local_status == "FAIL":
        refresh_ok = False
    else:
        refresh_ok = _truthy_pass(
            explicit_refresh
            or _detail_flag(live_data, "refresh_validation")
            or _detail_flag(live_data, "refresh_status")
            or preflight.get("refresh_validation")
        ) or (
            local_status == "PASS" and bool(explicit_refresh_ok)
        )
    if not require_refresh:
        gates.append(_gate("refresh_validation", "NOT_APPLICABLE", required=False))
    elif refresh_ok:
        gates.append(_gate("refresh_validation", "PASS", evidence="refresh endpoint"))
    else:
        gates.append(
            _gate(
                "refresh_validation",
                "FAIL" if local_data or live_data or preflight else "NOT_RUN",
                evidence="validate_local_web_report / validate_live_report_dom",
            )
        )

    # 5) Deterministic Playwright
    if not require_dom:
        gates.append(_gate("deterministic_playwright", "NOT_APPLICABLE", required=False))
    elif live_status == "PASS":
        gates.append(_gate("deterministic_playwright", "PASS", evidence="validate_live_report_dom.py"))
    else:
        gates.append(
            _gate(
                "deterministic_playwright",
                live_status if live_status != "NOT_RUN" else "NOT_RUN",
                evidence="validate_live_report_dom.py",
            )
        )

    # 6) Playwright MCP review (artifact review_status)
    review_json = root / "reports" / "agent" / "10_presentation" / "LLM_PLAYWRIGHT_REVIEW.json"
    review = load_json(review_json)
    review_status = str(review.get("review_status") or "").strip().upper() or "NOT_RUN"
    mcp_applicability = str(policy.get("llm_playwright_review_applicability") or "required").strip().lower()
    mcp_fixture_exempt = mcp_applicability == "not_applicable_fixture" and is_under_fixtures(root)
    if not require_mcp or mcp_fixture_exempt:
        gates.append(
            _gate(
                "playwright_mcp_review",
                "NOT_APPLICABLE",
                required=False,
                notes="mcp_not_required_or_fixture_exempt",
            )
        )
    elif review_status == "PASS":
        gates.append(_gate("playwright_mcp_review", "PASS", evidence=str(review_json)))
    else:
        gates.append(
            _gate(
                "playwright_mcp_review",
                review_status if review_status != "NOT_RUN" else "NOT_RUN",
                evidence=str(review_json),
            )
        )

    # 7) LLM review artifact validation
    if not require_mcp or mcp_fixture_exempt:
        gates.append(
            _gate(
                "llm_review_artifact_validation",
                "NOT_APPLICABLE",
                required=False,
                notes="mcp_not_required_or_fixture_exempt",
            )
        )
    elif llm_status == "PASS":
        gates.append(_gate("llm_review_artifact_validation", "PASS", evidence="check_llm_playwright_review.py"))
    elif llm_status == "SKIPPED":
        gates.append(_gate("llm_review_artifact_validation", "SKIPPED", evidence="check_llm_playwright_review.py"))
    else:
        gates.append(
            _gate(
                "llm_review_artifact_validation",
                llm_status if llm_status != "NOT_RUN" else "NOT_RUN",
                evidence="check_llm_playwright_review.py",
            )
        )

    # 8) Independent verification
    if not require_iv:
        gates.append(_gate("independent_verification", "NOT_APPLICABLE", required=False))
    elif indep_status == "PASS":
        gates.append(_gate("independent_verification", "PASS", evidence=str(indep_path)))
    else:
        gates.append(
            _gate(
                "independent_verification",
                indep_status if indep_status != "NOT_RUN" else "NOT_RUN",
                evidence=str(indep_path),
            )
        )

    # 9) Final acceptance — require ACCEPTANCE_GATE_REPORT.json PASS.
    # Handoff runs post-acceptance; sibling validators must not manufacture this PASS.
    if not require_final:
        gates.append(
            _gate(
                "final_acceptance",
                "NOT_APPLICABLE",
                required=False,
                notes="deferred_until_final_phase",
            )
        )
    elif accept_status == "PASS":
        gates.append(_gate("final_acceptance", "PASS", evidence=str(accept_path)))
    else:
        gates.append(
            _gate(
                "final_acceptance",
                accept_status if accept_status != "NOT_RUN" else "NOT_RUN",
                evidence=str(accept_path),
                notes="post_acceptance_handoff_requires_ACCEPTANCE_GATE_REPORT",
            )
        )

    details["independent_verification_status"] = indep_status
    details["acceptance_status"] = accept_status
    return gates, details


def derive_presentation_state(gates: list[dict[str, Any]], *, interactive: bool) -> str:
    if not interactive:
        return "BLOCKED"
    by_id = {g["gate_id"]: g for g in gates}

    def status(gid: str) -> str:
        return str((by_id.get(gid) or {}).get("status") or "NOT_RUN")

    runtime_ids = ("manifest_relation_resolution", "runtime_preflight", "initial_data_load", "refresh_validation")
    if any(status(g) in {"FAIL", "BLOCKED"} for g in runtime_ids):
        return "RUNTIME_PREFLIGHT_FAILED"
    if any(status(g) in {"NOT_RUN", "MISSING", "STALE"} for g in runtime_ids if (by_id.get(g) or {}).get("required", True)):
        return "RUNTIME_PREFLIGHT_PENDING"

    if status("deterministic_playwright") in {"FAIL", "BLOCKED", "WARN", "SKIPPED"}:
        return "BROWSER_VALIDATION_FAILED"
    if status("deterministic_playwright") in {"NOT_RUN", "MISSING", "STALE"}:
        return "BROWSER_VALIDATION_PENDING"

    if status("playwright_mcp_review") in {"FAIL", "BLOCKED", "WARN"}:
        return "MCP_REVIEW_FAILED"
    if status("llm_review_artifact_validation") in {"FAIL", "BLOCKED", "WARN", "SKIPPED"}:
        return "MCP_REVIEW_FAILED"
    if status("playwright_mcp_review") in {"NOT_RUN", "MISSING", "STALE"} or status(
        "llm_review_artifact_validation"
    ) in {"NOT_RUN", "MISSING", "STALE"}:
        return "MCP_REVIEW_PENDING"

    if status("independent_verification") in {"FAIL", "BLOCKED", "WARN", "SKIPPED", "NOT_RUN"} or status(
        "final_acceptance"
    ) in {"FAIL", "BLOCKED", "WARN", "SKIPPED", "NOT_RUN"}:
        if status("independent_verification") in {"FAIL", "BLOCKED"} or status("final_acceptance") in {
            "FAIL",
            "BLOCKED",
        }:
            return "BLOCKED"
        return "FINAL_VERIFICATION_PENDING"

    if all(
        (not g.get("required", True)) or g.get("status") in PASSING_GATE_STATUSES for g in gates
    ):
        return "VERIFIED_FOR_HANDOFF"
    return "BLOCKED"


def evaluate_handoff(
    root: Path,
    *,
    phase: str,
) -> tuple[list[str], list[str], dict[str, Any], bool, str, dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    policy = load_presentation_policy(root)
    interactive = interactive_report_exists(root)
    bundle_hash, file_hashes = compute_report_bundle_hash(root)

    if fixture_handoff_exempt(root, policy):
        payload = {
            "schema_version": "1.0",
            "status": "PASS",
            "open_allowed": False,
            "presentation_state": "PRESENTATION_GENERATED",
            "report_bundle_hash": bundle_hash,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "gates": [],
            "notes": "fixture_only_handoff_exempt — open_allowed remains false for synthetic fixtures",
        }
        # Fixture exemption skips blocking CI, but still withholds user open by default.
        # Tests that need open_allowed use a crafted PASS payload explicitly.
        if bool(policy.get("fixture_allow_open_when_exempt", False)):
            payload["open_allowed"] = True
            payload["presentation_state"] = "VERIFIED_FOR_HANDOFF"
        details = {"phase": phase, "fixture_exempt": True, "open_allowed": payload["open_allowed"]}
        return errors, warnings, details, True, "fixture_only_handoff_exempt", payload

    if not interactive:
        payload = {
            "schema_version": "1.0",
            "status": "PASS",
            "open_allowed": False,
            "presentation_state": "BLOCKED",
            "report_bundle_hash": bundle_hash,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "gates": [],
            "notes": "no interactive report",
        }
        return errors, warnings, {"phase": phase, "interactive_report": False}, True, "no_interactive_report", payload

    gates, details = evaluate_gates(root, phase=phase)
    details["interactive_report"] = True
    details["report_bundle_hash"] = bundle_hash
    details["file_hashes"] = file_hashes

    # Warehouse-backed runtime execution evidence (DuckDB refresh / query runs).
    runtime_path = root / "reports" / "agent" / "10_presentation" / "matplotlib" / "runtime_execution.json"
    if not runtime_path.exists():
        runtime_path = root / "reports" / "agent" / "10_presentation" / "runtime_execution.json"
    runtime = load_json(runtime_path) if runtime_path.exists() else {}
    runtime_status = str(runtime.get("status") or "").strip().upper()
    details["runtime_execution_status"] = runtime_status or "MISSING"
    details["runtime_execution_path"] = str(runtime_path) if runtime_path.exists() else ""
    if phase == "final" and bool(policy.get("require_live_report_refresh_execution", True)):
        if runtime_status != "PASS":
            gates.append(
                _gate(
                    "runtime_execution",
                    runtime_status or "FAIL",
                    evidence=str(runtime_path) if runtime_path.exists() else "runtime_execution.json",
                    notes="warehouse-backed refresh required before handoff",
                    required=True,
                )
            )
        else:
            gates.append(
                _gate("runtime_execution", "PASS", evidence=str(runtime_path), required=True)
            )

    # Freshness: validator evidence must match the current report bundle.
    # A prior REPORT_HANDOFF_READINESS.json is overwritten by this run and must
    # not block re-evaluation after legitimate report regeneration.
    live_report = load_json(root / "reports" / "agent" / "10_presentation" / "LIVE_REPORT_DOM_REPORT.json")
    live_bundle = str(live_report.get("report_bundle_hash") or "")
    details["live_report_bundle_hash"] = live_bundle or None
    if phase == "final" and not live_bundle:
        for gate in gates:
            if gate["gate_id"] == "deterministic_playwright" and gate["status"] == "PASS":
                gate["status"] = "FAIL"
                gate["notes"] = "live DOM report_bundle_hash binding missing"
                break
    elif live_bundle and live_bundle != bundle_hash:
        for gate in gates:
            if gate["gate_id"] == "deterministic_playwright" and gate["status"] == "PASS":
                gate["status"] = "STALE"
                gate["notes"] = "live DOM evidence stale for current report bundle"
                break

    review = load_json(root / "reports" / "agent" / "10_presentation" / "LLM_PLAYWRIGHT_REVIEW.json")
    review_bundle = str(review.get("report_bundle_hash") or "")
    if review_bundle and review_bundle != bundle_hash:
        for gate in gates:
            if gate["gate_id"] in {"playwright_mcp_review", "llm_review_artifact_validation"} and gate[
                "status"
            ] == "PASS":
                gate["status"] = "STALE"
                gate["notes"] = "LLM review stale for current report bundle"

    # Independent verification + acceptance must bind to current bundle/commit/manifest.
    indep = load_json(root / "reports" / "agent" / "INDEPENDENT_VERIFICATION_REPORT.json")
    accept = load_json(root / "reports" / "agent" / "ACCEPTANCE_GATE_REPORT.json")
    relation_meta = details.get("relation_resolution") if isinstance(details.get("relation_resolution"), dict) else {}
    current_manifest = str(relation_meta.get("manifest_checksum") or "")
    for label, artifact in (
        ("independent_verification", indep),
        ("final_acceptance", accept),
    ):
        if not isinstance(artifact, dict) or not artifact:
            if phase == "final":
                # evaluate_gates already flags NOT_RUN; only add binding FAIL when artifact exists without bind.
                continue
            continue
        art_bundle = str(
            artifact.get("report_bundle_hash")
            or (artifact.get("details") or {}).get("report_bundle_hash")
            or ""
        ).strip()
        art_manifest = str(
            artifact.get("manifest_checksum")
            or (artifact.get("details") or {}).get("manifest_checksum")
            or ""
        ).strip()
        art_commit = str(
            artifact.get("repository_commit_sha")
            or artifact.get("git_commit")
            or (artifact.get("details") or {}).get("repository_commit_sha")
            or ""
        ).strip()
        if phase == "final" and not (art_bundle or art_manifest or art_commit):
            for gate in gates:
                if gate["gate_id"] == label and gate["status"] == "PASS":
                    gate["status"] = "FAIL"
                    gate["notes"] = (
                        "missing binding fields "
                        "(report_bundle_hash and/or manifest_checksum and/or repository_commit_sha)"
                    )
                    break
            continue
        if art_bundle and art_bundle != bundle_hash:
            for gate in gates:
                if gate["gate_id"] == label and gate["status"] == "PASS":
                    gate["status"] = "STALE"
                    gate["notes"] = f"{label} report_bundle_hash stale for current report bundle"
                    break
        if art_manifest and current_manifest and art_manifest != current_manifest:
            for gate in gates:
                if gate["gate_id"] == label and gate["status"] == "PASS":
                    gate["status"] = "STALE"
                    gate["notes"] = f"{label} manifest_checksum stale"
                    break

    blocking = []
    for gate in gates:
        if not gate.get("required", True):
            continue
        if gate["status"] not in PASSING_GATE_STATUSES:
            blocking.append(f"{gate['gate_id']}={gate['status']}")
            errors.append(
                f"required handoff gate not PASS: {gate['gate_id']} status={gate['status']}"
                + (f" ({gate['notes']})" if gate.get("notes") else "")
            )

    state = derive_presentation_state(gates, interactive=True)
    # Opening is only released after final-phase verification.
    open_allowed = (
        phase == "final"
        and state == "VERIFIED_FOR_HANDOFF"
        and not blocking
        and not errors
    )
    # Validator PASS means readiness evaluation completed cleanly for this phase.
    # open_allowed may still be false before final verification.
    status = "FAIL" if blocking or errors else "PASS"
    if phase != "final":
        state = "FINAL_VERIFICATION_PENDING" if status == "PASS" else state
        open_allowed = False

    payload = {
        "schema_version": "1.0",
        "status": status,
        "open_allowed": bool(open_allowed),
        "presentation_state": state,
        "report_bundle_hash": bundle_hash,
        "file_hashes": file_hashes,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "gates": gates,
        "blocking_gates": blocking,
        "open_command": "reports/agent/10_presentation/matplotlib/open_report.bat",
        "report_url": "http://127.0.0.1:8765/",
        "open_instructions_released": bool(open_allowed),
    }
    details["presentation_state"] = state
    details["open_allowed"] = open_allowed
    details["status"] = status
    return errors, warnings, details, False, "", payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", default="final")
    parser.add_argument(
        "--require-pass",
        action="store_true",
        help="Exit nonzero unless open_allowed=true (used by open_report launchers).",
    )
    parser.add_argument(
        "--write-artifact/--no-write-artifact",
        dest="write_artifact",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Write REPORT_HANDOFF_READINESS.json/md under the project root.",
    )
    add_output_json_arg(parser)
    args = parser.parse_args()
    root = args.root.resolve()

    errors, warnings, details, skipped, skip_reason, payload = evaluate_handoff(
        root, phase=str(args.phase)
    )

    if args.write_artifact and not skipped:
        out_json = root / HANDOFF_JSON
        out_md = root / HANDOFF_MD
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_handoff_markdown(out_md, payload)
        details["handoff_artifact"] = str(out_json)

    if args.require_pass and not payload.get("open_allowed"):
        errors.append(
            "REPORT_HANDOFF_READINESS open_allowed=false — "
            "Report artifacts were generated, but the report is not ready to open. "
            "Runtime and browser verification are still pending."
        )

    code = print_results(
        "Report handoff readiness",
        errors,
        warnings,
        details=details,
        output_json=args.output_json,
        validator_id=Path(__file__).stem,
        skipped=skipped,
        skip_reason=skip_reason,
    )
    if args.require_pass and not payload.get("open_allowed"):
        return 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
