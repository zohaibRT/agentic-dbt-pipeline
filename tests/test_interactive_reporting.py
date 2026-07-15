#!/usr/bin/env python3
"""Tests for interactive charting and presentation validators."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TEMPLATES = ROOT / "templates" / "reports" / "10_presentation" / "matplotlib"

sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(TEMPLATES))

from chart_renderer import format_display_value  # noqa: E402
from validate_live_report_dom import tooltip_matches_registry  # noqa: E402


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd, cwd=str(SCRIPTS), capture_output=True, text=True)


class FormatDisplayValueTests(unittest.TestCase):
    def test_integer_with_unit(self) -> None:
        self.assertEqual(format_display_value(100, "integer", unit="events"), "100 events")

    def test_percent_precision(self) -> None:
        self.assertEqual(format_display_value(0.8, "percent", precision=1), "80.0%")

    def test_currency(self) -> None:
        self.assertEqual(format_display_value(12.5, "currency", currency="$", precision=2), "$12.50")


class ChartRegistryValidatorTests(unittest.TestCase):
    def _write_registry(self, root: Path, charts: list[dict]) -> None:
        matplotlib = root / "reports" / "agent" / "10_presentation" / "matplotlib"
        matplotlib.mkdir(parents=True, exist_ok=True)
        (matplotlib / "chart_registry.json").write_text(
            json.dumps({"version": "1", "charts": charts}, indent=2),
            encoding="utf-8",
        )
        (matplotlib / "rendered_metric_manifest.json").write_text(
            json.dumps(
                {
                    "version": "1",
                    "metrics": [
                        {
                            "metric_id": "KPI-001",
                            "display_name": "Volume KPI",
                            "chart_ids": ["volume_trend"],
                            "card_ids": ["volume_card"],
                            "proof_ids": ["010_volume"],
                            "formatted_value": "100",
                        }
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def test_duplicate_chart_id_fails(self) -> None:
        chart = {
            "chart_id": "volume_trend",
            "page_id": "executive_overview",
            "chart_type": "line",
            "title": "Volume",
            "metric_ids": ["KPI-001"],
            "proof_ids": ["010_volume"],
            "data": [{"formatted_value": "100", "tooltip_text": "100"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_registry(root, [chart, chart])
            proc = run_script("validate_chart_registry.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("duplicate chart_id", proc.stdout + proc.stderr)


class TooltipMatcherTests(unittest.TestCase):
    def test_exact_match_passes(self) -> None:
        self.assertTrue(
            tooltip_matches_registry("January: 100 events", ["January: 100 events", "90 events"])
        )

    def test_mismatch_fails(self) -> None:
        self.assertFalse(tooltip_matches_registry("January: 99 events", ["January: 100 events"]))


class DuckDbFixtureGateTests(unittest.TestCase):
    @unittest.skipUnless(
        (ROOT / "fixtures" / "dbt_duckdb" / "domain_a_transactional").exists(),
        "DuckDB fixture not built",
    )
    def test_duckdb_fixture_passes_final_strict_gate(self) -> None:
        """Rebuild domain_a if needed, then run final strict acceptance gate."""
        fixture_root = ROOT / "fixtures" / "dbt_duckdb" / "domain_a_transactional"
        plan = fixture_root / "AGENT_PLAN.md"
        if not plan.exists():
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "build_dbt_duckdb_fixtures.py")],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        proc = run_script(
            "run_acceptance_gate.py",
            "--root",
            str(fixture_root),
            "--phase",
            "final",
            "--strict",
            "--skip-dbt",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        combined = (proc.stdout + proc.stderr).lower()
        self.assertTrue(
            "overall status: pass" in combined or "acceptance gate overall status: pass" in combined,
            combined,
        )


if __name__ == "__main__":
    unittest.main()
