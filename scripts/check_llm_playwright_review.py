#!/usr/bin/env python3
"""Validate LLM-guided Playwright MCP final-report review artifacts.

This is separate from deterministic validate_live_report_dom.py.
Business approval status must remain unchanged by this review.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from lib_gate_common import add_output_json_arg, load_presentation_policy, print_results
from lib_llm_playwright_review import (
    REVIEW_JSON,
    REVIEW_MD,
    SCHEMA_VERSION,
    VALID_COMPARISON_STATUSES,
    VALID_FINDING_SEVERITIES,
    VALID_RESOLUTION,
    VALID_REVIEW_STATUSES,
    chart_series_names,
    compute_report_bundle_hash,
    interactive_charts,
    is_under_fixtures,
    load_json,
    looks_synthetic_production_review,
    registry_page_ids,
    registry_visual_ids,
    resolve_presentation_paths,
    sha256_file,
)


def _ratio(num: int, den: int) -> float:
    if den <= 0:
        return 1.0
    return float(num) / float(den)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def validate_review(
    root: Path,
    *,
    phase: str,
) -> tuple[list[str], list[str], dict[str, Any], bool, str]:
    """Return errors, warnings, details, skipped, skip_reason."""
    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {"phase": phase}
    policy = load_presentation_policy(root)
    require_at_final = bool(policy.get("require_llm_playwright_review_at_final", True))
    require_for_release = bool(policy.get("llm_playwright_review_required_for_release", True))
    applicability = str(policy.get("llm_playwright_review_applicability") or "required").strip().lower()
    final_like = phase in {"final", "presentation"}

    paths = resolve_presentation_paths(root)
    interactive = bool(paths.get("report_html") and paths["report_html"].exists())
    details["interactive_report"] = interactive
    details["applicability"] = applicability

    if applicability == "not_applicable_fixture":
        if not is_under_fixtures(root):
            errors.append(
                "llm_playwright_review_applicability=not_applicable_fixture is only valid "
                "under fixtures/ paths"
            )
            return errors, warnings, details, False, ""
        return (
            errors,
            warnings,
            details,
            True,
            "fixture_only_llm_playwright_review_exempt",
        )

    required = bool(
        interactive
        and final_like
        and (require_at_final or (phase == "final" and require_for_release))
    )
    if not interactive:
        return errors, warnings, details, True, "no_interactive_report"

    if not required:
        # Draft / non-final phases: missing review is OK
        json_path = root / REVIEW_JSON
        if not json_path.exists():
            return errors, warnings, details, True, "llm_review_not_required_for_phase"

    json_path = root / REVIEW_JSON
    md_path = root / REVIEW_MD
    if not json_path.exists():
        if required or phase == "final":
            errors.append(
                "missing LLM Playwright review JSON "
                f"({REVIEW_JSON.as_posix()}); deterministic Playwright PASS does not replace it"
            )
        else:
            warnings.append("[llm_review_missing_draft] LLM Playwright review JSON not present (draft OK)")
        return errors, warnings, details, False, ""
    if not md_path.exists():
        errors.append(f"missing LLM Playwright review Markdown ({REVIEW_MD.as_posix()})")

    payload = load_json(json_path)
    if not payload:
        errors.append("LLM Playwright review JSON is empty or invalid")
        return errors, warnings, details, False, ""

    if looks_synthetic_production_review(payload, root):
        errors.append("synthetic/fixture-only LLM Playwright review evidence used outside fixtures/")

    schema = str(payload.get("schema_version") or "")
    if schema not in {SCHEMA_VERSION, "1"}:
        errors.append(f"unsupported schema_version {schema!r}")

    status = str(payload.get("review_status") or "").upper()
    if status not in VALID_REVIEW_STATUSES:
        errors.append(f"invalid review_status {status!r}")
    details["review_status"] = status
    if status == "BLOCKED":
        errors.append("LLM Playwright review status is BLOCKED")
    elif status == "FAIL":
        errors.append("LLM Playwright review status is FAIL")

    # Technical vs business separation
    biz = str(payload.get("business_approval_status") or "")
    tech = str(payload.get("technical_verification_status") or "")
    details["business_approval_status"] = biz
    details["technical_verification_status"] = tech
    if not tech:
        errors.append("technical_verification_status missing on LLM review")
    # Business approval must not be auto-set to APPROVED by review alone without explicit note —
    # we only ensure the field exists as a separate status (may be PENDING etc.)
    if "business_approval_status" not in payload:
        errors.append("business_approval_status missing (must remain separate from browser review)")

    required_scalar = [
        "review_id",
        "reviewed_at",
        "repository_commit_sha",
        "report_bundle_hash",
        "report_html_hash",
        "page_registry_hash",
        "chart_registry_hash",
        "rendered_metric_manifest_hash",
        "browser_runtime",
        "mcp_server",
        "llm_reviewer",
        "report_url",
    ]
    for key in required_scalar:
        if not payload.get(key):
            errors.append(f"LLM review missing required field: {key}")

    mcp = str(payload.get("mcp_server") or "").lower()
    if "playwright" not in mcp and "cursor-ide-browser" not in mcp and "browser" not in mcp:
        errors.append(f"mcp_server does not indicate a Playwright/browser MCP runtime: {mcp!r}")

    # Freshness / hashes
    bundle_hash, file_hashes = compute_report_bundle_hash(root)
    details["computed_report_bundle_hash"] = bundle_hash
    recorded = str(payload.get("report_bundle_hash") or "")
    if policy.get("require_llm_review_artifact_freshness", True):
        if recorded and recorded != bundle_hash:
            errors.append(
                f"stale LLM Playwright review: report_bundle_hash mismatch "
                f"(recorded={recorded[:12]}… computed={bundle_hash[:12]}…)"
            )
        # Per-artifact hashes when files exist
        path_map = resolve_presentation_paths(root)
        hash_key_map = {
            "report_html": "report_html_hash",
            "page_registry": "page_registry_hash",
            "chart_registry": "chart_registry_hash",
            "rendered_metric_manifest": "rendered_metric_manifest_hash",
            "query_registry": "query_registry_hash",
            "proof_registry": "proof_registry_hash",
        }
        for path_key, payload_key in hash_key_map.items():
            path = path_map.get(path_key)
            if not path or not path.exists():
                continue
            expected = sha256_file(path)
            got = str(payload.get(payload_key) or "")
            if got and got != expected:
                errors.append(f"stale LLM review artifact hash for {payload_key}")

    # Coverage
    expected_pages = set(str(x) for x in _as_list(payload.get("expected_page_ids"))) or registry_page_ids(root)
    reviewed_pages = {str(x) for x in _as_list(payload.get("reviewed_page_ids")) if x}
    expected_visuals = set(str(x) for x in _as_list(payload.get("expected_visual_ids"))) or registry_visual_ids(root)
    reviewed_visuals = {str(x) for x in _as_list(payload.get("reviewed_visual_ids")) if x}
    known_pages = registry_page_ids(root)
    known_visuals = registry_visual_ids(root)

    for pid in reviewed_pages:
        if known_pages and pid not in known_pages:
            errors.append(f"unknown reviewed page_id: {pid}")
    for vid in reviewed_visuals:
        if known_visuals and vid not in known_visuals:
            errors.append(f"unknown reviewed visual_id: {vid}")

    page_cov = _ratio(len(expected_pages & reviewed_pages), len(expected_pages)) if expected_pages else 1.0
    visual_cov = (
        _ratio(len(expected_visuals & reviewed_visuals), len(expected_visuals)) if expected_visuals else 1.0
    )
    # Prefer explicit payload coverage when present and consistent
    try:
        if payload.get("page_coverage") is not None:
            page_cov = float(payload["page_coverage"])
        if payload.get("visual_coverage") is not None:
            visual_cov = float(payload["visual_coverage"])
    except (TypeError, ValueError):
        errors.append("page_coverage/visual_coverage must be numeric")

    details["page_coverage"] = page_cov
    details["visual_coverage"] = visual_cov
    req_page = float(policy.get("require_llm_review_page_coverage", 1.0))
    req_vis = float(policy.get("require_llm_review_visual_coverage", 1.0))
    if policy.get("require_llm_review_page_coverage", True) is not False and page_cov + 1e-9 < req_page:
        errors.append(f"LLM review page coverage {page_cov:.2%} below required {req_page:.2%}")
    if policy.get("require_llm_review_visual_coverage", True) is not False and visual_cov + 1e-9 < req_vis:
        missing = sorted(expected_visuals - reviewed_visuals)
        errors.append(
            f"LLM review visual coverage {visual_cov:.2%} below required {req_vis:.2%}"
            + (f"; missing={missing[:8]}" if missing else "")
        )
    if expected_pages - reviewed_pages and req_page >= 1.0:
        errors.append(
            "missing expected page review: " + ", ".join(sorted(expected_pages - reviewed_pages)[:12])
        )
    if expected_visuals - reviewed_visuals and req_vis >= 1.0:
        errors.append(
            "missing expected visual review: " + ", ".join(sorted(expected_visuals - reviewed_visuals)[:12])
        )

    # Viewports
    required_viewports = [str(v).lower() for v in (policy.get("llm_review_viewports") or ["desktop", "tablet", "mobile"])]
    tested = {str(v).lower() for v in _as_list(payload.get("tested_viewports"))}
    for vp in required_viewports:
        if vp not in tested:
            errors.append(f"missing required LLM review viewport: {vp}")

    # Interactions
    interactions = [i for i in _as_list(payload.get("interactions")) if isinstance(i, dict)]
    details["interaction_count"] = len(interactions)
    charts = interactive_charts(root)
    chart_by_id = {str(c.get("chart_id")): c for c in charts}
    for item in interactions:
        for key in ("page_id", "viewport", "interaction_type"):
            if not item.get(key):
                errors.append(f"interaction missing {key}: {item.get('chart_id') or item.get('visual_id')}")
        shot = item.get("screenshot_path")
        if shot:
            shot_path = root / str(shot)
            if not shot_path.exists():
                errors.append(f"interaction screenshot missing: {shot}")
        if item.get("interaction_success") is not True and phase == "final":
            warnings.append(
                f"[llm_interaction_failed] interaction not successful for "
                f"{item.get('chart_id') or item.get('visual_id')}"
            )

    # Screenshots list
    for shot in _as_list(payload.get("screenshots")):
        if isinstance(shot, dict):
            path = shot.get("path") or shot.get("screenshot_path")
        else:
            path = shot
        if path and not (root / str(path)).exists():
            errors.append(f"screenshot missing: {path}")

    # Multi-series + critical periods for interactive charts
    for chart in charts:
        cid = str(chart.get("chart_id") or "")
        series_names = chart_series_names(chart)
        chart_interactions = [
            i
            for i in interactions
            if str(i.get("chart_id") or "") == cid or str(i.get("visual_id") or "") == str(chart.get("visual_id") or "")
        ]
        if len(series_names) >= 2:
            covered = {
                str(i.get("series_name") or "").strip()
                for i in chart_interactions
                if i.get("series_name")
            }
            missing_series = [s for s in series_names if s not in covered]
            if missing_series:
                errors.append(
                    f"chart {cid}: missing multi-series LLM interaction coverage for {missing_series}"
                )
        # Critical periods: first/middle/last labels when time-series data present
        data_rows = [r for r in (chart.get("data") or []) if isinstance(r, dict) and not r.get("missing_period")]
        if len(data_rows) >= 2:
            labels = []
            for r in (data_rows[0], data_rows[len(data_rows) // 2], data_rows[-1]):
                labels.append(str(r.get("period_label") or r.get(chart.get("x_field") or "period") or ""))
            points = {
                str(i.get("point_or_category") or "").strip()
                for i in chart_interactions
                if i.get("point_or_category")
            }
            # Also accept period in tooltip text
            tip_blob = " | ".join(str(i.get("observed_tooltip_text") or "") for i in chart_interactions)
            missing_periods = [lab for lab in labels if lab and lab not in points and lab not in tip_blob]
            if missing_periods:
                errors.append(
                    f"chart {cid}: missing critical-period LLM coverage for {missing_periods}"
                )

    # Value comparisons
    comparisons = [c for c in _as_list(payload.get("observed_value_comparisons")) if isinstance(c, dict)]
    if charts and not comparisons and phase == "final":
        errors.append("LLM review missing observed_value_comparisons for interactive charts")
    for cmp_row in comparisons:
        st = str(cmp_row.get("comparison_status") or "").upper()
        if st and st not in VALID_COMPARISON_STATUSES:
            errors.append(f"invalid comparison_status {st!r}")
        if st == "FAIL":
            errors.append(
                f"value comparison FAIL for metric {cmp_row.get('metric_id')} "
                f"on {cmp_row.get('page_id')}/{cmp_row.get('visual_id')}"
            )

    # Findings
    findings = [f for f in _as_list(payload.get("findings")) if isinstance(f, dict)]
    unresolved_critical = []
    unresolved_high = []
    for finding in findings:
        fid = finding.get("finding_id") or "unknown"
        sev = str(finding.get("severity") or "").upper()
        res = str(finding.get("resolution_status") or "OPEN").upper()
        if sev not in VALID_FINDING_SEVERITIES:
            errors.append(f"finding {fid}: invalid severity {sev!r}")
        if res not in VALID_RESOLUTION:
            errors.append(f"finding {fid}: invalid resolution_status {res!r}")
        if res in {"OPEN", "DEFERRED"} and sev == "CRITICAL":
            unresolved_critical.append(fid)
        if res in {"OPEN", "DEFERRED"} and sev == "HIGH":
            unresolved_high.append(fid)
        evidence = finding.get("evidence")
        if evidence and isinstance(evidence, str) and ("/" in evidence or "\\" in evidence):
            if not (root / evidence).exists() and not Path(evidence).exists():
                warnings.append(f"[llm_finding_evidence_missing] finding {fid} evidence path missing: {evidence}")

    # Prefer explicit lists when present
    for fid in _as_list(payload.get("unresolved_critical_findings")):
        if fid and fid not in unresolved_critical:
            unresolved_critical.append(str(fid))
    for fid in _as_list(payload.get("unresolved_high_findings")):
        if fid and fid not in unresolved_high:
            unresolved_high.append(str(fid))

    details["unresolved_critical_findings"] = unresolved_critical
    details["unresolved_high_findings"] = unresolved_high
    if policy.get("llm_review_block_on_critical_findings", True) and unresolved_critical:
        errors.append("unresolved CRITICAL findings: " + ", ".join(unresolved_critical[:12]))
    if policy.get("llm_review_block_on_high_findings", True) and unresolved_high:
        errors.append("unresolved HIGH findings: " + ", ".join(unresolved_high[:12]))

    # WARN-only medium findings → allow WARN status without FAIL
    if status == "WARN" and not errors:
        med_open = [
            f.get("finding_id")
            for f in findings
            if str(f.get("severity") or "").upper() == "MEDIUM"
            and str(f.get("resolution_status") or "OPEN").upper() in {"OPEN", "DEFERRED"}
        ]
        if med_open:
            warnings.append(
                "[llm_review_medium_findings] open MEDIUM findings remain: "
                + ", ".join(str(x) for x in med_open[:8])
            )

    return errors, warnings, details, False, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."), help="dbt project root")
    parser.add_argument(
        "--phase",
        choices=["discovery", "analytics", "presentation", "final", "bronze", "silver", "gold"],
        default="analytics",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    errors, warnings, details, skipped, skip_reason = validate_review(root, phase=args.phase)
    return print_results(
        "LLM Playwright MCP review",
        errors,
        warnings,
        details=details,
        output_json=getattr(args, "output_json", None),
        validator_id=Path(__file__).stem,
        skipped=skipped,
        skip_reason=skip_reason,
    )


if __name__ == "__main__":
    raise SystemExit(main())
