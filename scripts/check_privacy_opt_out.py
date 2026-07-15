#!/usr/bin/env python3
"""Verify privacy opt-out is honored in attention board and gap register.

When the user opts out of privacy minimization, OPEN privacy blockers for
commercial/operational identifiers (phone, IMEI, serial, fingerprint, etc.)
must not remain. Only always-exclude fields (secrets, OTP, full bank dumps,
national IDs, PHI) may stay as CARRY_FORWARD notes — not OPEN KPI blockers.
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

# Fields that may proceed to gold/marts when user opted out of privacy minimization.
REPORTING_ALLOWED_UNDER_OPT_OUT = (
    r"\bphone\b",
    r"\bimei\b",
    r"\bserial\b",
    r"\bfingerprint\b",
    r"\bemail\b",
    r"\baddress\b",
    r"\bdevice id\b",
    r"\bclear-text\b",
    r"\bdirect identifiers?\b",
)

# Still exclude even under opt-out — should be CARRY_FORWARD, not OPEN blockers.
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

OPEN_STATUS_RE = re.compile(r"\bOPEN\b", re.I)
PRIVACY_BLOCKER_RE = re.compile(r"\bPRIVACY\b", re.I)


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


def row_mentions_reporting_allowed_privacy_block(row: str) -> bool:
    lower = row.lower()
    if not any(re.search(pattern, lower) for pattern in REPORTING_ALLOWED_UNDER_OPT_OUT):
        return False
    if any(re.search(pattern, lower) for pattern in ALWAYS_EXCLUDE_MARKERS):
        return False
    privacy_signals = (
        "privacy",
        "exclude",
        "mask",
        "hash",
        "pii",
        "identifier",
        "direct ident",
    )
    return any(token in lower for token in privacy_signals) or bool(PRIVACY_BLOCKER_RE.search(row))


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
            if not row_is_open(row):
                continue
            if row_mentions_reporting_allowed_privacy_block(row):
                findings.append(f"{rel}: {row[:220]}")
    return findings


FORBIDDEN_AVOID_COPY = (
    r"avoids?\s+phone",
    r"avoids?\s+imei",
    r"avoid rendering phone",
    r"keep identifiers off",
    r"this report avoids",
)


def find_presentation_privacy_avoid_copy(root: Path) -> list[str]:
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
        for pattern in FORBIDDEN_AVOID_COPY:
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
        errors.append(f"OPEN privacy blocker conflicts with user opt-out — {item}")
    for item in find_presentation_privacy_avoid_copy(root):
        errors.append(
            f"presentation still minimizes identifiers after opt-out — {item} "
            "(show phone/IMEI/serial when in gold; remove ‘avoids phone/IMEI’ copy)"
        )

    if not errors:
        print(
            "Privacy opt-out check PASSED — no OPEN commercial-identifier blockers "
            "and no presentation ‘avoid phone/IMEI’ copy"
        )
        return 0

    print("Privacy opt-out check FAILED")
    for item in errors:
        print(f"ERROR: {item}")
    print(
        "Fix: close OPEN privacy rows; allow tier-2 identifiers on the report; "
        "only secrets/OTP/full IBAN/national ID/PHI stay excluded unless the user asks."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
