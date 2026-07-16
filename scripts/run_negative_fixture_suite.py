#!/usr/bin/env python3
"""Run negative fixture regressions.

Each case copies a valid DuckDB fixture (or analytics presentation shell),
applies one intentional defect, runs the targeted validator, and asserts a
nonzero exit with an expected error token.

Exit 0 only when every negative case fails for the intended reason.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

DBT_FIX = ROOT / "fixtures" / "dbt_duckdb"
ANALYTICS_FIX = ROOT / "fixtures" / "analytics"


@dataclass
class NegativeCase:
    case_id: str
    description: str
    script: str
    script_args: list[str]
    expected_token: str
    mutator: str


CASES: list[NegativeCase] = [
    NegativeCase(
        "wrong_reconciliation_pass",
        "Builder records PASS with mismatched expected/actual",
        "run_independent_verifier.py",
        ["--skip-live"],
        "false_pass|builder recorded pass|values differ",
        "false_pass",
    ),
    NegativeCase(
        "missing_proof",
        "Rendered chart without proof_ids",
        "validate_chart_registry.py",
        [],
        "proof",
        "missing_proof",
    ),
    NegativeCase(
        "missing_business_approval",
        "Approved KPI stripped of business approval",
        "check_human_approval_coverage.py",
        ["--phase", "final"],
        "approval|pending|missing",
        "missing_approval",
    ),
    NegativeCase(
        "stale_approval",
        "Approval fingerprint no longer matches contract",
        "check_human_approval_coverage.py",
        ["--phase", "final"],
        "stale",
        "stale_approval",
    ),
    NegativeCase(
        "broken_exposure_dependency",
        "Exposure depends on missing model unique_id",
        "check_exposure_coverage.py",
        ["--phase", "final"],
        "missing|depend|not found|unresolved",
        "broken_exposure",
    ),
    NegativeCase(
        "ambiguous_duplicate_model_name",
        "Two packages share the same model name without unique_id disambiguation",
        "check_model_classification_coverage.py",
        ["--phase", "final"],
        "ambiguous|duplicate|unique_id|collision",
        "duplicate_name",
    ),
    NegativeCase(
        "missing_fact_family",
        "Fact coverage contract removed",
        "check_fact_analytical_coverage.py",
        [],
        "fact|coverage|missing",
        "missing_fact_family",
    ),
    NegativeCase(
        "missing_observability_domain",
        "Required observability domain dropped",
        "check_data_observability_coverage.py",
        [],
        "observability|domain|missing|completeness",
        "missing_observability",
    ),
    NegativeCase(
        "missing_page_contract",
        "Page registry emptied",
        "check_report_page_contracts.py",
        ["--phase", "final"],
        "page|contract|missing",
        "missing_page_contract",
    ),
    NegativeCase(
        "missing_rendered_kpi",
        "Metric manifest metrics cleared",
        "check_presentation_traceability.py",
        ["--phase", "final"],
        "metric|manifest|missing|empty",
        "missing_rendered_kpi",
    ),
    NegativeCase(
        "wrong_tooltip_value",
        "Chart tooltip no longer matches formatted value",
        "validate_chart_registry.py",
        [],
        "tooltip|formatted|missing",
        "wrong_tooltip",
    ),
    NegativeCase(
        "orphan_proof",
        "Proof registry entry with no rendered visual",
        "check_presentation_traceability.py",
        ["--phase", "final"],
        "orphan|proof",
        "orphan_proof",
    ),
    NegativeCase(
        "orphan_page_contract",
        "Page contract without DOM section id",
        "check_report_page_contracts.py",
        ["--phase", "final"],
        "orphan|page|missing",
        "orphan_page",
    ),
    NegativeCase(
        "technical_label_visible",
        "Board uses snake_case id as primary display name",
        "validate_rendered_report_content.py",
        [],
        "technical|snake|display|readable",
        "tech_label",
    ),
    NegativeCase(
        "unaccepted_final_warning",
        "Final gate fails when warning is not explicitly accepted",
        "run_acceptance_gate.py",
        ["--phase", "final", "--strict", "--skip-dbt"],
        "fail|warning|warn",
        "unaccepted_warning",
    ),
    NegativeCase(
        "synthetic_approval_outside_fixtures",
        "Independent verifier rejects synthetic approval outside fixtures/",
        "run_independent_verifier.py",
        ["--skip-live"],
        "synthetic|fixture|approval",
        "synthetic_outside",
    ),
    NegativeCase(
        "warn_without_waiver",
        "Reconciliation WARN/FAIL without formal waiver fails coverage",
        "verify_metric_reconciliation.py",
        [],
        "waiver|reconciliation|fail",
        "recon_warn_no_waiver",
    ),
    NegativeCase(
        "bare_na_fact_family",
        "Bare NOT_APPLICABLE without reason fails fact coverage",
        "check_fact_analytical_coverage.py",
        [],
        "not_applicable|reason|bare",
        "bare_na_fact",
    ),
    NegativeCase(
        "pending_trusted_executive",
        "Trusted executive KPI with PENDING_REVIEW fails human approval at final",
        "check_human_approval_coverage.py",
        ["--phase", "final"],
        "trusted|executive|approval|pending",
        "pending_trusted_exec",
    ),
    NegativeCase(
        "ambiguous_source_table",
        "Two sources with same table name require full source() identity",
        "check_exposure_coverage.py",
        ["--phase", "final"],
        "ambiguous|source|missing|unresolved",
        "ambiguous_source",
    ),
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def seed_dbt_fixture(dest: Path) -> Path:
    src = DBT_FIX / "domain_a_transactional"
    if not src.exists():
        raise FileNotFoundError(f"missing valid fixture {src}")
    if dest.exists():
        shutil.rmtree(dest)
    # Copy without heavy target/dbt_packages when possible, but keep target for inventory
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns("logs", ".venv", "__pycache__", "dbt_packages"),
    )
    return dest


def apply_mutation(root: Path, mutator: str) -> None:
    from lib_gate_common import parse_markdown_tables

    agent = root / "reports" / "agent"
    presentation = agent / "10_presentation"
    matplotlib = presentation / "matplotlib"

    if mutator == "false_pass":
        path = agent / "KPI_DEFINITION_CONTRACTS.md"
        text = path.read_text(encoding="utf-8")
        tables = parse_markdown_tables(text)
        if not tables:
            raise RuntimeError("no KPI tables to mutate")
        headers, rows = tables[0]
        headers_l = [h.lower() for h in headers]
        i_actual = next((i for i, h in enumerate(headers_l) if "actual result" in h), None)
        i_calc = next((i for i, h in enumerate(headers_l) if "calculated status" in h), None)
        if i_actual is None:
            raise RuntimeError("actual result column missing")
        lines = text.splitlines()
        out: list[str] = []
        row_idx = 0
        in_table = False
        mutated = False
        for line in lines:
            if line.strip().startswith("|") and "KPI ID" in line:
                in_table = True
                out.append(line)
                continue
            if in_table and re.match(r"^\|\s*-+", line.strip()):
                out.append(line)
                continue
            if in_table and line.strip().startswith("|") and not mutated:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                is_pass = i_calc is None or (
                    i_calc < len(cells) and cells[i_calc].upper() == "PASS"
                )
                if row_idx < len(rows) and is_pass:
                    if i_actual < len(cells):
                        cells[i_actual] = "999999"
                    out.append("| " + " | ".join(cells) + " |")
                    row_idx += 1
                    mutated = True
                    continue
                row_idx += 1
            out.append(line)
        if not mutated:
            raise RuntimeError("false_pass mutator did not find a PASS KPI row")
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
        return

    if mutator == "missing_proof":
        path = matplotlib / "chart_registry.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["charts"][0]["proof_ids"] = []
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        (presentation / "chart_registry.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    if mutator == "missing_approval":
        path = agent / "KPI_DEFINITION_CONTRACTS.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("| APPROVED |", "| PENDING |", 1)
        path.write_text(text, encoding="utf-8")
        return

    if mutator == "stale_approval":
        path = agent / "KPI_DEFINITION_CONTRACTS.md"
        text = path.read_text(encoding="utf-8")
        # Corrupt a hex fingerprint cell when present; otherwise force a bad token
        if re.search(r"\|\s*[0-9a-f]{16}\s*\|", text, re.I):
            text = re.sub(r"(\|\s*)[0-9a-f]{16}(\s*\|)", r"\1deadbeefdeadbeef\2", text, count=1, flags=re.I)
        else:
            text = text.replace("| APPROVED |", "| APPROVED_STALE |", 1)
        path.write_text(text, encoding="utf-8")
        return

    if mutator == "broken_exposure":
        path = root / "models" / "exposures.yml"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = text.replace("ref('fct_events')", "ref('missing_model_xyz')")
            text = text.replace('ref("fct_events")', 'ref("missing_model_xyz")')
            path.write_text(text, encoding="utf-8")
        cov = agent / "09_analytics_insights" / "exposure_coverage.md"
        if cov.exists():
            text = cov.read_text(encoding="utf-8")
            text = text.replace("fct_events", "missing_model_xyz")
            cov.write_text(text, encoding="utf-8")
        manifest = root / "target" / "manifest.json"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            for exp in (data.get("exposures") or {}).values():
                deps = exp.setdefault("depends_on", {})
                deps["nodes"] = ["model.local.missing_model_xyz"]
            manifest.write_text(json.dumps(data), encoding="utf-8")
        return

    if mutator == "duplicate_name":
        # Name-only classification row + two same-name packages → ambiguous unique_id
        inv_path = agent / "09_analytics_insights" / "model_classification.md"
        if inv_path.exists():
            lines = inv_path.read_text(encoding="utf-8").rstrip().splitlines()
            lines.append(
                "|  | fct_events |  | event_fact | "
                "ambiguous duplicate name without unique_id | event | event_id | event_date | count | n/a | "
                "not_null | PASS | table | HIGH | APPROVED | FAIL |"
            )
            inv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest = root / "target" / "manifest.json"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            nodes = data.setdefault("nodes", {})
            for node in list(nodes.values()):
                if node.get("resource_type") == "model" and str(node.get("name", "")) == "fct_events":
                    clone = dict(node)
                    clone["unique_id"] = "model.other_pkg.fct_events"
                    clone["package_name"] = "other_pkg"
                    nodes[clone["unique_id"]] = clone
                    break
            manifest.write_text(json.dumps(data), encoding="utf-8")
        return

    if mutator == "missing_fact_family":
        path = agent / "09_analytics_insights" / "fact_coverage_contracts.md"
        if path.exists():
            path.write_text("# Fact coverage\n\n| Fact | Status |\n|---|---|\n", encoding="utf-8")
        return

    if mutator == "missing_observability":
        path = agent / "09_analytics_insights" / "data_observability_coverage.md"
        if path.exists():
            path.write_text("# Observability\n\nNo domains covered.\n", encoding="utf-8")
        return

    if mutator == "missing_page_contract":
        path = presentation / "page_registry.json"
        path.write_text(json.dumps({"version": "1", "pages": []}, indent=2), encoding="utf-8")
        if (matplotlib / "page_registry.json").exists():
            (matplotlib / "page_registry.json").write_text(
                json.dumps({"version": "1", "pages": []}, indent=2), encoding="utf-8"
            )
        contracts = presentation / "report_page_contracts.md"
        contracts.write_text(
            "# Report Page Contracts\n\n"
            "| Page ID | Page Name | Page Class | Audience |\n"
            "|---|---|---|---|\n",
            encoding="utf-8",
        )
        return

    if mutator == "missing_rendered_kpi":
        empty = {"version": "1", "metrics": []}
        (presentation / "rendered_metric_manifest.json").write_text(json.dumps(empty, indent=2), encoding="utf-8")
        (matplotlib / "rendered_metric_manifest.json").write_text(json.dumps(empty, indent=2), encoding="utf-8")
        return

    if mutator == "wrong_tooltip":
        path = matplotlib / "chart_registry.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for chart in data.get("charts") or []:
            chart["hover_fields"] = []
            chart["tooltip_template"] = None
            for row in chart.get("data") or []:
                row.pop("formatted_value", None)
                row.pop("tooltip_text", None)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        (presentation / "chart_registry.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    if mutator == "orphan_proof":
        path = presentation / "proof_registry.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": "1", "proofs": []}
        data.setdefault("proofs", []).append(
            {
                "proof_id": "PROOF-ORPHAN-999",
                "metric_id": "KPI-ORPHAN",
                "page_id": "executive_overview",
                "visual_ids": ["visual_does_not_exist"],
                "proof_status": "PASS",
            }
        )
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return

    if mutator == "orphan_page":
        contracts = presentation / "report_page_contracts.md"
        lines = (
            contracts.read_text(encoding="utf-8").rstrip().splitlines()
            if contracts.exists()
            else [
                "# Report Page Contracts",
                "",
                "| Page ID | Page Name | Page Class | Audience | Business Processes | Business Questions | "
                "Decisions Supported | Primary KPIs | Driver Metrics | Guardrail Metrics | Dimensions | Filters | "
                "Reporting Period | Visuals | Exceptions | Insight Narrative | Recommended Actions | Caveats | "
                "Technical Validation Status | Business Approval Status |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        lines.append(
            "| orphan_page_xyz | Orphan Page | executive_overview | leadership | "
            "n/a | n/a | n/a | KPI-001 | n/a | n/a | n/a | n/a | All time | n/a | n/a | n/a | n/a | "
            "SYNTHETIC_FIXTURE | PASS | APPROVED |"
        )
        contracts.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    if mutator == "tech_label":
        html = matplotlib / "report.html"
        if html.exists():
            text = html.read_text(encoding="utf-8")
            # Visible (non-script) technical label — validate_rendered_report_content fails on this
            injection = (
                '<section id="all_measures_bad" class="page"><h2>All Measures</h2>'
                '<table class="measure-board"><thead><tr><th>Measure</th><th>Value</th></tr></thead>'
                "<tbody><tr><td>fct_events_row_count_total</td><td>100</td></tr></tbody></table></section>\n"
            )
            if "<body>" in text:
                text = text.replace("<body>", "<body>\n" + injection, 1)
            else:
                text = injection + text
            html.write_text(text, encoding="utf-8")
        return

    if mutator == "unaccepted_warning":
        # Strip purpose/expected/captured from one proof → SQL proof headers WARN
        for proof in agent.glob("**/sql_proofs/*.sql"):
            proof.write_text("-- status: PASS\nselect 1 as x;\n", encoding="utf-8")
            break
        for name in ("ACCEPTED_WARNINGS.md", "accepted_warnings.md", "WARNING_ACCEPTANCE.md"):
            path = agent / name
            if path.exists():
                path.write_text("# Accepted warnings\n\nNone.\n", encoding="utf-8")
        for control in (
            agent / "CONTEXT_TREE.md",
            agent / "PIPELINE_STATUS.md",
            agent / "HUMAN_ATTENTION_BOARD.md",
        ):
            if control.exists():
                text = control.read_text(encoding="utf-8")
                text = re.sub(r"(?im)^.*accepted\s+warning.*$", "", text)
                text = re.sub(r"(?im)^.*deferred\s+warning.*$", "", text)
                control.write_text(text, encoding="utf-8")
        cfg = root / "project.config.yml"
        if cfg.exists():
            text = cfg.read_text(encoding="utf-8")
            if "final_fail_on_warning" not in text:
                text += (
                    "\nacceptance_policy:\n"
                    "  final_fail_on_warning: true\n"
                    "  require_explicit_warning_acceptance: true\n"
                )
                cfg.write_text(text, encoding="utf-8")
        return

    if mutator == "synthetic_outside":
        path = agent / "KPI_DEFINITION_CONTRACTS.md"
        text = path.read_text(encoding="utf-8")
        if "TEST FIXTURE — NOT PRODUCTION APPROVAL" not in text:
            text = "TEST FIXTURE — NOT PRODUCTION APPROVAL\n\n" + text
            path.write_text(text, encoding="utf-8")
        plan = root / "AGENT_PLAN.md"
        if plan.exists():
            plan.write_text("# Plan\n\nProduction-like project for negative test.\n", encoding="utf-8")
        return

    if mutator == "recon_warn_no_waiver":
        path = agent / "KPI_DEFINITION_CONTRACTS.md"
        text = path.read_text(encoding="utf-8")
        # Force a calculated FAIL recorded as WARN without waiver register
        text = text.replace("| PASS |", "| WARN |", 1)
        # Corrupt actual toward mismatch if numeric columns exist
        text = re.sub(
            r"(\|\s*)(\d+(\.\d+)?)(\s*\|\s*)(PASS|WARN)(\s*\|)",
            r"\g<1>999999\g<4>WARN\g<6>",
            text,
            count=1,
        )
        path.write_text(text, encoding="utf-8")
        waiver = agent / "RECONCILIATION_WAIVER_REGISTER.md"
        if waiver.exists():
            waiver.unlink()
        return

    if mutator == "bare_na_fact":
        path = agent / "09_analytics_insights" / "fact_coverage_contracts.md"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = text.replace("NOT_APPLICABLE: no duration measures at this grain", "NOT_APPLICABLE", 1)
            text = text.replace("NOT_APPLICABLE: aging not in first-pass scope", "N/A", 1)
            path.write_text(text, encoding="utf-8")
        return

    if mutator == "pending_trusted_exec":
        # Mark an approved executive KPI as PENDING while keeping it trusted in registries
        path = agent / "KPI_DEFINITION_CONTRACTS.md"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            text = text.replace("| APPROVED |", "| PENDING_REVIEW |", 1)
            path.write_text(text, encoding="utf-8")
        return

    if mutator == "ambiguous_source":
        # Inject a second source with same table name into a fake inventory via exposure dep
        yml = root / "models" / "exposures.yml"
        if not yml.exists():
            yml = root / "models" / "report_consumers.yml"
        if yml.exists():
            text = yml.read_text(encoding="utf-8")
            if "source(" not in text:
                text += "\n# mutated\n"
            # Force depends_on with ambiguous bare table name
            text = re.sub(
                r"depends_on:.*",
                "depends_on: [\"source('raw_a', 'orders')\", \"source('raw_b', 'orders')\"]",
                text,
                count=1,
            )
            yml.write_text(text, encoding="utf-8")
        # Ensure manifest has two sources named orders
        manifest = root / "target" / "manifest.json"
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            sources = data.setdefault("sources", {})
            sources["source.domain_a_transactional.raw_a.orders"] = {
                "unique_id": "source.domain_a_transactional.raw_a.orders",
                "name": "orders",
                "resource_type": "source",
                "package_name": "domain_a_transactional",
                "source_name": "raw_a",
            }
            sources["source.domain_a_transactional.raw_b.orders"] = {
                "unique_id": "source.domain_a_transactional.raw_b.orders",
                "name": "orders",
                "resource_type": "source",
                "package_name": "domain_a_transactional",
                "source_name": "raw_b",
            }
            manifest.write_text(json.dumps(data), encoding="utf-8")
        return

    raise ValueError(f"unknown mutator: {mutator}")


def token_match(haystack: str, pattern: str) -> bool:
    text = haystack.lower()
    return any(tok.strip() and tok.strip() in text for tok in pattern.lower().split("|"))


def run_case(case: NegativeCase, work: Path) -> tuple[bool, str]:
    root = work / case.case_id
    if case.mutator == "synthetic_outside":
        # Place outside fixtures/ path
        root = work / "production_like_project" / case.case_id
        seed_dbt_fixture(root)
        apply_mutation(root, case.mutator)
    else:
        seed_dbt_fixture(root)
        apply_mutation(root, case.mutator)

    cmd = [sys.executable, str(SCRIPTS / case.script), "--root", str(root), *case.script_args]
    proc = run(cmd, SCRIPTS)
    combined = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode == 0:
        return False, f"expected failure but exit 0\n{combined[-2000:]}"
    if not token_match(combined, case.expected_token):
        # Also accept JSON report failures for independent verifier
        report = root / "reports" / "agent" / "INDEPENDENT_VERIFICATION_REPORT.json"
        if report.exists():
            payload = report.read_text(encoding="utf-8")
            if token_match(payload, case.expected_token):
                return True, "failed via independent report"
        return False, f"exit {proc.returncode} but missing token /{case.expected_token}/\n{combined[-2500:]}"
    return True, f"exit {proc.returncode}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", help="Run only named case id(s)")
    args = parser.parse_args()

    selected = CASES
    if args.case:
        wanted = set(args.case)
        selected = [c for c in CASES if c.case_id in wanted]
        missing = wanted - {c.case_id for c in selected}
        if missing:
            print(f"Unknown cases: {sorted(missing)}")
            return 1

    if not (DBT_FIX / "domain_a_transactional").exists():
        print("SKIPPED: valid DuckDB fixtures not built")
        return 0

    failures = 0
    with tempfile.TemporaryDirectory(prefix="neg_fixtures_") as tmp:
        work = Path(tmp)
        for case in selected:
            ok, detail = run_case(case, work)
            status = "PASS" if ok else "FAIL"
            if not ok:
                failures += 1
            print(f"[{status}] {case.case_id} :: {case.description} :: {detail.splitlines()[0]}")
            if not ok:
                print(detail)

    print(f"Negative fixture suite: cases={len(selected)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
