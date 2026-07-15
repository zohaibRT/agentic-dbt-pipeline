#!/usr/bin/env python3
"""Tests for policy implementation coverage audit."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class PolicyCoverageTests(unittest.TestCase):
    def test_skill_root_policy_coverage_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_policy_implementation_coverage.py"), "--root", str(ROOT)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = ROOT / "reports" / "agent" / "POLICY_IMPLEMENTATION_COVERAGE.md"
        self.assertTrue(report.exists())
        text = report.read_text(encoding="utf-8")
        self.assertIn("USED", text)
        self.assertNotIn("**UNUSED**", text)

    def test_banned_fail_on_warning_twin_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  fail_on_warning_at_final: true\n  completion_mode: process_coverage\n",
                encoding="utf-8",
            )
            # Minimal scripts tree so verify does not crash
            (root / "scripts").mkdir()
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "check_policy_implementation_coverage.py"),
                    "--root",
                    str(root),
                    "--report-root",
                    str(root),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            # May fail unused AND banned; banned must be reported
            combined = proc.stdout + proc.stderr
            self.assertNotEqual(proc.returncode, 0)
            self.assertTrue(
                "banned" in combined.lower() or "fail_on_warning_at_final" in combined,
                combined[-2000:],
            )


if __name__ == "__main__":
    unittest.main()
