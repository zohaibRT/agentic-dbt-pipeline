#!/usr/bin/env python3
"""Helpers for LLM-guided Playwright MCP review artifacts and freshness hashing."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

REVIEW_MD = Path("reports/agent/10_presentation/LLM_PLAYWRIGHT_REVIEW.md")
REVIEW_JSON = Path("reports/agent/10_presentation/LLM_PLAYWRIGHT_REVIEW.json")
EVIDENCE_DIR = Path("reports/agent/10_presentation/llm_playwright_evidence")

SCHEMA_VERSION = "1.0"
VALID_REVIEW_STATUSES = {"PASS", "WARN", "FAIL", "BLOCKED"}
VALID_FINDING_SEVERITIES = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_COMPARISON_STATUSES = {"PASS", "WARN", "FAIL", "SKIPPED", "BLOCKED"}
VALID_RESOLUTION = {"OPEN", "RESOLVED", "ACCEPTED", "DEFERRED", "WONT_FIX"}

BUNDLE_RELATIVE_CANDIDATES = (
    "reports/agent/10_presentation/matplotlib/report.html",
    "reports/agent/10_presentation/report.html",
    "reports/agent/10_presentation/page_registry.json",
    "reports/agent/10_presentation/matplotlib/page_registry.json",
    "reports/agent/10_presentation/chart_registry.json",
    "reports/agent/10_presentation/matplotlib/chart_registry.json",
    "reports/agent/10_presentation/rendered_metric_manifest.json",
    "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json",
    "reports/agent/10_presentation/query_registry.json",
    "reports/agent/10_presentation/matplotlib/query_registry.json",
    "reports/agent/10_presentation/proof_registry.json",
    "reports/agent/10_presentation/matplotlib/proof_registry.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_presentation_paths(root: Path) -> dict[str, Path]:
    """Resolve canonical presentation artifact paths (prefer matplotlib/ then root)."""
    base = root / "reports" / "agent" / "10_presentation"
    mpl = base / "matplotlib"

    def first(*rels: Path) -> Path | None:
        for rel in rels:
            if rel.exists():
                return rel
        return None

    return {
        "report_html": first(mpl / "report.html", base / "report.html"),
        "page_registry": first(base / "page_registry.json", mpl / "page_registry.json"),
        "chart_registry": first(base / "chart_registry.json", mpl / "chart_registry.json"),
        "rendered_metric_manifest": first(
            base / "rendered_metric_manifest.json", mpl / "rendered_metric_manifest.json"
        ),
        "query_registry": first(base / "query_registry.json", mpl / "query_registry.json"),
        "proof_registry": first(base / "proof_registry.json", mpl / "proof_registry.json"),
        "page_contracts": first(base / "page_contracts.json", mpl / "page_contracts.json"),
        "freshness": first(mpl / "freshness.json", base / "freshness.json"),
    }


def compute_report_bundle_hash(root: Path) -> tuple[str, dict[str, str]]:
    """Hash current report bundle inputs. Returns (bundle_hash, per-file hashes)."""
    paths = resolve_presentation_paths(root)
    parts: list[str] = []
    file_hashes: dict[str, str] = {}
    # Hash substantive report inputs only. Do not include freshness.json —
    # its generated_at / as_of timestamps change on every serve/DOM run and
    # would falsely mark a still-valid LLM review as stale.
    for key in (
        "report_html",
        "page_registry",
        "chart_registry",
        "rendered_metric_manifest",
        "query_registry",
        "proof_registry",
        "page_contracts",
    ):
        path = paths.get(key)
        if path and path.exists():
            digest = sha256_file(path)
            rel = path.relative_to(root).as_posix()
            file_hashes[key] = digest
            parts.append(f"{key}:{rel}:{digest}")
    # Include chart payload embedded in registry when present (browser data).
    chart_path = paths.get("chart_registry")
    if chart_path and chart_path.exists():
        try:
            chart_data = json.loads(chart_path.read_text(encoding="utf-8"))
            payload = json.dumps(chart_data, sort_keys=True, ensure_ascii=False, default=str)
            payload_hash = sha256_text(payload)
            file_hashes["chart_registry_canonical"] = payload_hash
            parts.append(f"chart_registry_canonical:{payload_hash}")
        except Exception:
            pass
    bundle = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return bundle, file_hashes


def is_under_fixtures(root: Path) -> bool:
    parts = {p.lower() for p in root.resolve().parts}
    return "fixtures" in parts


def rebind_fixture_observation_freshness(root: Path, observations_path: Path) -> dict[str, Any]:
    """Rebind fixture MCP observations to the current report bundle (fixtures/ only).

    Does not invent interactions, comparisons, or PASS. Only refreshes freshness
    binding fields so CI fixture rebuilds can assemble a review without weakening
    production stale-observation checks outside fixtures/.
    """
    if not is_under_fixtures(root):
        raise RuntimeError(
            "fixture observation rebinding is only allowed under fixtures/ "
            f"(root={root})"
        )
    if not observations_path.exists():
        raise FileNotFoundError(f"observations JSON not found: {observations_path}")
    data = json.loads(observations_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("observations JSON must be an object")

    bundle, _file_hashes = compute_report_bundle_hash(root)
    commit = ""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(root), text=True
        ).strip()
    except Exception:
        # Fixture trees may not be standalone git repos; fall back to workspace.
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip()
        except Exception:
            commit = str(data.get("repository_commit_sha") or "")

    data_version = ""
    for candidate in (
        root / "reports" / "agent" / "10_presentation" / "matplotlib" / "runtime_execution.json",
        root / "reports" / "agent" / "10_presentation" / "runtime_execution.json",
        root / "reports" / "agent" / "10_presentation" / "matplotlib" / "freshness.json",
        root / "reports" / "agent" / "10_presentation" / "freshness.json",
    ):
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("data_version"):
            data_version = str(payload["data_version"])
            break
    if not data_version:
        data_version = str(data.get("data_version_id") or f"fixture-dv-{bundle[:12]}")

    data["report_bundle_hash"] = bundle
    if commit:
        data["repository_commit_sha"] = commit
    data["data_version_id"] = data_version
    if not str(data.get("session_id") or "").strip():
        data["session_id"] = f"fixture-mcp-{bundle[:12]}"
    if not str(data.get("started_at") or "").strip():
        data["started_at"] = "2026-07-16T22:08:50+00:00"
    if not str(data.get("completed_at") or "").strip():
        data["completed_at"] = "2026-07-16T22:11:48+00:00"
    data["fixture_synthetic_evidence"] = True
    data["fixture_evidence_scope"] = "fixtures_only"
    notes = str(data.get("notes") or "").strip()
    marker = "FIXTURE_SYNTHETIC_EVIDENCE: freshness rebound after final report bundle."
    if marker not in notes:
        data["notes"] = f"{notes}\n{marker}".strip() if notes else marker

    screenshots = data.get("screenshots")
    if isinstance(screenshots, list):
        for shot in screenshots:
            if not isinstance(shot, dict):
                continue
            rel = str(shot.get("path") or "").strip()
            if not rel:
                continue
            path = root / rel
            if path.exists() and path.is_file():
                shot["content_sha256"] = sha256_file(path)

    observations_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return data


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def registry_page_ids(root: Path) -> set[str]:
    paths = resolve_presentation_paths(root)
    page_reg = paths.get("page_registry")
    if not page_reg:
        return set()
    data = load_json(page_reg)
    pages = data.get("pages") if isinstance(data.get("pages"), list) else []
    return {str(p.get("page_id") or "").strip() for p in pages if isinstance(p, dict) and p.get("page_id")}


def registry_visual_ids(root: Path) -> set[str]:
    paths = resolve_presentation_paths(root)
    ids: set[str] = set()
    for key in ("chart_registry", "page_registry"):
        path = paths.get(key)
        if not path:
            continue
        data = load_json(path)
        for chart in data.get("charts") or []:
            if isinstance(chart, dict):
                for field in ("visual_id", "chart_id"):
                    val = str(chart.get(field) or "").strip()
                    if val:
                        ids.add(val)
        for page in data.get("pages") or []:
            if isinstance(page, dict):
                for vid in page.get("visual_ids") or []:
                    if vid:
                        ids.add(str(vid).strip())
                for card in page.get("cards") or []:
                    if isinstance(card, dict) and card.get("visual_id"):
                        ids.add(str(card["visual_id"]).strip())
    chart_path = paths.get("chart_registry")
    if chart_path:
        data = load_json(chart_path)
        for card in data.get("cards") or []:
            if isinstance(card, dict) and card.get("visual_id"):
                ids.add(str(card["visual_id"]).strip())
    return {i for i in ids if i}


def chart_series_names(chart: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for series in chart.get("series") or []:
        if not isinstance(series, dict):
            continue
        name = str(series.get("display_name") or series.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def interactive_charts(root: Path) -> list[dict[str, Any]]:
    paths = resolve_presentation_paths(root)
    chart_path = paths.get("chart_registry")
    if not chart_path:
        return []
    data = load_json(chart_path)
    charts = []
    for chart in data.get("charts") or []:
        if isinstance(chart, dict) and chart.get("chart_id"):
            charts.append(chart)
    return charts


def looks_synthetic_production_review(payload: dict[str, Any], root: Path) -> bool:
    """Detect fixture-only / placeholder reviews used outside fixtures/."""
    if is_under_fixtures(root):
        return False
    if payload.get("fixture_synthetic_evidence") is True:
        return True
    if str(payload.get("fixture_evidence_scope") or "").strip().lower() == "fixtures_only":
        return True
    blob = json.dumps(payload, ensure_ascii=False).lower()
    tokens = (
        "synthetic fixture",
        "test fixture only",
        "not a real mcp review",
        "placeholder llm review",
        "fake playwright mcp",
        "fixture_synthetic_evidence",
        "fixture_evidence_scope",
        "fixture_synthetic_evidence:",
    )
    return any(token in blob for token in tokens)


def markdown_from_review(payload: dict[str, Any]) -> str:
    """Generate Markdown report from structured review JSON."""
    lines = [
        "# LLM Playwright MCP Review",
        "",
        f"- Review ID: `{payload.get('review_id', '')}`",
        f"- Review status: **{payload.get('review_status', 'UNKNOWN')}**",
        f"- Technical verification status: `{payload.get('technical_verification_status', '')}`",
        f"- Business approval status: `{payload.get('business_approval_status', '')}` "
        "(unchanged by this review)",
        f"- Reviewed at: `{payload.get('reviewed_at', '')}`",
        f"- MCP server: `{payload.get('mcp_server', '')}`",
        f"- Browser runtime: `{payload.get('browser_runtime', '')}`",
        f"- Report URL: `{payload.get('report_url', '')}`",
        f"- Report bundle hash: `{payload.get('report_bundle_hash', '')}`",
        f"- Page coverage: `{payload.get('page_coverage', '')}`",
        f"- Visual coverage: `{payload.get('visual_coverage', '')}`",
        "",
        "## Viewports",
        "",
    ]
    for vp in payload.get("tested_viewports") or []:
        lines.append(f"- {vp}")
    lines.extend(["", "## Pages reviewed", ""])
    for pid in payload.get("reviewed_page_ids") or []:
        lines.append(f"- `{pid}`")
    lines.extend(["", "## Visuals reviewed", ""])
    for vid in payload.get("reviewed_visual_ids") or []:
        lines.append(f"- `{vid}`")
    lines.extend(["", "## Interactions", ""])
    for item in payload.get("interactions") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('viewport')}` / `{item.get('page_id')}` / "
            f"`{item.get('visual_id') or item.get('chart_id')}` / "
            f"{item.get('interaction_type')} → "
            f"{'OK' if item.get('interaction_success') else 'FAIL'}"
        )
    lines.extend(["", "## Findings", ""])
    findings = payload.get("findings") or []
    if not findings:
        lines.append("None.")
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        lines.append(
            f"- **{finding.get('severity')}** `{finding.get('finding_id')}` "
            f"({finding.get('resolution_status')}): {finding.get('description')}"
        )
    lines.extend(["", "## Limitations", ""])
    for note in payload.get("limitations") or []:
        lines.append(f"- {note}")
    if payload.get("notes"):
        lines.extend(["", "## Notes", "", str(payload.get("notes")), ""])
    lines.append("")
    lines.append(
        "This review verifies technical presentation quality only. "
        "It does **not** grant business KPI approval."
    )
    lines.append("")
    return "\n".join(lines)


def write_review_artifacts(root: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / REVIEW_JSON
    md_path = root / REVIEW_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    (root / EVIDENCE_DIR).mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(markdown_from_review(payload), encoding="utf-8")
    return json_path, md_path


_PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|PLACEHOLDER|SYNTHETIC MCP)\b", re.I)
