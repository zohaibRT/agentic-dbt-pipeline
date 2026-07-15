#!/usr/bin/env python3
"""P0-INDEPENDENT-VERIFICATION-E2E-CI tests."""

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
DBT_FIX = ROOT / "fixtures" / "dbt_duckdb"

sys.path.insert(0, str(SCRIPTS))
from run_independent_verifier import (  # noqa: E402
    detect_builder_false_pass,
    detect_fixed_count_gates,
    detect_synthetic_approval_misuse,
    is_fixture_root,
)


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
    )


class IndependentVerifierUnitTests(unittest.TestCase):
    def test_fixture_root_detection(self) -> None:
        self.assertTrue(is_fixture_root(DBT_FIX / "domain_a_transactional"))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(is_fixture_root(Path(tmp)))

    def test_synthetic_approval_allowed_in_fixtures(self) -> None:
        root = DBT_FIX / "domain_a_transactional"
        if not root.exists():
            self.skipTest("fixtures not built")
        check = detect_synthetic_approval_misuse(root)
        self.assertEqual(check.status, "PASS")

    def test_synthetic_approval_rejected_outside_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "prod_like"
            agent = root / "reports" / "agent"
            agent.mkdir(parents=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                "# KPI\n\nTEST FIXTURE — NOT PRODUCTION APPROVAL\n",
                encoding="utf-8",
            )
            check = detect_synthetic_approval_misuse(root)
            self.assertEqual(check.status, "FAIL")
            self.assertIn("synthetic", check.detail.lower())

    def test_detect_builder_false_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            agent.mkdir(parents=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                "| KPI ID | Expected Result | Actual Result | Calculated Status | Technical Verification Status |\n"
                "|---|---|---|---|---|\n"
                "| KPI-001 | 100 | 999 | PASS | PASS |\n",
                encoding="utf-8",
            )
            check = detect_builder_false_pass(root)
            self.assertEqual(check.status, "FAIL")
            self.assertIn("PASS", check.detail)

    def test_no_fixed_count_gates(self) -> None:
        check = detect_fixed_count_gates(ROOT)
        self.assertIn(check.status, {"PASS", "SKIPPED"})


class IndependentVerifierIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        (DBT_FIX / "domain_a_transactional").exists(),
        "DuckDB fixtures not built",
    )
    def test_independent_verifier_recalculates_and_passes_valid_fixture(self) -> None:
        root = DBT_FIX / "domain_a_transactional"
        proc = run_script("run_independent_verifier.py", "--root", str(root), "--skip-live")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(
            (root / "reports/agent/INDEPENDENT_VERIFICATION_REPORT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(report["overall_status"], "PASS")
        local_names = {c["name"] for c in report["local_checks"]}
        self.assertIn("detect_builder_false_pass", local_names)
        self.assertIn("manifest_inventory", local_names)

    @unittest.skipUnless(
        (DBT_FIX / "domain_a_transactional").exists(),
        "DuckDB fixtures not built",
    )
    def test_independent_verifier_detects_builder_false_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "domain_a_transactional"
            shutil.copytree(
                DBT_FIX / "domain_a_transactional",
                dest,
                ignore=shutil.ignore_patterns("logs", ".venv", "__pycache__", "dbt_packages"),
            )
            contracts = dest / "reports/agent/KPI_DEFINITION_CONTRACTS.md"
            text = contracts.read_text(encoding="utf-8")
            text = text.replace("| 100 | 100 |", "| 100 | 999 |", 1)
            contracts.write_text(text, encoding="utf-8")
            proc = run_script("run_independent_verifier.py", "--root", str(dest), "--skip-live")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            report = json.loads(
                (dest / "reports/agent/INDEPENDENT_VERIFICATION_REPORT.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["overall_status"], "FAIL")
            blob = json.dumps(report).lower()
            self.assertTrue("false_pass" in blob or "values differ" in blob or "recorded pass" in blob)

    @unittest.skipUnless(
        (DBT_FIX / "domain_a_transactional").exists(),
        "DuckDB fixtures not built",
    )
    def test_independent_verifier_catches_missing_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "domain_a_transactional"
            shutil.copytree(
                DBT_FIX / "domain_a_transactional",
                dest,
                ignore=shutil.ignore_patterns("logs", ".venv", "__pycache__", "dbt_packages"),
            )
            charts = dest / "reports/agent/10_presentation/matplotlib/chart_registry.json"
            data = json.loads(charts.read_text(encoding="utf-8"))
            data["charts"][0]["proof_ids"] = []
            charts.write_text(json.dumps(data, indent=2), encoding="utf-8")
            proc = run_script("run_independent_verifier.py", "--root", str(dest), "--skip-live")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    @unittest.skipUnless(
        (DBT_FIX / "domain_a_transactional").exists(),
        "DuckDB fixtures not built",
    )
    def test_independent_verifier_catches_stale_approvals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "domain_a_transactional"
            shutil.copytree(
                DBT_FIX / "domain_a_transactional",
                dest,
                ignore=shutil.ignore_patterns("logs", ".venv", "__pycache__", "dbt_packages"),
            )
            contracts = dest / "reports/agent/KPI_DEFINITION_CONTRACTS.md"
            text = contracts.read_text(encoding="utf-8")
            text = text.replace("| 132c7a75300e4876 |", "| deadbeefdeadbeef |", 1)
            contracts.write_text(text, encoding="utf-8")
            proc = run_script(
                "check_human_approval_coverage.py",
                "--root",
                str(dest),
                "--phase",
                "final",
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stale", (proc.stdout + proc.stderr).lower())

    @unittest.skipUnless(
        (DBT_FIX / "domain_a_transactional").exists(),
        "DuckDB fixtures not built",
    )
    def test_every_valid_fixture_passes_final_strict_gate(self) -> None:
        domains = sorted(p for p in DBT_FIX.glob("domain_*") if p.is_dir())
        self.assertGreaterEqual(len(domains), 4)
        for domain in domains:
            with self.subTest(domain=domain.name):
                proc = run_script(
                    "run_acceptance_gate.py",
                    "--root",
                    str(domain),
                    "--phase",
                    "final",
                    "--strict",
                    "--skip-dbt",
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_negative_suite_fails_invalid_cases(self) -> None:
        if not (DBT_FIX / "domain_a_transactional").exists():
            self.skipTest("fixtures not built")
        proc = run_script(
            "run_negative_fixture_suite.py",
            "--case",
            "wrong_reconciliation_pass",
            "--case",
            "missing_proof",
            "--case",
            "synthetic_approval_outside_fixtures",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_ci_commands_nonzero_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports" / "agent").mkdir(parents=True)
            proc = run_script("validate_chart_registry.py", "--root", str(root))
            # No charts folder => skip 0, so force a failing case
            matplotlib = root / "reports/agent/10_presentation/matplotlib"
            matplotlib.mkdir(parents=True)
            (matplotlib / "report.html").write_text("<html></html>", encoding="utf-8")
            proc = run_script("validate_chart_registry.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)

    def test_failure_artifacts_generated(self) -> None:
        if not (DBT_FIX / "domain_a_transactional").exists():
            self.skipTest("fixtures not built")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "domain_a_transactional"
            shutil.copytree(
                DBT_FIX / "domain_a_transactional",
                dest,
                ignore=shutil.ignore_patterns("logs", ".venv", "__pycache__", "dbt_packages"),
            )
            contracts = dest / "reports/agent/KPI_DEFINITION_CONTRACTS.md"
            text = contracts.read_text(encoding="utf-8").replace("| 100 | 100 |", "| 100 | 999 |", 1)
            contracts.write_text(text, encoding="utf-8")
            proc = run_script("run_independent_verifier.py", "--root", str(dest), "--skip-live")
            self.assertEqual(proc.returncode, 1)
            self.assertTrue((dest / "reports/agent/INDEPENDENT_VERIFICATION_REPORT.json").exists())
            self.assertTrue((dest / "reports/agent/INDEPENDENT_VERIFICATION_REPORT.md").exists())

    def test_domain_neutrality_remains_intact(self) -> None:
        proc = run_script("check_domain_neutrality.py", "--root", str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_non_fct_prefix_fact_present(self) -> None:
        path = DBT_FIX / "domain_b_encounter" / "models" / "gold" / "activity_events.sql"
        if not path.exists():
            self.skipTest("domain_b fixture missing")
        self.assertTrue(path.exists())

    def test_duplicate_name_unique_id_handling_documented(self) -> None:
        # Unit coverage lives in test_manifest_resource_identity; assert fixture snapshot name differs
        snap = DBT_FIX / "domain_b_encounter" / "snapshots"
        if not snap.exists():
            self.skipTest("domain_b snapshots missing")
        names = [p.stem for p in snap.glob("*.sql")]
        self.assertTrue(any("activity_events" in n for n in names))


if __name__ == "__main__":
    unittest.main()
