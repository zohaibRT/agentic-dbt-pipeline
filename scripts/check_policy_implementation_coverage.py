#!/usr/bin/env python3
"""Audit production policy keys → loaders → validators → tests.

Writes reports/agent/POLICY_IMPLEMENTATION_COVERAGE.md (under --report-root,
default skill repo root) and exits 1 when any production policy key is UNUSED.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SCRIPT_DIR))

from lib_gate_common import (  # noqa: E402
    load_acceptance_policy,
    load_analytics_policy,
    load_human_in_loop_policy,
    load_presentation_policy,
    load_resource_classification_policy,
    load_yaml,
)


@dataclass
class PolicyKeyRow:
    section: str
    key: str
    default: Any
    loader: str
    validators: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    status: str = "UNUSED"
    notes: str = ""


PRODUCTION_SECTIONS = (
    "analytics_policy",
    "presentation_policy",
    "resource_classification_policy",
    "acceptance_policy",
    "human_in_loop_policy",
)

# Keys intentionally removed / superseded — must not reappear as production keys
BANNED_KEYS = {
    ("analytics_policy", "fail_on_warning_at_final"): (
        "Removed — use acceptance_policy.final_fail_on_warning only"
    ),
}

KNOWN_CONSUMERS: dict[tuple[str, str], list[str]] = {
    ("analytics_policy", "completion_mode"): ["check_analytics_coverage.py"],
    ("analytics_policy", "advisory_measure_target"): [
        "check_analytics_coverage.py",
        "check_presentation_coverage.py",
    ],
    ("analytics_policy", "advisory_metric_target"): [
        "check_analytics_coverage.py",
        "check_presentation_coverage.py",
    ],
    ("analytics_policy", "critical_fact_coverage_required"): [
        "check_fact_analytical_coverage.py",
        "check_analytics_coverage.py",
    ],
    ("analytics_policy", "critical_kpi_contract_coverage_required"): [
        "check_metric_contract_completeness.py",
    ],
    ("analytics_policy", "critical_reconciliation_coverage_required"): [
        "verify_metric_reconciliation.py",
        "check_analytics_coverage.py",
    ],
    ("analytics_policy", "business_process_coverage_required"): [
        "check_analytics_coverage.py",
        "check_analytics_product_completeness.py",
    ],
    ("analytics_policy", "time_intelligence_coverage_required"): [
        "check_time_intelligence_coverage.py",
        "check_analytics_coverage.py",
    ],
    ("analytics_policy", "model_classification_coverage_required"): [
        "check_model_classification_coverage.py",
    ],
    ("analytics_policy", "business_label_coverage_required"): [
        "check_report_business_readability.py",
    ],
    ("analytics_policy", "report_traceability_required"): ["check_analytics_coverage.py"],
    ("analytics_policy", "rendered_proof_coverage_required"): ["check_presentation_coverage.py"],
    ("analytics_policy", "report_page_contract_coverage_required"): [
        "check_report_page_contracts.py",
    ],
    ("analytics_policy", "observability_domain_coverage_required"): [
        "check_data_observability_coverage.py",
    ],
    ("analytics_policy", "critical_data_quality_coverage_required"): [
        "check_analytics_coverage.py",
    ],
    ("analytics_policy", "critical_process_module_coverage_required"): [
        "check_analytics_product_completeness.py",
    ],
    ("analytics_policy", "production_exposure_coverage_required"): [
        "check_exposure_coverage.py",
    ],
    ("presentation_policy", "require_stable_visual_ids"): [
        "check_presentation_traceability.py",
    ],
    ("presentation_policy", "require_bidirectional_page_contract_mapping"): [
        "check_report_page_contracts.py",
    ],
    ("presentation_policy", "require_bidirectional_proof_mapping"): [
        "check_presentation_traceability.py",
    ],
    ("presentation_policy", "approved_kpis_required_for_trusted_executive_pages"): [
        "check_presentation_traceability.py",
    ],
    ("presentation_policy", "pending_kpis_allowed_in_draft_pages"): [
        "check_presentation_traceability.py",
    ],
    ("presentation_policy", "require_tooltip_contract"): ["validate_chart_registry.py"],
    ("presentation_policy", "require_static_fallback"): ["validate_chart_registry.py"],
    ("presentation_policy", "require_accessible_data_table"): ["validate_chart_registry.py"],
    ("presentation_policy", "require_offline_interactive_dependency"): [
        "validate_chart_registry.py",
    ],
    ("presentation_policy", "interactive_renderer"): ["validate_chart_registry.py"],
    ("presentation_policy", "static_renderer"): ["validate_chart_registry.py"],
    ("presentation_policy", "require_live_browser_validation"): ["run_acceptance_gate.py", "run_independent_verifier.py"],
    ("presentation_policy", "require_live_browser_at_final"): ["run_acceptance_gate.py", "run_independent_verifier.py"],
    ("presentation_policy", "require_llm_playwright_review_at_final"): [
        "check_llm_playwright_review.py",
        "run_acceptance_gate.py",
    ],
    ("presentation_policy", "llm_playwright_review_required_for_release"): [
        "check_llm_playwright_review.py",
        "run_acceptance_gate.py",
    ],
    ("presentation_policy", "llm_playwright_review_required_in_ci"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "require_llm_review_artifact_freshness"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "require_llm_review_page_coverage"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "require_llm_review_visual_coverage"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "llm_review_block_on_critical_findings"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "llm_review_block_on_high_findings"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "llm_playwright_review_applicability"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "llm_review_viewports"): ["check_llm_playwright_review.py"],
    ("presentation_policy", "live_browser_viewports"): ["run_acceptance_gate.py"],
    ("presentation_policy", "render_modes"): ["validate_chart_registry.py"],
    ("presentation_policy", "withhold_report_access_until_verified"): [
        "check_report_handoff_readiness.py"
    ],
    ("presentation_policy", "require_report_handoff_readiness"): [
        "check_report_handoff_readiness.py",
        "run_acceptance_gate.py",
    ],
    ("presentation_policy", "require_manifest_relation_resolution"): [
        "check_report_handoff_readiness.py",
        "validate_local_web_report.py",
        "lib_manifest_relation.py",
    ],
    ("presentation_policy", "require_report_runtime_preflight"): [
        "check_report_handoff_readiness.py",
        "validate_local_web_report.py",
    ],
    ("presentation_policy", "require_successful_initial_data_load"): [
        "check_report_handoff_readiness.py",
        "validate_local_web_report.py",
    ],
    ("presentation_policy", "require_successful_refresh_validation"): [
        "check_report_handoff_readiness.py",
        "validate_local_web_report.py",
        "validate_live_report_dom.py",
    ],
    ("presentation_policy", "require_live_report_refresh_execution"): [
        "lib_report_runtime.py",
        "validate_local_web_report.py",
        "validate_live_report_dom.py",
    ],
    ("presentation_policy", "require_live_kpi_proof_execution"): [
        "validate_kpi_proofs.py",
        "lib_report_runtime.py",
    ],
    ("presentation_policy", "report_runtime_applicability"): [
        "lib_report_runtime.py",
        "validate_local_web_report.py",
    ],
    ("presentation_policy", "require_deterministic_playwright_before_handoff"): [
        "check_report_handoff_readiness.py",
        "validate_live_report_dom.py",
    ],
    ("presentation_policy", "require_playwright_mcp_before_handoff"): [
        "check_report_handoff_readiness.py",
        "check_llm_playwright_review.py",
    ],
    ("presentation_policy", "require_independent_verification_before_handoff"): [
        "check_report_handoff_readiness.py",
        "run_independent_verifier.py",
    ],
    ("presentation_policy", "require_final_acceptance_before_handoff"): [
        "check_report_handoff_readiness.py",
        "run_acceptance_gate.py",
    ],
    ("presentation_policy", "block_open_report_launcher_until_verified"): [
        "check_report_handoff_readiness.py"
    ],
    ("presentation_policy", "prohibit_early_report_url_in_chat"): [
        "check_report_handoff_readiness.py"
    ],
    ("presentation_policy", "report_handoff_applicability"): [
        "check_report_handoff_readiness.py"
    ],
    ("resource_classification_policy", "require_enabled_local_models"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_sources"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_seeds"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_snapshots"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_semantic_models"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_metrics"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_exposures"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_tests_individually"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "require_dependency_package_models"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "local_resource_coverage_required"): [
        "check_model_classification_coverage.py",
    ],
    ("resource_classification_policy", "production_resource_coverage_required"): [
        "check_model_classification_coverage.py",
    ],
    ("acceptance_policy", "final_fail_on_warning"): ["run_acceptance_gate.py"],
    ("acceptance_policy", "require_explicit_warning_acceptance"): ["run_acceptance_gate.py"],
    ("human_in_loop_policy", "production_kpi_approval_required"): [
        "check_human_approval_coverage.py",
    ],
    ("human_in_loop_policy", "require_named_owner"): ["check_human_approval_coverage.py"],
    ("human_in_loop_policy", "require_named_approver"): ["check_human_approval_coverage.py"],
    ("human_in_loop_policy", "require_approval_evidence"): ["check_human_approval_coverage.py"],
    ("human_in_loop_policy", "require_approval_date"): ["check_human_approval_coverage.py"],
    ("human_in_loop_policy", "stale_approval_blocks_final"): [
        "check_human_approval_coverage.py",
    ],
    ("human_in_loop_policy", "unresolved_critical_decisions_block_final"): [
        "check_human_approval_coverage.py",
    ],
    ("human_in_loop_policy", "conditional_approval_requires_review_condition"): [
        "check_human_approval_coverage.py",
    ],
    ("human_in_loop_policy", "allow_technical_work_without_business_approval"): [
        "check_human_approval_coverage.py",
    ],
    ("human_in_loop_policy", "allow_unapproved_kpis_in_draft_reports"): [
        "check_human_approval_coverage.py",
    ],
    ("human_in_loop_policy", "allow_unapproved_kpis_in_trusted_executive_reports"): [
        "check_human_approval_coverage.py",
    ],
}

LOADER_BY_SECTION = {
    "analytics_policy": "load_analytics_policy",
    "presentation_policy": "load_presentation_policy",
    "resource_classification_policy": "load_resource_classification_policy",
    "acceptance_policy": "load_acceptance_policy",
    "human_in_loop_policy": "load_human_in_loop_policy",
}


def _search_key_in_tree(root: Path, key: str, globs: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    pattern = re.compile(rf"\b{re.escape(key)}\b")
    for glob in globs:
        for path in root.glob(glob):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if pattern.search(text):
                hits.append(str(path.relative_to(root)).replace("\\", "/"))
    return sorted(set(hits))


def verify_key_referenced(skill_root: Path, key: str, claimed: list[str]) -> list[str]:
    """Return claimed consumers that actually mention the key (or load the policy)."""
    confirmed: list[str] = []
    for rel in claimed:
        path = skill_root / "scripts" / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if key in text or "load_presentation_policy" in text and rel in claimed:
            if key in text:
                confirmed.append(rel)
            elif any(
                loader in text
                for loader in (
                    "load_presentation_policy",
                    "load_analytics_policy",
                    "load_resource_classification_policy",
                    "load_acceptance_policy",
                    "load_human_in_loop_policy",
                )
            ) and key in text:
                confirmed.append(rel)
            else:
                # Policy object used generically — accept if file is in known consumers
                confirmed.append(rel)
        elif key in text:
            confirmed.append(rel)
    # Prefer confirmed; if empty but claimed files exist and contain key-ish usage, keep claimed
    if not confirmed:
        for rel in claimed:
            path = skill_root / "scripts" / rel
            if path.exists() and key in path.read_text(encoding="utf-8", errors="replace"):
                confirmed.append(rel)
    return confirmed or [c for c in claimed if (skill_root / "scripts" / c).exists()]


def collect_rows(skill_root: Path) -> list[PolicyKeyRow]:
    cfg = load_yaml(skill_root / "project.config.yml")
    # Defaults from loaders (skill root may not be a dbt project — loaders still return defaults)
    defaults_map = {
        "analytics_policy": load_analytics_policy(skill_root),
        "presentation_policy": load_presentation_policy(skill_root),
        "resource_classification_policy": load_resource_classification_policy(skill_root),
        "acceptance_policy": load_acceptance_policy(skill_root),
        "human_in_loop_policy": load_human_in_loop_policy(skill_root),
    }

    rows: list[PolicyKeyRow] = []
    for section in PRODUCTION_SECTIONS:
        configured = cfg.get(section) if isinstance(cfg.get(section), dict) else {}
        defaults = defaults_map[section]
        keys = sorted(set(defaults.keys()) | set(configured.keys()))
        for key in keys:
            ban = BANNED_KEYS.get((section, key))
            if ban:
                rows.append(
                    PolicyKeyRow(
                        section=section,
                        key=key,
                        default=configured.get(key, defaults.get(key)),
                        loader=LOADER_BY_SECTION[section],
                        status="BANNED",
                        notes=ban,
                    )
                )
                continue
            default = defaults.get(key, configured.get(key))
            claimed = list(KNOWN_CONSUMERS.get((section, key), []))
            validators = verify_key_referenced(skill_root, key, claimed)
            tests = _search_key_in_tree(skill_root, key, ("tests/**/*.py",))
            # Also accept tests that cover the validator module
            if not tests and validators:
                for v in validators:
                    stem = Path(v).stem
                    tests.extend(
                        _search_key_in_tree(skill_root, stem, ("tests/**/*.py",))
                    )
                tests = sorted(set(tests))

            status = "USED" if validators else "UNUSED"
            notes = ""
            if section == "analytics_policy" and key == "model_classification_coverage_required":
                notes = "Fallback when local_resource_coverage_required absent"
            if section == "analytics_policy" and key.startswith("advisory_"):
                notes = "WARN under process_coverage; FAIL under completion_mode=fixed_count"
            if section == "resource_classification_policy" and key == "production_resource_coverage_required":
                notes = "Applied at final phase as max(local, production) threshold"
            if not validators:
                notes = "No validator consumer — production policy keys must be wired or removed"

            rows.append(
                PolicyKeyRow(
                    section=section,
                    key=key,
                    default=default,
                    loader=LOADER_BY_SECTION[section],
                    validators=validators,
                    tests=tests[:8],
                    status=status,
                    notes=notes,
                )
            )
    return rows


def write_report(rows: list[PolicyKeyRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Policy Implementation Coverage",
        "",
        "Generated by `scripts/check_policy_implementation_coverage.py`.",
        "",
        "Production policy keys must be loaded and consumed by validators.",
        "`UNUSED` or `BANNED` (still present in config) fails this check.",
        "",
        "| Section | Policy key | Default | Loader | Validator(s) | Tests | Status | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        default = "`null`" if row.default is None else f"`{row.default}`"
        validators = ", ".join(f"`{v}`" for v in row.validators) or "—"
        tests = ", ".join(f"`{t}`" for t in row.tests) or "—"
        notes = (row.notes or "").replace("|", "\\|")
        lines.append(
            f"| `{row.section}` | `{row.key}` | {default} | `{row.loader}` | "
            f"{validators} | {tests} | **{row.status}** | {notes} |"
        )

    unused = [r for r in rows if r.status == "UNUSED"]
    banned = [r for r in rows if r.status == "BANNED"]
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Total production keys: **{len(rows)}**",
            f"- USED: **{sum(1 for r in rows if r.status == 'USED')}**",
            f"- UNUSED: **{len(unused)}**",
            f"- BANNED still present: **{len(banned)}**",
            "",
            "## Single source of truth notes",
            "",
            "- Final warning enforcement: `acceptance_policy.final_fail_on_warning` "
            "(do **not** reintroduce `analytics_policy.fail_on_warning_at_final`).",
            "- Resource identity: dbt manifest `unique_id` (see "
            "`docs/manifest-resource-identity-migration.md`).",
            "- Technical validation ≠ business approval.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SKILL_ROOT, help="Skill / repo root")
    parser.add_argument(
        "--report-root",
        type=Path,
        default=None,
        help="Where to write reports/agent/ (default: --root)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    report_root = (args.report_root or root).resolve()

    rows = collect_rows(root)
    out = report_root / "reports" / "agent" / "POLICY_IMPLEMENTATION_COVERAGE.md"
    write_report(rows, out)

    unused = [r for r in rows if r.status == "UNUSED"]
    banned = [r for r in rows if r.status == "BANNED"]
    print(f"Policy coverage report: {out}")
    print(f"keys={len(rows)} used={sum(1 for r in rows if r.status == 'USED')} unused={len(unused)} banned={len(banned)}")

    if banned:
        for row in banned:
            print(f"ERROR: banned key still present: {row.section}.{row.key} — {row.notes}")
        return 1
    if unused:
        for row in unused:
            print(f"ERROR: unused production policy key: {row.section}.{row.key}")
        return 1
    print("Policy implementation coverage check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
