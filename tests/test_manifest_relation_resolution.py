#!/usr/bin/env python3
"""Regression: exact unique_id resolution rejects shortened wrong relations."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib_manifest_relation import (  # noqa: E402
    physical_relation_exists,
    resolve_registered_relations,
    resolve_unique_id,
)


class ManifestRelationResolutionTests(unittest.TestCase):
    def test_exact_unique_id_resolves_and_short_name_fails(self) -> None:
        import duckdb

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "example"
            root.mkdir()
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
            # Physical table uses the full alias — shortened fct_events does not exist.
            con.execute('CREATE TABLE main."fct_alpha__events" AS SELECT 1 AS event_id')
            con.close()

            unique_id = "model.example.fct_alpha__events"
            relation_name = '"fixture"."main"."fct_alpha__events"'
            (target / "manifest.json").write_text(
                json.dumps(
                    {
                        "nodes": {
                            unique_id: {
                                "unique_id": unique_id,
                                "name": "fct_alpha__events",
                                "alias": "fct_alpha__events",
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
            presentation = root / "reports" / "agent" / "10_presentation"
            presentation.mkdir(parents=True)
            (presentation / "chart_registry.json").write_text(
                json.dumps(
                    {
                        "charts": [
                            {
                                "chart_id": "volume_trend",
                                "source_resource_ids": [unique_id],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            exact = resolve_unique_id(root, unique_id, require_physical=True)
            self.assertEqual(exact["status"], "PASS", exact)
            self.assertEqual(exact["relation_name"], relation_name)
            self.assertTrue(exact["physical_exists"])

            # Bare / shortened names are forbidden as unique_ids.
            short = resolve_unique_id(root, "fct_events", require_physical=True)
            self.assertEqual(short["status"], "FAIL")
            self.assertIn("not_an_exact_unique_id", short["notes"])

            # Wrong unique_id that would imply a shortened table must fail lookup.
            wrong = resolve_unique_id(root, "model.example.fct_events", require_physical=True)
            self.assertEqual(wrong["status"], "FAIL")
            self.assertIn("not found", (wrong.get("notes") or "").lower())

            # Physical check: shortened table name does not exist.
            exists, err = physical_relation_exists(
                adapter="duckdb",
                connection_path=str(db_path),
                relation_name='"main"."fct_events"',
                schema="main",
                alias="fct_events",
            )
            self.assertFalse(exists)
            self.assertTrue(err)

            report = resolve_registered_relations(root, require_physical=True)
            self.assertEqual(report["status"], "PASS", report)
            self.assertIn(unique_id, report["resolved_relations"])

            # Registering only a shortened identity must fail handoff-style resolution.
            (presentation / "chart_registry.json").write_text(
                json.dumps(
                    {
                        "charts": [
                            {
                                "chart_id": "volume_trend",
                                "source_resource_ids": ["fct_events"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            bad = resolve_registered_relations(root, require_physical=True)
            self.assertEqual(bad["status"], "FAIL")
            self.assertTrue(bad["errors"])


class McpObservationWriterTests(unittest.TestCase):
    def test_writer_requires_observations_json(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "write_llm_playwright_review_from_mcp.py"),
                    "--root",
                    str(root),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("observations-json", (proc.stdout + proc.stderr).lower())

    def test_writer_does_not_invent_pass_without_observations(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            obs = Path(tmp) / "obs.json"
            obs.write_text(json.dumps({"interactions": []}), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "write_llm_playwright_review_from_mcp.py"),
                    "--root",
                    str(root),
                    "--observations-json",
                    str(obs),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("non-empty", (proc.stdout + proc.stderr).lower())


if __name__ == "__main__":
    unittest.main()
