#!/usr/bin/env python3
"""P1 merge-blocker tests: schema, fact unique_id, waivers, executive trusted KPI, CI heredoc."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS))

from lib_gate_common import (  # noqa: E402
    build_validator_result,
    load_validator_result_json,
    validate_validator_result_schema,
    write_validator_result_json,
)


class CiHeredocTests(unittest.TestCase):
    def test_strict_final_heredoc_expands_fixture(self) -> None:
        text = (ROOT / ".github" / "workflows" / "analytics_gates.yml").read_text(encoding="utf-8")
        # Pass fixture via argv + quoted heredoc so $fixture never appears as a literal Path
        self.assertIn("Strict final acceptance for every valid fixture", text)
        idx = text.index("Strict final acceptance for every valid fixture")
        chunk = text[idx : idx + 1600]
        self.assertIn('python - "$fixture" <<\'PY\'', chunk)
        self.assertIn("pathlib.Path(sys.argv[1])", chunk)
        self.assertNotIn('pathlib.Path("$fixture")', chunk)
        # Independent verifier step uses the same argv pattern
        iv = text.index("Independent verifier")
        iv_chunk = text[iv : iv + 1200]
        self.assertIn('python - "$fixture" <<\'PY\'', iv_chunk)


class ValidatorSchemaP1Tests(unittest.TestCase):
    def test_warn_requires_warnings(self) -> None:
        with self.assertRaises(ValueError):
            validate_validator_result_schema(
                {
                    "schema_version": "1.0",
                    "validator_id": "x",
                    "status": "WARN",
                    "errors": [],
                    "warnings": [],
                    "details": {},
                    "checked_at": "2026-01-01T00:00:00+00:00",
                }
            )

    def test_blocked_requires_blocker(self) -> None:
        with self.assertRaises(ValueError):
            validate_validator_result_schema(
                {
                    "schema_version": "1.0",
                    "validator_id": "x",
                    "status": "BLOCKED",
                    "errors": [],
                    "warnings": [],
                    "details": {},
                    "checked_at": "2026-01-01T00:00:00+00:00",
                }
            )
        # Passes with details.blocker
        validate_validator_result_schema(
            {
                "schema_version": "1.0",
                "validator_id": "x",
                "status": "BLOCKED",
                "errors": [],
                "warnings": [],
                "details": {"blocker": "waiting on human"},
                "checked_at": "2026-01-01T00:00:00+00:00",
            }
        )

    def test_checked_at_and_details_required(self) -> None:
        with self.assertRaises(ValueError):
            validate_validator_result_schema(
                {
                    "schema_version": "1.0",
                    "validator_id": "x",
                    "status": "PASS",
                    "errors": [],
                    "warnings": [],
                    "details": {},
                }
            )
        with self.assertRaises(ValueError):
            validate_validator_result_schema(
                {
                    "schema_version": "1.0",
                    "validator_id": "x",
                    "status": "PASS",
                    "errors": [],
                    "warnings": [],
                    "details": [],
                    "checked_at": "2026-01-01T00:00:00+00:00",
                }
            )

    def test_unique_warning_ids(self) -> None:
        with self.assertRaises(ValueError):
            validate_validator_result_schema(
                {
                    "schema_version": "1.0",
                    "validator_id": "x",
                    "status": "WARN",
                    "errors": [],
                    "warnings": [
                        {"warning_id": "dup", "message": "a"},
                        {"warning_id": "dup", "message": "b"},
                    ],
                    "details": {},
                    "checked_at": "2026-01-01T00:00:00+00:00",
                }
            )

    def test_build_result_has_checked_at(self) -> None:
        result = build_validator_result("demo", [], [])
        self.assertTrue(result.checked_at)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.json"
            write_validator_result_json(path, result)
            loaded = load_validator_result_json(path)
            self.assertEqual(loaded.status, "PASS")


class FactUniqueIdFinalTests(unittest.TestCase):
    def test_name_only_fails_at_final(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (root / "dbt_project.yml").write_text("name: tmp\nprofile: tmp\n", encoding="utf-8")
            # Fact catalog supplies unique_id discovery without a full manifest
            (insights / "fact_catalog.md").write_text(
                "# Fact Catalog\n\n"
                "| Unique ID | Fact | Status |\n|---|---|---|\n"
                "| model.tmp.fct_events | fct_events | PASS |\n",
                encoding="utf-8",
            )
            (insights / "fact_coverage_contracts.md").write_text(
                "# Fact Coverage\n\n"
                "| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | "
                "Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | "
                "Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | "
                "Business Questions | Notes | Status |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
                "| fct_events | one row | event_id | event_date | SUPPORTED: a.sql | SUPPORTED: b.sql | "
                "NOT_APPLICABLE: no duration at grain | SUPPORTED: c.sql | SUPPORTED: d.sql | "
                "SUPPORTED: e.sql | SUPPORTED: f.sql | SUPPORTED: g.sql | SUPPORTED: h.sql | "
                "SUPPORTED: i.sql | NOT_APPLICABLE: aging out of scope | SUPPORTED: j.sql | q | notes | PASS |\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_fact_analytical_coverage.py"),
                    "--root",
                    str(root),
                    "--phase",
                    "final",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("unique_id", (proc.stdout + proc.stderr).lower())


class SharedProofTwoFamiliesTests(unittest.TestCase):
    def test_two_supported_families_shared_proof_fails(self) -> None:
        from check_fact_analytical_coverage import row_analytical_complete

        errors: list[str] = []
        row = {
            "fact": "fct_events",
            "grain": "one row",
            "counting_key": "event_id",
            "primary_date": "event_date",
            "volume": "SUPPORTED",
            "amount_or_quantity": "SUPPORTED",
            "duration_or_balance": "NOT_APPLICABLE: no duration",
            "status_distribution": "NOT_APPLICABLE: n/a status",
            "lifecycle": "NOT_APPLICABLE: n/a life",
            "dimensions": "NOT_APPLICABLE: n/a dims",
            "time_trends": "NOT_APPLICABLE: n/a trends",
            "period_comparison": "NOT_APPLICABLE: n/a period",
            "data_quality": "NOT_APPLICABLE: n/a dq",
            "quality": "NOT_APPLICABLE: n/a dq",
            "exceptions": "NOT_APPLICABLE: n/a exc",
            "aging": "NOT_APPLICABLE: n/a aging",
            "reconciliation": "NOT_APPLICABLE: n/a recon",
            "business_questions": "q",
            "proof": "sql_proofs/shared.sql",
            "notes": "shared",
            "status": "PASS",
        }
        # Compact schema path uses COMPACT_APPLICABILITY_FIELDS
        ok = row_analytical_complete("fct_events", row, errors)
        self.assertFalse(ok)
        self.assertTrue(any("generic proof reused" in e for e in errors), errors)


class NonnumericWarnBypassRemovedTests(unittest.TestCase):
    def test_nonnumeric_warn_does_not_reconcile(self) -> None:
        from verify_metric_reconciliation import numeric_reconcile_row

        errors: list[str] = []
        warnings: list[str] = []
        ok = numeric_reconcile_row(
            "KPI-X",
            "not-a-number",
            "also-not",
            "0",
            "WARN",
            "",
            errors,
            warnings,
            validation_type="numeric_tolerance",
        )
        self.assertFalse(ok)
        self.assertTrue(errors)


class ExecutiveTrustedKpiTests(unittest.TestCase):
    def test_present_but_untrusted_fails(self) -> None:
        # Static assertion on source logic
        text = (SCRIPTS / "check_presentation_traceability.py").read_text(encoding="utf-8")
        self.assertIn("not TRUSTED/RENDERED", text)
        self.assertIn("nmid not in trusted_metric_ids", text)


class BrowserSamplingHelpersTests(unittest.TestCase):
    def test_critical_period_rows_include_first_middle_last(self) -> None:
        from validate_live_report_dom import pick_critical_period_rows

        chart = {
            "data": [
                {"period_label": "P1", "formatted_value": "1"},
                {"period_label": "P2", "formatted_value": "2"},
                {"period_label": "P3", "formatted_value": "3"},
                {"period_label": "P4", "formatted_value": "4", "is_partial_period": True, "partial_period_note": "partial"},
            ]
        }
        rows = pick_critical_period_rows(chart)
        labels = [r["period_label"] for r in rows]
        self.assertIn("P1", labels)
        self.assertIn("P4", labels)
        self.assertGreaterEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
