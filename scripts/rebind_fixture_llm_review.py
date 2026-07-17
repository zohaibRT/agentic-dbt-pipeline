#!/usr/bin/env python3
"""Rebind fixture-only LLM Playwright evidence after the final report bundle.

Allowed only under fixtures/. Does not invent interactions or PASS status.
Intended for CI after the final deterministic browser refresh mutates chart/
metric payloads and therefore the report_bundle_hash.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib_llm_playwright_review import (  # noqa: E402
    is_under_fixtures,
    rebind_fixture_observation_freshness,
)


def rebind_and_refresh_review(root: Path) -> None:
    root = root.resolve()
    if not is_under_fixtures(root):
        raise SystemExit(
            f"refusing to rebind LLM review outside fixtures/: {root}"
        )
    observations = (
        root / "reports" / "agent" / "10_presentation" / "LLM_PLAYWRIGHT_OBSERVATIONS.json"
    ).resolve()
    evidence = (
        root / "reports" / "agent" / "10_presentation" / "llm_playwright_evidence"
    ).resolve()
    if not observations.exists():
        raise SystemExit(f"observations JSON missing: {observations}")
    if not evidence.exists() or not any(evidence.glob("*.png")):
        raise SystemExit(f"screenshot evidence missing under: {evidence}")

    rebind_fixture_observation_freshness(root, observations)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "write_llm_playwright_review_from_mcp.py"),
            "--root",
            str(root),
            "--observations-json",
            str(observations),
            "--screenshot-dir",
            str(evidence),
        ],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            "Failed to refresh fixture LLM Playwright review:\n"
            f"{proc.stdout}\n{proc.stderr}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Fixture project root under fixtures/",
    )
    args = parser.parse_args()
    rebind_and_refresh_review(args.root)
    print(f"Rebound fixture LLM review for {args.root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
