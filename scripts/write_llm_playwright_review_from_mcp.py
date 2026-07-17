#!/usr/bin/env python3
"""Assemble LLM_PLAYWRIGHT_REVIEW artifacts from real MCP session observations.

Observation-only assembler:
- Requires --observations-json produced by an actual MCP browser session.
- Never invents interactions, screenshots, displayed values, findings, or PASS.
- Always sets business_approval_status=UNCHANGED (browser review cannot approve KPIs).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib_llm_playwright_review import (
    compute_report_bundle_hash,
    registry_page_ids,
    registry_visual_ids,
    resolve_presentation_paths,
    sha256_file,
    write_review_artifacts,
)

ALLOWED_OBSERVATION_REVIEW_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED"}
REQUIRED_OBSERVATION_BINDINGS = (
    "report_bundle_hash",
    "repository_commit_sha",
    "data_version_id",
    "session_id",
    "started_at",
    "completed_at",
)


def _load_observations(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"observations JSON not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("observations JSON must be an object")
    return data


def _current_commit_sha(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(root), text=True
        ).strip()
    except Exception:
        return ""


def _copy_screenshots(
    root: Path,
    observations: dict[str, Any],
    screenshot_dir: Path | None,
) -> list[dict[str, Any]]:
    evidence = root / "reports" / "agent" / "10_presentation" / "llm_playwright_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    screenshots: list[dict[str, Any]] = []
    for item in observations.get("screenshots") or []:
        if not isinstance(item, dict):
            continue
        rel = str(item.get("path") or "").strip()
        name = Path(rel).name if rel else ""
        if not name and screenshot_dir is None:
            continue
        dest_name = name or Path(str(item.get("filename") or "")).name
        if not dest_name:
            continue
        dest = evidence / dest_name
        src_candidates = []
        if screenshot_dir is not None:
            src_candidates.append(screenshot_dir / dest_name)
        if rel:
            src_candidates.append(root / rel)
            src_candidates.append(Path(rel))
        for src in src_candidates:
            if src.exists() and src.is_file():
                try:
                    if src.resolve() != dest.resolve():
                        shutil.copy2(src, dest)
                except OSError:
                    # Same-path / locked file: keep existing evidence file.
                    pass
                break
        if not dest.exists():
            # Do not invent screenshot rows for missing files.
            continue
        observed_hash = str(item.get("content_sha256") or item.get("sha256") or "").strip()
        actual_hash = sha256_file(dest)
        if observed_hash and observed_hash != actual_hash:
            raise ValueError(
                f"stale observation screenshot hash for {dest_name}: "
                f"observed={observed_hash[:12]}… actual={actual_hash[:12]}…"
            )
        screenshots.append(
            {
                "path": f"reports/agent/10_presentation/llm_playwright_evidence/{dest_name}",
                "viewport": item.get("viewport"),
                "page_id": item.get("page_id"),
                "content_sha256": observed_hash or actual_hash,
            }
        )
    return screenshots


def assemble_review(
    root: Path,
    observations: dict[str, Any],
    *,
    report_url: str | None = None,
    mcp_server: str | None = None,
    screenshot_dir: Path | None = None,
) -> dict[str, Any]:
    """Build review payload by copying observation bindings (never invent freshness)."""
    interactions = observations.get("interactions")
    if not isinstance(interactions, list) or not interactions:
        raise ValueError(
            "observations.interactions must be a non-empty list from an actual MCP session"
        )
    comparisons = observations.get("observed_value_comparisons")
    if not isinstance(comparisons, list):
        raise ValueError("observations.observed_value_comparisons must be a list")

    for idx, row in enumerate(comparisons):
        if not isinstance(row, dict):
            raise ValueError(f"observed_value_comparisons[{idx}] must be an object")
        for key in ("displayed_value", "manifest_value", "proof_value"):
            if key not in row:
                raise ValueError(
                    f"observed_value_comparisons[{idx}] missing {key} "
                    "(must be recorded independently in MCP observations)"
                )

    for key in REQUIRED_OBSERVATION_BINDINGS:
        if not str(observations.get(key) or "").strip():
            raise ValueError(
                f"observations missing required freshness binding field: {key}"
            )

    review_status = str(observations.get("review_status") or "").strip().upper()
    if review_status not in ALLOWED_OBSERVATION_REVIEW_STATUSES:
        raise ValueError(
            "observations.review_status must be one of "
            f"{sorted(ALLOWED_OBSERVATION_REVIEW_STATUSES)} "
            "(writer will not invent PASS)"
        )
    tech_status = str(observations.get("technical_verification_status") or "").strip().upper()
    if tech_status not in {"PASS", "WARN", "FAIL", "BLOCKED"}:
        raise ValueError(
            "observations.technical_verification_status must be set by the MCP session "
            "(writer will not invent PASS)"
        )

    current_bundle, file_hashes = compute_report_bundle_hash(root)
    paths = resolve_presentation_paths(root)
    current_commit = _current_commit_sha(root)
    obs_bundle = str(observations.get("report_bundle_hash") or "").strip()
    obs_commit = str(observations.get("repository_commit_sha") or "").strip()
    if obs_bundle != current_bundle:
        raise ValueError(
            "stale observations: report_bundle_hash does not match current project "
            f"(observed={obs_bundle[:12]}… current={current_bundle[:12]}…)"
        )
    if current_commit and obs_commit != current_commit:
        raise ValueError(
            "stale observations: repository_commit_sha does not match current HEAD "
            f"(observed={obs_commit[:12]}… current={current_commit[:12]}…)"
        )

    for shot in observations.get("screenshots") or []:
        if isinstance(shot, dict) and not str(
            shot.get("content_sha256") or shot.get("sha256") or ""
        ).strip():
            raise ValueError(
                "observations.screenshots entries must include content_sha256 "
                "(screenshot hash binding required)"
            )
    screenshots = _copy_screenshots(root, observations, screenshot_dir)
    expected_pages = sorted(registry_page_ids(root))
    expected_visuals = sorted(registry_visual_ids(root))
    reviewed_pages = list(observations.get("reviewed_page_ids") or [])
    reviewed_visuals = list(observations.get("reviewed_visual_ids") or [])
    if not reviewed_pages or not reviewed_visuals:
        raise ValueError(
            "observations must include reviewed_page_ids and reviewed_visual_ids from the MCP session"
        )

    page_cov = observations.get("page_coverage")
    visual_cov = observations.get("visual_coverage")
    if page_cov is None or visual_cov is None:
        raise ValueError(
            "observations must include page_coverage and visual_coverage "
            "(writer will not invent 1.0)"
        )

    # Copy observation freshness bindings; do not overwrite with recomputed values.
    payload = {
        "schema_version": "1.0",
        "review_id": str(
            observations.get("review_id")
            or f"LLM-PW-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        ),
        "review_status": review_status,
        "technical_verification_status": tech_status,
        # Browser/MCP review must never approve business KPI definitions.
        "business_approval_status": "UNCHANGED",
        "reviewed_at": str(
            observations.get("reviewed_at")
            or observations.get("completed_at")
            or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        ),
        "repository_commit_sha": obs_commit,
        "dbt_invocation_id": observations.get("dbt_invocation_id"),
        "report_bundle_hash": obs_bundle,
        "data_version_id": str(observations.get("data_version_id") or ""),
        "session_id": str(observations.get("session_id") or ""),
        "started_at": str(observations.get("started_at") or ""),
        "completed_at": str(observations.get("completed_at") or ""),
        "report_html_hash": file_hashes.get("report_html")
        or (sha256_file(paths["report_html"]) if paths.get("report_html") else ""),
        "page_registry_hash": file_hashes.get("page_registry", ""),
        "chart_registry_hash": file_hashes.get("chart_registry", ""),
        "rendered_metric_manifest_hash": file_hashes.get("rendered_metric_manifest", ""),
        "query_registry_hash": file_hashes.get("query_registry", ""),
        "proof_registry_hash": file_hashes.get("proof_registry", ""),
        "browser_runtime": str(observations.get("browser_runtime") or ""),
        "mcp_server": str(mcp_server or observations.get("mcp_server") or ""),
        "llm_reviewer": str(observations.get("llm_reviewer") or ""),
        "report_url": str(report_url or observations.get("report_url") or ""),
        "tested_viewports": list(observations.get("tested_viewports") or []),
        "expected_page_ids": expected_pages,
        "reviewed_page_ids": reviewed_pages,
        "expected_visual_ids": expected_visuals,
        "reviewed_visual_ids": reviewed_visuals,
        "page_coverage": float(page_cov),
        "visual_coverage": float(visual_cov),
        "interactions": interactions,
        "observed_value_comparisons": comparisons,
        "screenshots": screenshots,
        "findings": list(observations.get("findings") or []),
        "unresolved_critical_findings": list(observations.get("unresolved_critical_findings") or []),
        "unresolved_high_findings": list(observations.get("unresolved_high_findings") or []),
        "limitations": list(observations.get("limitations") or []),
        "notes": str(observations.get("notes") or ""),
        "observations_source": "mcp_session_observations_json",
    }
    if not payload["browser_runtime"] or not payload["mcp_server"] or not payload["llm_reviewer"]:
        raise ValueError("observations must include browser_runtime, mcp_server, and llm_reviewer")
    if not payload["report_url"]:
        raise ValueError("report_url missing from observations and CLI")
    if not payload["tested_viewports"]:
        raise ValueError("observations.tested_viewports must be non-empty")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--observations-json",
        type=Path,
        required=True,
        help="Actual MCP session observation JSON (required; writer never invents interactions).",
    )
    parser.add_argument("--report-url", default=None)
    parser.add_argument(
        "--screenshot-dir",
        type=Path,
        default=None,
        help="Optional directory containing MCP screenshot files referenced by observations.",
    )
    parser.add_argument("--mcp-server", default=None)
    args = parser.parse_args()
    root = args.root.resolve()

    try:
        observations = _load_observations(args.observations_json.resolve())
        payload = assemble_review(
            root,
            observations,
            report_url=args.report_url,
            mcp_server=args.mcp_server,
            screenshot_dir=args.screenshot_dir.resolve() if args.screenshot_dir else None,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 2

    json_path, md_path = write_review_artifacts(root, payload)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"bundle={payload['report_bundle_hash']}")
    print(f"interactions={len(payload['interactions'])} screenshots={len(payload['screenshots'])}")
    print(f"business_approval_status={payload['business_approval_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
