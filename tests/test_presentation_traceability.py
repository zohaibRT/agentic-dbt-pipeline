#!/usr/bin/env python3
"""P0-PRESENTATION-TRACEABILITY-PAGE-CONTRACTS tests."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIX = ROOT / "fixtures" / "analytics"
DBT_FIX = ROOT / "fixtures" / "dbt_duckdb"

sys.path.insert(0, str(SCRIPTS))
from lib_gate_common import compare_formatted_values  # noqa: E402
from lib_interactive_presentation import write_interactive_presentation  # noqa: E402


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
    )


def _seed_minimal_presentation(root: Path) -> Path:
    """Copy a working analytics fixture presentation baseline into tmp root."""
    src = FIX / "domain_a_transactional"
    if not src.exists():
        raise unittest.SkipTest("analytics fixtures not built")
    # copy key trees
    for rel in (
        "reports/agent/KPI_DEFINITION_CONTRACTS.md",
        "reports/agent/10_presentation",
        "project.config.yml",
        "models/gold",
    ):
        src_path = src / rel
        dst_path = root / rel
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        elif src_path.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
    matplotlib = root / "reports" / "agent" / "10_presentation" / "matplotlib"
    write_interactive_presentation(matplotlib, volume_total=100, completion_rate=0.8)
    return matplotlib


class PresentationTraceabilityTests(unittest.TestCase):
    def test_01_duplicate_page_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            pages = root / "reports" / "agent" / "10_presentation" / "page_registry.json"
            data = json.loads(pages.read_text(encoding="utf-8"))
            data["pages"].append(dict(data["pages"][0]))
            pages.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("duplicate page_id", (proc.stdout + proc.stderr).lower())

    def test_02_duplicate_visual_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            charts = root / "reports" / "agent" / "10_presentation" / "chart_registry.json"
            data = json.loads(charts.read_text(encoding="utf-8"))
            data["charts"].append(dict(data["charts"][0]))
            charts.write_text(json.dumps(data), encoding="utf-8")
            # mirror
            (root / "reports/agent/10_presentation/matplotlib/chart_registry.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            out = (proc.stdout + proc.stderr).lower()
            self.assertTrue("duplicate visual_id" in out or "duplicate chart_id" in out)

    def test_03_duplicate_metric_id_mapping_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            man = root / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"].append(dict(data["metrics"][0]))
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("duplicate metric_id", (proc.stdout + proc.stderr).lower())

    def test_04_rendered_item_without_proof_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            man = root / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"][0]["proof_ids"] = []
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("missing proof", (proc.stdout + proc.stderr).lower())

    def test_05_proof_without_rendered_item_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            proofs = root / "reports" / "agent" / "10_presentation" / "proof_registry.json"
            data = json.loads(proofs.read_text(encoding="utf-8"))
            data["proofs"].append(
                {
                    "proof_id": "PROOF-orphan-exec",
                    "metric_id": "KPI-999",
                    "kpi_id": "KPI-999",
                    "page_id": "executive_overview",
                    "visual_ids": ["visual_missing"],
                    "proof_status": "PASS",
                    "captured_value": "1",
                    "displayed_value": "1",
                }
            )
            proofs.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("no rendered item", (proc.stdout + proc.stderr).lower())

    def test_06_proof_kpi_id_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            proofs = root / "reports" / "agent" / "10_presentation" / "proof_registry.json"
            data = json.loads(proofs.read_text(encoding="utf-8"))
            data["proofs"][0]["kpi_id"] = "KPI-WRONG"
            data["proofs"][0]["metric_id"] = "KPI-WRONG"
            proofs.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("mismatch", (proc.stdout + proc.stderr).lower())

    def test_07_approved_kpi_absent_from_trusted_report_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            pages = root / "reports" / "agent" / "10_presentation" / "page_registry.json"
            data = json.loads(pages.read_text(encoding="utf-8"))
            for page in data["pages"]:
                if page.get("page_id") == "executive_overview":
                    page["primary_kpi_ids"] = ["KPI-001", "KPI-002", "KPI-MISSING"]
                    page["trusted"] = True
            pages.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("absent", (proc.stdout + proc.stderr).lower())

    def test_08_pending_kpi_displayed_as_trusted_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            man = root / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"][0]["business_approval_status"] = "PENDING_REVIEW"
            data["metrics"][0]["trust_level"] = "TRUSTED"
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("pending", (proc.stdout + proc.stderr).lower())

    def test_09_draft_kpi_visibly_labelled_pending_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            man = root / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"].append(
                {
                    "metric_id": "KPI-DRAFT",
                    "kpi_id": "KPI-DRAFT",
                    "display_name": "Draft Volume (Pending)",
                    "page_ids": ["all_metrics"],
                    "visual_ids": ["card_draft"],
                    "proof_ids": [],
                    "trust_level": "DRAFT",
                    "business_approval_status": "PENDING_REVIEW",
                    "technical_validation_status": "PASS",
                    "formatted_value": "0",
                    "displayed_value": "0",
                }
            )
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script(
                "check_presentation_traceability.py", "--root", str(root), "--phase", "presentation"
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_10_displayed_value_differing_from_proof_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            man = root / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"][0]["displayed_value"] = "999"
            data["metrics"][0]["formatted_value"] = "999"
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("differ", (proc.stdout + proc.stderr).lower())

    def test_11_formatting_only_difference_within_precision_passes(self) -> None:
        ok, _ = compare_formatted_values("80.0%", "0.8", format_rule="percent")
        self.assertTrue(ok)
        ok2, _ = compare_formatted_values("1,000", "1000", format_rule="integer")
        self.assertTrue(ok2)

    def test_12_missing_page_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            (root / "reports" / "agent" / "10_presentation" / "report_page_contracts.md").unlink()
            proc = run_script("check_report_page_contracts.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("missing report_page_contracts", (proc.stdout + proc.stderr).lower())

    def test_13_orphan_page_contract_fails_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            contracts = root / "reports" / "agent" / "10_presentation" / "report_page_contracts.md"
            # Replace contracts with known pages plus an orphan row (same schema)
            base_rows = contracts.read_text(encoding="utf-8").strip().splitlines()
            header = [line for line in base_rows if line.startswith("| Page ID")][0]
            sep = [line for line in base_rows if line.startswith("|---")][0]
            keep = [line for line in base_rows if line.startswith("| executive_overview")]
            orphan = (
                "| orphan_page_xyz | Orphan Page | process_performance | auditors | p | q | d | "
                "KPI-001 | KPI-001 | NOT_APPLICABLE: none | dim | f | All time | v | "
                "NOT_APPLICABLE: none | i | a | c | PASS | APPROVED |"
            )
            contracts.write_text(
                "# Report Page Contracts\n\n" + "\n".join([header, sep] + keep + [orphan]) + "\n",
                encoding="utf-8",
            )
            proc = run_script("check_report_page_contracts.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("orphan", (proc.stdout + proc.stderr).lower())

    def test_14_incomplete_page_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            contracts = root / "reports" / "agent" / "10_presentation" / "report_page_contracts.md"
            contracts.write_text(
                """
# Report Page Contracts

| Page ID | Page Name | Audience | Status |
|---|---|---|---|
| executive_overview | Executive Overview | leadership | PASS |
""",
                encoding="utf-8",
            )
            proc = run_script("check_report_page_contracts.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("incomplete", (proc.stdout + proc.stderr).lower())

    def test_15_dimension_page_detection_uses_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True, exist_ok=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.local.dim_entities | dim_entities | dimension | PASS |
""",
                encoding="utf-8",
            )
            # Remove dimensions page from contracts
            contracts = root / "reports" / "agent" / "10_presentation" / "report_page_contracts.md"
            lines = [
                line
                for line in contracts.read_text(encoding="utf-8").splitlines()
                if "all_dimensions" not in line and "dimension_explorer" not in line.lower()
            ]
            contracts.write_text("\n".join(lines) + "\n", encoding="utf-8")
            proc = run_script("check_report_page_contracts.py", "--root", str(root), "--phase", "presentation")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("classification", (proc.stdout + proc.stderr).lower())

    def test_16_technical_id_in_internal_json_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed_minimal_presentation(root)
            man = matplotlib / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"][0]["source_resource_unique_id"] = "model.demo.fct_events"
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script(
                "validate_rendered_report_content.py",
                "--root",
                str(root),
                "--report-dir",
                str(matplotlib),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_17_technical_id_visible_as_display_label_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed_minimal_presentation(root)
            man = matplotlib / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"][0]["display_name"] = "fct_events_count"
            man.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script(
                "validate_rendered_report_content.py",
                "--root",
                str(root),
                "--report-dir",
                str(matplotlib),
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("technical label", (proc.stdout + proc.stderr).lower())

    def test_18_dq_metric_on_executive_without_guardrail_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            pages = root / "reports" / "agent" / "10_presentation" / "page_registry.json"
            data = json.loads(pages.read_text(encoding="utf-8"))
            for page in data["pages"]:
                if page.get("page_id") == "executive_overview":
                    page["primary_kpi_ids"] = ["KPI-001", "DQ-001"]
                    page["guardrail_metric_ids"] = []
            pages.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("guardrail", (proc.stdout + proc.stderr).lower())

    def test_19_display_name_change_does_not_break_id_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            man = root / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"][0]["display_name"] = "Total Event Volume (Renamed)"
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script("check_presentation_traceability.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_20_human_approval_separate_from_technical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_minimal_presentation(root)
            man = root / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json"
            data = json.loads(man.read_text(encoding="utf-8"))
            data["metrics"][0]["technical_validation_status"] = "PASS"
            data["metrics"][0]["business_approval_status"] = "PENDING_REVIEW"
            data["metrics"][0]["trust_level"] = "DRAFT"
            data["metrics"][0]["display_name"] = "Volume KPI (Pending Review)"
            data["metrics"][0]["page_ids"] = ["all_metrics"]
            man.write_text(json.dumps(data), encoding="utf-8")
            (root / "reports/agent/10_presentation/matplotlib/rendered_metric_manifest.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            proc = run_script(
                "check_presentation_traceability.py", "--root", str(root), "--phase", "presentation"
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_fixtures_pass_traceability(self) -> None:
        for base in (FIX / "domain_a_transactional", DBT_FIX / "domain_a_transactional"):
            if not base.exists():
                continue
            if not (base / "reports" / "agent" / "10_presentation" / "rendered_metric_manifest.json").exists() and not (
                base / "reports" / "agent" / "10_presentation" / "matplotlib" / "rendered_metric_manifest.json"
            ).exists():
                continue
            proc = run_script("check_presentation_traceability.py", "--root", str(base), "--phase", "final")
            self.assertEqual(proc.returncode, 0, f"{base}: {proc.stdout}{proc.stderr}")


if __name__ == "__main__":
    unittest.main()
