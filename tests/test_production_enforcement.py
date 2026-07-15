#!/usr/bin/env python3
"""Negative and regression tests for production enforcement gates."""

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
from lib_gate_common import list_gold_fact_names, named_status  # noqa: E402
from run_acceptance_gate import GateReport, WarningRecord, compute_exit_code  # noqa: E402
from verify_metric_reconciliation import detect_contract_schema  # noqa: E402


def run_script(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd, cwd=str(cwd or SCRIPTS), capture_output=True, text=True)


def write_minimal_contract_root(root: Path, *, include_proof: bool = True, formula: str = "count(*)") -> None:
    agent = root / "reports" / "agent"
    proofs = agent / "sql_proofs"
    proofs.mkdir(parents=True, exist_ok=True)
    insights = agent / "09_analytics_insights"
    insights.mkdir(parents=True, exist_ok=True)
    (insights / "kpis").mkdir(parents=True, exist_ok=True)
    if include_proof:
        (proofs / "a.sql").write_text(
            "-- purpose: test\n-- expected result: 1\n-- captured result: 1\n-- status: PASS\nselect 1;\n",
            encoding="utf-8",
        )
    (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
        f"""
| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Unit/Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-1 | Volume | kpi | p | How many? | Plan | Fix | o | {formula} | e | id | d | occurred | all | none | s | count | integer | additive | Target not defined | increase | fct | path | reports/agent/sql_proofs/a.sql | 1000 | 600 | 0 | APPROVED | PASS | ok |
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (agent / "METRIC_VERIFICATION_MATRIX.md").write_text(
        """
| Metric | Source Proof | Current Model Proof | Expected Result | Actual Result | Diff | Status | Notes |
|---|---|---|---|---|---|---|---|
| Volume | reports/agent/sql_proofs/a.sql | reports/agent/sql_proofs/a.sql | 1000 | 600 | 400 | PASS | ok |
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "project.config.yml").write_text(
        "analytics_policy:\n  critical_reconciliation_coverage_required: 1.0\n",
        encoding="utf-8",
    )


def write_minimal_gate_root(root: Path) -> None:
    discovery = root / "reports" / "agent" / "00_discovery"
    discovery.mkdir(parents=True, exist_ok=True)
    for rel in (
        "AGENT_PLAN.md",
        "reports/agent/00_discovery/core_profile.json",
        "reports/agent/00_discovery/discovery_raw.json",
        "reports/agent/00_discovery/requirements.md",
        "reports/agent/PIPELINE_STATUS.md",
        "reports/agent/CONTEXT_TREE.md",
        "reports/agent/REPORT_INDEX.md",
        "reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md",
        "reports/agent/LAYER_VERIFICATION_LEDGER.md",
        "reports/agent/KPI_DEFINITION_CONTRACTS.md",
        "reports/agent/METRIC_VERIFICATION_MATRIX.md",
    ):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            path.write_text("{}", encoding="utf-8")
        else:
            path.write_text("# TEST FIXTURE\n\nStatus: PASS\n", encoding="utf-8")
    (root / "dbt_project.yml").write_text("name: gate_test\nversion: '1.0.0'\n", encoding="utf-8")
    (root / "project.config.yml").write_text(
        """
acceptance_policy:
  final_fail_on_warning: true
  require_explicit_warning_acceptance: true
""".strip()
        + "\n",
        encoding="utf-8",
    )


class ReconciliationNegativeTests(unittest.TestCase):
    def test_expected_actual_mismatch_with_pass_verification_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_minimal_contract_root(root)
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("contradicts", (proc.stdout + proc.stderr).lower())

    def test_missing_sql_proof_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_minimal_contract_root(root, include_proof=False)
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("proof", (proc.stdout + proc.stderr).lower())


class MetricContractNegativeTests(unittest.TestCase):
    def test_approved_row_missing_formula_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_minimal_contract_root(root, formula="")
            (root / "reports" / "agent" / "09_analytics_insights").mkdir(parents=True, exist_ok=True)
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  critical_kpi_contract_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


class StatusColumnWinsTests(unittest.TestCase):
    def test_blocked_status_not_overridden_by_pass_notes(self) -> None:
        row = {"status": "BLOCKED", "notes": "PASS", "verification": "PASS"}
        self.assertEqual(named_status(row), "FAIL")

    def test_reconciliation_matrix_blocked_with_pass_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            proofs = agent / "sql_proofs"
            proofs.mkdir(parents=True, exist_ok=True)
            (proofs / "a.sql").write_text(
                "-- purpose: test\n-- expected result: 1\n-- captured result: 1\n-- status: PASS\nselect 1;\n",
                encoding="utf-8",
            )
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """
| KPI ID | Display Name | Formula | SQL Proof | Expected | Actual | Approval | Verification |
|---|---|---|---|---|---|---|---|
| KPI-1 | Volume | count(*) | reports/agent/sql_proofs/a.sql | 1 | 1 | APPROVED | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (agent / "METRIC_VERIFICATION_MATRIX.md").write_text(
                """
| Metric | Source Proof | Current Model Proof | Expected Result | Actual Result | Diff | Status | Notes |
|---|---|---|---|---|---|---|---|
| Volume | reports/agent/sql_proofs/a.sql | reports/agent/sql_proofs/a.sql | 1 | 1 | 0 | BLOCKED | PASS in notes |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


class PresentationNegativeTests(unittest.TestCase):
    def test_duplicate_rendered_coverage_rows_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = root / "reports" / "agent" / "10_presentation" / "matplotlib"
            matplotlib.mkdir(parents=True, exist_ok=True)
            (matplotlib / "kpi_figure_coverage.md").write_text(
                """
| Item | Status | Proof |
|---|---|---|
| Volume KPI | RENDERED | sql_verification/010_volume.sql |
| Volume KPI | RENDERED | sql_verification/010_volume.sql |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (matplotlib / "label_dictionary.md").write_text(
                "| field_name | raw_code | business_label | source | confidence |\n|---|---|---|---|---|\n",
                encoding="utf-8",
            )
            (matplotlib / "sql_verification").mkdir(parents=True, exist_ok=True)
            (matplotlib / "sql_verification" / "_proof_index.md").write_text(
                "| Item | Proof | Status |\n|---|---|---|\n| Volume KPI | 010_volume.sql | PASS |\n",
                encoding="utf-8",
            )
            (matplotlib / "report_builder.py").write_text("TABS = ['Executive Overview', 'Dimensions']\n", encoding="utf-8")
            (root / "project.config.yml").write_text("analytics_policy: {}\n", encoding="utf-8")
            proc = run_script("check_presentation_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("duplicate", (proc.stdout + proc.stderr).lower())

    def test_validate_rendered_report_content_fails_on_snake_case_and_raw_float(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = root / "reports" / "agent" / "10_presentation" / "matplotlib"
            matplotlib.mkdir(parents=True, exist_ok=True)
            (matplotlib / "report.html").write_text(
                """
                <table>
                <tr><th>dim_programs_row_count</th><td>30</td></tr>
                <tr><td>active_operating_share</td><td>0.2611111111111111</td></tr>
                </table>
                """.strip(),
                encoding="utf-8",
            )
            proc = run_script("validate_rendered_report_content.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


class TimeIntelligenceNegativeTests(unittest.TestCase):
    def test_published_kpi_missing_from_time_intelligence_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            insights = agent / "09_analytics_insights"
            insights.mkdir(parents=True, exist_ok=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """
| KPI ID | Display Name | Approval | Verification |
|---|---|---|---|
| KPI-999 | Orphan KPI | APPROVED | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (insights / "time_intelligence_coverage.md").write_text(
                """
| Metric ID | Date field | Date role | Current period | Prior period | MoM/YoY | MTD/QTD/YTD | Rolling | Target/baseline | Status |
|---|---|---|---|---|---|---|---|---|---|
| Volume KPI | event_date | occurred | yes | yes | yes | yes | yes | Target not defined | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  time_intelligence_coverage_required: 0.8\n",
                encoding="utf-8",
            )
            proc = run_script("check_time_intelligence_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


class ObservabilityNegativeTests(unittest.TestCase):
    def test_missing_observability_domain_row_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True, exist_ok=True)
            (insights / "data_observability_coverage.md").write_text(
                """
| Domain | Evidence | Owner | Status | Notes |
|---|---|---|---|---|
| completeness | evidence | analytics | PASS | ok |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  observability_domain_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_data_observability_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


class AcceptanceGateStrictTests(unittest.TestCase):
    def test_compute_exit_code_fails_on_unaccepted_warnings(self) -> None:
        gate = GateReport(enforce_warning_policy=True)
        gate.warning_records.append(
            WarningRecord(warning_id="Human verification guide", message="Human verification guide: missing", accepted=False)
        )
        gate.failures.append("Human verification guide: missing")
        gate.overall_status = "FAIL"
        self.assertEqual(compute_exit_code(gate), 1)

    def test_strict_gate_cli_exits_nonzero_without_accepted_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_minimal_gate_root(root)
            proc = run_script(
                "run_acceptance_gate.py",
                "--root",
                str(root),
                "--skip-dbt",
                "--phase",
                "final",
                "--strict",
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


class PrefixIndependentFactTests(unittest.TestCase):
    def test_activity_events_without_fct_prefix_is_counted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gold = root / "models" / "gold"
            gold.mkdir(parents=True, exist_ok=True)
            (gold / "activity_events.sql").write_text("select 1 as event_id\n", encoding="utf-8")
            (gold / "dim_statuses.sql").write_text("select 1 as status_code\n", encoding="utf-8")
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True, exist_ok=True)
            (insights / "model_classification.md").write_text(
                """
| Model | Class | Status |
|---|---|---|
| activity_events | fact/event | PASS |
| dim_statuses | dimension | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            facts = list_gold_fact_names(root)
            self.assertIn("activity_events", facts)


class LegacySchemaTests(unittest.TestCase):
    def test_legacy_kpi_contract_headers_still_parse(self) -> None:
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


class SeparatedCatalogTests(unittest.TestCase):
    def test_separated_catalogs_without_legacy_measure_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            insights = root / "reports" / "agent" / "09_analytics_insights"
            kpis = insights / "kpis"
            kpis.mkdir(parents=True, exist_ok=True)
            (root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md").write_text("# KPI\n", encoding="utf-8")
            (root / "reports" / "agent" / "METRIC_VERIFICATION_MATRIX.md").write_text("# Matrix\n", encoding="utf-8")
            (insights / "business_process_catalog.md").write_text("# Process\n", encoding="utf-8")
            (insights / "fact_catalog.md").write_text("# Facts\n", encoding="utf-8")
            (kpis / "business_measure_catalog.md").write_text(
                "| Measure | Display name | Format | Status |\n|---|---|---|---|\n| event_count | Event count | integer | PASS |\n",
                encoding="utf-8",
            )
            (kpis / "business_metric_catalog.md").write_text(
                "| Metric | Display name | Format | Status |\n|---|---|---|---|\n| completion_rate | Completion rate | percent | PASS |\n",
                encoding="utf-8",
            )
            (kpis / "kpi_catalog.md").write_text(
                "| KPI | Display name | Status |\n|---|---|---|\n| volume_kpi | Volume KPI | PASS |\n",
                encoding="utf-8",
            )
            proc = run_script("validate_kpi_proofs.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class DomainNeutralityNegativeTests(unittest.TestCase):
    def test_detects_must_build_dim_customer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "references").mkdir()
            (root / "references" / "bad-requirement.md").write_text(
                "Agents must build dim_customer for every project.\n",
                encoding="utf-8",
            )
            (root / "scripts").mkdir()
            proc = run_script("check_domain_neutrality.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("dim_customer", (proc.stdout + proc.stderr).lower())


if __name__ == "__main__":
    unittest.main()
