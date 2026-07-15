#!/usr/bin/env python3
"""P0-INTERACTIVE-CHARTS-HOVER-STATIC-EXPORT tests.

Static / unit coverage only. Live browser hover verification is Batch 6.
"""

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

sys.path.insert(0, str(SCRIPTS))
from lib_chart_renderer import (  # noqa: E402
    build_chart_spec,
    build_tooltip_text,
    ensure_offline_plotly_vendor,
    export_static_image,
    format_display_value,
    plotly_available,
    render_interactive_chart,
)
from lib_interactive_presentation import write_interactive_presentation  # noqa: E402


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
    )


def _seed(root: Path) -> Path:
    src = FIX / "domain_a_transactional"
    if not src.exists():
        raise unittest.SkipTest("analytics fixtures not built")
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
    write_interactive_presentation(matplotlib, volume_total=5986, completion_rate=0.2611)
    return matplotlib


class InteractiveChartsTests(unittest.TestCase):
    def test_01_interactive_line_chart_generated(self) -> None:
        spec = build_chart_spec(
            chart_id="line_demo",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI Trend",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            unit="events",
            data=[
                {"period": "Jan", "period_label": "January 2026", "volume": 100},
                {"period": "Mar", "period_label": "March 2026", "volume": 5986},
            ],
        )
        html = render_interactive_chart(spec)
        self.assertIn("data-chart-id=\"line_demo\"", html)
        self.assertIn("Volume KPI", html)
        self.assertTrue("svg-chart" in html or "plotly-chart" in html)

    def test_02_exact_value_in_chart_data(self) -> None:
        spec = build_chart_spec(
            chart_id="exact_value",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            data=[{"period": "Mar", "period_label": "March 2026", "volume": 5986}],
        )
        payload = json.dumps(spec["data"])
        self.assertIn("5986", payload)
        self.assertIn("5,986", spec["data"][0]["formatted_value"])

    def test_03_hover_template_contains_metric_display_name(self) -> None:
        row = {
            "metric_display_name": "Volume KPI",
            "period_label": "March 2026",
            "formatted_value": "5,986 events",
            "series_display_name": "Actual",
        }
        tip = build_tooltip_text(row)
        self.assertIn("Volume KPI", tip)
        spec = build_chart_spec(
            chart_id="hover_name",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            metric_display_name="Volume KPI",
            data=[{"period": "Mar", "period_label": "March 2026", "volume": 5986}],
        )
        self.assertIn("Volume KPI", spec["data"][0]["tooltip_text"])
        self.assertTrue(spec.get("tooltip_template"))

    def test_04_currency_formatting(self) -> None:
        text = format_display_value(63136022.16, "currency", currency="SAR", precision=2)
        self.assertEqual(text, "SAR 63,136,022.16")

    def test_05_percentage_formatting(self) -> None:
        text = format_display_value(0.2611, "percent", precision=2)
        self.assertEqual(text, "26.11%")

    def test_06_date_formatting(self) -> None:
        spec = build_chart_spec(
            chart_id="date_fmt",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            date_grain="month",
            data=[
                {
                    "period": "Mar",
                    "full_date": "2026-03-01",
                    "period_label": "March 2026",
                    "volume": 100,
                }
            ],
        )
        self.assertIn("March 2026", spec["data"][0]["tooltip_text"])
        self.assertEqual(spec["date_grain"], "month")

    def test_07_multi_series_tooltip_identifies_series(self) -> None:
        tip = build_tooltip_text(
            {
                "metric_display_name": "Volume KPI",
                "series_display_name": "Prior period",
                "period_label": "March 2026",
                "formatted_value": "5,978 events",
            }
        )
        self.assertIn("Prior period", tip)

    def test_08_missing_periods_not_interpolated(self) -> None:
        spec = build_chart_spec(
            chart_id="gap_line",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            connect_missing=False,
            data=[
                {"period": "Jan", "period_label": "January 2026", "volume": 90},
                {"period": "Feb", "period_label": "February 2026", "volume": None, "missing_period": True},
                {"period": "Mar", "period_label": "March 2026", "volume": 100},
            ],
        )
        html = render_interactive_chart(spec)
        self.assertIn("missing", html.lower())
        self.assertTrue(spec["data"][1].get("missing_period"))
        self.assertIsNone(spec["data"][1].get("volume"))
        # Must not silently interpolate: SVG uses chart-missing; Plotly uses connectgaps=false + null y
        self.assertTrue(
            "chart-missing" in html
            or "connectgaps" in html.lower()
            or '"y":[90,null,100]' in html.replace(" ", "")
            or "null" in html and "connectgaps\":false" in html.replace(" ", "").lower().replace("'", '"')
            or '"connectgaps": false' in html
            or "\"connectgaps\":false" in html.replace(" ", ""),
            msg="expected explicit missing-period handling without interpolation",
        )
        self.assertIn("not interpolated", html.lower() + json.dumps(spec["data"]).lower())

    def test_09_partial_period_labelled(self) -> None:
        spec = build_chart_spec(
            chart_id="partial",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            data=[
                {
                    "period": "Mar",
                    "period_label": "March 2026",
                    "volume": 100,
                    "is_partial_period": True,
                }
            ],
        )
        self.assertIn("Partial period", spec["data"][0]["tooltip_text"])
        self.assertIn("partial", (spec["data"][0].get("partial_period_note") or "").lower())

    def test_10_mobile_tap_configuration(self) -> None:
        spec = build_chart_spec(
            chart_id="mobile",
            page_id="executive_overview",
            chart_type="bar",
            title="Completion Rate KPI",
            metric_ids=["KPI-002"],
            proof_ids=["PROOF-020"],
            query_id="Q-2",
            y_fields=["rate"],
            format="percent",
            data=[{"period": "Mar", "period_label": "March 2026", "rate": 0.8}],
        )
        self.assertTrue(spec["mobile_tap_enabled"])
        html = render_interactive_chart(spec)
        self.assertIn('data-mobile-tap="true"', html)

    def test_11_accessible_chart_name(self) -> None:
        spec = build_chart_spec(
            chart_id="a11y",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI Trend",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            accessible_name="Volume KPI Trend",
            data=[{"period": "Mar", "period_label": "March 2026", "volume": 10}],
        )
        self.assertEqual(spec["accessible_name"], "Volume KPI Trend")
        html = render_interactive_chart(spec)
        self.assertIn('aria-label="Volume KPI Trend"', html)

    def test_12_equivalent_data_table(self) -> None:
        spec = build_chart_spec(
            chart_id="table_eq",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            data=[{"period": "Mar", "period_label": "March 2026", "volume": 10}],
        )
        html = render_interactive_chart(spec)
        self.assertIn("chart-data-table", html)
        self.assertIn("March 2026", html)

    def test_13_static_matplotlib_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "volume_trend.png"
            spec = build_chart_spec(
                chart_id="volume_trend",
                page_id="executive_overview",
                chart_type="line",
                title="Volume KPI Trend",
                metric_ids=["KPI-001"],
                proof_ids=["PROOF-010"],
                query_id="Q-1",
                y_fields=["volume"],
                format="integer",
                data=[
                    {"period": "Jan", "period_label": "January", "volume": 90},
                    {"period": "Mar", "period_label": "March", "volume": 100},
                ],
            )
            path = export_static_image(spec, out)
            self.assertIsNotNone(path)
            self.assertTrue(out.exists())
            self.assertTrue(out.with_suffix(".pdf").exists())

    def test_14_offline_interactive_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dest = ensure_offline_plotly_vendor(Path(tmp))
            self.assertIsNotNone(dest)
            self.assertTrue(dest.exists())
            self.assertGreater(dest.stat().st_size, 10)

    def test_15_duplicate_chart_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed(root)
            registry_path = matplotlib / "chart_registry.json"
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            data["charts"].append(dict(data["charts"][0]))
            registry_path.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("validate_chart_registry.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("duplicate chart_id", (proc.stdout + proc.stderr).lower())

    def test_16_chart_without_tooltip_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed(root)
            registry_path = matplotlib / "chart_registry.json"
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            data["charts"][0]["hover_fields"] = []
            data["charts"][0]["tooltip_template"] = None
            registry_path.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("validate_chart_registry.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            out = (proc.stdout + proc.stderr).lower()
            self.assertTrue("tooltip" in out or "hover_fields" in out)

    def test_17_chart_without_proof_mapping_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed(root)
            registry_path = matplotlib / "chart_registry.json"
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            data["charts"][0]["proof_ids"] = []
            registry_path.write_text(json.dumps(data), encoding="utf-8")
            proc = run_script("validate_chart_registry.py", "--root", str(root))
            self.assertEqual(proc.returncode, 1)
            self.assertIn("proof", (proc.stdout + proc.stderr).lower())

    def test_18_pending_kpi_labelled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed(root)
            manifest = json.loads(
                (matplotlib / "rendered_metric_manifest.json").read_text(encoding="utf-8")
            )
            pending = [
                m
                for m in manifest["metrics"]
                if str(m.get("business_approval_status", "")).upper() == "PENDING"
            ]
            self.assertTrue(pending)
            for metric in pending:
                blob = f"{metric.get('formatted_value')} {metric.get('pending_label')}".lower()
                self.assertIn("pending", blob)

    def test_19_technical_ids_hidden_from_visible_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed(root)
            registry = json.loads((matplotlib / "chart_registry.json").read_text(encoding="utf-8"))
            for chart in registry["charts"]:
                for key in ("title", "display_name", "accessible_name"):
                    label = str(chart.get(key) or "")
                    self.assertFalse(label.startswith("model."), label)
                    self.assertNotRegex(label, r"^[a-z]+_[a-z0-9_]+$")

    def test_20_domain_neutrality_scan_passes(self) -> None:
        proc = run_script("check_domain_neutrality.py", "--root", str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_21_fixture_hooks_and_validator_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matplotlib = _seed(root)
            html = (matplotlib / "report.html").read_text(encoding="utf-8")
            for hook in (
                "__REPORT_READY__",
                "__REPORT_CHART_REGISTRY__",
                "__REPORT_METRIC_MANIFEST__",
                "__REPORT_DATA_VERSION__",
                "__REPORT_REFRESH_STATUS__",
            ):
                self.assertIn(hook, html)
            self.assertTrue((matplotlib / "vendor" / "plotly.min.js").exists())
            self.assertTrue((matplotlib / "static" / "volume_trend.png").exists())
            proc = run_script("validate_chart_registry.py", "--root", str(root))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_22_plotly_path_when_available(self) -> None:
        if not plotly_available():
            self.skipTest("plotly not installed")
        spec = build_chart_spec(
            chart_id="plotly_line",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI Trend",
            metric_ids=["KPI-001"],
            proof_ids=["PROOF-010"],
            query_id="Q-1",
            y_fields=["volume"],
            format="integer",
            data=[{"period": "Mar", "period_label": "March 2026", "volume": 5986}],
        )
        html = render_interactive_chart(spec, mode="interactive_html", include_plotlyjs=False)
        self.assertIn("plotly", html.lower())
        self.assertIn("Volume KPI", html)


if __name__ == "__main__":
    unittest.main()
