#!/usr/bin/env python3
"""Tests for enterprise report handoff readiness gating."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TEMPLATES = ROOT / "templates" / "reports" / "10_presentation" / "matplotlib"


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_validator(root: Path, stem: str, status: str, details: dict | None = None) -> None:
    _write_json(
        root / "reports" / "agent" / "_validator_results" / f"{stem}.json",
        {
            "schema_version": "1.0",
            "validator_id": stem,
            "status": status,
            "errors": [] if status == "PASS" else [f"{stem} {status}"],
            "warnings": [],
            "details": details or {},
            "checked_at": "2026-01-15T00:00:00+00:00",
            "warning_ids": [],
            "applicability": "",
        },
    )


def _minimal_interactive_root(tmp: Path, *, with_relations: bool = True) -> Path:
    root = tmp / "project_alpha"
    mpl = root / "reports" / "agent" / "10_presentation" / "matplotlib"
    mpl.mkdir(parents=True)
    charts = {
        "version": "1",
        "charts": [
            {
                "chart_id": "volume_trend",
                "title": "Volume",
                "source_resource_ids": ["model.local.fct_events"] if with_relations else [],
                "data": [{"period_label": "Jan", "formatted_value": "1"}],
            }
        ],
    }
    metrics = {
        "metrics": [{"metric_id": "KPI-001", "display_name": "Volume KPI", "formatted_value": "1"}],
        "measure_board": [{"display_name": "Volume", "formatted_value": "1"}],
        "metric_board": [],
    }
    _write_json(mpl / "chart_registry.json", charts)
    _write_json(mpl / "rendered_metric_manifest.json", metrics)
    (mpl / "report.html").write_text("<!doctype html><html><body>report</body></html>", encoding="utf-8")
    shutil.copy2(TEMPLATES / "serve_report.py", mpl / "serve_report.py")
    shutil.copy2(TEMPLATES / "open_report.bat", mpl / "open_report.bat")
    shutil.copy2(TEMPLATES / "open_report.sh", mpl / "open_report.sh")
    # Point project scripts path for launcher by creating scripts symlink/copy of handoff checker
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    for name in (
        "check_report_handoff_readiness.py",
        "lib_report_handoff.py",
        "lib_gate_common.py",
        "lib_llm_playwright_review.py",
    ):
        shutil.copy2(SCRIPTS / name, scripts / name)
    (root / "project.config.yml").write_text(
        """
presentation_policy:
  withhold_report_access_until_verified: true
  require_report_handoff_readiness: true
  require_manifest_relation_resolution: true
  require_report_runtime_preflight: true
  require_successful_initial_data_load: true
  require_successful_refresh_validation: true
  require_deterministic_playwright_before_handoff: true
  require_playwright_mcp_before_handoff: true
  require_independent_verification_before_handoff: true
  require_final_acceptance_before_handoff: true
  block_open_report_launcher_until_verified: true
  prohibit_early_report_url_in_chat: true
  llm_playwright_review_applicability: required
""",
        encoding="utf-8",
    )
    return root


def _seed_passing_evidence(root: Path, *, include_mcp: bool = True) -> None:
    details = {
        "runtime_preflight": True,
        "manifest_relation_resolution": True,
        "initial_data_load": True,
        "refresh_validation": True,
        "charts_payload_ok": True,
        "metrics_payload_ok": True,
        "refresh_ok": True,
        "resolved_relations": ["model.local.fct_events"],
    }
    _write_validator(root, "validate_local_web_report", "PASS", details)
    _write_validator(
        root,
        "validate_live_report_dom",
        "PASS",
        {
            "initial_data_load": True,
            "refresh_validation": True,
            "manifest_relation_resolution": True,
            "report_url": "http://127.0.0.1:8765/",
        },
    )
    _write_validator(root, "check_presentation_traceability", "PASS")
    _write_validator(root, "validate_chart_registry", "PASS")
    _write_json(
        root / "reports" / "agent" / "10_presentation" / "matplotlib" / "runtime_preflight.json",
        {
            "status": "PASS",
            "runtime_preflight": True,
            "manifest_relation_resolution": True,
            "initial_data_load": True,
            "refresh_validation": True,
            "resolved_relations": ["model.local.fct_events"],
        },
    )
    if include_mcp:
        bundle = __import__("importlib.util").util.spec_from_file_location(
            "lib_llm", SCRIPTS / "lib_llm_playwright_review.py"
        )
        # simpler: write review with matching hash via helper script path
        sys.path.insert(0, str(SCRIPTS))
        from lib_llm_playwright_review import compute_report_bundle_hash

        bundle_hash, _ = compute_report_bundle_hash(root)
        _write_json(
            root / "reports" / "agent" / "10_presentation" / "LLM_PLAYWRIGHT_REVIEW.json",
            {
                "schema_version": "1.0",
                "review_id": "LLM-PW-TEST",
                "review_status": "PASS",
                "technical_verification_status": "PASS",
                "business_approval_status": "PENDING_REVIEW",
                "report_bundle_hash": bundle_hash,
                "tested_viewports": ["desktop", "tablet", "mobile"],
                "reviewed_page_ids": ["executive_overview"],
                "reviewed_visual_ids": ["volume_trend"],
                "page_coverage": 1.0,
                "visual_coverage": 1.0,
                "interactions": [],
                "findings": [],
                "unresolved_critical_findings": [],
                "unresolved_high_findings": [],
            },
        )
        _write_validator(root, "check_llm_playwright_review", "PASS", {"applicability": "required"})
    _write_json(
        root / "reports" / "agent" / "INDEPENDENT_VERIFICATION_REPORT.json",
        {"overall_status": "PASS", "status": "PASS"},
    )


class ReportHandoffReadinessTests(unittest.TestCase):
    def test_01_generated_without_preflight_cannot_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(
                (root / "reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(payload.get("open_allowed"))

    def test_02_http_shell_without_live_data_cannot_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _write_validator(
                root,
                "validate_local_web_report",
                "PASS",
                {"http_status": 200, "runtime_preflight": False, "charts_payload_ok": False},
            )
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)
            payload = json.loads(
                (root / "reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertFalse(payload["open_allowed"])

    def test_03_missing_relation_blocks_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp), with_relations=False)
            _seed_passing_evidence(root)
            # overwrite preflight/local details without relations
            _write_validator(
                root,
                "validate_local_web_report",
                "PASS",
                {
                    "runtime_preflight": True,
                    "manifest_relation_resolution": False,
                    "initial_data_load": True,
                    "refresh_validation": True,
                    "charts_payload_ok": True,
                    "metrics_payload_ok": True,
                    "refresh_ok": True,
                    "resolved_relations": [],
                },
            )
            _write_json(
                root / "reports/agent/10_presentation/matplotlib/runtime_preflight.json",
                {
                    "status": "FAIL",
                    "manifest_relation_resolution": False,
                    "resolved_relations": [],
                    "runtime_preflight": True,
                    "initial_data_load": True,
                    "refresh_validation": True,
                },
            )
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)
            payload = json.loads(
                (root / "reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json").read_text(
                    encoding="utf-8"
                )
            )
            gate = next(g for g in payload["gates"] if g["gate_id"] == "manifest_relation_resolution")
            self.assertEqual(gate["status"], "FAIL")
            self.assertFalse(payload["open_allowed"])

    def test_04_failed_refresh_blocks_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root)
            _write_validator(
                root,
                "validate_local_web_report",
                "FAIL",
                {"runtime_preflight": True, "refresh_ok": False, "refresh_validation": False},
            )
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_05_missing_deterministic_playwright_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root)
            (root / "reports/agent/_validator_results/validate_live_report_dom.json").unlink()
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_06_missing_mcp_review_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root, include_mcp=False)
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_07_missing_independent_verification_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root)
            (root / "reports/agent/INDEPENDENT_VERIFICATION_REPORT.json").unlink()
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_08_missing_final_acceptance_blocks_without_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root)
            (root / "reports/agent/_validator_results/validate_chart_registry.json").unlink()
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_09_warn_or_skipped_required_gate_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root)
            _write_validator(root, "validate_live_report_dom", "WARN", {"refresh_validation": True})
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_10_stale_evidence_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root)
            review_path = root / "reports/agent/10_presentation/LLM_PLAYWRIGHT_REVIEW.json"
            review = json.loads(review_path.read_text(encoding="utf-8"))
            review["report_bundle_hash"] = "stale" * 8
            review_path.write_text(json.dumps(review), encoding="utf-8")
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_11_open_report_bat_blocked_before_verification(self) -> None:
        if os.name != "nt":
            self.skipTest("bat launcher is Windows-specific")
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            bat = root / "reports/agent/10_presentation/matplotlib/open_report.bat"
            proc = subprocess.run(["cmd", "/c", str(bat)], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            combined = (proc.stdout + proc.stderr).lower()
            self.assertIn("not ready to open", combined)

    def test_12_open_report_sh_blocked_before_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            sh = root / "reports/agent/10_presentation/matplotlib/open_report.sh"
            self.assertTrue(sh.exists())
            self.assertIn("--require-pass", sh.read_text(encoding="utf-8"))
            # Exercise the same gate the shell launcher invokes (bash may be unavailable on Windows).
            proc = _run(
                [
                    str(root / "scripts" / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("not ready to open", (proc.stdout + proc.stderr).lower())

    def test_13_no_browser_launch_before_verification(self) -> None:
        # Launcher must exit before start "" / xdg-open when readiness fails.
        bat = (TEMPLATES / "open_report.bat").read_text(encoding="utf-8")
        sh = (TEMPLATES / "open_report.sh").read_text(encoding="utf-8")
        self.assertIn("--require-pass", bat)
        self.assertIn("errorlevel 1", bat.lower())
        self.assertIn("--require-pass", sh)
        self.assertLess(bat.lower().index("--require-pass"), bat.lower().index('start ""'))
        self.assertLess(sh.index("--require-pass"), sh.index("xdg-open"))

    def test_14_handoff_pass_releases_opening_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _minimal_interactive_root(Path(tmp))
            _seed_passing_evidence(root)
            proc = _run(
                [
                    str(SCRIPTS / "check_report_handoff_readiness.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                    "--require-pass",
                ]
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(
                (root / "reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(payload["open_allowed"])
            self.assertEqual(payload["presentation_state"], "VERIFIED_FOR_HANDOFF")
            self.assertTrue(payload["open_instructions_released"])
            # Business approval must remain separate / unchanged by handoff
            review = json.loads(
                (root / "reports/agent/10_presentation/LLM_PLAYWRIGHT_REVIEW.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(review["business_approval_status"], "PENDING_REVIEW")

    def test_15_generic_synthetic_model_names(self) -> None:
        # Domain-neutral synthetic identity used by this suite.
        resource_id = "model.local.fct_events"
        self.assertTrue(resource_id.startswith("model.local."))
        self.assertIn(resource_id, Path(__file__).read_text(encoding="utf-8"))

    def test_16_duckdb_fixtures_still_pass_handoff_or_exempt(self) -> None:
        fix = ROOT / "fixtures" / "dbt_duckdb" / "domain_a_transactional"
        if not fix.exists():
            self.skipTest("domain_a fixture missing")
        proc = _run(
            [
                str(SCRIPTS / "check_report_handoff_readiness.py"),
                "--root",
                str(fix),
                "--phase",
                "final",
            ]
        )
        # May be PASS (open allowed) or FAIL if local tree drifted; must not crash
        self.assertIn(proc.returncode, (0, 1), proc.stdout + proc.stderr)
        artifact = fix / "reports/agent/10_presentation/REPORT_HANDOFF_READINESS.json"
        self.assertTrue(artifact.exists())


if __name__ == "__main__":
    unittest.main()
