#!/usr/bin/env python3
"""Focused tests for warehouse-backed report refresh (DuckDB-first)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib_report_runtime import refresh_report_from_warehouse  # noqa: E402


def _write_min_duckdb_project(root: Path) -> tuple[Path, str]:
    import duckdb

    (root / "dbt_project.yml").write_text(
        "name: example\nversion: '1.0.0'\nconfig-version: 2\nprofile: fixture_duckdb\n",
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
        "presentation_policy:\n  require_live_report_refresh_execution: true\n  report_runtime_applicability: required\n",
        encoding="utf-8",
    )
    target = root / "target"
    target.mkdir()
    db_path = target / "fixture.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute("CREATE TABLE main.fct_events AS SELECT 1 AS event_id UNION ALL SELECT 2")
    con.close()
    unique_id = "model.example.fct_events"
    relation_name = '"fixture"."main"."fct_events"'
    (target / "manifest.json").write_text(
        json.dumps(
            {
                "nodes": {
                    unique_id: {
                        "unique_id": unique_id,
                        "name": "fct_events",
                        "alias": "fct_events",
                        "resource_type": "model",
                        "package_name": "example",
                        "database": "fixture",
                        "schema": "main",
                        "relation_name": relation_name,
                        "config": {"enabled": True},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    report = root / "reports" / "agent" / "10_presentation" / "matplotlib"
    report.mkdir(parents=True)
    sql_dir = report / "sql_verification"
    sql_dir.mkdir()
    (sql_dir / "010_volume.sql").write_text(
        "-- expected result: 2\n-- captured result: 2\n-- status: PASS\nselect count(*) from main.fct_events;\n",
        encoding="utf-8",
    )
    (report / "query_registry.json").write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query_id": "q_volume",
                        "sql_path": "reports/agent/10_presentation/matplotlib/sql_verification/010_volume.sql",
                        "source_resource_ids": [unique_id],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report / "chart_registry.json").write_text(
        json.dumps(
            {
                "charts": [
                    {
                        "chart_id": "volume_trend",
                        "query_id": "q_volume",
                        "metric_ids": ["KPI-001"],
                        "source_resource_ids": [unique_id],
                        "data": [{"period_label": "Mar", "value": 0, "formatted_value": "0"}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report / "rendered_metric_manifest.json").write_text(
        json.dumps(
            {
                "metrics": [
                    {
                        "metric_id": "KPI-001",
                        "query_id": "q_volume",
                        "value": 0,
                        "formatted_value": "0",
                    }
                ],
                "measure_board": [],
                "metric_board": [],
            }
        ),
        encoding="utf-8",
    )
    return report, unique_id


class ReportRuntimeRefreshTests(unittest.TestCase):
    def test_duckdb_live_refresh_regenerates_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            report, _ = _write_min_duckdb_project(root)
            before = json.loads((report / "rendered_metric_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(before["metrics"][0]["value"], 0)

            payload = refresh_report_from_warehouse(root, report)
            self.assertEqual(payload["status"], "PASS", payload)
            self.assertTrue(payload.get("execution_ids"))
            self.assertTrue(payload.get("result_hashes"))
            self.assertTrue(payload.get("data_version"))
            runtime = json.loads((report / "runtime_execution.json").read_text(encoding="utf-8"))
            self.assertEqual(runtime["status"], "PASS")

            after = json.loads((report / "rendered_metric_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(after["metrics"][0]["value"], 2)

    def test_failed_query_blocks_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            report, unique_id = _write_min_duckdb_project(root)
            (report / "sql_verification" / "010_volume.sql").write_text(
                "select count(*) from main.does_not_exist;\n",
                encoding="utf-8",
            )
            payload = refresh_report_from_warehouse(root, report)
            self.assertEqual(payload["status"], "FAIL", payload)
            self.assertTrue(payload.get("errors"))
            # Prior metric payload must not be rewritten as success.
            metrics = json.loads((report / "rendered_metric_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(metrics["metrics"][0]["value"], 0)

    def test_static_timestamp_only_refresh_is_not_pass_without_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            report, _ = _write_min_duckdb_project(root)
            (report / "query_registry.json").write_text(json.dumps({"queries": []}), encoding="utf-8")
            payload = refresh_report_from_warehouse(root, report)
            self.assertEqual(payload["status"], "BLOCKED")
            self.assertIn("no query_registry", " ".join(payload.get("errors") or []))


if __name__ == "__main__":
    unittest.main()
