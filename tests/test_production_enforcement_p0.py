#!/usr/bin/env python3
"""P0 production-enforcement tests: ValidatorResult JSON, HITL denominator, waivers, browser."""

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

from lib_gate_common import (  # noqa: E402
    VALIDATOR_RESULT_SCHEMA_VERSION,
    build_validator_result,
    discover_production_kpi_obligations,
    evaluate_typed_acceptance_rule,
    find_valid_waiver_for_kpi,
    load_validator_result_json,
    project_package_name,
    resolve_source_reference,
    stable_warning_id,
    write_validator_result_json,
)


class ValidatorResultJsonTests(unittest.TestCase):
    def test_warn_json_exit_0(self) -> None:
        result = build_validator_result("demo_validator", [], ["something odd"])
        self.assertEqual(result.status, "WARN")
        self.assertTrue(result.warning_ids)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            write_validator_result_json(path, result)
            loaded = load_validator_result_json(path)
            self.assertEqual(loaded.status, "WARN")
            self.assertEqual(loaded.schema_version, VALIDATOR_RESULT_SCHEMA_VERSION)
            self.assertNotEqual(loaded.status, "PASS")
            # Structured warnings in JSON
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(raw["warnings"], list)
            self.assertIsInstance(raw["warnings"][0], dict)
            self.assertIn("warning_id", raw["warnings"][0])
            self.assertIn("message", raw["warnings"][0])

    def test_pass_with_warnings_fails_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "validator_id": "x",
                        "status": "PASS",
                        "errors": [],
                        "warnings": [{"warning_id": "x:w0:abc", "message": "nope"}],
                        "details": {},
                        "checked_at": "2026-01-01T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_validator_result_json(path)

    def test_unknown_status_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "validator_id": "x",
                        "status": "MAYBE",
                        "errors": [],
                        "warnings": [],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_validator_result_json(path)

    def test_stable_warning_id_deterministic(self) -> None:
        a = stable_warning_id("v", "same message", 0)
        b = stable_warning_id("v", "same message", 0)
        self.assertEqual(a, b)

    def test_malformed_json_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"status": "PASS"}', encoding="utf-8")  # missing schema
            with self.assertRaises(ValueError):
                load_validator_result_json(path)

    def test_gate_records_warn_and_strict_fails(self) -> None:
        """Acceptance gate records WARN; strict fails unaccepted WARN; accepted ID allows pass."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Minimal project shell
            (root / "reports" / "agent").mkdir(parents=True)
            (root / "AGENT_PLAN.md").write_text("# plan\n", encoding="utf-8")
            for rel in (
                "reports/agent/00_discovery/core_profile.json",
                "reports/agent/00_discovery/discovery_raw.json",
                "reports/agent/00_discovery/requirements.md",
                "reports/agent/PIPELINE_STATUS.md",
                "reports/agent/CONTEXT_TREE.md",
                "reports/agent/REPORT_INDEX.md",
            ):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".json":
                    path.write_text("{}\n", encoding="utf-8")
                else:
                    path.write_text("# ok\n", encoding="utf-8")

            # Stub validator that emits WARN JSON via a tiny script
            stub = root / "stub_warn.py"
            stub.write_text(
                """
import sys
from pathlib import Path
sys.path.insert(0, r"%s")
from lib_gate_common import print_results, add_output_json_arg
import argparse
p = argparse.ArgumentParser()
add_output_json_arg(p)
p.add_argument("--root", type=Path, default=Path("."))
args = p.parse_args()
raise SystemExit(print_results("Stub", [], ["demo warning for gate"], output_json=args.output_json, validator_id="stub_warn"))
"""
                % str(SCRIPTS).replace("\\", "\\\\"),
                encoding="utf-8",
            )

            # Unit-level: simulate gate run_command JSON consumption
            from run_acceptance_gate import GateReport, CheckResult, run_command

            out_json = root / "warn.json"
            completed = subprocess.run(
                [sys.executable, str(stub), "--root", str(root), "--output-json", str(out_json)],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0)
            loaded = load_validator_result_json(out_json)
            self.assertEqual(loaded.status, "WARN")
            wid = loaded.warning_ids[0]

            gate = GateReport(enforce_warning_policy=True)
            gate.add(
                CheckResult(
                    "stub",
                    "WARN",
                    f"demo warning; warning_ids={wid}",
                )
            )
            gate.finalize(set(), require_explicit_warning_acceptance=True)
            self.assertEqual(gate.overall_status, "FAIL")  # unaccepted WARN under enforce

            gate2 = GateReport(enforce_warning_policy=True)
            gate2.add(CheckResult("stub", "WARN", f"demo; warning_ids={wid}"))
            gate2.finalize({wid.lower()}, require_explicit_warning_acceptance=True)
            self.assertIn(gate2.overall_status, {"PASS", "WARN"})
            # Accepted warning remains visible
            self.assertTrue(any(r.accepted for r in gate2.warning_records))

    def test_missing_json_fails_in_run_command(self) -> None:
        from run_acceptance_gate import run_command

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing.json"
            # python -c "pass" exits 0 but no JSON
            result = run_command(
                [sys.executable, "-c", "print('ok')"],
                root,
                30,
                result_json=missing,
            )
            self.assertEqual(result.status, "FAIL")
            self.assertIn("missing validator result JSON", result.detail)

    def test_exit_json_contradiction_fails(self) -> None:
        from run_acceptance_gate import run_command

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "bad.json"
            write_validator_result_json(
                path,
                build_validator_result("x", ["boom"], []),
            )
            # process exits 0 but JSON is FAIL
            result = run_command(
                [sys.executable, "-c", "print('ok')"],
                root,
                30,
                result_json=path,
            )
            self.assertEqual(result.status, "FAIL")
            self.assertIn("contradict", result.detail.lower())


class ProductionKpiObligationTests(unittest.TestCase):
    def test_pending_and_trusted_in_denominator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            agent.mkdir(parents=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """# KPI

| KPI ID | Display Name | Business Approval Status | Technical Verification Status | SQL Proof | Trust Level |
|---|---|---|---|---|---|
| kpi_pending | Volume A | PENDING_REVIEW | PASS | proofs/a.sql | production |
| kpi_approved | Volume B | APPROVED | PASS | proofs/b.sql | production |
| kpi_draft_only | Draft Only | NOT_REQUESTED | PASS | proofs/c.sql | draft |
""",
                encoding="utf-8",
            )
            presentation = agent / "10_presentation"
            presentation.mkdir(parents=True)
            (presentation / "rendered_metric_manifest.json").write_text(
                json.dumps(
                    {
                        "metrics": [
                            {
                                "kpi_id": "kpi_trusted_blank",
                                "trust_level": "TRUSTED",
                                "technical_status": "PASS",
                            },
                            {
                                "kpi_id": "kpi_pending",
                                "trust_level": "TRUSTED",
                            },
                            {
                                "kpi_id": "kpi_draft_rendered",
                                "trust_level": "DRAFT",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (presentation / "page_registry.json").write_text(
                json.dumps(
                    {
                        "pages": [
                            {
                                "page_id": "exec",
                                "page_class": "executive_overview",
                                "audience": "leadership",
                                "trusted": True,
                                "primary_kpi_ids": ["kpi_dup_a", "kpi_dup_b"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            obligations = discover_production_kpi_obligations(root)
            ids = {o.kpi_id for o in obligations}
            self.assertIn("kpi_pending", ids)
            self.assertIn("kpi_approved", ids)
            self.assertIn("kpi_trusted_blank", ids)
            self.assertIn("kpi_dup_a", ids)
            self.assertIn("kpi_dup_b", ids)
            self.assertNotIn("kpi_draft_only", ids)
            self.assertNotIn("kpi_draft_rendered", ids)
            # Duplicate display names with distinct IDs stay separate
            self.assertEqual(len([o for o in obligations if o.kpi_id.startswith("kpi_dup_")]), 2)
            self.assertGreaterEqual(len(obligations), 5)
            blank = next(o for o in obligations if o.kpi_id == "kpi_trusted_blank")
            self.assertTrue(blank.trusted_or_executive)


class WaiverTests(unittest.TestCase):
    def test_warn_without_waiver_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports" / "agent").mkdir(parents=True)
            waiver, errs, disposition = find_valid_waiver_for_kpi(root, "kpi_x")
            self.assertIsNone(waiver)
            self.assertEqual(disposition, "MISSING_WAIVER")
            self.assertTrue(errs)

    def test_valid_waiver_preserves_calculated_fail_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            agent.mkdir(parents=True)
            evidence = agent / "waiver_evidence.md"
            evidence.write_text("human approved variance\n", encoding="utf-8")
            (agent / "RECONCILIATION_WAIVER_REGISTER.md").write_text(
                """# Waivers

| Waiver ID | Object Type | Object ID | Validation Type | Calculated Status | Calculated Difference | Tolerance | Reason | Business Impact | Risk Owner | Approver | Approval Evidence | Approval Date | Expiry Or Review Condition | Reconciliation Fingerprint | Governance Disposition | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W-001 | kpi | kpi_x | numeric_tolerance | FAIL | 5 | 1 | known lag | low | Risk Owner | Jane Approver | reports/agent/waiver_evidence.md | 2026-01-01 | 2099-01-01 | abc123 | APPROVED_WAIVER | APPROVED_WAIVER |
""",
                encoding="utf-8",
            )
            waiver, errs, disposition = find_valid_waiver_for_kpi(root, "kpi_x", fingerprint="abc123")
            self.assertIsNotNone(waiver)
            self.assertEqual(disposition, "APPROVED_WAIVER")
            self.assertEqual(errs, [])
            # Wrong KPI
            w2, e2, d2 = find_valid_waiver_for_kpi(root, "kpi_other", fingerprint="abc123")
            self.assertIsNone(w2)
            self.assertIn(d2, {"MISSING_WAIVER", "INVALID_WAIVER"})


class AcceptanceRuleTests(unittest.TestCase):
    def test_each_rule_type_positive_and_negative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artifact.txt").write_text("x", encoding="utf-8")
            cases = [
                (
                    {
                        "acceptance_rule_id": "R1",
                        "acceptance_rule_type": "numeric_comparison",
                        "acceptance_rule_description": "within tol",
                        "expected_condition": "10",
                        "evaluated_input": "10",
                        "tolerance": "0",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "R1b",
                        "acceptance_rule_type": "numeric_comparison",
                        "acceptance_rule_description": "within tol",
                        "expected_condition": "10",
                        "evaluated_input": "99",
                        "tolerance": "0",
                        "proof_artifact": "artifact.txt",
                    },
                    "FAIL",
                ),
                (
                    {
                        "acceptance_rule_id": "R2",
                        "acceptance_rule_type": "regex_match",
                        "acceptance_rule_description": "pattern",
                        "expected_condition": r"^OK$",
                        "evaluated_input": "OK",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "R2b",
                        "acceptance_rule_type": "regex_match",
                        "acceptance_rule_description": "pattern",
                        "expected_condition": r"^OK$",
                        "evaluated_input": "NO",
                        "proof_artifact": "artifact.txt",
                    },
                    "FAIL",
                ),
                (
                    {
                        "acceptance_rule_id": "R3",
                        "acceptance_rule_type": "sql_boolean",
                        "acceptance_rule_description": "bool",
                        "evaluated_input": "TRUE",
                        "expected_condition": "TRUE",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "R4",
                        "acceptance_rule_type": "artifact_presence",
                        "acceptance_rule_description": "file exists",
                        "expected_condition": "artifact.txt",
                        "evaluated_input": "1",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "R5",
                        "acceptance_rule_type": "set_constraint",
                        "acceptance_rule_description": "set",
                        "expected_condition": "a,b",
                        "evaluated_input": "a,b",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "R6",
                        "acceptance_rule_type": "row_count_constraint",
                        "acceptance_rule_description": "rows",
                        "expected_condition": "3",
                        "evaluated_input": "3",
                        "tolerance": "0",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "R7",
                        "acceptance_rule_type": "approved_human_decision",
                        "acceptance_rule_description": "human",
                        "business_approval_status": "APPROVED",
                        "approval_evidence": "artifact.txt",
                        "evaluated_input": "yes",
                        "expected_condition": "yes",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "R8",
                        "acceptance_rule_type": "custom_python_predicate",
                        "acceptance_rule_description": "custom",
                        "predicate_name": "nonempty",
                        "evaluated_input": "abc",
                        "expected_condition": "",
                        "proof_artifact": "artifact.txt",
                    },
                    "PASS",
                ),
                (
                    {
                        "acceptance_rule_id": "PASS",
                        "acceptance_rule_type": "numeric_comparison",
                        "acceptance_rule_description": "PASS",
                        "expected_condition": "1",
                        "evaluated_input": "1",
                        "proof_artifact": "artifact.txt",
                    },
                    "FAIL",  # free-text rule id
                ),
                (
                    {
                        "acceptance_rule_id": "R9",
                        "acceptance_rule_type": "unknown_magic",
                        "acceptance_rule_description": "desc",
                        "expected_condition": "1",
                        "evaluated_input": "1",
                        "proof_artifact": "artifact.txt",
                    },
                    "FAIL",
                ),
            ]
            for row, expected in cases:
                got = evaluate_typed_acceptance_rule(
                    root, row, allowlisted_predicates={"nonempty", "equals_expected"}
                )
                self.assertEqual(
                    got["calculated_status"],
                    expected,
                    msg=f"{row.get('acceptance_rule_id')}: {got}",
                )


class LocalPackageAndSourceTests(unittest.TestCase):
    def test_project_package_from_dbt_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dbt_project.yml").write_text("name: my_local_pkg\n", encoding="utf-8")
            self.assertEqual(project_package_name(root), "my_local_pkg")

    def test_source_resolution_requires_both_names(self) -> None:
        inventory = [
            {
                "unique_id": "source.pkg.raw_a.orders",
                "name": "orders",
                "resource_type": "source",
                "package_name": "pkg",
            },
            {
                "unique_id": "source.pkg.raw_b.orders",
                "name": "orders",
                "resource_type": "source",
                "package_name": "pkg",
            },
        ]
        match, status = resolve_source_reference(inventory, "raw_a", "orders")
        self.assertEqual(status, "ok")
        self.assertEqual(match["unique_id"], "source.pkg.raw_a.orders")
        match2, status2 = resolve_source_reference(inventory, "raw_b", "orders")
        self.assertEqual(status2, "ok")
        self.assertEqual(match2["unique_id"], "source.pkg.raw_b.orders")


class IndependentVerifierWarnPropagationTests(unittest.TestCase):
    def test_warn_not_converted_to_pass_in_report_logic(self) -> None:
        from run_independent_verifier import ChildResult, VerificationReport

        report = VerificationReport()
        report.add_child(
            ChildResult(script="x.py", category="c", status="WARN", return_code=0)
        )
        statuses = {r.status for r in report.results}
        self.assertIn("WARN", statuses)
        self.assertNotIn("PASS", statuses)


class BrowserFinalEnforcementTests(unittest.TestCase):
    def test_final_gate_script_list_has_no_skip_live(self) -> None:
        from run_acceptance_gate import PROJECT_VALIDATION_SCRIPTS

        for name, args, _phase in PROJECT_VALIDATION_SCRIPTS:
            if name == "run_independent_verifier.py":
                self.assertNotIn("--skip-live", args)

    def test_require_live_browser_at_final_default(self) -> None:
        from lib_gate_common import load_presentation_policy

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "project.config.yml").write_text(
                "presentation_policy:\n  require_live_browser_validation: true\n"
                "  require_live_browser_at_final: true\n",
                encoding="utf-8",
            )
            policy = load_presentation_policy(root)
            self.assertTrue(policy.get("require_live_browser_at_final"))


class HumanApprovalDenominatorExtraTests(unittest.TestCase):
    def test_zero_approved_with_nonzero_obligations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "reports" / "agent"
            agent.mkdir(parents=True)
            (agent / "KPI_DEFINITION_CONTRACTS.md").write_text(
                """# KPI
| KPI ID | Business Approval Status | Technical Verification Status | SQL Proof | Trust Level |
|---|---|---|---|---|
| kpi_a | PENDING_REVIEW | PASS | a.sql | production |
| kpi_b | NOT_REQUESTED | PASS | b.sql | production |
| kpi_c | PROPOSED | PASS | c.sql | production |
""",
                encoding="utf-8",
            )
            obligations = discover_production_kpi_obligations(root)
            self.assertEqual(len(obligations), 3)
            approved = [
                o
                for o in obligations
                if o.business_approval_status in {"APPROVED", "APPROVED_WITH_CONDITIONS"}
            ]
            self.assertEqual(len(approved), 0)


if __name__ == "__main__":
    unittest.main()
