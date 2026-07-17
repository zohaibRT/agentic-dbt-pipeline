#!/usr/bin/env python3
"""Focused tests for MCP observation freshness binding and independent compares."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib_llm_playwright_review import compute_report_bundle_hash, write_review_artifacts  # noqa: E402
from write_llm_playwright_review_from_mcp import assemble_review  # noqa: E402


def _min_root(tmp: str) -> Path:
    root = Path(tmp) / "proj"
    root.mkdir()
    presentation = root / "reports" / "agent" / "10_presentation"
    presentation.mkdir(parents=True)
    (presentation / "page_registry.json").write_text(
        json.dumps({"pages": [{"page_id": "executive_overview"}]}),
        encoding="utf-8",
    )
    (presentation / "chart_registry.json").write_text(
        json.dumps(
            {
                "charts": [
                    {
                        "chart_id": "volume_trend",
                        "visual_id": "visual_volume_trend",
                        "page_id": "executive_overview",
                        "render_mode": "interactive_html",
                        "data": [{"period_label": "Mar", "value": 5}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (presentation / "rendered_metric_manifest.json").write_text(
        json.dumps({"metrics": [{"metric_id": "KPI-001", "formatted_value": "5"}]}),
        encoding="utf-8",
    )
    (presentation / "matplotlib").mkdir(exist_ok=True)
    (presentation / "matplotlib" / "report.html").write_text("<html></html>", encoding="utf-8")
    evidence = presentation / "llm_playwright_evidence"
    evidence.mkdir()
    for name in ("desktop.png", "tablet.png", "mobile.png"):
        (evidence / name).write_bytes(b"\x89PNG\r\n\x1a\nfake-" + name.encode())
    (root / "project.config.yml").write_text(
        "presentation_policy:\n  require_llm_playwright_review_at_final: true\n",
        encoding="utf-8",
    )
    return root


def _base_observations(root: Path) -> dict:
    from lib_manifest_relation import sha256_file

    bundle, _ = compute_report_bundle_hash(root)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
    except Exception:
        commit = "testcommit"
    evidence = root / "reports" / "agent" / "10_presentation" / "llm_playwright_evidence"
    return {
        "review_status": "PASS",
        "technical_verification_status": "PASS",
        "report_bundle_hash": bundle,
        "repository_commit_sha": commit,
        "data_version_id": "dv-test",
        "session_id": "sess-1",
        "started_at": "2026-07-17T00:00:00+00:00",
        "completed_at": "2026-07-17T00:01:00+00:00",
        "browser_runtime": "chromium",
        "mcp_server": "user-playwright",
        "llm_reviewer": "cursor-agent",
        "report_url": "http://127.0.0.1:8765/",
        "tested_viewports": ["desktop", "tablet", "mobile"],
        "reviewed_page_ids": ["executive_overview"],
        "reviewed_visual_ids": ["visual_volume_trend", "volume_trend"],
        "page_coverage": 1.0,
        "visual_coverage": 1.0,
        "interactions": [
            {
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "chart_id": "volume_trend",
                "viewport": "desktop",
                "interaction_type": "hover",
                "interaction_success": True,
            }
        ],
        "observed_value_comparisons": [
            {
                "metric_id": "KPI-001",
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "displayed_value": "5",
                "manifest_value": "5",
                "proof_value": "5",
                "comparison_status": "PASS",
            }
        ],
        "screenshots": [
            {
                "path": "reports/agent/10_presentation/llm_playwright_evidence/desktop.png",
                "viewport": "desktop",
                "content_sha256": sha256_file(evidence / "desktop.png"),
            },
            {
                "path": "reports/agent/10_presentation/llm_playwright_evidence/tablet.png",
                "viewport": "tablet",
                "content_sha256": sha256_file(evidence / "tablet.png"),
            },
            {
                "path": "reports/agent/10_presentation/llm_playwright_evidence/mobile.png",
                "viewport": "mobile",
                "content_sha256": sha256_file(evidence / "mobile.png"),
            },
        ],
        "findings": [],
    }


class McpObservationBindingTests(unittest.TestCase):
    def test_stale_observations_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _min_root(tmp)
            obs = _base_observations(root)
            obs["report_bundle_hash"] = "0" * 64
            with self.assertRaises(ValueError) as ctx:
                assemble_review(root, obs)
            self.assertIn("stale observations", str(ctx.exception).lower())

    def test_writer_copies_observation_bundle_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _min_root(tmp)
            obs = _base_observations(root)
            payload = assemble_review(root, obs)
            self.assertEqual(payload["report_bundle_hash"], obs["report_bundle_hash"])
            self.assertEqual(payload["repository_commit_sha"], obs["repository_commit_sha"])
            self.assertEqual(payload["data_version_id"], obs["data_version_id"])
            self.assertEqual(payload["session_id"], obs["session_id"])
            self.assertEqual(payload["business_approval_status"], "UNCHANGED")

    def test_review_pass_with_tech_fail_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _min_root(tmp)
            bundle, hashes = compute_report_bundle_hash(root)
            payload = {
                "schema_version": "1.0",
                "review_id": "R1",
                "review_status": "PASS",
                "technical_verification_status": "FAIL",
                "business_approval_status": "UNCHANGED",
                "reviewed_at": "2026-07-17T00:00:00+00:00",
                "repository_commit_sha": "abc",
                "report_bundle_hash": bundle,
                "report_html_hash": hashes.get("report_html", "x"),
                "page_registry_hash": hashes.get("page_registry", "x"),
                "chart_registry_hash": hashes.get("chart_registry", "x"),
                "rendered_metric_manifest_hash": hashes.get("rendered_metric_manifest", "x"),
                "browser_runtime": "chromium",
                "mcp_server": "user-playwright",
                "llm_reviewer": "agent",
                "report_url": "http://127.0.0.1:8765/",
                "tested_viewports": ["desktop", "tablet", "mobile"],
                "expected_page_ids": ["executive_overview"],
                "reviewed_page_ids": ["executive_overview"],
                "expected_visual_ids": ["visual_volume_trend", "volume_trend"],
                "reviewed_visual_ids": ["visual_volume_trend", "volume_trend"],
                "page_coverage": 1.0,
                "visual_coverage": 1.0,
                "interactions": [
                    {
                        "page_id": "executive_overview",
                        "visual_id": "visual_volume_trend",
                        "chart_id": "volume_trend",
                        "viewport": "desktop",
                        "interaction_type": "hover",
                        "point_or_category": "Mar",
                        "series_name": "Actual",
                        "interaction_success": True,
                    }
                ],
                "observed_value_comparisons": [
                    {
                        "metric_id": "KPI-001",
                        "displayed_value": "5",
                        "manifest_value": "5",
                        "proof_value": "5",
                        "comparison_status": "PASS",
                    }
                ],
                "screenshots": [
                    {
                        "path": "reports/agent/10_presentation/llm_playwright_evidence/desktop.png",
                        "viewport": "desktop",
                    },
                    {
                        "path": "reports/agent/10_presentation/llm_playwright_evidence/tablet.png",
                        "viewport": "tablet",
                    },
                    {
                        "path": "reports/agent/10_presentation/llm_playwright_evidence/mobile.png",
                        "viewport": "mobile",
                    },
                ],
                "findings": [],
            }
            write_review_artifacts(root, payload)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_llm_playwright_review.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("technical_verification_status", (proc.stdout + proc.stderr).lower())

    def test_false_manual_comparison_pass_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _min_root(tmp)
            bundle, hashes = compute_report_bundle_hash(root)
            payload = {
                "schema_version": "1.0",
                "review_id": "R2",
                "review_status": "PASS",
                "technical_verification_status": "PASS",
                "business_approval_status": "UNCHANGED",
                "reviewed_at": "2026-07-17T00:00:00+00:00",
                "repository_commit_sha": "abc",
                "report_bundle_hash": bundle,
                "report_html_hash": hashes.get("report_html", "x"),
                "page_registry_hash": hashes.get("page_registry", "x"),
                "chart_registry_hash": hashes.get("chart_registry", "x"),
                "rendered_metric_manifest_hash": hashes.get("rendered_metric_manifest", "x"),
                "browser_runtime": "chromium",
                "mcp_server": "user-playwright",
                "llm_reviewer": "agent",
                "report_url": "http://127.0.0.1:8765/",
                "tested_viewports": ["desktop", "tablet", "mobile"],
                "expected_page_ids": ["executive_overview"],
                "reviewed_page_ids": ["executive_overview"],
                "expected_visual_ids": ["visual_volume_trend", "volume_trend"],
                "reviewed_visual_ids": ["visual_volume_trend", "volume_trend"],
                "page_coverage": 1.0,
                "visual_coverage": 1.0,
                "interactions": [
                    {
                        "page_id": "executive_overview",
                        "visual_id": "visual_volume_trend",
                        "chart_id": "volume_trend",
                        "viewport": "desktop",
                        "interaction_type": "hover",
                        "point_or_category": "Mar",
                        "series_name": "Actual",
                        "interaction_success": True,
                    }
                ],
                "observed_value_comparisons": [
                    {
                        "metric_id": "KPI-001",
                        "page_id": "executive_overview",
                        "visual_id": "visual_volume_trend",
                        "displayed_value": "5",
                        "manifest_value": "999",
                        "proof_value": "999",
                        "comparison_status": "PASS",
                    }
                ],
                "screenshots": [
                    {
                        "path": "reports/agent/10_presentation/llm_playwright_evidence/desktop.png",
                        "viewport": "desktop",
                    },
                    {
                        "path": "reports/agent/10_presentation/llm_playwright_evidence/tablet.png",
                        "viewport": "tablet",
                    },
                    {
                        "path": "reports/agent/10_presentation/llm_playwright_evidence/mobile.png",
                        "viewport": "mobile",
                    },
                ],
                "findings": [],
            }
            write_review_artifacts(root, payload)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_llm_playwright_review.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            blob = (proc.stdout + proc.stderr).lower()
            self.assertIn("independent value comparison fail", blob)


if __name__ == "__main__":
    unittest.main()
