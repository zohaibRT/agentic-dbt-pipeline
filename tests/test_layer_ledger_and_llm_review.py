#!/usr/bin/env python3
"""Tests for expanded layer ledger parsing and LLM Playwright MCP review gate."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIX_DBT = ROOT / "fixtures" / "dbt_duckdb" / "domain_a_transactional"

sys.path.insert(0, str(SCRIPTS))

from check_layer_proof_coverage import (  # noqa: E402
    is_expanded_schema,
    map_headers,
    validate_ledger,
)
from lib_llm_playwright_review import (  # noqa: E402
    compute_report_bundle_hash,
    write_review_artifacts,
)


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


EXPANDED_HEADER = (
    "| Phase | Layer | Model / Artifact | Expected Grain | Row Count | Upstream Comparison | "
    "Key / Grain Proof | Relationship Proof | Measure / KPI Proof | Privacy Check | "
    "Proof Files | dbt Command Result | Overall Status | Notes |"
)
EXPANDED_SEP = "|---|---|---|---|---:|---|---|---|---|---|---|---|---|---|"


def _write_proof(root: Path, rel: str = "reports/agent/03_bronze/sql_proofs/010_row_count.sql") -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("-- proof\nselect 1;\n", encoding="utf-8")
    return rel


def _expanded_ledger(root: Path, proof: str, status: str = "PASS") -> None:
    text = f"""# Layer Verification Ledger

{EXPANDED_HEADER}
{EXPANDED_SEP}
| 03_bronze | bronze/staging | stg_events | event | 5 | match | PASS | PASS | PASS | PASS | {proof} | PASS | {status} | ok |
"""
    path = root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class LayerLedgerTests(unittest.TestCase):
    def test_01_canonical_template_parses(self) -> None:
        headers = [
            "Phase",
            "Layer",
            "Model / Artifact",
            "Expected Grain",
            "Row Count",
            "Upstream Comparison",
            "Key / Grain Proof",
            "Relationship Proof",
            "Measure / KPI Proof",
            "Privacy Check",
            "Proof Files",
            "dbt Command Result",
            "Overall Status",
            "Notes",
        ]
        mapping = map_headers(headers)
        self.assertTrue(is_expanded_schema(mapping))

    def test_02_reordered_columns_parse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = _write_proof(root)
            text = f"""# Ledger

| Overall Status | Model / Artifact | Proof Files | Phase | Layer | Expected Grain | Row Count | Upstream Comparison | Key / Grain Proof | Relationship Proof | Measure / KPI Proof | Privacy Check | dbt Command Result | Notes |
|---|---|---|---|---|---|---:|---|---|---|---|---|---|---|
| PASS | stg_events | {proof} | 03_bronze | bronze/staging | event | 5 | match | PASS | PASS | PASS | PASS | PASS | ok |
"""
            (root / "reports" / "agent").mkdir(parents=True, exist_ok=True)
            (root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md").write_text(text, encoding="utf-8")
            errors, warnings, details = validate_ledger(root, phase="final")
            self.assertEqual(errors, [], errors)
            self.assertEqual(details["schema"], "expanded")

    def test_03_legacy_template_warns_outside_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = """# Ledger

| Phase | Model | Expected Grain | Row Count | Key Proof | Relationship Proof | Measure Proof | Privacy Proof | Status | Notes |
|---|---|---|---:|---|---|---|---|---|---|
| 03_bronze | stg_events | event | 5 | PASS | PASS | PASS | PASS | PASS | ok |
"""
            (root / "reports" / "agent").mkdir(parents=True, exist_ok=True)
            (root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md").write_text(text, encoding="utf-8")
            errors, warnings, details = validate_ledger(root, phase="analytics")
            self.assertEqual(errors, [], errors)
            self.assertTrue(any("legacy" in w.lower() for w in warnings), warnings)
            self.assertEqual(details["schema"], "legacy")

    def test_04_legacy_template_fails_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = """# Ledger

| Phase | Model | Expected Grain | Row Count | Key Proof | Relationship Proof | Measure Proof | Privacy Proof | Status | Notes |
|---|---|---|---:|---|---|---|---|---|---|
| 03_bronze | stg_events | event | 5 | PASS | PASS | PASS | PASS | PASS | ok |
"""
            (root / "reports" / "agent").mkdir(parents=True, exist_ok=True)
            (root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md").write_text(text, encoding="utf-8")
            errors, _warnings, _details = validate_ledger(root, phase="final")
            self.assertTrue(any("expanded" in e.lower() for e in errors), errors)

    def test_05_missing_proof_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _expanded_ledger(root, "reports/agent/03_bronze/sql_proofs/missing.sql", "PASS")
            errors, _w, _d = validate_ledger(root, phase="final")
            self.assertTrue(any("not found" in e.lower() for e in errors), errors)

    def test_06_invalid_status_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proof = _write_proof(root)
            _expanded_ledger(root, proof, "YEET")
            errors, _w, _d = validate_ledger(root, phase="final")
            self.assertTrue(any("invalid" in e.lower() for e in errors), errors)

    def test_07_pass_with_todo_proof_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _expanded_ledger(root, "TODO", "PASS")
            errors, _w, _d = validate_ledger(root, phase="final")
            self.assertTrue(any("missing proof" in e.lower() or "placeholder" in e.lower() for e in errors), errors)

    def test_08_empty_ledger_fails_when_models_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "models").mkdir(parents=True, exist_ok=True)
            (root / "models" / "stg_x.sql").write_text("select 1\n", encoding="utf-8")
            text = f"""# Ledger

{EXPANDED_HEADER}
{EXPANDED_SEP}
| TODO | TODO | TODO | TODO | 0 | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
"""
            (root / "reports" / "agent").mkdir(parents=True, exist_ok=True)
            (root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md").write_text(text, encoding="utf-8")
            errors, _w, _d = validate_ledger(root, phase="final")
            self.assertTrue(any("no applicable" in e.lower() for e in errors), errors)

    def test_09_multiple_proof_files_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p1 = _write_proof(root, "reports/agent/03_bronze/sql_proofs/a.sql")
            p2 = _write_proof(root, "reports/agent/03_bronze/sql_proofs/b.sql")
            text = f"""# Ledger

{EXPANDED_HEADER}
{EXPANDED_SEP}
| 03_bronze | bronze/staging | stg_events | event | 5 | match | PASS | PASS | PASS | PASS | {p1}, {p2} | PASS | PASS | ok |
"""
            (root / "reports" / "agent").mkdir(parents=True, exist_ok=True)
            (root / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md").write_text(text, encoding="utf-8")
            errors, _w, _d = validate_ledger(root, phase="final")
            self.assertEqual(errors, [], errors)

    def test_10_fixture_expanded_ledgers_pass(self) -> None:
        if not (FIX_DBT / "reports" / "agent" / "LAYER_VERIFICATION_LEDGER.md").exists():
            self.skipTest("duckdb fixture missing")
        proc = run_script(
            "check_layer_proof_coverage.py", "--root", str(FIX_DBT), "--phase", "final"
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


def _minimal_presentation(root: Path) -> None:
    base = root / "reports" / "agent" / "10_presentation"
    mpl = base / "matplotlib"
    mpl.mkdir(parents=True, exist_ok=True)
    (mpl / "report.html").write_text("<html><body>report</body></html>", encoding="utf-8")
    pages = {
        "pages": [
            {
                "page_id": "executive_overview",
                "page_name": "Executive",
                "visual_ids": ["visual_volume_trend"],
            }
        ]
    }
    charts = {
        "charts": [
            {
                "chart_id": "volume_trend",
                "visual_id": "visual_volume_trend",
                "page_id": "executive_overview",
                "series": [
                    {"name": "actual", "display_name": "Actual", "data": [{"period_label": "January 2026", "volume": 1}]},
                    {"name": "prior", "display_name": "Prior period", "data": [{"period_label": "January 2026", "volume": 1}]},
                ],
                "data": [
                    {"period_label": "January 2026", "volume": 1, "formatted_value": "1 events"},
                    {"period_label": "February 2026", "volume": 2, "formatted_value": "2 events"},
                    {"period_label": "March 2026", "volume": 3, "formatted_value": "3 events", "is_partial_period": True},
                ],
                "x_field": "period",
            }
        ]
    }
    manifest = {
        "metrics": [
            {
                "metric_id": "KPI-001",
                "display_name": "Volume KPI",
                "formatted_value": "3 events",
                "business_approval_status": "PENDING_REVIEW",
                "technical_validation_status": "PASS",
            }
        ]
    }
    (base / "page_registry.json").write_text(json.dumps(pages), encoding="utf-8")
    (base / "chart_registry.json").write_text(json.dumps(charts), encoding="utf-8")
    (base / "rendered_metric_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (base / "query_registry.json").write_text(json.dumps({"queries": []}), encoding="utf-8")
    (base / "proof_registry.json").write_text(json.dumps({"proofs": []}), encoding="utf-8")
    (root / "project.config.yml").write_text(
        """
presentation_policy:
  require_llm_playwright_review_at_final: true
  llm_playwright_review_required_for_release: true
  require_llm_review_artifact_freshness: true
  require_llm_review_page_coverage: 1.0
  require_llm_review_visual_coverage: 1.0
  llm_review_block_on_critical_findings: true
  llm_review_block_on_high_findings: true
  llm_playwright_review_applicability: required
  llm_review_viewports: [desktop, tablet, mobile]
""",
        encoding="utf-8",
    )


def _complete_review(root: Path, **overrides: object) -> dict:
    bundle, file_hashes = compute_report_bundle_hash(root)
    evidence = root / "reports" / "agent" / "10_presentation" / "llm_playwright_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    shot = evidence / "desktop_executive.png"
    shot.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    payload = {
        "schema_version": "1.0",
        "review_id": "LLM-REVIEW-TEST-001",
        "review_status": "PASS",
        "technical_verification_status": "PASS",
        "business_approval_status": "PENDING_REVIEW",
        "reviewed_at": "2026-07-16T12:00:00+00:00",
        "repository_commit_sha": "deadbeef",
        "dbt_invocation_id": None,
        "report_bundle_hash": bundle,
        "report_html_hash": file_hashes.get("report_html", "x"),
        "page_registry_hash": file_hashes.get("page_registry", "x"),
        "chart_registry_hash": file_hashes.get("chart_registry", "x"),
        "rendered_metric_manifest_hash": file_hashes.get("rendered_metric_manifest", "x"),
        "query_registry_hash": file_hashes.get("query_registry", "x"),
        "proof_registry_hash": file_hashes.get("proof_registry", "x"),
        "browser_runtime": "chromium",
        "mcp_server": "user-playwright",
        "llm_reviewer": "cursor-agent-test",
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
                "metric_ids": ["KPI-001"],
                "viewport": "desktop",
                "interaction_type": "hover",
                "point_or_category": "January 2026",
                "series_name": "Actual",
                "expected_tooltip_fields": ["Volume KPI", "January 2026"],
                "observed_tooltip_text": "Volume KPI — Actual\nJanuary 2026\n1 events",
                "interaction_success": True,
                "screenshot_path": "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png",
                "finding_ids": [],
            },
            {
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "chart_id": "volume_trend",
                "metric_ids": ["KPI-001"],
                "viewport": "desktop",
                "interaction_type": "hover",
                "point_or_category": "February 2026",
                "series_name": "Actual",
                "expected_tooltip_fields": ["February 2026"],
                "observed_tooltip_text": "Volume KPI — Actual\nFebruary 2026\n2 events",
                "interaction_success": True,
                "screenshot_path": "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png",
                "finding_ids": [],
            },
            {
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "chart_id": "volume_trend",
                "metric_ids": ["KPI-001"],
                "viewport": "desktop",
                "interaction_type": "hover",
                "point_or_category": "March 2026",
                "series_name": "Actual",
                "expected_tooltip_fields": ["March 2026"],
                "observed_tooltip_text": "Volume KPI — Actual\nMarch 2026\n3 events\nPartial",
                "interaction_success": True,
                "screenshot_path": "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png",
                "finding_ids": [],
            },
            {
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "chart_id": "volume_trend",
                "metric_ids": ["KPI-001"],
                "viewport": "desktop",
                "interaction_type": "hover",
                "point_or_category": "January 2026",
                "series_name": "Prior period",
                "expected_tooltip_fields": ["Prior period"],
                "observed_tooltip_text": "Volume KPI — Prior period\nJanuary 2026\n1 events",
                "interaction_success": True,
                "screenshot_path": "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png",
                "finding_ids": [],
            },
            {
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "chart_id": "volume_trend",
                "metric_ids": ["KPI-001"],
                "viewport": "mobile",
                "interaction_type": "tap",
                "point_or_category": "March 2026",
                "series_name": "Actual",
                "expected_tooltip_fields": ["March 2026"],
                "observed_tooltip_text": "Volume KPI — Actual\nMarch 2026\n3 events",
                "interaction_success": True,
                "screenshot_path": "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png",
                "finding_ids": [],
            },
            {
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "chart_id": "volume_trend",
                "metric_ids": ["KPI-001"],
                "viewport": "tablet",
                "interaction_type": "hover",
                "point_or_category": "March 2026",
                "series_name": "Actual",
                "expected_tooltip_fields": ["March 2026"],
                "observed_tooltip_text": "Volume KPI — Actual\nMarch 2026\n3 events",
                "interaction_success": True,
                "screenshot_path": "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png",
                "finding_ids": [],
            },
        ],
        "observed_value_comparisons": [
            {
                "metric_id": "KPI-001",
                "page_id": "executive_overview",
                "visual_id": "visual_volume_trend",
                "displayed_value": "3 events",
                "manifest_value": "3 events",
                "proof_value": "3 events",
                "formatting_rule": "integer+unit",
                "comparison_status": "PASS",
                "reason": "match",
            }
        ],
        "screenshots": [
            {"path": "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png", "viewport": "desktop"}
        ],
        "findings": [],
        "unresolved_critical_findings": [],
        "unresolved_high_findings": [],
        "limitations": ["Fixture synthetic presentation for unit tests"],
        "notes": "unit test review",
    }
    payload.update(overrides)
    write_review_artifacts(root, payload)
    return payload


class LlmPlaywrightReviewTests(unittest.TestCase):
    def test_01_missing_review_fails_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("missing LLM Playwright review", proc.stdout + proc.stderr)

    def test_02_missing_review_ok_draft(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_03_deterministic_pass_does_not_replace_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            # Fake live DOM PASS artifact without LLM review
            (root / "reports/agent/10_presentation/LIVE_REPORT_DOM_REPORT.json").write_text(
                json.dumps({"status": "PASS"}), encoding="utf-8"
            )
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("does not replace", proc.stdout + proc.stderr)

    def test_04_stale_bundle_hash_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root, report_bundle_hash="stalehash")
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("stale", (proc.stdout + proc.stderr).lower())

    def test_05_missing_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root, reviewed_page_ids=[], page_coverage=0.0)
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)

    def test_06_missing_visual_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root, reviewed_visual_ids=[], visual_coverage=0.0)
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)

    def test_07_missing_screenshot_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            payload = _complete_review(root)
            # Delete screenshot after write
            shot = root / "reports/agent/10_presentation/llm_playwright_evidence/desktop_executive.png"
            shot.unlink()
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("screenshot", (proc.stdout + proc.stderr).lower())

    def test_08_unknown_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root, reviewed_page_ids=["executive_overview", "ghost_page"])
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("unknown reviewed page", (proc.stdout + proc.stderr).lower())

    def test_09_unknown_visual_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(
                root,
                reviewed_visual_ids=["visual_volume_trend", "volume_trend", "ghost_visual"],
            )
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("unknown reviewed visual", (proc.stdout + proc.stderr).lower())

    def test_10_missing_desktop_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root, tested_viewports=["tablet", "mobile"])
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("desktop", (proc.stdout + proc.stderr).lower())

    def test_11_missing_mobile_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root, tested_viewports=["desktop", "tablet"])
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("mobile", (proc.stdout + proc.stderr).lower())

    def test_12_missing_multiseries_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            payload = _complete_review(root)
            # Drop Prior period interactions
            payload["interactions"] = [
                i for i in payload["interactions"] if i.get("series_name") != "Prior period"
            ]
            write_review_artifacts(root, payload)
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("multi-series", (proc.stdout + proc.stderr).lower())

    def test_13_missing_critical_period_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            payload = _complete_review(root)
            payload["interactions"] = [
                i for i in payload["interactions"] if i.get("point_or_category") == "January 2026"
            ]
            write_review_artifacts(root, payload)
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("critical-period", (proc.stdout + proc.stderr).lower())

    def test_14_unresolved_high_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(
                root,
                findings=[
                    {
                        "finding_id": "F-H1",
                        "severity": "HIGH",
                        "category": "usability",
                        "page_id": "executive_overview",
                        "visual_id": "visual_volume_trend",
                        "description": "clipping",
                        "expected_behavior": "readable",
                        "observed_behavior": "clipped",
                        "evidence": "",
                        "recommended_action": "fix layout",
                        "resolution_status": "OPEN",
                    }
                ],
                unresolved_high_findings=["F-H1"],
                review_status="WARN",
            )
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("HIGH", proc.stdout + proc.stderr)

    def test_15_unresolved_critical_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(
                root,
                findings=[
                    {
                        "finding_id": "F-C1",
                        "severity": "CRITICAL",
                        "category": "data",
                        "page_id": "executive_overview",
                        "visual_id": "visual_volume_trend",
                        "description": "wrong value",
                        "expected_behavior": "match proof",
                        "observed_behavior": "mismatch",
                        "evidence": "",
                        "recommended_action": "fix",
                        "resolution_status": "OPEN",
                    }
                ],
                unresolved_critical_findings=["F-C1"],
                review_status="FAIL",
            )
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("CRITICAL", proc.stdout + proc.stderr)

    def test_16_warn_medium_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(
                root,
                review_status="WARN",
                findings=[
                    {
                        "finding_id": "F-M1",
                        "severity": "MEDIUM",
                        "category": "style",
                        "page_id": "executive_overview",
                        "visual_id": "visual_volume_trend",
                        "description": "tight spacing",
                        "expected_behavior": "comfortable",
                        "observed_behavior": "tight",
                        "evidence": "",
                        "recommended_action": "adjust",
                        "resolution_status": "OPEN",
                    }
                ],
            )
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("WARN", proc.stdout)

    def test_17_business_approval_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            payload = _complete_review(root, business_approval_status="PENDING_REVIEW")
            self.assertEqual(payload["business_approval_status"], "PENDING_REVIEW")
            self.assertEqual(payload["technical_verification_status"], "PASS")
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_18_synthetic_outside_fixtures_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root, notes="SYNTHETIC FIXTURE — NOT A REAL MCP REVIEW")
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("synthetic", (proc.stdout + proc.stderr).lower())

    def test_19_fixture_applicability_skip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Must be under a fixtures/ path segment
            root = Path(tmp) / "fixtures" / "demo"
            root.mkdir(parents=True, exist_ok=True)
            _minimal_presentation(root)
            (root / "project.config.yml").write_text(
                "presentation_policy:\n  llm_playwright_review_applicability: not_applicable_fixture\n",
                encoding="utf-8",
            )
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("SKIPPED", proc.stdout)

    def test_20_complete_review_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _minimal_presentation(root)
            _complete_review(root)
            proc = run_script("check_llm_playwright_review.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
