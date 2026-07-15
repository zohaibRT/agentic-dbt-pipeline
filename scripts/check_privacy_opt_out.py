#!/usr/bin/env python3
"""Verify privacy opt-out is honored without assuming warehouse column names.

When the user opts out of privacy minimization:
- OPEN Attention Board / Gap Register rows must not keep blocking reporting via
  privacy minimization (exclude/mask/hash of reporting attributes).
- Presentation must not keep saying it hides or avoids identifiers after opt-out.

Stay domain-neutral: do not hardcode industry- or project-specific field names.
Discover attributes from each project's evidence; this gate only checks policy behavior.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


OPT_OUT_PATTERNS = (
    r"do not apply privacy minimization unless i explicitly request it",
    r"do not apply privacy minimization",
    r"no privacy until specifically asked",
    r"keep dimensions / clear attributes for reporting",
    r"privacy minimization opt-out",
    r"privacy opt-out",
)

# Still exclude even under opt-out — OPEN blockers for these alone are not the focus;
# they should be CARRY_FORWARD, but we do not require industry attribute names.
ALWAYS_EXCLUDE_MARKERS = (
    r"\bsecret\b",
    r"\bpassword\b",
    r"\botp\b",
    r"\bone[- ]time\b",
    r"\bfull iban\b",
    r"\biban dump\b",
    r"\bnational id\b",
    r"\bphi\b",
    r"\bprotected health\b",
    r"\bmedical identifier\b",
)

# Generic "still minimizing after opt-out" copy — no industry field names.
FORBIDDEN_MINIMIZATION_COPY = (
    r"keep identifiers off",
    r"identifiers? (are )?(not |never )?(shown|rendered|displayed|included)",
    r"this report avoids",
    r"avoid rendering .{0,60}identifiers?",
    r"privacy minimization .{0,40}(avoid|hide|off the report|not shown)",
    r"report avoids .{0,40}(identifier|pii|personal)",
)

OPEN_STATUS_RE = re.compile(r"\bOPEN\b", re.I)
PRIVACY_BLOCKER_RE = re.compile(r"\bPRIVACY\b", re.I)
MINIMIZE_RE = re.compile(
    r"\b(exclude|mask|hash|minimization|minimise|minimize|keep out|keep off|do not (include|expose|show))\b",
    re.I,
)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def privacy_opt_out_recorded(root: Path) -> tuple[bool, list[str]]:
    sources: list[tuple[str, Path]] = [
        ("requirements", root / "reports" / "agent" / "00_discovery" / "requirements.md"),
        ("context tree", root / "reports" / "agent" / "CONTEXT_TREE.md"),
        ("agent plan", root / "AGENT_PLAN.md"),
    ]
    hits: list[str] = []
    for label, path in sources:
        lower = read_text(path).lower()
        for pattern in OPT_OUT_PATTERNS:
            if re.search(pattern, lower):
                hits.append(f"{label}: {path.relative_to(root)}")
                break
    return bool(hits), hits


def table_rows(text: str) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*-+", stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        header_tokens = {
            "id",
            "need from human",
            "agent recommendation",
            "blocker type",
            "status",
            "gap",
            "attention id",
            "kpi candidate",
        }
        if cells[0].lower() in header_tokens:
            continue
        rows.append(stripped)
    return rows


def row_is_open(row: str) -> bool:
    return bool(OPEN_STATUS_RE.search(row))


def row_is_open_privacy_minimization_blocker(row: str) -> bool:
    """OPEN privacy-minimization blocker for reporting attributes (domain-neutral)."""
    if not row_is_open(row):
        return False
    lower = row.lower()
    privacy_signal = bool(PRIVACY_BLOCKER_RE.search(row)) or "privacy" in lower or "pii" in lower
    if not privacy_signal:
        return False
    if not MINIMIZE_RE.search(row):
        return False
    # If the row is only about always-exclude secret classes, treat as CARRY_FORWARD material —
    # still fail OPEN so agents move them off OPEN blockers.
    return True


def find_open_privacy_blockers(root: Path) -> list[str]:
    findings: list[str] = []
    for rel in (
        "reports/agent/HUMAN_ATTENTION_BOARD.md",
        "reports/agent/KPI_GAP_REGISTER.md",
    ):
        path = root / rel
        if not path.exists():
            continue
        for row in table_rows(read_text(path)):
            if row_is_open_privacy_minimization_blocker(row):
                findings.append(f"{rel}: {row[:220]}")
    return findings


def find_presentation_privacy_minimization_copy(root: Path) -> list[str]:
    findings: list[str] = []
    presentation = root / "reports" / "agent" / "10_presentation"
    if not presentation.exists():
        return findings
    for path in presentation.rglob("*"):
        if path.suffix.lower() not in {".md", ".py", ".html"}:
            continue
        if "__pycache__" in path.parts:
            continue
        lower = read_text(path).lower()
        for pattern in FORBIDDEN_MINIMIZATION_COPY:
            if re.search(pattern, lower):
                findings.append(f"{path.relative_to(root).as_posix()}: matches /{pattern}/")
                break
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    opted_out, sources = privacy_opt_out_recorded(root)
    if not opted_out:
        print("SKIPPED: no recorded privacy minimization opt-out in requirements/context/plan")
        return 0

    print(f"Privacy opt-out recorded in: {', '.join(sources)}")
    errors: list[str] = []
    for item in find_open_privacy_blockers(root):
        errors.append(f"OPEN privacy-minimization blocker conflicts with user opt-out — {item}")
    for item in find_presentation_privacy_minimization_copy(root):
        errors.append(
            f"presentation still applies privacy minimization after opt-out — {item} "
            "(show reporting attributes that exist in gold; do not hide for privacy)"
        )

    if not errors:
        print(
            "Privacy opt-out check PASSED — no OPEN privacy-minimization blockers "
            "and no presentation minimization copy"
        )
        return 0

    print("Privacy opt-out check FAILED")
    for item in errors:
        print(f"ERROR: {item}")
    print(
        "Fix: close OPEN privacy-minimization rows (CARRY_FORWARD / ANSWERED); "
        "present attributes that exist in gold. Only secrets/OTP/full bank dumps/"
        "national ID/PHI need an explicit ask — keep gates domain-neutral."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
