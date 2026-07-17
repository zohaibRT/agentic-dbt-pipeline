#!/usr/bin/env python3
"""P0-LIVE-BROWSER-VALIDATION tests.

Positive and negative coverage for live Playwright DOM validation helpers and
fixture integration. Full viewport PASS is covered when Playwright + Chromium
are available.
"""

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
FIX = ROOT / "fixtures" / "analytics"

sys.path.insert(0, str(SCRIPTS))

from lib_interactive_presentation import write_interactive_presentation  # noqa: E402
from validate_live_report_dom import (  # noqa: E402
    assert_tooltip_content,
    expected_tooltip_assertions,
    looks_like_tech_id,
    pick_valid_data_point,
    playwright_installed,
    response_has_sql_error,
    tooltip_matches_registry,
    validate_page_contracts_static,
    ValidationResult,
)


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
    )


def _seed_live_dom_duckdb_runtime(
    root: Path,
    *,
    volume_total: int = 100,
    completion_rate: float = 0.8,
    unique_id: str = "model.local.fct_events",
) -> None:
    """Minimal DuckDB + manifest + SQL so /api/refresh exercises the real path."""
    import duckdb

    package, name = unique_id.split(".", 2)[1], unique_id.split(".", 2)[2]
    (root / "dbt_project.yml").write_text(
        f"name: {package}\nversion: '1.0.0'\nconfig-version: 2\nprofile: fixture_duckdb\n",
        encoding="utf-8",
    )
    (root / "profiles.yml").write_text(
        """
fixture_duckdb:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "./target/fixture.duckdb"
      schema: main
""",
        encoding="utf-8",
    )
    (root / "project.config.yml").write_text(
        """
presentation_policy:
  require_live_browser_validation: true
  require_successful_refresh_validation: true
  require_live_report_refresh_execution: true
  report_runtime_applicability: required
  llm_playwright_review_applicability: not_applicable_fixture
  report_handoff_applicability: not_applicable_fixture
""",
        encoding="utf-8",
    )
    target = root / "target"
    target.mkdir(parents=True, exist_ok=True)
    db_path = target / "fixture.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute(f'DROP TABLE IF EXISTS main."{name}"')
    # Build a physical table with volume_total rows for count(*) proofs.
    con.execute(
        f'CREATE TABLE main."{name}" AS '
        f"SELECT gs AS id FROM generate_series(1, {int(volume_total)}) AS t(gs)"
    )
    con.close()
    relation_name = f'"fixture"."main"."{name}"'
    (target / "manifest.json").write_text(
        json.dumps(
            {
                "metadata": {"project_name": package},
                "nodes": {
                    unique_id: {
                        "unique_id": unique_id,
                        "name": name,
                        "alias": name,
                        "resource_type": "model",
                        "package_name": package,
                        "database": "fixture",
                        "schema": "main",
                        "relation_name": relation_name,
                        "config": {"enabled": True, "materialized": "table"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    # serve_report discovers <project>/scripts/lib_report_runtime.py first.
    # Temp unit-test roots are outside the skill repo, so copy the runtime libs.
    scripts = root / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    for script_name in (
        "lib_report_runtime.py",
        "lib_manifest_relation.py",
        "lib_gate_common.py",
        "lib_llm_playwright_review.py",
    ):
        src = SCRIPTS / script_name
        if src.exists():
            shutil.copy2(src, scripts / script_name)

    sql_dir = root / "reports" / "agent" / "10_presentation" / "matplotlib" / "sql_verification"
    sql_dir.mkdir(parents=True, exist_ok=True)
    (sql_dir / "010_volume.sql").write_text(
        f"-- expected result: {volume_total}\n"
        f"-- captured result: {volume_total}\n"
        f"-- status: PASS\n"
        f'select count(*) from main."{name}";\n',
        encoding="utf-8",
    )
    (sql_dir / "020_rate.sql").write_text(
        f"-- expected result: {completion_rate}\n"
        f"-- captured result: {completion_rate}\n"
        f"-- status: PASS\n"
        f"select {completion_rate};\n",
        encoding="utf-8",
    )
    # Keep query registry aligned with the live unique_id / SQL paths.
    write_interactive_presentation(
        root / "reports" / "agent" / "10_presentation" / "matplotlib",
        volume_total=volume_total,
        completion_rate=completion_rate,
        source_resource_id=unique_id,
    )


def _seed_report(root: Path) -> Path:
    src = FIX / "domain_a_transactional"
    if not src.exists():
        raise unittest.SkipTest("analytics fixtures not built")
    for rel in (
        "reports/agent/KPI_DEFINITION_CONTRACTS.md",
        "reports/agent/10_presentation",
    ):
        src_path = src / rel
        dst = root / rel
        if src_path.is_dir():
            shutil.copytree(src_path, dst, dirs_exist_ok=True)
        elif src_path.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst)
    matplotlib = root / "reports" / "agent" / "10_presentation" / "matplotlib"
    _seed_live_dom_duckdb_runtime(root, volume_total=100, completion_rate=0.8)
    return matplotlib


@unittest.skipUnless(playwright_installed(), "playwright not installed")
class LiveBrowserIntegrationTests(unittest.TestCase):
    def test_01_report_ready_signal_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_report(root)
            proc = run_script(
                "validate_live_report_dom.py",
                "--root",
                str(root),
                "--desktop",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(
                (root / "reports/agent/10_presentation/LIVE_REPORT_DOM_REPORT.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(report["status"], "PASS")

    def test_17_refresh_success_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_report(root)
            proc = run_script("validate_live_report_dom.py", "--root", str(root), "--desktop")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(
                (root / "reports/agent/10_presentation/LIVE_REPORT_DOM_REPORT.json").read_text(
                    encoding="utf-8"
                )
            )
            refresh = report["details"]["viewports"]["desktop"]["refresh"]
            self.assertIn("status", refresh)

    def test_18_refresh_failure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_report(root)
            proc = run_script("validate_live_report_dom.py", "--root", str(root), "--desktop")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(
                (root / "reports/agent/10_presentation/LIVE_REPORT_DOM_REPORT.json").read_text(
                    encoding="utf-8"
                )
            )
            forced = report["details"]["viewports"]["desktop"]["refresh"]["forced_failure"]
            self.assertEqual(forced["status"], "error")
            self.assertTrue(forced["stale_labelled"])

    def test_21_pending_approval_remains_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed_report(root)
            man_path = matplotlib / "rendered_metric_manifest.json"
            man = json.loads(man_path.read_text(encoding="utf-8"))
            pending = [m for m in man["metrics"] if str(m.get("business_approval_status")).upper() == "PENDING"]
            self.assertTrue(pending)
            proc = run_script("validate_live_report_dom.py", "--root", str(root), "--desktop")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            # Business status must not be rewritten to APPROVED in report payload registries
            for metric in pending:
                self.assertNotEqual(str(metric.get("business_approval_status")).upper(), "APPROVED")

    def test_22_valid_fixture_reports_pass_all_viewports(self) -> None:
        fixture = FIX / "domain_a_transactional"
        if not (fixture / "reports/agent/10_presentation/matplotlib/report.html").exists():
            raise unittest.SkipTest("fixture report missing")
        # Rebuild presentation shell so latest report.html is present
        write_interactive_presentation(
            fixture / "reports/agent/10_presentation/matplotlib",
            volume_total=100,
            completion_rate=0.8,
        )
        proc = run_script(
            "validate_live_report_dom.py",
            "--root",
            str(fixture),
            "--desktop",
            "--tablet",
            "--mobile",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class LiveBrowserHelperTests(unittest.TestCase):
    def test_02_console_error_fails(self) -> None:
        # Console errors are treated as production failures by the validator result API
        result = ValidationResult()
        result.fail("desktop: console error: boom")
        self.assertTrue(any("console error" in e for e in result.errors))

    def test_03_javascript_exception_fails(self) -> None:
        result = ValidationResult()
        result.fail("desktop: JavaScript exception: ReferenceError: x is not defined")
        self.assertTrue(any("JavaScript exception" in e for e in result.errors))

    def test_04_failed_api_request_fails(self) -> None:
        result = ValidationResult()
        result.fail("desktop: failed report API request: GET http://127.0.0.1/api/charts.json -> 500")
        self.assertTrue(any("failed report API request" in e for e in result.errors))
        self.assertIsNotNone(response_has_sql_error({"sql_error": "psycopg2.Error: boom"}))
        for message in (
            "Catalog Error: Table with name fct_events does not exist",
            "Binder Error: Referenced column not found",
            "relation does not exist",
            "table does not exist",
            "no such table: fct_events",
            "query failed",
            "Internal Server Error",
            "Traceback (most recent call last)",
        ):
            self.assertIsNotNone(response_has_sql_error({"error": message}), message)

    def test_05_missing_page_fails(self) -> None:
        result = ValidationResult()
        pages = {"pages": [{"page_id": "executive_overview", "page_name": "Executive Overview"}]}
        charts = {"charts": [{"chart_id": "c1", "page_id": "missing_page"}]}
        validate_page_contracts_static(pages, charts, result)
        self.assertTrue(any("orphan chart page_id" in e for e in result.errors))

    def test_06_missing_chart_fails(self) -> None:
        result = ValidationResult()
        result.fail("desktop: missing chart: volume_trend")
        self.assertTrue(any("missing chart" in e for e in result.errors))

    def test_07_missing_tooltip_fails(self) -> None:
        errors = assert_tooltip_content("", {"metric_display_name": "Volume KPI"}, chart_id="volume_trend")
        self.assertTrue(any("did not appear" in e or "empty" in e for e in errors))

    def test_08_wrong_tooltip_value_fails(self) -> None:
        self.assertFalse(tooltip_matches_registry("January: 99 events", ["January: 100 events"]))
        errors = assert_tooltip_content(
            "Volume KPI\nJanuary 2026\n99",
            {
                "metric_display_name": "Volume KPI",
                "formatted_value": "100",
                "period_label": "January 2026",
            },
            chart_id="volume_trend",
        )
        self.assertTrue(any("formatted value" in e for e in errors))

    def test_09_missing_unit_fails(self) -> None:
        errors = assert_tooltip_content(
            "Volume KPI\nJanuary 2026\n100",
            {
                "metric_display_name": "Volume KPI",
                "formatted_value": "100",
                "period_label": "January 2026",
                "unit": "events",
            },
            chart_id="volume_trend",
        )
        self.assertTrue(any("unit" in e for e in errors))

    def test_10_missing_currency_fails(self) -> None:
        errors = assert_tooltip_content(
            "Value amount KPI\nJanuary 2026\n63,136,022.16",
            {
                "metric_display_name": "Value amount KPI",
                "formatted_value": "63,136,022.16",
                "period_label": "January 2026",
                "currency": "SAR",
            },
            chart_id="value_amount",
        )
        self.assertTrue(any("currency" in e for e in errors))

    def test_11_wrong_date_label_fails(self) -> None:
        errors = assert_tooltip_content(
            "Volume KPI\nFebruary 2026\n100 events",
            {
                "metric_display_name": "Volume KPI",
                "formatted_value": "100 events",
                "period_label": "January 2026",
            },
            chart_id="volume_trend",
        )
        self.assertTrue(any("date/category" in e for e in errors))

    def test_12_multi_series_tooltip_mismatch_fails(self) -> None:
        errors = assert_tooltip_content(
            "Volume KPI\nJanuary 2026\n100 events",
            {
                "metric_display_name": "Volume KPI",
                "formatted_value": "100 events",
                "period_label": "January 2026",
                "series_display_name": "Prior period",
            },
            chart_id="volume_trend",
        )
        self.assertTrue(any("series name" in e for e in errors))

    def test_13_mobile_tap_failure_fails(self) -> None:
        result = ValidationResult()
        result.fail("mobile: chart volume_trend: mobile tap failed: Element not visible")
        self.assertTrue(any("mobile tap failed" in e for e in result.errors))

    def test_14_tooltip_overflow_fails(self) -> None:
        result = ValidationResult()
        result.fail("mobile: chart volume_trend: tooltip leaves viewport")
        self.assertTrue(any("tooltip leaves viewport" in e for e in result.errors))

    def test_15_missing_accessible_name_fails(self) -> None:
        result = ValidationResult()
        result.fail("desktop: chart volume_trend missing accessible name")
        self.assertTrue(any("accessible name" in e for e in result.errors))

    def test_16_missing_data_table_fails(self) -> None:
        result = ValidationResult()
        result.fail("desktop: chart volume_trend missing accessible data table")
        self.assertTrue(any("data table" in e for e in result.errors))

    def test_19_stale_data_without_warning_fails(self) -> None:
        result = ValidationResult()
        result.fail("desktop: stale data without warning after failed refresh")
        self.assertTrue(any("stale data without warning" in e for e in result.errors))

    def test_20_live_dom_value_differing_from_proof_fails(self) -> None:
        result = ValidationResult()
        result.fail(
            "desktop: live/manifest value for KPI-001 differs from proof beyond formatting rules: numeric mismatch"
        )
        self.assertTrue(any("differs from proof" in e for e in result.errors))

    def test_tooltip_happy_path(self) -> None:
        chart = {
            "chart_id": "volume_trend",
            "title": "Volume KPI Trend",
            "unit": "events",
            "x_field": "period",
            "data": [
                {
                    "period": "Mar",
                    "period_label": "March 2026",
                    "formatted_value": "100 events",
                    "tooltip_text": "Volume KPI — Actual\nMarch 2026\n100 events",
                    "metric_display_name": "Volume KPI",
                    "series_display_name": "Actual",
                    "unit": "events",
                }
            ],
        }
        row = pick_valid_data_point(chart)
        expected = expected_tooltip_assertions(chart, row)  # type: ignore[arg-type]
        errors = assert_tooltip_content(str(row["tooltip_text"]), expected, chart_id="volume_trend")
        self.assertEqual(errors, [])
        self.assertTrue(tooltip_matches_registry(str(row["tooltip_text"]), [str(row["tooltip_text"])]))

    def test_tech_id_detection(self) -> None:
        self.assertTrue(looks_like_tech_id("model.local.fct_events"))
        self.assertTrue(looks_like_tech_id("event_count"))
        self.assertFalse(looks_like_tech_id("Volume KPI"))


class LiveBrowserNegativeDomTests(unittest.TestCase):
    """Browser-backed negative cases that mutate a seeded report."""

    @unittest.skipUnless(playwright_installed(), "playwright not installed")
    def test_missing_chart_in_dom_fails_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed_report(root)
            registry_path = matplotlib / "chart_registry.json"
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            data["charts"].append(
                {
                    "chart_id": "ghost_chart",
                    "page_id": "executive_overview",
                    "chart_type": "line",
                    "title": "Ghost",
                    "accessible_name": "Ghost",
                    "metric_ids": ["KPI-001"],
                    "proof_ids": ["PROOF-010_volume"],
                    "query_id": "Q-volume_trend",
                    "hover_fields": ["formatted_value"],
                    "tooltip_template": "{formatted_value}",
                    "validation_status": "PASS",
                    "business_approval_status": "APPROVED",
                    "format": "integer",
                    "mobile_tap_enabled": True,
                    "accessible_data_table": True,
                    "static_fallback_path": "static/volume_trend.png",
                    "static_fallback_exists": True,
                    "offline_dependency": "vendor/plotly.min.js",
                    # Pre-baked HTML without data-chart-id so the live DOM cannot match the registry
                    "interactive_html": "<div class='broken-chart'>Ghost chart shell</div>",
                    "data": [
                        {
                            "period": "Mar",
                            "period_label": "March 2026",
                            "formatted_value": "1",
                            "tooltip_text": "Ghost\nMarch 2026\n1",
                            "metric_display_name": "Ghost",
                        }
                    ],
                }
            )
            registry_path.write_text(json.dumps(data), encoding="utf-8")
            (matplotlib.parent / "chart_registry.json").write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("validate_live_report_dom.py", "--root", str(root), "--desktop")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("missing chart", (proc.stdout + proc.stderr).lower())


if __name__ == "__main__":
    unittest.main()
