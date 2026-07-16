#!/usr/bin/env python3
"""Validate dbt exposures with unique_id identity, deps, and HITL approval."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from lib_gate_common import (
    add_output_json_arg,
    build_resource_inventory,
    business_approval_status,
    cell,
    compute_exposure_fingerprint,
    is_meaningful_text,
    load_analytics_policy,
    load_manifest,
    load_yaml,
    print_results,
    ratio,
    read_text,
    resolve_named_resource,
    resolve_source_reference,
    resources_by_name,
    table_dicts,
)

INVALID_EVIDENCE = {
    "",
    "pass",
    "approved",
    "agent approved",
    "looks correct",
    "n/a",
    "na",
    "none",
    "todo",
}

_AGENT_FABRICATED_EVIDENCE = (
    "agent approved",
    "agent-approved",
    "agent generated",
    "agent-generated",
    "self-approved by agent",
    "auto-approved by agent",
)


def _is_agent_fabricated_evidence(evidence: str) -> bool:
    """Reject fabricated agent approval phrases, not paths that contain 'agent'."""
    lowered = evidence.lower().strip()
    return any(token in lowered for token in _AGENT_FABRICATED_EVIDENCE)


def parse_exposure_yaml_files(root: Path) -> list[dict[str, Any]]:
    """Parse top-level dbt exposures from models/snapshots/analyses YAML files."""
    exposures: list[dict[str, Any]] = []
    search_roots = [
        root / "models",
        root / "snapshots",
        root / "analyses",
        root,
    ]
    seen_paths: set[str] = set()
    for base in search_roots:
        if not base.exists():
            continue
        patterns = ("*.yml", "*.yaml") if base != root else ("dbt_project.yml",)
        paths: list[Path] = []
        if base == root:
            for name in ("dbt_project.yml", "dbt_project.yaml"):
                candidate = root / name
                if candidate.exists():
                    paths.append(candidate)
        else:
            for pattern in patterns:
                paths.extend(sorted(base.rglob(pattern)))
        for path in paths:
            key = str(path.resolve())
            if key in seen_paths:
                continue
            seen_paths.add(key)
            # Skip non-resource YAML noise under target/
            if "target" in path.parts or "dbt_packages" in path.parts:
                continue
            data = load_yaml(path)
            if not isinstance(data, dict):
                continue
            entries = data.get("exposures")
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and entry.get("name"):
                    row = dict(entry)
                    row["_source"] = str(path.relative_to(root).as_posix())
                    exposures.append(row)
    return exposures


def manifest_exposures(root: Path) -> list[dict[str, Any]]:
    manifest = load_manifest(root)
    if not manifest:
        return []
    nodes = manifest.get("exposures", {})
    results: list[dict[str, Any]] = []
    if isinstance(nodes, dict):
        for node_id, node in nodes.items():
            if isinstance(node, dict):
                row = dict(node)
                row["unique_id"] = node_id
                results.append(row)
    return results


def _owner_name(entry: dict[str, Any]) -> str:
    owner = entry.get("owner")
    if isinstance(owner, dict):
        return str(owner.get("name") or owner.get("email") or "").strip()
    if isinstance(owner, str):
        return owner.strip()
    meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
    return str(meta.get("owner") or meta.get("owner_name") or "").strip()


def _meta_get(entry: dict[str, Any], *keys: str) -> str:
    meta = entry.get("meta") if isinstance(entry.get("meta"), dict) else {}
    for key in keys:
        if key in entry:
            return str(entry.get(key) or "").strip()
        if key in meta:
            return str(meta.get(key) or "").strip()
    return ""


def normalize_depends(entry: dict[str, Any]) -> list[str]:
    depends = entry.get("depends_on")
    deps: list[str] = []
    if isinstance(depends, dict):
        deps = [str(x) for x in (depends.get("nodes") or [])]
    elif isinstance(depends, list):
        deps = [str(x) for x in depends]
    return deps


def resolve_dep_token(token: str, inventory: list[dict[str, Any]]) -> tuple[str | None, str]:
    """Resolve ref()/source()/unique_id/name to unique_id."""
    raw = token.strip().strip("'\"")
    if not raw:
        return None, "missing"
    if raw.startswith(("model.", "source.", "snapshot.", "metric.", "seed.")):
        match, status = resolve_named_resource(inventory, unique_id=raw)
        return (str(match["unique_id"]) if match else None), status
    ref_match = re.match(r"ref\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*v(?:ersion)?\s*=\s*(\d+)\s*)?\)", raw, re.I)
    if ref_match:
        name = ref_match.group(1)
        version = ref_match.group(2) or ""
        match, status = resolve_named_resource(inventory, name=name, version=version)
        if status == "ambiguous":
            return None, "ambiguous"
        return (str(match["unique_id"]) if match else None), status
    src_match = re.match(r"source\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)", raw, re.I)
    if src_match:
        source_name = src_match.group(1)
        table = src_match.group(2)
        match, status = resolve_source_reference(inventory, source_name, table)
        return (str(match["unique_id"]) if match else None), status
    # bare name — migration-only; ambiguous fails
    match, status = resolve_named_resource(inventory, name=raw)
    return (str(match["unique_id"]) if match else None), status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--phase", choices=("analytics", "presentation", "final"), default="analytics")
    args = parser.parse_args()
    root = args.root.resolve()
    policy = load_analytics_policy(root)
    required_ratio = float(policy.get("production_exposure_coverage_required", 1.0))

    insights = root / "reports" / "agent" / "09_analytics_insights"
    presentation = root / "reports" / "agent" / "10_presentation"
    coverage_path = insights / "exposure_coverage.md"
    dbt_project = root / "dbt_project.yml"
    inventory, inv_source = build_resource_inventory(root)

    yaml_exposures = parse_exposure_yaml_files(root)
    manifest_rows = manifest_exposures(root)

    if not insights.exists() and not presentation.exists() and not yaml_exposures and not manifest_rows:
        print("SKIPPED: no analytics/presentation/exposures yet")
        return 0

    errors: list[str] = []
    warnings: list[str] = []
    presentation_exists = (presentation / "matplotlib" / "report.html").exists() or presentation.exists()

    if presentation_exists and not coverage_path.exists():
        errors.append("presentation exists but exposure_coverage.md is missing")
        return print_results("Exposure coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)

    coverage_rows: list[dict[str, str]] = []
    docs_by_key: dict[str, dict[str, str]] = {}
    if coverage_path.exists():
        coverage_rows = table_dicts(
            coverage_path,
            required_any_headers=("exposure", "owner", "unique_id", "name"),
        )
        for row in coverage_rows:
            uid = cell(row, "unique_id", "exposure_id")
            name = cell(row, "exposure", "name", "exposure_name")
            if uid:
                docs_by_key[uid.lower()] = row
            if name:
                docs_by_key[name.lower()] = row

    # Prefer manifest exposures when present
    if manifest_rows:
        exposure_sources = manifest_rows
        source_label = "manifest"
    else:
        exposure_sources = yaml_exposures
        source_label = "yaml"
        if dbt_project.exists() and yaml_exposures and args.phase == "final":
            warnings.append(
                "final phase using YAML exposures without manifest — run dbt parse for unique_ids"
            )

    print(f"Exposure discovery: source={source_label} inventory={inv_source} count={len(exposure_sources)}")

    if presentation_exists and dbt_project.exists() and not exposure_sources:
        blocked = False
        for row in coverage_rows:
            status = cell(row, "validation status", "technical_validation_status", "status").upper()
            if status in {"BLOCKED", "DEFERRED"} and cell(row, "owner") and cell(row, "next_action", "next action"):
                blocked = True
        if not blocked:
            if args.phase == "final":
                errors.append(
                    "production presentation with dbt_project.yml requires a real dbt exposure "
                    "(documentation-only rows do not satisfy final coverage)"
                )
            else:
                warnings.append(
                    "presentation exists without dbt exposure — document BLOCKED/DEFERRED or add exposures YAML"
                )

    production_presentations = 0
    if presentation_exists and dbt_project.exists():
        production_presentations = 1

    complete = 0
    for entry in exposure_sources:
        name = str(entry.get("name") or entry.get("label") or "").strip()
        unique_id = str(entry.get("unique_id") or "").strip()
        if not unique_id and name:
            # Synthesize fallback id for YAML-only until manifest exists
            unique_id = f"exposure.local.{name}"
            entry["unique_id"] = unique_id
        label = unique_id or name
        if not name:
            errors.append("exposure entry missing name")
            continue

        owner = _owner_name(entry)
        purpose = _meta_get(entry, "business_purpose", "description")
        criticality = _meta_get(entry, "criticality")
        refresh = _meta_get(entry, "refresh_expectation", "refresh", "freshness_sla")
        audience = _meta_get(entry, "audience")
        biz_status = _meta_get(entry, "business_approval_status") or "NOT_REQUESTED"
        tech_status = _meta_get(entry, "technical_validation_status") or "PASS"
        evidence = _meta_get(entry, "approval_evidence", "evidence")
        fingerprint = _meta_get(entry, "exposure_fingerprint", "fingerprint")
        no_dep_reason = _meta_get(entry, "no_dependency_reason", "dependency_reason")

        doc = docs_by_key.get(unique_id.lower()) or docs_by_key.get(name.lower())
        if doc:
            owner = cell(doc, "owner", "owner_name") or owner
            purpose = cell(doc, "business purpose", "business_purpose", "purpose") or purpose
            criticality = cell(doc, "criticality") or criticality
            refresh = cell(doc, "refresh", "refresh_expectation", "freshness_sla") or refresh
            audience = cell(doc, "audience") or audience
            biz_status = cell(doc, "business_approval_status", "business approval status") or biz_status
            tech_status = (
                cell(doc, "technical_validation_status", "validation status", "validation_status", "status")
                or tech_status
            )
            evidence = cell(doc, "approval_evidence", "evidence") or evidence
            fingerprint = cell(doc, "exposure_fingerprint", "fingerprint") or fingerprint
            no_dep_reason = cell(doc, "no_dependency_reason", "notes") or no_dep_reason

        if not is_meaningful_text(owner):
            errors.append(f"exposure {label}: missing owner")
        if not is_meaningful_text(purpose):
            errors.append(f"exposure {label}: missing business purpose")
        if not is_meaningful_text(criticality):
            errors.append(f"exposure {label}: missing criticality")
        if not is_meaningful_text(refresh):
            errors.append(f"exposure {label}: missing refresh expectation")

        deps = normalize_depends(entry)
        if not deps and not is_meaningful_text(no_dep_reason):
            errors.append(f"exposure {label}: no dependencies require an explicit reason")
        resolved_deps: list[str] = []
        for dep in deps:
            resolved, status = resolve_dep_token(dep, inventory)
            if status == "ambiguous":
                errors.append(f"exposure {label}: ambiguous dependency {dep!r} — require unique_id")
            elif status == "missing" or not resolved:
                errors.append(f"exposure {label}: missing dependency {dep!r}")
            else:
                # disabled production dependency
                match, _ = resolve_named_resource(inventory, unique_id=resolved)
                if match and match.get("enabled") is False and args.phase in {"presentation", "final"}:
                    errors.append(f"exposure {label}: depends on disabled resource {resolved}")
                resolved_deps.append(resolved)

        if presentation_exists and not doc:
            errors.append(f"exposure {label}: not documented in exposure_coverage.md")

        calc_fp = compute_exposure_fingerprint(
            {
                "type": entry.get("type"),
                "business_purpose": purpose,
                "audience": audience,
                "depends_on_models": resolved_deps,
                "depends_on_sources": [],
                "depends_on_metrics": _meta_get(entry, "depends_on_metrics"),
                "url": entry.get("url") or _meta_get(entry, "delivery_location", "url"),
                "delivery_location": _meta_get(entry, "delivery_location", "url"),
                "refresh_expectation": refresh,
                "criticality": criticality,
                "sensitive_data_classification": _meta_get(entry, "sensitive_data_classification"),
            }
        )
        if fingerprint and fingerprint != calc_fp:
            msg = f"exposure {label}: approval stale — fingerprint changed ({fingerprint} -> {calc_fp})"
            if args.phase == "final":
                errors.append(msg)
            else:
                warnings.append(msg)
            biz_status = "PENDING_REVIEW"

        biz_upper = biz_status.upper()
        if args.phase == "final":
            if biz_upper not in {"APPROVED", "APPROVED_WITH_CONDITIONS"}:
                errors.append(
                    f"exposure {label}: production requires business approval "
                    f"(status={biz_upper or 'MISSING'})"
                )
            elif evidence.lower() in INVALID_EVIDENCE or _is_agent_fabricated_evidence(evidence):
                errors.append(f"exposure {label}: invalid or agent-generated approval evidence")
            elif not evidence:
                errors.append(f"exposure {label}: missing approval evidence")
        elif biz_upper in {"PENDING_REVIEW", "NOT_REQUESTED", "PROPOSED", ""}:
            warnings.append(f"exposure {label}: business approval {biz_upper or 'NOT_REQUESTED'} (draft OK)")

        # Documentation-only cannot satisfy when counting production completeness
        row_ok = (
            is_meaningful_text(owner)
            and is_meaningful_text(purpose)
            and is_meaningful_text(criticality)
            and is_meaningful_text(refresh)
            and (resolved_deps or is_meaningful_text(no_dep_reason))
            and not any(err.startswith(f"exposure {label}:") for err in errors)
        )
        if row_ok and args.phase == "final":
            if biz_upper in {"APPROVED", "APPROVED_WITH_CONDITIONS"} and evidence.lower() not in INVALID_EVIDENCE:
                complete += 1
        elif row_ok and args.phase != "final":
            complete += 1

    # Coverage denominator
    if production_presentations:
        total = max(len(exposure_sources), production_presentations)
        if not exposure_sources and args.phase == "final":
            errors.append(
                "production presentation artifacts exist but no real dbt exposures "
                "(empty denominator is not 100%)"
            )
        else:
            cov = ratio(complete, total)
            if cov is None:
                errors.append("empty production exposure denominator is not 100%")
            else:
                print(f"Production exposure coverage: {complete}/{total} ({cov:.0%})")
                if cov < required_ratio and args.phase in {"presentation", "final"}:
                    errors.append(
                        f"production exposure coverage {cov:.0%} below required {required_ratio:.0%}"
                    )
    elif exposure_sources:
        print(f"Exposure technical rows validated: {complete}/{len(exposure_sources)}")

    return print_results("Exposure coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)


if __name__ == "__main__":
    raise SystemExit(main())
