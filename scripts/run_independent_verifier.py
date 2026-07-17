#!/usr/bin/env python3
"""Independent verification — fresh process, repository evidence only.

Recalculates coverage by invoking deterministic validators in subprocesses and
performing local artifact recalculation. Does not depend on builder chat context.

Writes:
  reports/agent/INDEPENDENT_VERIFICATION_REPORT.md
  reports/agent/INDEPENDENT_VERIFICATION_REPORT.json

Exit 1 when any required check fails.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lib_gate_common import (  # noqa: E402
    compare_formatted_values,
    inventory_from_manifest,
    load_accepted_warnings,
    load_analytics_policy,
    load_presentation_policy,
    load_validator_result_json,
    parse_markdown_tables,
    read_text,
    VALIDATOR_RESULT_SCHEMA_VERSION,
)

# Deterministic validators — never include run_acceptance_gate or this script.
REQUIRED_CHECKS: list[tuple[str, list[str], str]] = [
    ("check_model_classification_coverage.py", ["--phase", "final"], "manifest_inventory_classification"),
    ("check_fact_analytical_coverage.py", [], "fact_coverage"),
    ("check_metric_contract_completeness.py", [], "kpi_contract_completeness"),
    ("verify_metric_reconciliation.py", [], "numeric_and_set_reconciliation"),
    ("check_human_approval_coverage.py", ["--phase", "final"], "human_approval_coverage"),
    ("check_time_intelligence_coverage.py", [], "time_intelligence_coverage"),
    ("check_data_observability_coverage.py", [], "observability_coverage"),
    ("check_exposure_coverage.py", ["--phase", "final"], "exposure_coverage"),
    ("check_report_page_contracts.py", ["--phase", "final"], "page_contracts"),
    ("check_presentation_traceability.py", ["--phase", "final"], "visual_traceability_proof_mapping"),
    ("validate_rendered_report_content.py", [], "rendered_values"),
    ("validate_chart_registry.py", [], "chart_registry_proof_mapping"),
    ("check_report_business_readability.py", [], "technical_labels_not_visible"),
    ("validate_kpi_proofs.py", [], "proof_mapping"),
    ("check_layer_proof_coverage.py", [], "layer_proof_mapping"),
    ("check_requirement_traceability.py", [], "requirement_traceability"),
]

OPTIONAL_CHECKS: list[tuple[str, list[str], str]] = [
    ("check_presentation_coverage.py", [], "presentation_coverage"),
    (
        "validate_live_report_dom.py",
        ["--desktop", "--tablet", "--mobile"],
        "live_browser_behavior",
    ),
]

SYNTHETIC_APPROVAL_MARKERS = (
    "TEST FIXTURE — NOT PRODUCTION APPROVAL",
    "TEST FIXTURE - NOT PRODUCTION APPROVAL",
    "TEST FIXTURE ONLY",
    "synthetic approval evidence",
)

FIXTURE_PATH_TOKENS = frozenset({"fixtures", "fixture"})


@dataclass
class ChildResult:
    script: str
    category: str
    status: str
    return_code: int
    stdout: str = ""
    stderr: str = ""


@dataclass
class LocalCheck:
    name: str
    status: str
    detail: str = ""


@dataclass
class VerificationReport:
    overall_status: str = "PASS"
    checked_at: str = ""
    root: str = ""
    mode: str = "independent"
    results: list[ChildResult] = field(default_factory=list)
    local_checks: list[LocalCheck] = field(default_factory=list)
    recalculation: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)

    def add_child(self, result: ChildResult) -> None:
        self.results.append(result)
        if result.status in {"FAIL", "BLOCKED"}:
            self.failures.append(f"{result.script} [{result.category}]: {result.status} exit {result.return_code}")
        # WARN is recorded in results; overall_status handles escalation — never convert to PASS

    def add_local(self, check: LocalCheck) -> None:
        self.local_checks.append(check)
        if check.status == "FAIL":
            self.failures.append(f"local:{check.name}: {check.detail}")


def is_fixture_root(root: Path) -> bool:
    """Synthetic approvals are only permitted when the project path is under fixtures/."""
    return bool({p.lower() for p in root.parts} & FIXTURE_PATH_TOKENS)


def run_child(
    script: str,
    args: list[str],
    category: str,
    root: Path,
    timeout: int,
    *,
    allow_skip_live: bool,
    require_live: bool = False,
) -> ChildResult:
    script_path = SCRIPT_DIR / script
    if not script_path.exists():
        return ChildResult(script=script, category=category, status="SKIPPED", return_code=0)

    result_dir = root / "reports" / "agent" / "_validator_results"
    result_dir.mkdir(parents=True, exist_ok=True)
    result_json = result_dir / f"independent_{Path(script).stem}.json"

    cmd = [sys.executable, str(script_path), "--root", str(root), *args]
    if script == "validate_live_report_dom.py" and allow_skip_live and not require_live:
        cmd.append("--allow-skip")
    # validate_rendered_report_content accepts --root; prefer report-dir when present
    if script == "validate_rendered_report_content.py":
        report_dir = root / "reports" / "agent" / "10_presentation" / "matplotlib"
        if report_dir.exists():
            cmd = [sys.executable, str(script_path), "--report-dir", str(report_dir)]
        else:
            return ChildResult(script=script, category=category, status="SKIPPED", return_code=0)

    # Prefer machine-readable results when supported
    if "--output-json" not in cmd:
        cmd.extend(["--output-json", str(result_json)])

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "INDEPENDENT_VERIFIER_ACTIVE": "1"},
        )
    except subprocess.TimeoutExpired:
        return ChildResult(
            script=script,
            category=category,
            status="FAIL",
            return_code=124,
            stderr="timeout",
        )

    out = (completed.stdout or "") + (completed.stderr or "")
    status = None
    if result_json.exists():
        try:
            payload = load_validator_result_json(result_json)
            status = payload.status
            # Contradiction checks
            if status in {"FAIL", "BLOCKED"} and completed.returncode == 0:
                status = "FAIL"
                out = f"JSON status {payload.status} contradicts exit 0\n" + out
            elif status == "PASS" and completed.returncode != 0:
                status = "FAIL"
                out = f"JSON status PASS contradicts exit {completed.returncode}\n" + out
            elif status in {"WARN", "SKIPPED"} and completed.returncode != 0:
                status = "FAIL"
                out = f"JSON status {payload.status} contradicts exit {completed.returncode}\n" + out
        except Exception as exc:  # noqa: BLE001
            return ChildResult(
                script=script,
                category=category,
                status="FAIL",
                return_code=completed.returncode,
                stdout=(completed.stdout or "")[-2000:],
                stderr=f"malformed validator result JSON: {exc}",
            )
    else:
        # Missing JSON is a failure for production validators (not optional skip)
        if "--output-json" in cmd:
            return ChildResult(
                script=script,
                category=category,
                status="FAIL",
                return_code=completed.returncode,
                stdout=(completed.stdout or "")[-2000:],
                stderr=f"missing validator result JSON: {result_json}",
            )

    if status is None:
        if completed.returncode == 0 and "SKIPPED:" in out:
            status = "SKIPPED"
        elif completed.returncode == 0:
            status = "PASS"
        else:
            status = "FAIL"

    # Required live browser SKIPPED is FAIL
    if script == "validate_live_report_dom.py" and require_live and status == "SKIPPED":
        status = "FAIL"
        out = "live browser SKIPPED is not allowed when interactive report requires Playwright\n" + out

    return ChildResult(
        script=script,
        category=category,
        status=status,
        return_code=completed.returncode,
        stdout=(completed.stdout or "")[-4000:],
        stderr=(completed.stderr or "")[-2000:],
    )


def recalculate_manifest_inventory(root: Path) -> dict[str, Any]:
    manifest_path = root / "target" / "manifest.json"
    if not manifest_path.exists():
        return {"status": "SKIPPED", "detail": "no target/manifest.json", "count": 0}
    try:
        manifest = json.loads(read_text(manifest_path))
        inventory = inventory_from_manifest(manifest)
    except Exception as exc:  # noqa: BLE001
        return {"status": "FAIL", "detail": str(exc), "count": 0}
    by_type: dict[str, int] = {}
    for row in inventory:
        rt = str(row.get("resource_type") or "unknown")
        by_type[rt] = by_type.get(rt, 0) + 1
    return {
        "status": "PASS",
        "count": len(inventory),
        "by_resource_type": by_type,
        "sample_unique_ids": [r.get("unique_id") for r in inventory[:8]],
    }


def detect_builder_false_pass(root: Path) -> LocalCheck:
    """Recalculate KPI expected vs actual using validation types/tolerances."""
    from lib_gate_common import (
        cell,
        parse_markdown_tables,
        parse_number,
        reconcile_numeric,
        reconcile_row_count,
        reconcile_set_match,
        table_dicts,
    )

    contracts = root / "reports" / "agent" / "KPI_DEFINITION_CONTRACTS.md"
    if not contracts.exists():
        return LocalCheck("recalculate_numeric_values", "SKIPPED", "no KPI_DEFINITION_CONTRACTS.md")

    mismatches: list[str] = []
    checked = 0
    rows = table_dicts(
        contracts,
        required_any_headers=("kpi id", "kpi_id", "expected", "expected result"),
    )
    if not rows:
        # Fallback: legacy header scan
        text = read_text(contracts)
        for headers, raw_rows in parse_markdown_tables(text):
            headers_l = [h.lower() for h in headers]

            def idx(*names: str) -> int | None:
                for name in names:
                    for i, h in enumerate(headers_l):
                        if name in h:
                            return i
                return None

            i_kpi = idx("kpi id", "kpi_id")
            i_expected = idx("expected result", "expected")
            i_actual = idx("actual result", "actual")
            i_calc = idx("calculated status", "calculated")
            i_tech = idx("technical verification status", "technical verification")
            if i_expected is None or i_actual is None:
                continue
            for cells in raw_rows:
                if not cells:
                    continue
                expected = str(cells[i_expected] if i_expected < len(cells) else "").strip()
                actual = str(cells[i_actual] if i_actual < len(cells) else "").strip()
                if not expected and not actual:
                    continue
                if expected.upper().startswith("NOT_APPLICABLE") or actual.upper().startswith("NOT_APPLICABLE"):
                    continue
                checked += 1
                kpi = str(cells[i_kpi] if i_kpi is not None and i_kpi < len(cells) else "?").strip()
                calc = (
                    str(cells[i_calc] if i_calc is not None and i_calc < len(cells) else "").strip().upper()
                )
                tech = (
                    str(cells[i_tech] if i_tech is not None and i_tech < len(cells) else "").strip().upper()
                )
                ok, reason = compare_formatted_values(actual, expected)
                recorded_pass = calc == "PASS" or tech == "PASS"
                if recorded_pass and not ok:
                    mismatches.append(
                        f"{kpi}: builder recorded PASS but values differ ({actual!r} vs {expected!r}): {reason}"
                    )
    else:
        for row in rows:
            kpi = cell(row, "kpi id", "kpi_id", "id") or "?"
            expected = cell(row, "expected result", "expected")
            actual = cell(row, "actual result", "actual")
            if not expected and not actual:
                continue
            if expected.upper().startswith("NOT_APPLICABLE") or actual.upper().startswith("NOT_APPLICABLE"):
                continue
            vtype = cell(row, "validation_type", "recon_type").lower() or "numeric_tolerance"
            tolerance = cell(row, "diff_tolerance", "tolerance", "diff") or "0"
            calc = cell(row, "calculated status", "calculated_status").upper()
            tech = cell(row, "technical verification status", "technical_verification_status").upper()
            recorded_pass = calc == "PASS" or tech == "PASS"
            checked += 1
            calc_status = "PASS"
            if vtype == "set_match":
                result = reconcile_set_match(expected, actual, tolerance)
                calc_status = result["calculated_status"]
            elif vtype == "row_count_match":
                result = reconcile_row_count(expected, actual, tolerance)
                calc_status = result["calculated_status"]
            elif parse_number(expected) is not None and parse_number(actual) is not None:
                result = reconcile_numeric(
                    expected,
                    actual,
                    "exact" if vtype == "numeric_exact" else tolerance,
                )
                calc_status = result["calculated_status"]
            else:
                ok, reason = compare_formatted_values(actual, expected)
                if recorded_pass and not ok:
                    mismatches.append(
                        f"{kpi}: builder recorded PASS but values differ ({actual!r} vs {expected!r}): {reason}"
                    )
                continue
            if recorded_pass and calc_status == "FAIL":
                mismatches.append(
                    f"{kpi}: builder recorded PASS but typed recalculation FAIL "
                    f"(type={vtype}, tolerance={tolerance!r}, expected={expected!r}, actual={actual!r})"
                )

    if mismatches:
        return LocalCheck(
            "detect_builder_false_pass",
            "FAIL",
            "; ".join(mismatches[:5]),
        )
    return LocalCheck(
        "detect_builder_false_pass",
        "PASS",
        f"checked={checked} false_pass=0",
    )


def detect_synthetic_approval_misuse(root: Path) -> LocalCheck:
    """Reject fake production approval markers outside fixture paths."""
    if is_fixture_root(root):
        return LocalCheck(
            "synthetic_approval_path_guard",
            "PASS",
            "fixture path — synthetic approval evidence permitted",
        )

    hits: list[str] = []
    agent = root / "reports" / "agent"
    if not agent.exists():
        return LocalCheck("synthetic_approval_path_guard", "PASS", "no reports/agent")

    for path in agent.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json", ".yml", ".yaml", ".txt"}:
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        for marker in SYNTHETIC_APPROVAL_MARKERS:
            if marker.lower() in text.lower():
                hits.append(str(path.relative_to(root)).replace("\\", "/"))
                break
    if hits:
        return LocalCheck(
            "synthetic_approval_path_guard",
            "FAIL",
            "synthetic TEST FIXTURE approval found outside fixture paths: " + ", ".join(hits[:8]),
        )
    return LocalCheck("synthetic_approval_path_guard", "PASS", "no synthetic markers outside fixtures")


def detect_fixed_count_gates(root: Path) -> LocalCheck:
    """Ensure analytics_policy does not encode arbitrary fixed model/KPI count gates."""
    try:
        policy = load_analytics_policy(root)
    except Exception as exc:  # noqa: BLE001
        return LocalCheck("no_fixed_count_gates", "SKIPPED", str(exc))

    banned_keys = {
        "min_models",
        "min_kpis",
        "min_charts",
        "required_kpi_count",
        "required_model_count",
        "fixed_model_count",
        "exact_kpi_count",
    }
    found = [k for k in banned_keys if k in (policy or {})]
    # Nested presentation/analytics policies
    for nested_name in ("presentation_policy", "analytics_policy", "acceptance_policy"):
        nested = (policy or {}).get(nested_name) if isinstance(policy, dict) else None
        if isinstance(nested, dict):
            found.extend(f"{nested_name}.{k}" for k in banned_keys if k in nested)

    # Also scan project.config.yml text for suspicious fixed-count requirements
    cfg = root / "project.config.yml"
    if cfg.exists():
        text = read_text(cfg).lower()
        if re.search(r"\bmin_(models|kpis|charts)\s*:", text):
            found.append("project.config.yml:min_* gate")

    if found:
        return LocalCheck("no_fixed_count_gates", "FAIL", "fixed count gates present: " + ", ".join(found))
    return LocalCheck("no_fixed_count_gates", "PASS", "no arbitrary fixed-count gates")


def _evidence_bindings(root: Path) -> dict[str, str]:
    """Fingerprint fields that bind IV to the current report/manifest/commit."""
    bindings: dict[str, str] = {}
    try:
        from lib_llm_playwright_review import compute_report_bundle_hash

        bundle, _ = compute_report_bundle_hash(root)
        if bundle:
            bindings["report_bundle_hash"] = bundle
    except Exception:  # noqa: BLE001
        pass
    manifest = root / "target" / "manifest.json"
    if manifest.exists():
        try:
            from lib_manifest_relation import sha256_file

            bindings["manifest_checksum"] = sha256_file(manifest)
        except Exception:  # noqa: BLE001
            pass
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(root), text=True
        ).strip()
        if commit:
            bindings["repository_commit_sha"] = commit
    except Exception:  # noqa: BLE001
        pass
    return bindings


def write_reports(root: Path, report: VerificationReport) -> None:
    agent = root / "reports" / "agent"
    agent.mkdir(parents=True, exist_ok=True)

    payload = {
        "overall_status": report.overall_status,
        "checked_at": report.checked_at,
        "root": report.root,
        "mode": report.mode,
        "results": [asdict(item) for item in report.results],
        "local_checks": [asdict(item) for item in report.local_checks],
        "recalculation": report.recalculation,
        "failures": report.failures,
        "notes": [
            "Independent verifier reads repository/dbt/report artifacts only.",
            "Browser PASS does not grant business approval.",
            "Synthetic TEST FIXTURE approvals are valid only under fixtures/ paths.",
        ],
    }
    payload.update(_evidence_bindings(root))
    (agent / "INDEPENDENT_VERIFICATION_REPORT.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Independent Verification Report",
        "",
        f"**Overall status:** {report.overall_status}",
        f"**Checked at:** {report.checked_at}",
        f"**Project root:** `{report.root}`",
        f"**Mode:** `{report.mode}`",
        "",
        "## Local recalculation",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for item in report.local_checks:
        detail = (item.detail or "").replace("|", "\\|")
        lines.append(f"| {item.name} | {item.status} | {detail} |")

    lines.extend(
        [
            "",
            "## Validator Results",
            "",
            "| Script | Category | Status | Exit Code |",
            "|---|---|---|---|",
        ]
    )
    for item in report.results:
        lines.append(
            f"| {item.script} | {item.category} | {item.status} | {item.return_code} |"
        )
    lines.extend(["", "## Failures", ""])
    if report.failures:
        lines.extend(f"- {failure}" for failure in report.failures)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Fresh process; no builder chat context.",
            "- Synthetic fixture approvals must not appear outside `fixtures/`.",
            "",
        ]
    )
    (agent / "INDEPENDENT_VERIFICATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument(
        "--phase",
        default="analytics",
        help="Verification phase. final/presentation enforce live browser when interactive.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat like final for live-browser enforcement when an interactive report exists.",
    )
    parser.add_argument(
        "--allow-skip-live",
        action="store_true",
        help="Allow live browser check to SKIP when Playwright is unavailable (non-final/dev only).",
    )
    parser.add_argument(
        "--skip-live",
        action="store_true",
        help="Skip live browser validation (still records SKIPPED). Rejected at final/strict.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    presentation_policy = load_presentation_policy(root)
    interactive = (
        root / "reports" / "agent" / "10_presentation" / "matplotlib" / "report.html"
    ).exists()
    phase = str(args.phase or "analytics").strip().lower()
    final_like = phase in {"final", "acceptance"} or bool(args.strict)
    policy_require = bool(presentation_policy.get("require_live_browser_validation", True))
    require_at_final = bool(presentation_policy.get("require_live_browser_at_final", True))
    # Live is mandatory for interactive reports at final/strict when policy requires it.
    require_live = bool(interactive and policy_require and final_like and require_at_final)
    if args.skip_live and require_live:
        print(
            "ERROR: --skip-live rejected when interactive report requires live browser "
            "validation at final/strict"
        )
        return 1
    # Development-only: explicit skip flags record SKIPPED and never claim PASS for live.
    allow_skip_live = (bool(args.allow_skip_live) or bool(args.skip_live)) and not require_live

    report = VerificationReport(
        checked_at=datetime.now(timezone.utc).isoformat(),
        root=str(root),
    )

    # Local recalculation first (does not trust builder PASS fields blindly)
    inv = recalculate_manifest_inventory(root)
    report.recalculation["manifest_inventory"] = inv
    report.add_local(
        LocalCheck(
            "manifest_inventory",
            inv.get("status", "FAIL"),
            inv.get("detail") or f"resources={inv.get('count', 0)}",
        )
    )
    report.add_local(detect_builder_false_pass(root))
    report.add_local(detect_synthetic_approval_misuse(root))
    report.add_local(detect_fixed_count_gates(root))

    matplotlib = root / "reports" / "agent" / "10_presentation" / "matplotlib"
    has_presentation = (matplotlib / "report.html").exists()

    for script, extra, category in REQUIRED_CHECKS:
        # Skip presentation-only scripts when no presentation folder
        if category in {
            "page_contracts",
            "visual_traceability_proof_mapping",
            "rendered_values",
            "chart_registry_proof_mapping",
            "technical_labels_not_visible",
        } and not matplotlib.exists():
            report.add_child(
                ChildResult(script=script, category=category, status="SKIPPED", return_code=0)
            )
            continue
        result = run_child(
            script,
            extra,
            category,
            root,
            args.timeout,
            allow_skip_live=allow_skip_live,
            require_live=False,
        )
        # Legitimate SKIPPED (applicability) remains SKIPPED; do not convert to PASS
        report.add_child(result)
        print(f"{result.script}: {result.status} (exit {result.return_code})")

    for script, extra, category in OPTIONAL_CHECKS:
        if script == "validate_live_report_dom.py":
            if args.skip_live and not require_live:
                report.add_child(
                    ChildResult(script=script, category=category, status="SKIPPED", return_code=0)
                )
                print(f"{script}: SKIPPED")
                continue
            if not has_presentation:
                report.add_child(
                    ChildResult(script=script, category=category, status="SKIPPED", return_code=0)
                )
                print(f"{script}: SKIPPED (no interactive report)")
                continue
        result = run_child(
            script,
            extra,
            category,
            root,
            args.timeout,
            allow_skip_live=allow_skip_live,
            require_live=require_live and script == "validate_live_report_dom.py",
        )
        report.add_child(result)
        print(f"{result.script}: {result.status} (exit {result.return_code})")

    # WARN must not become PASS unless every child warning is explicitly accepted
    statuses = {r.status for r in report.results} | {c.status for c in report.local_checks}
    if report.failures or "FAIL" in statuses or "BLOCKED" in statuses:
        report.overall_status = "FAIL"
    elif "WARN" in statuses:
        accepted = load_accepted_warnings(root)
        unaccepted: list[str] = []
        result_dir = root / "reports" / "agent" / "_validator_results"
        for child in report.results:
            if child.status != "WARN":
                continue
            # Prefer machine-readable warning_ids from child JSON
            json_path = result_dir / f"independent_{Path(child.script).stem}.json"
            warning_ids: list[str] = []
            if json_path.exists():
                try:
                    payload = load_validator_result_json(json_path)
                    warning_ids = list(payload.warning_ids or [])
                except Exception:
                    warning_ids = []
            if not warning_ids:
                warning_ids = [child.script]
            for wid in warning_ids:
                hay = wid.lower()
                if not any(token == hay for token in accepted if token and token not in {"accepted", "deferred", "warning", "warnings"}):
                    unaccepted.append(wid)
        if unaccepted:
            report.overall_status = "WARN"
            report.failures.append(
                "unaccepted independent-verifier warnings: " + ", ".join(unaccepted[:8])
            )
            report.overall_status = "FAIL"
        else:
            # Accepted warnings remain visible in child results; overall may PASS
            report.overall_status = "PASS"
    else:
        report.overall_status = "PASS"
    write_reports(root, report)
    print(f"Independent verification overall status: {report.overall_status}")
    print("Wrote reports/agent/INDEPENDENT_VERIFICATION_REPORT.md")
    print("Wrote reports/agent/INDEPENDENT_VERIFICATION_REPORT.json")
    # Exit 0 for PASS and WARN (WARN preserved in JSON); FAIL -> 1
    return 1 if report.overall_status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
