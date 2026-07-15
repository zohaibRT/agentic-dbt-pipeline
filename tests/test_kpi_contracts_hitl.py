#!/usr/bin/env python3
"""P0 KPI contract, reconciliation, and human-in-the-loop tests."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIX = ROOT / "fixtures" / "analytics"

sys.path.insert(0, str(SCRIPTS))
from fixture_kpi_contracts import (  # noqa: E402
    approval_register_markdown,
    decision_log_markdown,
    kpi_contracts_markdown,
    matrix_markdown,
    rate_sql,
    volume_sql,
)
from lib_gate_common import (  # noqa: E402
    compute_contract_fingerprint,
    parse_set,
    reconcile_acceptance_rule,
    reconcile_numeric,
    reconcile_row_count,
    reconcile_set_match,
)


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd, cwd=str(SCRIPTS), capture_output=True, text=True)


def _write_proof(root: Path, name: str, body: str) -> None:
    path = root / "reports" / "agent" / "sql_proofs" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip() + "\n", encoding="utf-8")


def _seed_fixture_project(root: Path, *, volume: str = "100") -> None:
    agent = root / "reports" / "agent"
    (agent / "09_analytics_insights" / "kpis").mkdir(parents=True, exist_ok=True)
    (agent / "sql_proofs").mkdir(parents=True, exist_ok=True)
    (root / "project.config.yml").write_text(
        (
            "analytics_policy:\n"
            "  critical_kpi_contract_coverage_required: 1.0\n"
            "  critical_reconciliation_coverage_required: 1.0\n"
            "human_in_loop_policy:\n"
            "  production_kpi_approval_required: 1.0\n"
            "  require_named_owner: true\n"
            "  require_named_approver: true\n"
            "  require_approval_evidence: true\n"
            "  require_approval_date: true\n"
            "  stale_approval_blocks_final: true\n"
            "  unresolved_critical_decisions_block_final: true\n"
            "  conditional_approval_requires_review_condition: true\n"
            "  allow_technical_work_without_business_approval: true\n"
            "  allow_unapproved_kpis_in_draft_reports: true\n"
            "  allow_unapproved_kpis_in_trusted_executive_reports: false\n"
        ),
        encoding="utf-8",
    )
    (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
        kpi_contracts_markdown(process="Fixture process", fact="fct_events", volume_expected=volume),
        encoding="utf-8",
    )
    (agent / "BUSINESS_APPROVAL_REGISTER.md").write_text(
        approval_register_markdown(process="Fixture process", fact="fct_events", volume_expected=volume),
        encoding="utf-8",
    )
    (agent / "DECISION_LOG.md").write_text(decision_log_markdown(), encoding="utf-8")
    (agent / "METRIC_VERIFICATION_MATRIX.md").write_text(
        matrix_markdown(volume_expected=volume), encoding="utf-8"
    )
    (agent / "HUMAN_ATTENTION_BOARD.md").write_text(
        """
| Decision ID | Decision Type | Area | Business Process | Object Type | Object ID | Question Requiring Human Input | Machine Evidence | Machine Recommendation | Alternative Options | Risk of No Decision | Proposed Owner | Due or Review Condition | Status | Final Human Decision | Approval Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| HA-NONE | MACHINE_RESOLVABLE | analytics | n/a | n/a | n/a | none | n/a | continue | n/a | none | fixture-owner | n/a | APPROVED | continue | reports/agent/DECISION_LOG.md |
""",
        encoding="utf-8",
    )
    rate = "0.8" if volume == "100" else "0.4"
    _write_proof(root, "010_volume.sql", volume_sql(kpi_id="KPI-001", expected=volume))
    _write_proof(root, "020_rate.sql", rate_sql(kpi_id="KPI-002", expected=rate))


def _replace_in_contracts(root: Path, old: str, new: str) -> None:
    path = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class P0KpiContractsHitlTests(unittest.TestCase):
    """Required positive/negative cases for P0-KPI-CONTRACTS-RECONCILIATION-HITL."""

    def test_01_complete_approved_kpi_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_02_missing_business_definition_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "Total count of valid events in period", "")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("business_definition", (proc.stdout + proc.stderr).lower())

    def test_03_missing_formula_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| count(*) |", "|  |")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("formula", (proc.stdout + proc.stderr).lower())

    def test_04_same_definition_and_formula_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(
                root,
                "Total count of valid events in period | count(*)",
                "count(*) | count(*)",
            )
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("business_definition and formula", (proc.stdout + proc.stderr).lower())

    def test_05_missing_source_models_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| fct_events | event_id,event_date,status |", "|  | event_id,event_date,status |")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("source_models", (proc.stdout + proc.stderr).lower())

    def test_06_ratio_without_numerator_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| completed_count | event_count |", "|  | event_count |")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("numerator", (proc.stdout + proc.stderr).lower())

    def test_07_ratio_without_denominator_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| completed_count | event_count |", "| completed_count |  |")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("denominator", (proc.stdout + proc.stderr).lower())

    def test_08_count_does_not_require_numerator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("NOT_APPLICABLE: count KPI has no numerator", (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8"))

    def test_09_currency_kpi_without_currency_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace("| count | NOT_APPLICABLE: nonfinancial count | integer |", "| currency |  | currency |", 1)
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("currency", (proc.stdout + proc.stderr).lower())

    def test_10_nonfinancial_count_does_not_require_currency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_11_ratio_without_zero_denominator_behavior_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| return null | daily |", "|  | daily |")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("zero_denominator", (proc.stdout + proc.stderr).lower())

    def test_12_target_without_target_source_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace(
                "| Target not defined | NOT_APPLICABLE: target not defined |",
                "| 95 |  |",
                1,
            )
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("target_source", (proc.stdout + proc.stderr).lower())

    def test_13_missing_technical_verification_status_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            # Blank first technical status cell after calculated status PASS
            text = text.replace("| 0 | PASS | PASS | APPROVED |", "| 0 | PASS |  | APPROVED |", 1)
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("technical_verification", (proc.stdout + proc.stderr).lower())

    def test_14_missing_business_approval_status_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace("| PASS | APPROVED | reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-001 |", "| PASS |  | reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-001 |", 1)
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def _blocked_row(self, **overrides: str) -> str:
        base = {
            "kpi_id": "KPI-B",
            "version": "1.0",
            "display": "Blocked KPI",
            "metric_class": "kpi",
            "process": "Fixture process",
            "question": "What is blocked?",
            "reason": "Cannot determine inclusion of reversed records because source flag is missing from warehouse extract",
            "missing": "source reverse_flag column proof",
            "owner": "fixture-owner",
            "next": "Request reverse_flag in next extract",
            "review": "When reverse_flag lands in source",
            "approval": "BLOCKED",
            "verification": "BLOCKED",
        }
        base.update(overrides)
        return (
            f"| {base['kpi_id']} | {base['version']} | n/a | {base['display']} | {base['metric_class']} | "
            f"{base['process']} | {base['question']} | n/a | n/a | {base['owner']} | n/a | n/a | n/a | n/a | n/a | "
            f"n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | "
            f"n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | "
            f"{base['verification']} | {base['approval']} | n/a | n/a | n/a | n/a | n/a | {base['reason']} | "
            f"{base['missing']} | {base['next']} | {base['review']} |"
        )

    def test_15_to_20_blocked_deferred_rules(self) -> None:
        cases = [
            ("owner", {"owner": ""}, "owner"),
            ("missing", {"missing": ""}, "missing"),
            ("next", {"next": ""}, "next"),
            ("review", {"review": ""}, "review"),
            ("deferred_owner", {"approval": "DEFERRED", "verification": "DEFERRED", "owner": ""}, "owner"),
            ("generic", {"reason": "TODO"}, "generic"),
        ]
        for name, overrides, needle in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    _seed_fixture_project(root)
                    path = root / "reports/agent/KPI_DEFINITION_CONTRACTS.md"
                    text = path.read_text(encoding="utf-8")
                    # Append blocked row — use a minimal blocked-oriented rewrite via completeness BLOCKED path
                    # Replace second KPI with blocked incomplete row by rewriting file to single blocked row table
                    path.write_text(
                        """
# contracts
| KPI ID | Contract Version | Display Name | Metric Class | Business Process | Business Question | Reason | Missing Evidence | Business Owner | Recommended Next Action | Review Or Resolution Condition | Business Approval Status | Technical Verification Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
"""
                        + self._blocked_row(**overrides).split("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ")[-1],
                        encoding="utf-8",
                    )
                    # Simpler blocked table:
                    b = {**{
                        "kpi_id": "KPI-B", "version": "1.0", "display": "Blocked KPI", "metric_class": "kpi",
                        "process": "Fixture process", "question": "What is blocked?",
                        "reason": "Cannot determine inclusion of reversed records because source flag is missing from warehouse extract",
                        "missing": "source reverse_flag column proof", "owner": "fixture-owner",
                        "next": "Request reverse_flag in next extract", "review": "When reverse_flag lands in source",
                        "approval": "BLOCKED", "verification": "BLOCKED",
                    }, **overrides}
                    path.write_text(
                        f"""
| KPI ID | Contract Version | Display Name | Metric Class | Business Process | Business Question | Reason | Missing Evidence | Business Owner | Recommended Next Action | Review Or Resolution Condition | Business Approval Status | Technical Verification Status | SQL Proof | Approval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {b['kpi_id']} | {b['version']} | {b['display']} | {b['metric_class']} | {b['process']} | {b['question']} | {b['reason']} | {b['missing']} | {b['owner']} | {b['next']} | {b['review']} | {b['approval']} | {b['verification']} | none | {b['approval']} |
""",
                        encoding="utf-8",
                    )
                    proc = run_script("check_metric_contract_completeness.py", "--root", str(root))
                    self.assertEqual(proc.returncode, 1, name + proc.stdout + proc.stderr)

    def test_21_unknown_validation_type_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| numeric_tolerance |", "| made_up_type |")
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("unknown validation_type", (proc.stdout + proc.stderr).lower())

    def test_22_legacy_schema_migration_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports/agent"
            agent.mkdir(parents=True)
            (agent / "09_analytics_insights").mkdir(parents=True)
            (agent / "sql_proofs").mkdir(parents=True)
            _write_proof(
                root,
                "a.sql",
                "-- expected result: 1\n-- captured result: 1\n-- status: PASS\nselect 1;",
            )
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """
| KPI ID | Display Name | Metric Class | Business Process | Business Question | Decision Supported | Action When Bad | Owner | Formula | Grain | Counting Key | Date Field | Date Role | Included Rows | Excluded Rows | Dimensions | Unit/Currency | Format | Aggregation | Target | Desired Direction | Source Models | Built In | SQL Proof | Expected | Actual | Diff / Tolerance | Approval | Verification | Why Correct / Open Question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KPI-1 | Volume | kpi | p | How many? | Plan | Fix | o | count(*) | e | id | d | occurred | all | none | s | count | integer | additive | Target not defined | increase | fct | path | reports/agent/sql_proofs/a.sql | 1 | 1 | 0 | APPROVED | PASS | ok |
""",
                encoding="utf-8",
            )
            (agent / "METRIC_VERIFICATION_MATRIX.md").write_text(
                """
| Metric | Source Proof | Current Model Proof | Expected Result | Actual Result | Diff | Status | Notes |
|---|---|---|---|---|---|---|---|
| Volume | reports/agent/sql_proofs/a.sql | reports/agent/sql_proofs/a.sql | 1 | 1 | 0 | PASS | ok |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  critical_reconciliation_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("legacy", (proc.stdout + proc.stderr).lower())
            self.assertIn("migration", (proc.stdout + proc.stderr).lower())

    def test_23_new_schema_requires_validation_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace("| numeric_tolerance |", "|  |", 1)
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("validation_type", (proc.stdout + proc.stderr).lower())

    def test_24_to_29_numeric_reconciliation(self) -> None:
        exact = reconcile_numeric("1000", "1000", "exact")
        self.assertEqual(exact["calculated_status"], "PASS")
        mismatch = reconcile_numeric("1000", "600", "exact")
        self.assertEqual(mismatch["calculated_status"], "FAIL")
        abs_ok = reconcile_numeric("SAR 1,000.00", "SAR 1,000.50", "absolute:1")
        self.assertEqual(abs_ok["calculated_status"], "PASS")
        rel_ok = reconcile_numeric("80%", "79.6%", "relative:1%")
        self.assertEqual(rel_ok["calculated_status"], "PASS")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| 100 | 100 | 0 | PASS | PASS | APPROVED |", "| 1000 | 600 | 0 | PASS | PASS | APPROVED |")
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("contradicts", (proc.stdout + proc.stderr).lower())
        bad_tol = reconcile_numeric("10", "10", "not-a-tolerance")
        # ambiguous tolerance kinds become acceptance_rule in parse_tolerance; numeric path should fail via verify
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| numeric_tolerance | 0 |", "| numeric_tolerance | weird_tol |")
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| 100 | 100 | 0 | PASS |", "| 100 | 100 | 99 | PASS |")
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("diff", (proc.stdout + proc.stderr).lower())

    def test_30_to_33_row_counts(self) -> None:
        self.assertEqual(reconcile_row_count("10", "10")["calculated_status"], "PASS")
        self.assertTrue(reconcile_row_count("10", "10.5")["errors"])
        self.assertTrue(reconcile_row_count("-1", "1")["errors"])
        bad = reconcile_row_count("10", "11")
        self.assertEqual(bad["calculated_status"], "FAIL")

    def test_34_to_39_set_match(self) -> None:
        self.assertEqual(reconcile_set_match("A, B, C", "A, B, C")["calculated_status"], "PASS")
        bad = reconcile_set_match("A, B, C", "A, B, D")
        self.assertEqual(bad["calculated_status"], "FAIL")
        self.assertIn("c", bad["missing"])
        self.assertIn("d", bad["unexpected"])
        ci = reconcile_set_match("A,B", "a,b", "lowercase")
        self.assertEqual(ci["calculated_status"], "PASS")
        dup = reconcile_set_match("A,A,B", "A,B", "keep_duplicates")
        self.assertTrue(dup["duplicate_members"])
        self.assertEqual(reconcile_set_match('["A","B"]', "A|B")["calculated_status"], "PASS")
        self.assertEqual(sorted(parse_set("A|B|C")), ["a", "b", "c"])

    def test_40_to_43_acceptance_rule(self) -> None:
        row = {
            "acceptance_rule_id": "",
            "acceptance_rule_description": "rule",
            "sql_proof": "p.sql",
            "actual": "ok",
            "verification": "PASS",
        }
        self.assertEqual(reconcile_acceptance_rule(row)["calculated_status"], "FAIL")
        row["acceptance_rule_id"] = "AR-1"
        row["sql_proof"] = ""
        self.assertEqual(reconcile_acceptance_rule(row)["calculated_status"], "FAIL")
        # free-text PASS insufficient
        free = {
            "acceptance_rule_id": "PASS",
            "acceptance_rule_description": "PASS",
            "sql_proof": "p.sql",
            "actual": "PASS",
            "verification": "PASS",
        }
        self.assertEqual(reconcile_acceptance_rule(free)["calculated_status"], "FAIL")

    def test_44_to_49_sql_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            (root / "reports/agent/sql_proofs/010_volume.sql").unlink()
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("not found", (proc.stdout + proc.stderr).lower())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _write_proof(root, "010_volume.sql", "-- kpi_id: KPI-001\n-- status: PASS\nnot sql")
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("runnable sql", (proc.stdout + proc.stderr).lower())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _write_proof(
                root,
                "010_volume.sql",
                "-- validation_type: numeric_tolerance\n-- expected result: 100\n-- captured result: 100\n-- tolerance: 0\n-- status: PASS\nselect 100;",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("kpi id", (proc.stdout + proc.stderr).lower())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _write_proof(
                root,
                "010_volume.sql",
                "-- kpi_id: KPI-009\n-- validation_type: numeric_tolerance\n-- expected result: 100\n-- captured result: 100\n-- tolerance: 0\n-- status: PASS\nselect 100;",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("does not match", (proc.stdout + proc.stderr).lower())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _write_proof(
                root,
                "010_volume.sql",
                "-- kpi_id: KPI-001\n-- validation_type: numeric_tolerance\n-- expected result: 100\n-- tolerance: 0\n-- status: PASS\nselect 100;",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("captured", (proc.stdout + proc.stderr).lower())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _write_proof(
                root,
                "010_volume.sql",
                "-- kpi_id: KPI-001\n-- expected result: 100\n-- captured result: 100\n-- tolerance: 0\n-- status: PASS\nselect 100;",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("validation type", (proc.stdout + proc.stderr).lower())

    def test_50_to_52_reconciliation_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| 100 | 100 | 0 | PASS | PASS | APPROVED |", "| 100 | 50 | 0 | PASS | PASS | APPROVED |")
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("coverage", (proc.stdout + proc.stderr).lower())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports/agent"
            agent.mkdir(parents=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                "| KPI ID | Display Name | Grain | SQL Proof | Approval | Verification |\n|---|---|---|---|---|---|\n",
                encoding="utf-8",
            )
            (agent / "METRIC_VERIFICATION_MATRIX.md").write_text(
                "| Metric | Status |\n|---|---|\n| none | SKIPPED |\n",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  critical_reconciliation_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("verify_metric_reconciliation.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            joined = (proc.stdout + proc.stderr).lower()
            self.assertTrue(
                "not 100%" in joined or "no contract rows" in joined or "no approved/proposed" in joined,
                joined,
            )

    def test_53_to_74_human_in_the_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            # Technical PASS without business approval is not trusted
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace("| APPROVED |", "| PENDING_REVIEW |", 1)
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("not trusted", (proc.stdout + proc.stderr).lower())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| fixture-owner | fixture-approver |", "|  | fixture-approver |")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("business_owner", (proc.stdout + proc.stderr).lower())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| fixture-owner | fixture-approver |", "| fixture-owner |  |")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("approver", (proc.stdout + proc.stderr).lower())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(
                root,
                "reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-001",
                "Business approved",
            )
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("evidence", (proc.stdout + proc.stderr).lower())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| 2026-01-15 |", "|  |")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("approval_date", (proc.stdout + proc.stderr).lower())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(
                root,
                "reports/agent/BUSINESS_APPROVAL_REGISTER.md#KPI-001",
                "agent-generated APPROVED",
            )
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("agent", (proc.stdout + proc.stderr).lower())

        # Pending may exist in draft analytics
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace("| APPROVED |", "| PENDING_REVIEW |")
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        # Fingerprint change invalidates approval
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| count(*) |", "| count(distinct event_id) |")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("fingerprint", (proc.stdout + proc.stderr).lower())

        # Source model change invalidates
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| fct_events | event_id,event_date,status |", "| fct_other | event_id,event_date,status |")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("fingerprint", (proc.stdout + proc.stderr).lower())

        # Inclusion change invalidates
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            _replace_in_contracts(root, "| all valid | test rows |", "| all valid including tests | none |")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)

        # Cosmetic display name does not invalidate fingerprint
        fp_before = compute_contract_fingerprint(
            {"business_definition": "x", "formula": "y", "display_name": "Old"}
        )
        fp_after = compute_contract_fingerprint(
            {"business_definition": "x", "formula": "y", "display_name": "New"}
        )
        self.assertEqual(fp_before, fp_after)

        # Conditional approval without review condition fails
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace("| APPROVED |", "| APPROVED_WITH_CONDITIONS |", 1)
            text = text.replace(
                "| NOT_APPLICABLE: unconditional approval | NOT_APPLICABLE: unconditional approval |",
                "| temporary tolerance 5% |  |",
                1,
            )
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("review", (proc.stdout + proc.stderr).lower())

        # Expired conditional approval
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            text = (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").read_text(encoding="utf-8")
            text = text.replace("| APPROVED |", "| APPROVED_WITH_CONDITIONS |", 1)
            text = text.replace(
                "| NOT_APPLICABLE: unconditional approval | NOT_APPLICABLE: unconditional approval |",
                "| temporary tolerance 5% | 2020-01-01 |",
                1,
            )
            (root / "reports/agent/KPI_DEFINITION_CONTRACTS.md").write_text(text, encoding="utf-8")
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("expired", (proc.stdout + proc.stderr).lower())

        # Valid approval passes
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_fixture_project(root)
            proc = run_script("check_human_approval_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        # Domain neutrality of human approval script (no industry hardcodes in errors on fixture)
        proc = run_script(
            "check_domain_neutrality.py",
            "--root",
            str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        # Existing fixtures remain valid
        for slug in ("domain_a_transactional", "domain_b_encounter"):
            root = FIX / slug
            for script in (
                "check_metric_contract_completeness.py",
                "verify_metric_reconciliation.py",
                "validate_kpi_proofs.py",
                "check_human_approval_coverage.py",
            ):
                proc = run_script(script, "--root", str(root))
                self.assertEqual(proc.returncode, 0, f"{slug} {script}\n{proc.stdout}\n{proc.stderr}")

    def test_75_separated_catalogs_still_supported(self) -> None:
        root = FIX / "domain_a_transactional"
        self.assertTrue((root / "reports/agent/09_analytics_insights/kpis/business_measure_catalog.md").exists())
        self.assertTrue((root / "reports/agent/09_analytics_insights/kpis/business_metric_catalog.md").exists())
        proc = run_script("validate_kpi_proofs.py", "--root", str(root))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
