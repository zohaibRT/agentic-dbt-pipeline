#!/usr/bin/env python3
"""Validate stable presentation IDs and bidirectional proof/page/metric traceability.

Exact mapping (not count heuristics):
KPI contract → catalog → page → visual → query → source unique_id → proof →
rendered item → displayed value.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from lib_gate_common import (
    cell,
    compare_formatted_values,
    load_json_registry,
    load_presentation_policy,
    presentation_registry_paths,
    print_results,
    table_dicts,
)


def normalize_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def collect_contract_rows(root: Path) -> dict[str, dict[str, str]]:
    contracts_path = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    mapping: dict[str, dict[str, str]] = {}
    if not contracts_path.exists():
        return mapping
    for row in table_dicts(contracts_path, required_any_headers=("kpi id", "display name", "kpi_id")):
        kpi_id = cell(row, "kpi id", "kpi_id", "id")
        if not kpi_id:
            continue
        mapping[normalize_id(kpi_id)] = row
        display = cell(row, "display name", "display_name", "name")
        if display:
            mapping[normalize_id(display)] = row
    return mapping


def collect_proof_index(root: Path) -> dict[str, dict[str, str]]:
    index_path = (
        root / "reports" / "agent" / "10_presentation" / "matplotlib" / "sql_verification" / "_proof_index.md"
    )
    mapping: dict[str, dict[str, str]] = {}
    if not index_path.exists():
        return mapping
    for row in table_dicts(index_path, required_any_headers=("item", "proof", "proof_id")):
        proof_id = cell(row, "proof_id", "proof id") or Path(cell(row, "proof", "sql_proof", "proof_path")).stem
        item = cell(row, "item", "name", "kpi", "metric", "metric_id")
        proof = cell(row, "proof", "sql_proof", "proof_path")
        if proof_id:
            mapping[normalize_id(proof_id)] = row
            mapping[normalize_id(Path(proof_id).stem)] = row
        if item:
            mapping[normalize_id(item)] = row
        if proof:
            mapping[normalize_id(Path(proof).stem)] = row
    return mapping


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in re.split(r"[,;|]", text) if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report-dir", type=Path, default=None)
    parser.add_argument("--phase", choices=("analytics", "presentation", "final"), default="presentation")
    args = parser.parse_args()

    root = args.root.resolve()
    policy = load_presentation_policy(root)
    matplotlib = (
        args.report_dir.resolve()
        if args.report_dir
        else root / "reports" / "agent" / "10_presentation" / "matplotlib"
    )
    presentation = matplotlib.parent if matplotlib.name == "matplotlib" else matplotlib

    errors: list[str] = []
    warnings: list[str] = []

    paths = presentation_registry_paths(root)
    manifest_path = paths["rendered_metric_manifest.json"]
    if not manifest_path.exists():
        if matplotlib.exists() and (matplotlib / "chart_registry.json").exists():
            errors.append("chart_registry exists but rendered_metric_manifest.json is missing")
            return print_results("Presentation traceability check", errors, warnings)
        print("SKIPPED: no rendered_metric_manifest.json")
        return 0

    manifest = load_json_registry(manifest_path)
    if not isinstance(manifest, dict):
        errors.append("rendered_metric_manifest.json must be an object")
        return print_results("Presentation traceability check", errors, warnings)

    chart_reg = load_json_registry(paths["chart_registry.json"])
    proof_reg = load_json_registry(paths["proof_registry.json"])
    query_reg = load_json_registry(paths["query_registry.json"])
    page_reg = load_json_registry(paths["page_registry.json"])

    contract_rows = collect_contract_rows(root)
    proof_index = collect_proof_index(root)

    metrics = list(manifest.get("metrics") or [])
    metric_ids_seen: set[str] = set()
    rendered_visual_ids: set[str] = set()
    rendered_proof_ids: set[str] = set()
    trusted_metric_ids: set[str] = set()

    for metric in metrics:
        metric_id = str(metric.get("metric_id") or metric.get("kpi_id") or "").strip()
        if not metric_id:
            errors.append("manifest metric missing metric_id")
            continue
        norm = normalize_id(metric_id)
        if norm in metric_ids_seen:
            errors.append(f"duplicate metric_id mapping: {metric_id}")
        metric_ids_seen.add(norm)

        display_name = str(metric.get("display_name") or "").strip()
        if not display_name:
            errors.append(f"metric {metric_id}: missing display_name")

        trust = str(metric.get("trust_level") or metric.get("status") or "TRUSTED").upper()
        biz = str(metric.get("business_approval_status") or "NOT_REQUESTED").upper()
        tech = str(
            metric.get("technical_validation_status")
            or metric.get("technical_verification_status")
            or metric.get("validation_status")
            or ""
        ).upper()

        if contract_rows and norm not in contract_rows and normalize_id(display_name) not in contract_rows:
            # DQ/pipeline fixture metrics may not be in KPI contracts; draft metrics are allowed pending
            if trust in {"DRAFT", "PENDING"}:
                pass
            elif not metric_id.upper().startswith(("DQ-", "PIPE-", "OBS-")):
                errors.append(f"metric {metric_id}: not found in KPI_DEFINITION_CONTRACTS")

        if trust in {"TRUSTED", "RENDERED"} and biz not in {
            "APPROVED",
            "APPROVED_WITH_CONDITIONS",
        }:
            page_ids = {normalize_id(p) for p in _as_list(metric.get("page_ids"))}
            if "executive_overview" in page_ids or any("executive" in p for p in page_ids):
                if policy.get("approved_kpis_required_for_trusted_executive_pages", True):
                    errors.append(
                        f"metric {metric_id}: pending/unapproved KPI displayed as trusted on executive page "
                        f"(business_approval_status={biz})"
                    )
            elif trust == "TRUSTED" and biz in {"PENDING_REVIEW", "NOT_REQUESTED", "PROPOSED"}:
                errors.append(
                    f"metric {metric_id}: pending KPI displayed as trusted "
                    f"(label draft/pending or remove from trusted sections)"
                )

        if trust in {"TRUSTED", "RENDERED"}:
            trusted_metric_ids.add(norm)

        if trust in {"DRAFT", "PENDING"} and biz in {"PENDING_REVIEW", "NOT_REQUESTED"}:
            if not policy.get("pending_kpis_allowed_in_draft_pages", True):
                errors.append(
                    f"metric {metric_id}: pending KPIs not allowed on draft pages "
                    f"(presentation_policy.pending_kpis_allowed_in_draft_pages=false)"
                )
            else:
                label = (display_name + " " + str(metric.get("label") or "")).lower()
                if "pending" not in label and "draft" not in label:
                    warnings.append(
                        f"metric {metric_id}: draft/pending trust should include visible pending/draft label"
                    )

        visual_ids = _as_list(metric.get("visual_ids")) + _as_list(metric.get("chart_ids")) + _as_list(
            metric.get("card_ids")
        )
        if not visual_ids:
            msg = f"metric {metric_id}: no visual_ids/chart_ids/card_ids mapped"
            if policy.get("require_stable_visual_ids", True) and trust in {"TRUSTED", "RENDERED"}:
                errors.append(msg + " (require_stable_visual_ids)")
            else:
                warnings.append(msg)
        for vid in visual_ids:
            rendered_visual_ids.add(normalize_id(vid))

        proof_ids = _as_list(metric.get("proof_ids"))
        if trust in {"TRUSTED", "RENDERED"} and not proof_ids:
            errors.append(f"rendered item {metric_id}: missing proof_ids")
        for proof_id in proof_ids:
            rendered_proof_ids.add(normalize_id(proof_id))
            # Prefer proof registry; fall back to _proof_index
            if isinstance(proof_reg, dict):
                proofs = {normalize_id(p.get("proof_id", "")): p for p in (proof_reg.get("proofs") or []) if isinstance(p, dict)}
                preg = proofs.get(normalize_id(proof_id)) or proofs.get(normalize_id(Path(proof_id).stem))
            else:
                preg = None
            if preg:
                preg_kpi = str(preg.get("kpi_id") or preg.get("metric_id") or "")
                if preg_kpi and normalize_id(preg_kpi) != norm:
                    errors.append(
                        f"proof {proof_id}: KPI ID mismatch proof={preg_kpi} rendered={metric_id}"
                    )
                captured = str(preg.get("captured_value") or "")
                displayed = str(
                    metric.get("displayed_value")
                    or metric.get("formatted_value")
                    or preg.get("displayed_value")
                    or ""
                )
                ok, reason = compare_formatted_values(
                    displayed,
                    captured or str(preg.get("displayed_value") or ""),
                    format_rule=str(metric.get("formatting_rule") or metric.get("format") or preg.get("formatting_rule") or ""),
                )
                # Prefer comparing displayed to proof registry displayed/captured
                if captured:
                    ok2, reason2 = compare_formatted_values(
                        displayed,
                        captured,
                        format_rule=str(metric.get("formatting_rule") or metric.get("format") or ""),
                    )
                    if not ok2:
                        errors.append(
                            f"metric {metric_id}: displayed value differs from proven value ({reason2})"
                        )
                if not preg.get("proof_path") and not preg.get("path"):
                    errors.append(f"proof {proof_id}: missing proof_path")
                if not preg.get("query_id"):
                    warnings.append(f"proof {proof_id}: missing query_id")
                if not _as_list(preg.get("source_resource_ids")) and not preg.get("source_resource_unique_id"):
                    warnings.append(f"proof {proof_id}: missing source_resource_ids")
            elif proof_index:
                if normalize_id(proof_id) not in proof_index and normalize_id(Path(str(proof_id)).stem) not in proof_index:
                    errors.append(f"metric {metric_id}: proof_id {proof_id} not in proof registry or _proof_index.md")

        if not metric.get("query_ids") and not metric.get("query_id"):
            if policy.get("require_bidirectional_proof_mapping"):
                warnings.append(f"metric {metric_id}: missing query_id mapping")

        source_ids = _as_list(metric.get("source_resource_ids"))
        if metric.get("source_resource_unique_id"):
            source_ids.append(str(metric.get("source_resource_unique_id")))
        if trust in {"TRUSTED", "RENDERED"} and not source_ids:
            warnings.append(f"metric {metric_id}: missing source_resource_unique_id")

        if not metric.get("refresh_timestamp") and not manifest.get("freshness_timestamp"):
            warnings.append(f"metric {metric_id}: missing refresh/freshness timestamp")

        # Human approval separate from technical
        if tech == "PASS" and biz in {"APPROVED", "APPROVED_WITH_CONDITIONS"}:
            pass
        elif tech == "PASS" and biz not in {"APPROVED", "APPROVED_WITH_CONDITIONS", ""}:
            # OK — technical pass without business approval must remain distinct
            if trust in {"TRUSTED", "RENDERED"} and any(
                "executive" in normalize_id(p) for p in _as_list(metric.get("page_ids"))
            ):
                pass  # already errored above when required

    # Proof registry bidirectional: every RENDERED proof maps to a rendered item
    if isinstance(proof_reg, dict) and policy.get("require_bidirectional_proof_mapping", True):
        proof_ids_seen: set[str] = set()
        for preg in proof_reg.get("proofs") or []:
            if not isinstance(preg, dict):
                continue
            proof_id = str(preg.get("proof_id") or "").strip()
            if not proof_id:
                errors.append("proof registry entry missing proof_id")
                continue
            nproof = normalize_id(proof_id)
            if nproof in proof_ids_seen:
                errors.append(f"duplicate proof_id: {proof_id}")
            proof_ids_seen.add(nproof)
            visuals = _as_list(preg.get("visual_ids"))
            # Proofs for trusted executive visuals must appear in rendered metrics
            page_id = normalize_id(str(preg.get("page_id") or ""))
            if page_id.startswith("executive") or "executive" in page_id:
                if nproof not in rendered_proof_ids and visuals:
                    errors.append(f"proof {proof_id}: no rendered item mapping for executive proof")
            elif visuals and nproof not in rendered_proof_ids:
                # Non-executive proofs may be page-local; warn unless final
                msg = f"proof {proof_id}: no rendered metric mapping"
                if args.phase == "final":
                    # Only fail if proof claims RENDERED trust via visuals on trusted pages
                    if str(preg.get("proof_status") or "").upper() == "PASS" and visuals:
                        warnings.append(msg)
                else:
                    warnings.append(msg)

    # Chart registry visual ID uniqueness + metric mapping
    if isinstance(chart_reg, dict):
        visual_seen: set[str] = set()
        chart_seen: set[str] = set()
        for chart in chart_reg.get("charts") or []:
            if not isinstance(chart, dict):
                continue
            chart_id = str(chart.get("chart_id") or "")
            visual_id = str(chart.get("visual_id") or chart_id)
            if chart_id:
                ncid = normalize_id(chart_id)
                if ncid in chart_seen:
                    errors.append(f"duplicate chart_id: {chart_id}")
                chart_seen.add(ncid)
            if visual_id:
                nvid = normalize_id(visual_id)
                if nvid in visual_seen:
                    errors.append(f"duplicate visual_id: {visual_id}")
                visual_seen.add(nvid)
            for mid in _as_list(chart.get("metric_ids")):
                if normalize_id(mid) not in metric_ids_seen:
                    errors.append(f"chart {chart_id}: metric_id {mid} missing from manifest")
        for card in chart_reg.get("cards") or []:
            if not isinstance(card, dict):
                continue
            visual_id = str(card.get("visual_id") or card.get("card_id") or "")
            if visual_id:
                nvid = normalize_id(visual_id)
                if nvid in visual_seen:
                    errors.append(f"duplicate visual_id: {visual_id}")
                visual_seen.add(nvid)

    # Page registry duplicate page IDs
    if isinstance(page_reg, dict):
        page_seen: set[str] = set()
        for page in page_reg.get("pages") or []:
            if not isinstance(page, dict):
                continue
            page_id = str(page.get("page_id") or "").strip()
            if not page_id:
                errors.append("page registry entry missing page_id")
                continue
            npid = normalize_id(page_id)
            if npid in page_seen:
                errors.append(f"duplicate page_id: {page_id}")
            page_seen.add(npid)

            # Approved KPIs required on trusted executive pages only
            if policy.get("approved_kpis_required_for_trusted_executive_pages") and (
                page.get("page_class") == "executive_overview" or "executive" in npid
            ):
                for mid in _as_list(page.get("primary_kpi_ids")):
                    if normalize_id(mid) not in trusted_metric_ids and normalize_id(mid) not in metric_ids_seen:
                        errors.append(
                            f"page {page_id}: approved/trusted KPI {mid} absent from rendered metric manifest"
                        )

            # DQ metrics must not be primary on executive unless guardrail
            if page.get("page_class") == "executive_overview" or "executive" in npid:
                guardrails = {normalize_id(x) for x in _as_list(page.get("guardrail_metric_ids"))}
                for mid in _as_list(page.get("primary_kpi_ids")):
                    if mid.upper().startswith(("DQ-", "PIPE-", "OBS-")) and normalize_id(mid) not in guardrails:
                        errors.append(
                            f"page {page_id}: data-quality/pipeline metric {mid} on executive page "
                            f"without guardrail classification"
                        )

    # Query registry optional uniqueness
    if isinstance(query_reg, dict):
        q_seen: set[str] = set()
        for query in query_reg.get("queries") or []:
            if not isinstance(query, dict):
                continue
            qid = str(query.get("query_id") or "").strip()
            if not qid:
                errors.append("query registry entry missing query_id")
                continue
            nqid = normalize_id(qid)
            if nqid in q_seen:
                errors.append(f"duplicate query_id: {qid}")
            q_seen.add(nqid)

    # Coverage markdown RENDERED rows without proof
    coverage = matplotlib / "kpi_figure_coverage.md"
    if coverage.exists():
        for row in table_dicts(coverage, required_any_headers=("item", "status")):
            status = cell(row, "status").upper()
            if status not in {"RENDERED", "TRUSTED"}:
                continue
            item = cell(row, "item", "name", "metric", "kpi", "metric_id")
            proof = cell(row, "proof", "proof_id", "sql_proof")
            if not proof and item:
                # allow mapping via proof registry / index by item
                if normalize_id(item) not in proof_index and normalize_id(item) not in rendered_proof_ids:
                    if not any(normalize_id(item) == normalize_id(m.get("display_name", "")) for m in metrics):
                        errors.append(f"rendered item {item}: has no proof mapping")

    print(
        f"Presentation traceability: metrics={len(metrics)} "
        f"visuals~{len(rendered_visual_ids)} proofs~{len(rendered_proof_ids)} errors={len(errors)}"
    )
    return print_results("Presentation traceability check", errors, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
