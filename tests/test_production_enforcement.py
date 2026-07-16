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
from run_acceptance_gate import (  # noqa: E402
    GateReport,
    WarningRecord,
    compute_exit_code,
    detect_ci_orchestration_evidence,
    resolve_enforce_warning_policy,
)
from verify_metric_reconciliation import detect_contract_schema  # noqa: E402
from lib_gate_common import REQUIRED_OBSERVABILITY_DOMAINS  # noqa: E402

# Include HITL suite when running: python -m unittest tests.test_production_enforcement
from tests.test_kpi_contracts_hitl import P0KpiContractsHitlTests  # noqa: E402,F401
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


def _write_fact_root(root: Path, contract_md: str) -> None:
    gold = root / "models" / "gold"
    gold.mkdir(parents=True, exist_ok=True)
    (gold / "fct_events.sql").write_text("select 1 as event_id\n", encoding="utf-8")
    insights = root / "reports" / "agent" / "09_analytics_insights"
    insights.mkdir(parents=True, exist_ok=True)
    (insights / "model_classification.md").write_text(
        """
| Model | Class | Status |
|---|---|---|
| fct_events | fact/event | PASS |
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (insights / "fact_coverage_contracts.md").write_text(contract_md.strip() + "\n", encoding="utf-8")
    (root / "project.config.yml").write_text(
        "analytics_policy:\n  critical_fact_coverage_required: 1.0\n",
        encoding="utf-8",
    )


COMPLETE_FACT_CONTRACT = """
| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fct_events | one row per event | event_id | event_date | SUPPORTED: sql_proofs/vol.sql | SUPPORTED: sql_proofs/amt.sql | NOT_APPLICABLE: no duration column at this grain | SUPPORTED: sql_proofs/status.sql | SUPPORTED: sql_proofs/lifecycle.sql | SUPPORTED: sql_proofs/dims.sql | SUPPORTED: sql_proofs/trends.sql | SUPPORTED: sql_proofs/period.sql | SUPPORTED: sql_proofs/quality.sql | SUPPORTED: sql_proofs/exceptions.sql | NOT_APPLICABLE: aging out of first-pass scope | SUPPORTED: sql_proofs/recon.sql | volume and completion | Fixture notes | PASS |
"""


class P0AcceptanceFactsTests(unittest.TestCase):
    """P0-ACCEPTANCE-FACTS: warning policy, CI, observability neutrality, fact coverage."""

    def test_analytics_warning_does_not_fail_without_strict(self) -> None:
        from run_acceptance_gate import CheckResult

        policy = {"final_fail_on_warning": True, "require_explicit_warning_acceptance": True}
        self.assertFalse(
            resolve_enforce_warning_policy(
                phase="analytics", strict=False, fail_on_warning=False, acceptance_policy=policy
            )
        )
        gate = GateReport(phase="analytics", enforce_warning_policy=False)
        gate.add(CheckResult("Source freshness", "WARN", "missing freshness"))
        gate.finalize(set(), require_explicit_warning_acceptance=True)
        self.assertEqual(gate.overall_status, "WARN")
        self.assertEqual(compute_exit_code(gate), 0)

    def test_analytics_warning_fails_with_strict(self) -> None:
        policy = {"final_fail_on_warning": True, "require_explicit_warning_acceptance": True}
        self.assertTrue(
            resolve_enforce_warning_policy(
                phase="analytics", strict=True, fail_on_warning=False, acceptance_policy=policy
            )
        )
        from run_acceptance_gate import CheckResult

        gate = GateReport(phase="analytics", enforce_warning_policy=True)
        gate.add(CheckResult("Source freshness", "WARN", "missing freshness"))
        gate.finalize(set(), require_explicit_warning_acceptance=True)
        self.assertEqual(gate.overall_status, "FAIL")
        self.assertEqual(compute_exit_code(gate), 1)

    def test_final_unaccepted_warning_fails(self) -> None:
        policy = {"final_fail_on_warning": True, "require_explicit_warning_acceptance": True}
        self.assertTrue(
            resolve_enforce_warning_policy(
                phase="final", strict=False, fail_on_warning=False, acceptance_policy=policy
            )
        )
        from run_acceptance_gate import CheckResult

        gate = GateReport(phase="final", enforce_warning_policy=True)
        gate.add(CheckResult("Human verification guide", "WARN", "missing guide"))
        gate.finalize(set(), require_explicit_warning_acceptance=True)
        self.assertEqual(gate.overall_status, "FAIL")
        self.assertEqual(compute_exit_code(gate), 1)

    def test_final_accepted_warning_passes(self) -> None:
        from run_acceptance_gate import CheckResult

        gate = GateReport(phase="final", enforce_warning_policy=True)
        gate.add(CheckResult("Human verification guide", "WARN", "missing guide"))
        gate.finalize({"human verification guide"}, require_explicit_warning_acceptance=True)
        # Accepted warnings remain visible but overall completes as PASS
        self.assertEqual(gate.overall_status, "PASS")
        self.assertEqual(compute_exit_code(gate), 0)
        self.assertTrue(gate.warning_records[0].accepted)

    def test_analytics_gates_yml_detected_as_relevant_ci(self) -> None:
        summary = detect_ci_orchestration_evidence(ROOT)
        self.assertTrue(summary.get("has_relevant_ci"), summary)
        joined = " ".join(str(item) for item in (summary.get("workflows") or [])).lower()
        self.assertIn("analytics_gates", joined)

    def test_empty_workflow_not_treated_as_ci(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wf = root / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / "empty.yml").write_text(
                "name: empty\non: push\njobs: {}\n",
                encoding="utf-8",
            )
            summary = detect_ci_orchestration_evidence(root)
            self.assertFalse(summary.get("has_relevant_ci"), summary)

    def test_custom_observability_evidence_passes_without_elementary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            insights = root / "reports" / "agent" / "09_analytics_insights"
            kpis = insights / "kpis"
            kpis.mkdir(parents=True, exist_ok=True)
            rows = [
                "| Domain | Scope | Models | Metric IDs | Business Or Engineering Question | "
                "Validation Method | Proof Or Telemetry | Threshold Or SLA | Expected Result | "
                "Actual Result | Owner | Incident Or Action | Status | Notes | Reassessment Condition |"
            ]
            rows.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for domain in sorted(REQUIRED_OBSERVABILITY_DOMAINS):
                rows.append(
                    f"| {domain} | scope | models | mid | question | custom sql proof | "
                    f"reports/agent/sql_proofs/obs.sql | sla | PASS | PASS | analytics | none | "
                    f"PASS | Custom dbt-test evidence | n/a |"
                )
            (insights / "data_observability_coverage.md").write_text(
                "\n".join(rows) + "\n", encoding="utf-8"
            )
            (kpis / "data_quality_metric_catalog.md").write_text(
                "| Metric | Status |\n|---|---|\n| orphan_rate | PASS |\n",
                encoding="utf-8",
            )
            (kpis / "pipeline_health_metric_catalog.md").write_text(
                "| Metric | Status |\n|---|---|\n| build_success_rate | PASS |\n",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  observability_domain_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            text = (insights / "data_observability_coverage.md").read_text(encoding="utf-8").lower()
            self.assertNotIn("elementary", text)
            proc = run_script("check_data_observability_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_overall_status_pass_does_not_satisfy_status_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Single overall Status column — must NOT count as status_distribution
            _write_fact_root(
                root,
                """
| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fct_events | one row per event | event_id | event_date | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | volume | Proof present | PASS |
""",
            )
            proc = run_script("check_fact_analytical_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("status_distribution", (proc.stdout + proc.stderr).lower())

    def test_fact_missing_amount_applicability_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fact_root(
                root,
                """
| Fact | Grain | Counting Key | Primary Date | Volume | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fct_events | one row per event | event_id | event_date | SUPPORTED | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | volume | Proof present | PASS |
""",
            )
            proc = run_script("check_fact_analytical_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            joined = (proc.stdout + proc.stderr).lower()
            self.assertTrue(
                "amount" in joined or "amount_or_quantity" in joined,
                joined,
            )

    def test_not_applicable_without_reason_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fact_root(
                root,
                """
| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fct_events | one row per event | event_id | event_date | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | volume |  | PASS |
""",
            )
            proc = run_script("check_fact_analytical_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("not_applicable", (proc.stdout + proc.stderr).lower())
            self.assertIn("reason", (proc.stdout + proc.stderr).lower())

    def test_blocked_without_owner_or_next_action_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fact_root(
                root,
                """
| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Owner | Missing Evidence | Next Action | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fct_events | one row per event | event_id | event_date | SUPPORTED | SUPPORTED | NOT_APPLICABLE | BLOCKED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | volume | Missing status map |  |  |  | PASS |
""",
            )
            proc = run_script("check_fact_analytical_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            joined = (proc.stdout + proc.stderr).lower()
            self.assertIn("blocked", joined)
            self.assertTrue("owner" in joined or "next_action" in joined, joined)

    def test_complete_valid_fact_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_fact_root(root, COMPLETE_FACT_CONTRACT)
            proc = run_script("check_fact_analytical_coverage.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
