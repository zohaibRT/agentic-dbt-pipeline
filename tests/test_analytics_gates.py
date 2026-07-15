#!/usr/bin/env python3
"""Unit tests for domain-neutral analytics gate scripts and multi-domain fixtures."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIX = ROOT / "fixtures" / "analytics"


def run_script(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd, cwd=str(cwd or SCRIPTS), capture_output=True, text=True)


class DomainNeutralityTests(unittest.TestCase):
    def test_skill_domain_neutrality_passes(self) -> None:
        proc = run_script("check_domain_neutrality.py", "--root", str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class MultiDomainFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        proc = run_script("build_analytics_fixtures.py", cwd=ROOT)
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout + proc.stderr)

    def test_fixtures_exist(self) -> None:
        expected = [
            "domain_a_transactional",
            "domain_b_encounter",
            "domain_c_asset_events",
            "domain_d_case_activity",
        ]
        for slug in expected:
            self.assertTrue((FIX / slug).exists(), slug)

    def test_validators_pass_each_fixture(self) -> None:
        checks = [
            "check_analytics_coverage.py",
            "check_analytics_product_completeness.py",
            "check_fact_analytical_coverage.py",
            "check_model_classification_coverage.py",
            "check_metric_contract_completeness.py",
            "check_time_intelligence_coverage.py",
            "check_data_observability_coverage.py",
            "check_presentation_coverage.py",
            "check_report_page_contracts.py",
            "check_report_business_readability.py",
            "check_exposure_coverage.py",
        ]
        for slug in (
            "domain_a_transactional",
            "domain_b_encounter",
            "domain_c_asset_events",
            "domain_d_case_activity",
        ):
            root = FIX / slug
            for script in checks:
                with self.subTest(fixture=slug, script=script):
                    proc = run_script(script, "--root", str(root))
                    self.assertEqual(
                        proc.returncode,
                        0,
                        f"{slug} {script}\n{proc.stdout}\n{proc.stderr}",
                    )

    def test_no_cross_fixture_industry_leak_requirement(self) -> None:
        """Encounter fixture must not require commerce-only entities."""
        text = (FIX / "domain_b_encounter" / "reports" / "agent" / "09_analytics_insights" / "analytics_coverage_matrix.md").read_text(
            encoding="utf-8"
        ).lower()
        self.assertIn("encounter", text)
        self.assertNotIn("subscription", text)
        self.assertNotIn("sku", text)


class PresentationReadabilityGateTests(unittest.TestCase):
    def test_legacy_sql_dump_board_fails_readability(self) -> None:
        # Use a temp-like fixture under fixtures/analytics/_bad_sql_dump
        bad = FIX / "_bad_sql_dump"
        matplotlib = bad / "reports" / "agent" / "10_presentation" / "matplotlib"
        matplotlib.mkdir(parents=True, exist_ok=True)
        (matplotlib / "report.html").write_text(
            """
            <h1>All Measures</h1>
            <table>
            <tr><th>Name</th><th>Live value</th></tr>
            <tr><td>dim_programs_row_count</td><td>30</td></tr>
            <tr><td>active_operating_share_of_subscriptions</td><td>0.2611111111111111</td></tr>
            <tr><td>avg_order_amount_sar</td><td>4037.6045379548</td></tr>
            <tr><td>orders_orphan_rate</td><td>0.09642834881256623</td></tr>
            <tr><td>crm_paid_rate</td><td>0.06386885833296009</td></tr>
            <tr><td>crm_failed_rate</td><td>0.27392842746450485</td></tr>
            <tr><td>avg_crm_payment_amount_sar</td><td>484.9132024006808</td></tr>
            <tr><td>invoice_avg_total_amount</td><td>809.2809532215357</td></tr>
            </table>
            """,
            encoding="utf-8",
        )
        (matplotlib / "report_builder.py").write_text("tabs = ['All Measures']\n", encoding="utf-8")
        proc = run_script("check_report_business_readability.py", "--root", str(bad))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
