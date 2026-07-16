#!/usr/bin/env python3
"""Regression tests for production analytics P2 gate correctness fixes."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
from check_fact_analytical_coverage import (  # noqa: E402
    _legacy_field_value,
    normalize_applicability,
)
from lib_gate_common import parse_set, reconcile_set_match  # noqa: E402
from run_acceptance_gate import detect_ci_orchestration_evidence  # noqa: E402


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd, cwd=str(SCRIPTS), capture_output=True, text=True)


class FactCoverageStatusAliasTests(unittest.TestCase):
    def test_status_distribution_aliases_exclude_generic_status(self) -> None:
        row = {
            "status": "PASS",
            "volume": "SUPPORTED",
            "grain": "SUPPORTED",
            "counting_key": "SUPPORTED",
            "primary_date": "SUPPORTED",
            "amount_or_quantity": "SUPPORTED",
            "duration_or_balance": "NOT_APPLICABLE",
            "lifecycle": "SUPPORTED",
            "dimensions": "SUPPORTED",
            "time_trends": "SUPPORTED",
            "period_comparison": "SUPPORTED",
            "data_quality": "SUPPORTED",
            "exceptions": "SUPPORTED",
            "aging": "NOT_APPLICABLE",
            "reconciliation": "SUPPORTED",
            "business_questions": "SUPPORTED",
            "notes": "ok",
        }
        self.assertEqual(_legacy_field_value(row, "status_distribution", ("status_distribution",)), "")
        row["status_distribution"] = "SUPPORTED"
        self.assertEqual(
            _legacy_field_value(row, "status_distribution", ("status_distribution",)),
            "SUPPORTED",
        )

    def test_overall_status_not_used_as_status_distribution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            insights = root / "reports" / "agent" / "09_analytics_insights"
            gold = root / "models" / "gold"
            gold.mkdir(parents=True)
            insights.mkdir(parents=True)
            (gold / "fct_events.sql").write_text("select 1\n", encoding="utf-8")
            (insights / "model_classification.md").write_text(
                """
| Model | Class | Status |
|---|---|---|
| fct_events | fact/event | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            # Legacy dual Status columns: first = status_distribution, last = overall.
            # Overall PASS must never satisfy status_distribution by itself.
            (insights / "fact_coverage_contracts.md").write_text(
                """
| Fact | Grain | Counting Key | Volume | Value | Status | Time | Dimensions | Quality | Reconciliation | Business Questions | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| fct_events | one row per event | event_id | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | q | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  critical_fact_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_fact_analytical_coverage.py", "--root", str(root))
            out = (proc.stdout + proc.stderr).lower()
            # status_distribution must be taken from the first Status=SUPPORTED column
            self.assertIn("status_distribution", out)
            self.assertIn("supported requires family-specific proof", out)
            # Must not claim status_distribution is missing (that would mean overall PASS was ignored
            # and the first Status column was dropped)
            self.assertNotIn("missing applicability for status_distribution", out)
            # Incomplete contracts still fail overall — that is correct production behavior
            self.assertNotEqual(proc.returncode, 0)


class SetMatchReconciliationTests(unittest.TestCase):
    def test_set_match_mismatch_with_pass_fails(self) -> None:
        result = reconcile_set_match("a,b,c", "a,b")
        self.assertEqual(result["calculated_status"], "FAIL")
        self.assertIn("c", result["missing"])

    def test_set_match_passes_when_sets_equal(self) -> None:
        result = reconcile_set_match("a, b", "b;a")
        self.assertEqual(result["calculated_status"], "PASS")

    def test_verify_script_fails_set_match_pass_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            proofs = agent / "sql_proofs"
            proofs.mkdir(parents=True)
            (proofs / "a.sql").write_text(
                "-- purpose: test\n-- expected result: a,b,c\n-- captured result: a,b\n-- status: PASS\nselect 1;\n",
                encoding="utf-8",
            )
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """
| KPI ID | Display Name | Business Question | Decision Supported | Action When Bad | Owner | Grain | Counting Key | Business Definition | Formula | Validation Type | SQL Proof | Expected | Actual | Approval | Verification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-SET | Status mix | Q? | D | A | o | e | id | def | n/a | set_match | reports/agent/sql_proofs/a.sql | a,b,c | a,b | APPROVED | PASS |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            (agent / "METRIC_VERIFICATION_MATRIX.md").write_text(
                """
| Metric | Source Proof | Current Model Proof | Expected Result | Actual Result | Diff | Status | Notes |
|---|---|---|---|---|---|---|---|
| KPI-SET | reports/agent/sql_proofs/a.sql | reports/agent/sql_proofs/a.sql | a,b,c | a,b | n/a | PASS | ok |
""".strip()
                + "\n",
                encoding="utf-8",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("set_match", (proc.stdout + proc.stderr).lower())


class BlockedKpiContractTests(unittest.TestCase):
    def test_blocked_kpi_without_next_action_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            agent.mkdir(parents=True)
            (root / "reports" / "agent" / "09_analytics_insights").mkdir(parents=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """
| KPI ID | Display Name | Business Process | Business Question | Reason | Missing Evidence | Owner | Approval | Verification |
|---|---|---|---|---|---|---|---|---|
| KPI-BLK | Blocked KPI | process | question? | waiting on source | proof file | analytics | BLOCKED | FAIL |
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
            self.assertIn("next_action", (proc.stdout + proc.stderr).lower())


class WarningPolicyTests(unittest.TestCase):
    def test_discovery_phase_does_not_enforce_warnings(self) -> None:
        from run_acceptance_gate import GateReport, WarningRecord, compute_exit_code

        gate = GateReport(phase="discovery", enforce_warning_policy=False)
        gate.warning_records.append(
            WarningRecord(warning_id="test-warning", message="test warning", accepted=False)
        )
        gate.overall_status = "WARN"
        self.assertEqual(compute_exit_code(gate), 0)


class CiDetectionTests(unittest.TestCase):
    def test_analytics_gates_yml_counts_as_evidence(self) -> None:
        summary = detect_ci_orchestration_evidence(ROOT)
        self.assertTrue(summary.get("has_relevant_ci"))
        joined = " ".join(str(item) for item in (summary.get("workflows") or [])).lower()
        self.assertIn("analytics_gates", joined)


class ApplicabilityTokenTests(unittest.TestCase):
    def test_supported_normalizes_pass(self) -> None:
        self.assertEqual(normalize_applicability("PASS"), "SUPPORTED")
        self.assertEqual(normalize_applicability("supported"), "SUPPORTED")

    def test_parse_set_normalizes_tokens(self) -> None:
        self.assertEqual(parse_set("A, B; c"), {"a", "b", "c"})


if __name__ == "__main__":
    unittest.main()
