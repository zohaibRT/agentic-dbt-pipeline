#!/usr/bin/env python3
"""Validate human-in-the-loop business approval coverage for KPIs.

Separates technical verification from business approval. Technical PASS never
implies business APPROVED. Agent-generated approval text is not valid evidence.
"""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime
from pathlib import Path

from lib_gate_common import (
    add_output_json_arg,
    INVALID_APPROVAL_EVIDENCE_TOKENS,
    business_approval_status,
    cell,
    compute_contract_fingerprint,
    discover_production_kpi_obligations,
    has_production_presentation_artifacts,
    is_meaningful_text,
    load_human_in_loop_policy,
    normalize_header,
    normalize_field_value,
    parse_markdown_tables,
    print_results,
    ratio,
    read_text,
    technical_verification_status,
)

KPI_CONTRACTS = Path("reports/agent/KPI_DEFINITION_CONTRACTS.md")
APPROVAL_REGISTER = Path("reports/agent/BUSINESS_APPROVAL_REGISTER.md")
ATTENTION_BOARD = Path("reports/agent/HUMAN_ATTENTION_BOARD.md")
DECISION_LOG = Path("reports/agent/DECISION_LOG.md")

PRODUCTION_APPROVALS = {"APPROVED", "APPROVED_WITH_CONDITIONS"}
TRUSTED_LABELS = re.compile(
    r"\b(trusted|production[- ]approved|executive\s+kpi|executive\s+report)\b",
    re.I,
)
PENDING_LABEL = re.compile(r"pending\s+business\s+approval", re.I)
AGENT_EVIDENCE = re.compile(
    r"\b(agent[- ]?(generated|approved|wrote)|auto[- ]?approved|inferred\s+owner)\b",
    re.I,
)


def table_rows(path: Path, required_any: set[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    for headers, data in parse_markdown_tables(read_text(path)):
        norm = [normalize_header(h) for h in headers]
        if not (set(norm) & required_any):
            continue
        for cells in data:
            row = {
                norm[i]: (cells[i].strip() if i < len(cells) else "")
                for i in range(len(norm))
                if norm[i]
            }
            # Skip placeholder-only rows
            first = next(iter(row.values()), "")
            if first.lower() in {"none", "n/a", "na", "<d-01>", "todo"}:
                continue
            rows.append(row)
        if rows:
            return rows
    return rows


def parse_date(text: str | None) -> date | None:
    raw = (text or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    return None


def evidence_is_valid(root: Path, evidence: str) -> tuple[bool, str]:
    token = (evidence or "").strip()
    if not token:
        return False, "missing approval evidence"
    lower = token.lower()
    if lower in INVALID_APPROVAL_EVIDENCE_TOKENS:
        return False, f"invalid approval evidence token {token!r}"
    if AGENT_EVIDENCE.search(token):
        return False, "agent-generated approval is not valid human evidence"
    if lower in {"pass", "sql pass", "dbt build success", "test success"}:
        return False, "technical success is not business approval evidence"
    # Path-like evidence must exist (strip markdown anchors)
    if "/" in token or "\\" in token or token.endswith((".md", ".txt", ".pdf")) or "#" in token:
        cleaned = token.strip("`").split("#", 1)[0]
        candidates = [root / cleaned, root / "reports" / "agent" / Path(cleaned).name]
        if cleaned and not any(c.exists() for c in candidates):
            return False, f"approval evidence path not found: {token}"
    return True, ""


def contract_rows(root: Path) -> list[dict[str, str]]:
    path = root / KPI_CONTRACTS
    return table_rows(
        path,
        {"kpi_id", "kpi", "sql_proof", "approval", "business_approval_status", "grain"},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--phase",
        choices=("analytics", "presentation", "final"),
        default="analytics",
        help="enforcement phase (final fails on missing production approvals)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_human_in_loop_policy(root)
    errors: list[str] = []
    warnings: list[str] = []

    contracts_path = root / KPI_CONTRACTS
    insights = root / "reports" / "agent" / "09_analytics_insights"
    if not contracts_path.exists():
        if insights.exists():
            errors.append("KPI_DEFINITION_CONTRACTS.md missing while analytics insights exist")
            return print_results(
                "Human approval coverage check",
                errors,
                warnings,
                output_json=getattr(args, "output_json", None),
                validator_id=Path(__file__).stem,
            )
        return print_results(
            "Human approval coverage check",
            [],
            [],
            output_json=getattr(args, "output_json", None),
            validator_id=Path(__file__).stem,
            skipped=True,
            skip_reason="no KPI contracts",
        )
    rows = contract_rows(root)
    contracts_by_id: dict[str, dict[str, str]] = {}
    for index, row in enumerate(rows, start=1):
        kid = cell(row, "kpi_id", "id") or cell(row, "kpi", "display_name") or f"row-{index}"
        contracts_by_id[normalize_field_value(kid)] = row

    register = table_rows(
        root / APPROVAL_REGISTER,
        {"approval_id", "object_id", "approval status", "approval_status"},
    )
    attention = table_rows(
        root / ATTENTION_BOARD,
        {"decision_id", "id", "status", "question requiring human input", "need from human"},
    )
    decisions = table_rows(
        root / DECISION_LOG,
        {"decision_id", "final human decision", "original question"},
    )

    register_by_object: dict[str, dict[str, str]] = {}
    for row in register:
        object_id = cell(row, "object_id", "kpi_id", "object id", "id")
        if object_id:
            register_by_object[normalize_field_value(object_id)] = row

    obligations = discover_production_kpi_obligations(root)
    production_total = len(obligations)
    production_approved = 0
    today = date.today()

    # Warn when technical PASS without business approval on any contract row
    for index, row in enumerate(rows, start=1):
        kpi_id = cell(row, "kpi_id", "kpi", "id", "display_name") or f"row-{index}"
        biz = business_approval_status(row)
        tech = technical_verification_status(row)
        if tech == "PASS" and biz not in PRODUCTION_APPROVALS:
            warnings.append(
                f"{kpi_id}: technical PASS without business approval "
                f"({biz or 'missing'}) — not trusted for production"
            )

    for obl in obligations:
        kpi_id = obl.kpi_id
        row = contracts_by_id.get(normalize_field_value(kpi_id), {})
        biz = business_approval_status(row) if row else (obl.business_approval_status or "NOT_REQUESTED")
        legacy = cell(row, "approval", "approval_status").upper() if row else ""
        if biz == "PENDING_REVIEW" and legacy in {"APPROVED", "PROPOSED"}:
            if not cell(row, "approval_evidence", "approval evidence"):
                biz = "PENDING_REVIEW"
                warnings.append(
                    f"{kpi_id}: legacy approval without evidence treated as PENDING_REVIEW"
                )
            else:
                biz = legacy if legacy != "PROPOSED" else "PENDING_REVIEW"
        tech = technical_verification_status(row) if row else obl.technical_status

        if obl.trusted_or_executive and biz not in PRODUCTION_APPROVALS:
            if args.phase in {"presentation", "final"}:
                errors.append(
                    f"{kpi_id}: trusted/executive KPI requires business approval "
                    f"(status={biz or 'blank'})"
                )
            else:
                warnings.append(
                    f"{kpi_id}: trusted/executive KPI pending business approval ({biz or 'blank'})"
                )

        if biz in {"BLOCKED", "DEFERRED"}:
            found = any(
                normalize_field_value(cell(a, "object_id", "object id", "id", "blocks"))
                == normalize_field_value(kpi_id)
                or kpi_id.lower() in cell(a, "need from human", "question requiring human input", "blocks").lower()
                for a in attention
            )
            if not found and args.phase in {"presentation", "final"}:
                errors.append(
                    f"{kpi_id}: BLOCKED/DEFERRED KPI requires HUMAN_ATTENTION_BOARD entry"
                )
            elif not found:
                warnings.append(
                    f"{kpi_id}: BLOCKED/DEFERRED should appear on HUMAN_ATTENTION_BOARD"
                )
            continue

        if biz in PRODUCTION_APPROVALS or (
            legacy in {"APPROVED"} and cell(row, "approval_evidence")
        ):
            owner = cell(row, "business_owner", "owner") or obl.owner
            approver = cell(row, "approver", "approved_by") or obl.approver
            evidence = cell(row, "approval_evidence", "approval evidence", "evidence_path") or obl.approval_evidence
            approval_date = cell(row, "approval_date", "approval date", "approved_at") or obl.approval_date
            fingerprint = (
                cell(row, "contract_fingerprint", "fingerprint")
                or obl.contract_fingerprint
                or (compute_contract_fingerprint(row) if row else "")
            )
            calculated_fp = compute_contract_fingerprint(row) if row else fingerprint

            if policy.get("require_named_owner") and not is_meaningful_text(owner):
                errors.append(f"{kpi_id}: approved KPI missing named business_owner")
            if policy.get("require_named_approver") and not is_meaningful_text(approver):
                errors.append(f"{kpi_id}: approved KPI missing named approver")
            if policy.get("require_approval_evidence"):
                ok, reason = evidence_is_valid(root, evidence)
                if not ok:
                    errors.append(f"{kpi_id}: {reason}")
            if policy.get("require_approval_date") and not parse_date(approval_date):
                errors.append(f"{kpi_id}: approved KPI missing approval_date")

            if fingerprint and calculated_fp and fingerprint != calculated_fp:
                msg = (
                    f"{kpi_id}: approval stale — contract fingerprint changed "
                    f"({fingerprint} -> {calculated_fp})"
                )
                if policy.get("stale_approval_blocks_final") and args.phase == "final":
                    errors.append(msg)
                else:
                    warnings.append(msg)
                    warnings.append(f"{kpi_id}: business approval should return to PENDING_REVIEW")

            if biz == "APPROVED_WITH_CONDITIONS":
                conditions = cell(row, "approval_conditions", "conditions")
                review = cell(
                    row,
                    "approval_expiry_or_review_condition",
                    "review condition",
                    "expiry",
                )
                if policy.get("conditional_approval_requires_review_condition"):
                    if not is_meaningful_text(conditions):
                        errors.append(f"{kpi_id}: conditional approval missing conditions")
                    if not is_meaningful_text(review):
                        errors.append(
                            f"{kpi_id}: conditional approval missing review/expiry condition"
                        )
                expiry = parse_date(review)
                if expiry and expiry < today:
                    errors.append(
                        f"{kpi_id}: conditional approval expired on {expiry.isoformat()}"
                    )

            reg = register_by_object.get(normalize_field_value(kpi_id))
            if not reg and args.phase == "final":
                errors.append(f"{kpi_id}: missing BUSINESS_APPROVAL_REGISTER row")
            elif reg:
                reg_status = cell(reg, "approval_status", "approval status").upper()
                if reg_status and reg_status not in PRODUCTION_APPROVALS | {"APPROVED"}:
                    warnings.append(
                        f"{kpi_id}: register status {reg_status} does not match contract {biz}"
                    )
                reg_fp = cell(reg, "contract_fingerprint", "fingerprint")
                if reg_fp and reg_fp != calculated_fp and args.phase == "final":
                    errors.append(f"{kpi_id}: register fingerprint stale vs contract")

            if not any(err.startswith(f"{kpi_id}:") for err in errors):
                production_approved += 1

        elif biz in {"PENDING_REVIEW", "PROPOSED", "NOT_REQUESTED"} or not biz:
            if not policy.get("allow_unapproved_kpis_in_draft_reports") and args.phase == "analytics":
                errors.append(f"{kpi_id}: unapproved KPI not allowed even in draft reports")
            if not policy.get("allow_unapproved_kpis_in_trusted_executive_reports"):
                report_html = (
                    root
                    / "reports"
                    / "agent"
                    / "10_presentation"
                    / "matplotlib"
                    / "report.html"
                )
                if report_html.exists():
                    html = read_text(report_html)
                    # Only fail when the pending KPI is labeled trusted/executive without a pending cue nearby
                    pending_trusted = re.search(
                        rf'data-kpi-id=["\']{re.escape(kpi_id)}["\'][^>]*(trusted|executive|trust_level\s*=\s*["\']TRUSTED)',
                        html,
                        re.I,
                    ) or re.search(
                        rf'(trusted|executive|trust_level\s*=\s*["\']TRUSTED)[^>]*data-kpi-id=["\']{re.escape(kpi_id)}["\']',
                        html,
                        re.I,
                    )
                    if pending_trusted and not PENDING_LABEL.search(html):
                        if args.phase in {"presentation", "final"}:
                            errors.append(
                                f"{kpi_id}: pending KPI must not appear as trusted executive KPI"
                            )

    # Unresolved critical decisions
    open_critical = [
        row
        for row in attention
        if cell(row, "status").upper() in {"OPEN", "PENDING_REVIEW", "BLOCKED"}
        and (
            "critical" in cell(row, "decision type", "decision_type", "area").lower()
            or "critical" in cell(row, "risk of no decision", "need from human").lower()
            or cell(row, "decision type", "decision_type").upper() == "HUMAN_DECISION_REQUIRED"
        )
    ]
    if open_critical and policy.get("unresolved_critical_decisions_block_final"):
        msg = (
            f"{len(open_critical)} unresolved critical human decision(s) on HUMAN_ATTENTION_BOARD"
        )
        if args.phase == "final":
            errors.append(msg)
        else:
            warnings.append(msg)

    # Hybrid decisions should preserve recommendation + human decision in DECISION_LOG
    for row in decisions:
        dtype = cell(row, "decision type", "decision_type").upper()
        if dtype == "HYBRID_DECISION" or "hybrid" in cell(row, "notes", "options considered").lower():
            if not cell(row, "machine recommendation", "machine_recommendation"):
                warnings.append(
                    f"{cell(row, 'decision_id', 'id')}: hybrid decision missing machine_recommendation"
                )
            if not cell(row, "final human decision", "human_decision"):
                errors.append(
                    f"{cell(row, 'decision_id', 'id')}: hybrid decision missing final human decision"
                )

    required = float(policy.get("production_kpi_approval_required", 1.0))
    if args.phase == "final":
        cov = ratio(production_approved, production_total)
        if production_total == 0:
            if has_production_presentation_artifacts(root):
                errors.append(
                    "production presentation exists but no production KPI obligations discovered (0/0 invalid)"
                )
            else:
                warnings.append("no production KPI obligations in final phase denominator")
        elif cov is None or cov < required:
            errors.append(
                f"production KPI approval coverage {production_approved}/{production_total} "
                f"below required {required:.0%}"
            )
        print(
            f"Human approval coverage: {production_approved}/{production_total} "
            f"(phase={args.phase}, obligations={production_total})"
        )
    else:
        print(
            f"Human approval coverage (advisory at {args.phase}): "
            f"production_approved={production_approved} production_total={production_total}"
        )
        if not policy.get("allow_technical_work_without_business_approval"):
            for row in rows:
                tech = technical_verification_status(row)
                biz = business_approval_status(row)
                if tech in {"PASS", "WARN"} and biz not in PRODUCTION_APPROVALS:
                    errors.append(
                        f"{cell(row, 'kpi_id', 'kpi')}: technical work not allowed without business approval"
                    )

    return print_results(
        "Human approval coverage check",
        errors,
        warnings,
        output_json=getattr(args, "output_json", None),
        validator_id=Path(__file__).stem,
        details={
            "production_approved": production_approved,
            "production_total": production_total,
            "obligation_ids": [o.kpi_id for o in obligations],
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
