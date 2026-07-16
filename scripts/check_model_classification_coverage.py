#!/usr/bin/env python3
"""Check model/resource classification coverage using manifest unique_ids."""

from __future__ import annotations

import argparse
from pathlib import Path

from lib_gate_common import (
    add_output_json_arg,
    build_resource_inventory,
    cell,
    load_analytics_policy,
    load_resource_classification_policy,
    print_results,
    project_package_name,
    ratio,
    resolve_named_resource,
    resources_by_name,
    table_dicts,
)

KNOWN_CLASSES = {
    "source",
    "staging",
    "intermediate",
    "conformed_entity",
    "core_entity",
    "dimension",
    "role_playing_dimension",
    "bridge",
    "transaction_fact",
    "event_fact",
    "factless_fact",
    "periodic_snapshot_fact",
    "accumulating_snapshot_fact",
    "reporting_fact",
    "reporting_mart",
    "reference",
    "catalog",
    "semantic_model",
    "metric",
    "exposure",
    "snapshot",
    "seed",
    "analysis",
    "test",
    "audit",
    "utility",
    "excluded",
    "unsupported",
    "deferred",
    # legacy aliases still accepted
    "fact",
    "fact/event",
    "fact event",
    "gold fact",
}


def required_resource_types(policy: dict) -> set[str]:
    types: set[str] = set()
    if policy.get("require_enabled_local_models"):
        types.add("model")
    if policy.get("require_sources"):
        types.add("source")
    if policy.get("require_seeds"):
        types.add("seed")
    if policy.get("require_snapshots"):
        types.add("snapshot")
    if policy.get("require_semantic_models"):
        types.add("semantic_model")
    if policy.get("require_metrics"):
        types.add("metric")
    if policy.get("require_exposures"):
        types.add("exposure")
    if policy.get("require_tests_individually"):
        types.add("test")
    return types


def in_scope_unique_ids(
    inventory: list[dict],
    policy: dict,
    *,
    local_package: str | None,
) -> dict[str, dict]:
    present_types = {str(r.get("resource_type")) for r in inventory}
    types = required_resource_types(policy)
    # Only require types that actually exist in the inventory
    types = {t for t in types if t in present_types or t == "model"}
    if "model" not in present_types:
        types.discard("model")
    scoped: dict[str, dict] = {}
    for resource in inventory:
        rtype = str(resource.get("resource_type") or "")
        if rtype not in types:
            continue
        if resource.get("enabled") is False:
            continue
        package = str(resource.get("package_name") or "")
        if (
            not policy.get("require_dependency_package_models")
            and local_package
            and package
            and package != local_package
            and rtype == "model"
        ):
            continue
        uid = str(resource.get("unique_id") or "")
        if uid:
            scoped[uid] = resource
    return scoped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--phase", choices=("analytics", "presentation", "final"), default="analytics")
    args = parser.parse_args()
    root = args.root.resolve()
    analytics_policy = load_analytics_policy(root)
    class_policy = load_resource_classification_policy(root)
    required = float(
        class_policy.get(
            "local_resource_coverage_required",
            analytics_policy.get("model_classification_coverage_required", 1.0),
        )
    )
    production_required = float(class_policy.get("production_resource_coverage_required", required))
    if args.phase == "final":
        # Final release uses the stricter of local vs production coverage thresholds.
        required = max(required, production_required)

    insights = root / "reports" / "agent" / "09_analytics_insights"
    classification = insights / "model_classification.md"
    inventory, inv_source = build_resource_inventory(root)
    # Local package ALWAYS prefers dbt_project.yml name (never inventory order).
    configured = project_package_name(root)
    has_configured = any(str(r.get("package_name") or "") == configured for r in inventory)
    if has_configured:
        local_package = configured
    else:
        # No matching configured package (missing/placeholder dbt_project.yml):
        # use most common non-dbt package — never pick the first inventory row alone.
        from collections import Counter

        pkgs = [
            str(r.get("package_name") or "")
            for r in inventory
            if r.get("package_name")
            and not str(r.get("package_name")).startswith("dbt")
        ]
        local_package = Counter(pkgs).most_common(1)[0][0] if pkgs else configured
    scoped = in_scope_unique_ids(inventory, class_policy, local_package=local_package)
    required_uids = set(scoped.keys())

    if not insights.exists() and not required_uids:
        print("SKIPPED: no analytics insights or in-scope resources yet")
        return 0
    if not required_uids:
        # Models might still be required
        model_uids = {
            uid
            for uid, res in in_scope_unique_ids(
                inventory,
                {**class_policy, "require_sources": False, "require_seeds": False,
                 "require_snapshots": False, "require_semantic_models": False,
                 "require_metrics": False, "require_exposures": False},
                local_package=local_package,
            ).items()
        }
        if not model_uids:
            print("SKIPPED: no in-scope enabled resources")
            return 0
        required_uids = model_uids
        scoped = {uid: next(r for r in inventory if r.get("unique_id") == uid) for uid in required_uids}

    errors: list[str] = []
    warnings: list[str] = []

    if not classification.exists():
        errors.append("missing reports/agent/09_analytics_insights/model_classification.md")
        return print_results("Model classification coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)

    rows = table_dicts(
        classification,
        required_any_headers=("model", "class", "name", "unique_id", "resource_name"),
    )
    if not rows:
        errors.append("model_classification.md has no classification rows")
        return print_results("Model classification coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)

    classified_uids: set[str] = set()
    name_only_ok = 0

    for row in rows:
        unique_id = cell(row, "unique_id", "unique id", "node_id", "node id")
        model_name = cell(row, "model", "model_name", "name", "resource_name").lower().replace("`", "")
        package = cell(row, "package_name", "package")
        version = cell(row, "version")
        class_text = cell(row, "class", "model_class", "classification", "structural_class")
        status = cell(row, "status", "human_approval_status").upper()

        if not model_name and not unique_id:
            continue

        if not class_text:
            errors.append(f"{unique_id or model_name}: classification row missing structural class")
            continue

        normalized_class = class_text.lower().replace(" ", "_").replace("/", "_")
        known = any(
            normalized_class == k.replace(" ", "_").replace("/", "_")
            or k.replace("_", " ") in class_text.lower()
            for k in KNOWN_CLASSES
        )
        if not known and class_text.upper() not in {"EXCLUDED", "UNSUPPORTED", "DEFERRED"}:
            errors.append(f"{unique_id or model_name}: unknown class {class_text!r}")

        if class_text.lower() in {"excluded", "unsupported"}:
            reason = cell(row, "exclusion_reason", "reason", "notes")
            if not reason:
                errors.append(f"{unique_id or model_name}: EXCLUDED/UNSUPPORTED requires exclusion_reason")

        resolved, resolve_status = resolve_named_resource(
            inventory,
            unique_id=unique_id,
            name=model_name,
            package_name=package,
            version=version,
        )
        if resolve_status == "ambiguous":
            collisions = resources_by_name(inventory, model_name)
            detail = ", ".join(
                f"{c.get('unique_id')} ({c.get('package_name')}/{c.get('original_file_path')})"
                for c in collisions[:6]
            )
            errors.append(
                f"{model_name}: ambiguous name-only classification — require unique_id "
                f"(candidates: {detail})"
            )
            continue
        if resolve_status == "missing" and unique_id:
            # Allow classification of planned resources not yet in inventory during analytics
            if args.phase == "final":
                errors.append(f"{unique_id}: classification unique_id not found in inventory")
            else:
                warnings.append(f"{unique_id}: classified but not in current inventory")
            classified_uids.add(unique_id)
            continue
        if resolve_status == "missing":
            warnings.append(f"{model_name}: classified name not found in inventory")
            continue

        assert resolved is not None
        uid = str(resolved.get("unique_id"))
        classified_uids.add(uid)
        if resolve_status == "name_only_ok":
            name_only_ok += 1
            msg = (
                f"{model_name}: unambiguous legacy name-only classification — "
                f"migrate to unique_id={uid}"
            )
            if args.phase == "final" and inv_source == "manifest":
                errors.append(msg + " (final phase requires unique_id)")
            else:
                warnings.append(msg)

        # Ambiguous machine recommendation without human approval
        machine = cell(row, "machine_recommendation", "machine_recommended_class")
        human = cell(row, "human_approval_status", "approval_status", "status").upper()
        if machine and machine.lower() != class_text.lower() and human in {"", "PENDING_REVIEW", "NOT_REQUESTED"}:
            if args.phase == "final":
                errors.append(
                    f"{uid}: ambiguous machine classification requires human approval "
                    f"(recommended={machine}, approved={class_text})"
                )
            else:
                warnings.append(
                    f"{uid}: ambiguous classification pending human review "
                    f"(recommended={machine})"
                )

    missing = sorted(uid for uid in required_uids if uid not in classified_uids)
    # Only require model classifications strictly when models are in scope;
    # sources/seeds may use lightweight rows — count models first for primary coverage
    model_required = {
        uid for uid, res in scoped.items() if res.get("resource_type") == "model"
    }
    model_missing = sorted(uid for uid in model_required if uid not in classified_uids)
    matched = len(model_required) - len(model_missing)
    coverage = ratio(matched, len(model_required)) if model_required else ratio(
        len(required_uids) - len(missing), len(required_uids)
    )

    print(
        f"Model classification ({inv_source}): classified={matched}/"
        f"{len(model_required) or len(required_uids)} "
        f"({(coverage or 0):.0%}) unique_id_denominator=yes"
    )
    if coverage is None:
        errors.append("no built models to classify (empty inventory is NOT_APPLICABLE, not 100%)")
    elif coverage < required:
        examples = model_missing[:8] or missing[:8]
        errors.append(
            f"model classification coverage {coverage:.0%} below required {required:.0%}; "
            f"missing unique_ids: {', '.join(examples)}"
        )
    elif model_missing:
        warnings.append(f"unclassified models remain: {', '.join(model_missing[:8])}")

    if name_only_ok and inv_source == "manifest" and args.phase != "final":
        warnings.append(
            f"{name_only_ok} unambiguous name-only classification row(s) — migrate to unique_id"
        )

    # Enforce non-model resource types when policy requires them and they exist
    for rtype, policy_key in (
        ("snapshot", "require_snapshots"),
        ("semantic_model", "require_semantic_models"),
        ("metric", "require_metrics"),
        ("exposure", "require_exposures"),
        ("source", "require_sources"),
        ("seed", "require_seeds"),
    ):
        if not class_policy.get(policy_key):
            continue
        type_uids = {uid for uid, res in scoped.items() if res.get("resource_type") == rtype}
        type_missing = sorted(uid for uid in type_uids if uid not in classified_uids)
        if type_missing and args.phase == "final":
            errors.append(f"{rtype}s missing classification: {', '.join(type_missing[:6])}")
        elif type_missing:
            warnings.append(f"{rtype}s missing classification: {', '.join(type_missing[:6])}")

    return print_results("Model classification coverage check", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)


if __name__ == "__main__":
    raise SystemExit(main())
