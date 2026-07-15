#!/usr/bin/env python3
"""Unit tests for domain-neutral analytics gate scripts and multi-domain fixtures."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIX = ROOT / "fixtures" / "analytics"
DBT_FIX = ROOT / "fixtures" / "dbt_duckdb"

sys.path.insert(0, str(SCRIPTS))
from lib_gate_common import named_status, ratio, list_gold_fact_names  # noqa: E402
from verify_metric_reconciliation import detect_contract_schema  # noqa: E402
from tests.test_manifest_resource_identity import (  # noqa: E402,F401
    CanonicalIdentityTests,
    ClassificationPolicyTests,
    CoverageRegressionTests,
    ExposureTests,
    FactDiscoveryTests,
    ManifestInventoryTests,
)
from tests.test_presentation_traceability import PresentationTraceabilityTests  # noqa: E402,F401


def run_script(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd, cwd=str(cwd or SCRIPTS), capture_output=True, text=True)


class HumanApprovalGateTests(unittest.TestCase):
    def test_human_approval_script_passes_analytics_fixtures(self) -> None:
        for slug in ("domain_a_transactional", "domain_d_case_activity"):
            proc = run_script(
                "check_human_approval_coverage.py",
                "--root",
                str(FIX / slug),
                "--phase",
                "analytics",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_fingerprint_ignores_display_name(self) -> None:
        from lib_gate_common import compute_contract_fingerprint

        a = compute_contract_fingerprint({"formula": "count(*)", "business_definition": "volume", "display_name": "A"})
        b = compute_contract_fingerprint({"formula": "count(*)", "business_definition": "volume", "display_name": "B"})
        self.assertEqual(a, b)


class DomainNeutralityTests(unittest.TestCase):
    def test_skill_domain_neutrality_passes(self) -> None:
        proc = run_script("check_domain_neutrality.py", "--root", str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_detects_hardcoded_required_model_in_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "references").mkdir()
            bad = root / "references" / "bad-requirement.md"
            bad.write_text(
                "Agents must build dim_customer and fct_orders for every project.\n",
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            proc = run_script("check_domain_neutrality.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("hardcoded", (proc.stdout + proc.stderr).lower())


class SharedHelperTests(unittest.TestCase):
    def test_empty_ratio_is_not_complete(self) -> None:
        self.assertIsNone(ratio(0, 0))
        self.assertEqual(ratio(1, 2), 0.5)

    def test_named_status_ignores_approval_cells(self) -> None:
        row = {
            "approval": "APPROVED",
            "status": "BLOCKED",
            "notes": "SUPPORTED",
        }
        self.assertEqual(named_status(row), "FAIL")


class ReconciliationHeaderTests(unittest.TestCase):
    def test_detects_expanded_schema(self) -> None:
        headers = [
            "KPI ID",
            "Display Name",
            "Business Question",
            "Counting Key",
            "Decision Supported",
            "Business Definition",
            "Validation Type",
            "SQL Proof",
            "Expected",
            "Actual",
            "Approval",
            "Verification",
        ]
        self.assertEqual(detect_contract_schema(headers), "expanded")

    def test_legacy_schema_detection(self) -> None:
        headers = [
            "KPI",
            "Business meaning",
            "Source model",
            "Grain",
            "SQL proof",
            "Expected",
            "Actual",
            "Approval status",
            "Verification status",
        ]
        self.assertEqual(detect_contract_schema(headers), "legacy_with_verification")

    def test_expanded_contract_passes_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            proofs = agent / "sql_proofs"
            proofs.mkdir(parents=True)
            (proofs / "a.sql").write_text(
                "-- purpose: test\n-- expected result: 1\n-- captured result: 1\n-- status: PASS\nselect 1;\n",
                encoding="utf-8",
            )
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """
| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Unit/Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-1 | Volume | kpi | p | How many? | Plan | Fix | o | count(*) | e | id | d | occurred | all | none | s | count | integer | additive | Target not defined | increase | fct | path | reports/agent/sql_proofs/a.sql | 1 | 1 | 0 | APPROVED | PASS | ok |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (agent / "METRIC_VERIFICATION_MATRIX.md").write_text(
                """
| Metric | Source Proof | Current Model Proof | Expected Result | Actual Result | Diff | Status | Notes |
|---|---|---|---|---|---|---|---|
| Volume | reports/agent/sql_proofs/a.sql | reports/agent/sql_proofs/a.sql | 1 | 1 | 0 | PASS | ok |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("expanded", proc.stdout)


class MetricContractRowAwareTests(unittest.TestCase):
    def test_split_fields_across_rows_fail(self) -> None:
        """Global keyword scan would pass; per-row validation must fail."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            agent.mkdir(parents=True)
            (root / "reports" / "agent" / "09_analytics_insights").mkdir(parents=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """
| KPI ID | Display Name | Business Question | Decision Supported | Action When Bad | Owner | Grain | Counting Key | SQL Proof | Approval | Verification |
|---|---|---|---|---|---|---|---|---|---|---|
| KPI-A | Alpha | What is volume? | | | analytics | event | id | reports/agent/a.sql | APPROVED | PASS |
| KPI-B | Beta | | Capacity | Investigate | | event | id | reports/agent/b.sql | APPROVED | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  critical_kpi_contract_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


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
            "verify_metric_reconciliation.py",
            "validate_chart_registry.py",
            "check_presentation_traceability.py",
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
            report_html = root / "reports" / "agent" / "10_presentation" / "matplotlib" / "report.html"
            if report_html.exists():
                with self.subTest(fixture=slug, script="validate_rendered_report_content.py"):
                    proc = run_script("validate_rendered_report_content.py", "--root", str(root))
                    self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_no_cross_fixture_industry_leak_requirement(self) -> None:
        text = (
            FIX
            / "domain_b_encounter"
            / "reports"
            / "agent"
            / "09_analytics_insights"
            / "analytics_coverage_matrix.md"
        ).read_text(encoding="utf-8").lower()
        self.assertIn("encounter", text)
        self.assertNotIn("subscription", text)
        self.assertNotIn("sku", text)


class PresentationReadabilityGateTests(unittest.TestCase):
    def test_legacy_sql_dump_board_fails_readability(self) -> None:
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


class DuckDbFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        proc = run_script("build_dbt_duckdb_fixtures.py", cwd=ROOT)
        if proc.returncode != 0:
            raise RuntimeError(proc.stdout + proc.stderr)

    def test_dbt_fixtures_exist(self) -> None:
        for slug in (
            "domain_a_transactional",
            "domain_b_encounter",
            "domain_c_asset_events",
            "domain_d_case_activity",
        ):
            self.assertTrue((DBT_FIX / slug / "dbt_project.yml").exists(), slug)

    def test_activity_events_fact_detected_in_domain_b(self) -> None:
        facts = list_gold_fact_names(DBT_FIX / "domain_b_encounter")
        self.assertIn("activity_events", facts)
        self.assertIn("fct_encounters", facts)

    def test_dbt_validators_pass_each_fixture(self) -> None:
        checks = [
            "check_fact_analytical_coverage.py",
            "check_metric_contract_completeness.py",
            "check_model_classification_coverage.py",
            "verify_metric_reconciliation.py",
            "validate_rendered_report_content.py",
        ]
        for slug in (
            "domain_a_transactional",
            "domain_b_encounter",
            "domain_c_asset_events",
            "domain_d_case_activity",
        ):
            root = DBT_FIX / slug
            for script in checks:
                with self.subTest(fixture=slug, script=script):
                    proc = run_script(script, "--root", str(root))
                    self.assertEqual(
                        proc.returncode,
                        0,
                        f"{slug} {script}\n{proc.stdout}\n{proc.stderr}",
                    )


if __name__ == "__main__":
    unittest.main()
