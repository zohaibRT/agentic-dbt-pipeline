#!/usr/bin/env python3
"""Focused tests for DuckDB live KPI proof SQL execution."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib_report_runtime import execute_kpi_proof_sql  # noqa: E402


class KpiProofExecutionTests(unittest.TestCase):
    def _project(self, root: Path) -> Path:
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
        target = root / "target"
        target.mkdir()
        db_path = target / "fixture.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE main.fct_events AS SELECT 1 AS id UNION ALL SELECT 2 UNION ALL SELECT 3")
        con.close()
        (target / "manifest.json").write_text(
            json.dumps(
                {
                    "nodes": {
                        "model.example.fct_events": {
                            "unique_id": "model.example.fct_events",
                            "name": "fct_events",
                            "alias": "fct_events",
                            "resource_type": "model",
                            "schema": "main",
                            "relation_name": '"fixture"."main"."fct_events"',
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        proofs = root / "reports" / "agent" / "sql_proofs"
        proofs.mkdir(parents=True)
        return proofs

    def test_duckdb_executes_proof_and_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            proofs = self._project(root)
            path = proofs / "010_volume.sql"
            path.write_text(
                "-- expected result: 3\n-- captured result: 3\n-- tolerance: 0\n"
                "-- status: PASS\nselect count(*) from {{ ref('fct_events') }};\n",
                encoding="utf-8",
            )
            result = execute_kpi_proof_sql(root, path)
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["live_value"], 3)

    def test_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            proofs = self._project(root)
            path = proofs / "010_volume.sql"
            path.write_text(
                "-- expected result: 99\n-- captured result: 99\n-- tolerance: 0\n"
                "-- status: PASS\nselect count(*) from main.fct_events;\n",
                encoding="utf-8",
            )
            result = execute_kpi_proof_sql(root, path)
            self.assertEqual(result["status"], "FAIL", result)
            self.assertIn("mismatch", (result.get("error") or "").lower())

    def test_non_duckdb_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "proj"
            root.mkdir()
            (root / "dbt_project.yml").write_text(
                "name: example\nversion: '1.0.0'\nconfig-version: 2\nprofile: snow\n",
                encoding="utf-8",
            )
            (root / "profiles.yml").write_text(
                "snow:\n  target: dev\n  outputs:\n    dev:\n      type: snowflake\n      account: x\n",
                encoding="utf-8",
            )
            path = root / "proof.sql"
            path.write_text(
                "-- expected result: 1\n-- captured result: 1\nselect 1;\n",
                encoding="utf-8",
            )
            result = execute_kpi_proof_sql(root, path)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("unsupported", (result.get("error") or "").lower())


if __name__ == "__main__":
    unittest.main()
