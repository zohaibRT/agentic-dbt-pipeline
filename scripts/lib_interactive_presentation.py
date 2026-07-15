"""Generate interactive presentation artifacts for test fixtures.

Writes stable-ID registries under reports/agent/10_presentation/ and mirrors
chart/manifest files into matplotlib/ for existing validators.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "reports" / "10_presentation" / "matplotlib"
SCRIPTS = ROOT / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lib_chart_renderer import (  # noqa: E402
    build_chart_spec,
    ensure_offline_plotly_vendor,
    export_static_image,
)


def _volume_data(volume_total: int, *, freshness: str | None = None) -> list[dict]:
    """Volume series with an intentional missing middle period (no interpolation)."""
    points = [
        ("Jan", "2026-01-01", "January 2026", max(volume_total - 10, 0), False, False),
        ("Feb", "2026-02-01", "February 2026", None, True, False),  # missing — not interpolated
        ("Mar", "2026-03-01", "March 2026", volume_total, False, True),  # partial current period
    ]
    rows = []
    for period, full_date, period_label, volume, missing, partial in points:
        row = {
            "period": period,
            "full_date": full_date,
            "period_label": period_label,
            "volume": volume,
            "missing_period": missing,
            "is_partial_period": partial,
            "metric_display_name": "Volume KPI",
            "series_display_name": "Actual",
            "unit": "events",
            "status_label": "On track",
            "freshness_timestamp": freshness,
        }
        if partial:
            row["partial_period_note"] = "Partial period — incomplete"
        if missing:
            row["formatted_value"] = "—"
            row["tooltip_text"] = (
                f"Volume KPI — Actual\n{period_label}\n—\nMissing period — value not interpolated"
            )
        rows.append(row)
    return rows


def _rate_data(rate: float, *, freshness: str | None = None) -> list[dict]:
    points = [
        ("Jan", "2026-01-01", "January 2026", max(rate - 0.05, 0), False),
        ("Feb", "2026-02-01", "February 2026", max(rate - 0.02, 0), False),
        ("Mar", "2026-03-01", "March 2026", rate, True),
    ]
    rows = []
    for period, full_date, period_label, value, partial in points:
        row = {
            "period": period,
            "full_date": full_date,
            "period_label": period_label,
            "rate": value,
            "is_partial_period": partial,
            "metric_display_name": "Completion rate KPI",
            "series_display_name": "Actual",
            "freshness_timestamp": freshness,
        }
        if partial:
            row["partial_period_note"] = "Partial period — incomplete"
        rows.append(row)
    return rows


def _currency_data(amount: float, *, freshness: str | None = None) -> list[dict]:
    points = [
        ("Jan", "2026-01-01", "January 2026", amount * 0.9, False),
        ("Feb", "2026-02-01", "February 2026", amount * 0.95, False),
        ("Mar", "2026-03-01", "March 2026", amount, True),
    ]
    rows = []
    for period, full_date, period_label, value, partial in points:
        row = {
            "period": period,
            "full_date": full_date,
            "period_label": period_label,
            "amount": value,
            "is_partial_period": partial,
            "metric_display_name": "Value amount KPI",
            "series_display_name": "Actual",
            "currency": "SAR",
            "freshness_timestamp": freshness,
        }
        if partial:
            row["partial_period_note"] = "Partial period — incomplete"
        rows.append(row)
    return rows


def _prior_series_data(volume_total: int, *, freshness: str | None = None) -> list[dict]:
    """Prior-year companion series for multi-line tooltips."""
    points = [
        ("Jan", "2026-01-01", "January 2026", max(volume_total - 20, 0)),
        ("Feb", "2026-02-01", "February 2026", max(volume_total - 15, 0)),
        ("Mar", "2026-03-01", "March 2026", max(volume_total - 8, 0)),
    ]
    rows = []
    for period, full_date, period_label, volume in points:
        rows.append(
            {
                "period": period,
                "full_date": full_date,
                "period_label": period_label,
                "volume": volume,
                "metric_display_name": "Volume KPI",
                "series_display_name": "Prior period",
                "unit": "events",
                "freshness_timestamp": freshness,
            }
        )
    return rows


def build_page_registry() -> dict:
    return {
        "version": "1",
        "pages": [
            {
                "page_id": "executive_overview",
                "page_name": "Executive Overview",
                "page_class": "executive_overview",
                "audience": "leadership",
                "trusted": True,
                "primary_kpi_ids": ["KPI-001", "KPI-002"],
                "driver_metric_ids": ["KPI-002"],
                "guardrail_metric_ids": [],
                "visual_ids": ["visual_volume_trend", "visual_completion_rate_trend", "card_volume", "card_completion"],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "page_id": "exceptions_and_data_quality",
                "page_name": "Exceptions and Data Quality",
                "page_class": "exceptions_quality",
                "audience": "data engineering",
                "trusted": True,
                "primary_kpi_ids": ["DQ-001"],
                "visual_ids": [],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "page_id": "pipeline_health",
                "page_name": "Pipeline Health",
                "page_class": "pipeline_health",
                "audience": "platform",
                "trusted": True,
                "primary_kpi_ids": ["PIPE-001"],
                "visual_ids": [],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "page_id": "all_measures",
                "page_name": "All Measures",
                "page_class": "metric_dictionary",
                "audience": "analysts",
                "trusted": False,
                "visual_ids": [],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "page_id": "all_metrics",
                "page_name": "All Metrics",
                "page_class": "metric_dictionary",
                "audience": "analysts",
                "trusted": False,
                "visual_ids": [],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "page_id": "all_dimensions",
                "page_name": "Dimensions",
                "page_class": "dimension_explorer",
                "audience": "analysts",
                "trusted": False,
                "visual_ids": [],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
        ],
    }


def build_chart_registry(
    volume_total: int,
    completion_rate: float,
    *,
    source_resource_id: str = "model.local.fct_events",
) -> dict:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    volume_rows = _volume_data(volume_total, freshness=timestamp)
    prior_rows = _prior_series_data(volume_total, freshness=timestamp)
    rate_rows = _rate_data(completion_rate, freshness=timestamp)

    volume_chart = build_chart_spec(
        chart_id="volume_trend",
        visual_id="visual_volume_trend",
        visual_type="line_chart",
        page_id="executive_overview",
        chart_type="line",
        title="Volume KPI Trend",
        subtitle="Exact hover values; gaps are not interpolated",
        business_question="How is validated volume changing over time?",
        metric_ids=["KPI-001"],
        series=[
            {"name": "actual", "display_name": "Actual", "y_field": "volume", "data": volume_rows},
            {"name": "prior", "display_name": "Prior period", "y_field": "volume", "data": prior_rows},
        ],
        x_field="period",
        y_fields=["volume"],
        date_role="event_date",
        date_grain="month",
        dimensions=[],
        filters=[],
        format="integer",
        unit="events",
        precision=0,
        aggregation_behavior="sum_additive",
        proof_ids=["PROOF-010_volume"],
        query_id="Q-volume_trend",
        source_resource_ids=[source_resource_id],
        freshness_timestamp=timestamp,
        partial_period_behavior="label_and_include",
        empty_state_behavior="show_empty_message",
        validation_status="PASS",
        technical_validation_status="PASS",
        business_approval_status="APPROVED",
        period_label="Current quarter",
        accessible_name="Volume KPI Trend",
        accessible_description="Line chart of volume KPI by month with prior-period comparison",
        mobile_tap_enabled=True,
        hover_mode="x unified",
        connect_missing=False,
        data=volume_rows,
        metric_display_name="Volume KPI",
        series_display_name="Actual",
    )

    rate_chart = build_chart_spec(
        chart_id="completion_rate_trend",
        visual_id="visual_completion_rate_trend",
        visual_type="bar_chart",
        page_id="executive_overview",
        chart_type="bar",
        title="Completion Rate KPI",
        subtitle="Percentage formatted to contract precision",
        business_question="What share of work completed in each period?",
        metric_ids=["KPI-002"],
        series=[{"name": "actual", "display_name": "Actual", "y_field": "rate"}],
        x_field="period",
        y_fields=["rate"],
        date_role="event_date",
        date_grain="month",
        format="percent",
        precision=2,
        aggregation_behavior="ratio_non_additive",
        proof_ids=["PROOF-020_rate"],
        query_id="Q-completion_rate",
        source_resource_ids=[source_resource_id],
        freshness_timestamp=timestamp,
        validation_status="PASS",
        technical_validation_status="PASS",
        business_approval_status="APPROVED",
        period_label="Current quarter",
        accessible_name="Completion Rate KPI",
        accessible_description="Bar chart of completion rate by month",
        mobile_tap_enabled=True,
        data=rate_rows,
        metric_display_name="Completion rate KPI",
    )

    # Pre-render offline interactive HTML (SVG path keeps fixture JSON portable).
    # Plotly remains available via chart_renderer for projects that prefer it.
    from lib_chart_renderer import _render_svg_chart, plotly_available

    for chart in (volume_chart, rate_chart):
        chart["interactive_html"] = _render_svg_chart(chart, list(chart.get("data") or []))
        chart["renderer"] = "svg"
        chart["plotly_available"] = plotly_available()
        chart["accessible_data_table"] = True
        chart["mobile_tap_enabled"] = True

    return {
        "version": "1",
        "freshness_timestamp": timestamp,
        "data_version": timestamp,
        "charts": [volume_chart, rate_chart],
        "cards": [
            {
                "card_id": "volume_card",
                "visual_id": "card_volume",
                "visual_type": "kpi_card",
                "page_id": "executive_overview",
                "metric_ids": ["KPI-001"],
                "display_name": "Volume KPI",
                "proof_ids": ["PROOF-010_volume"],
                "query_id": "Q-volume_card",
                "source_resource_ids": [source_resource_id],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "card_id": "completion_card",
                "visual_id": "card_completion",
                "visual_type": "kpi_card",
                "page_id": "executive_overview",
                "metric_ids": ["KPI-002"],
                "display_name": "Completion rate KPI",
                "proof_ids": ["PROOF-020_rate"],
                "query_id": "Q-completion_card",
                "source_resource_ids": [source_resource_id],
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
        ],
    }


def build_query_registry(*, source_resource_id: str = "model.local.fct_events") -> dict:
    return {
        "version": "1",
        "queries": [
            {
                "query_id": "Q-volume_trend",
                "metric_ids": ["KPI-001"],
                "source_resource_ids": [source_resource_id],
                "sql_path": "reports/agent/10_presentation/matplotlib/sql_verification/010_volume.sql",
                "description": "Volume trend query",
            },
            {
                "query_id": "Q-completion_rate",
                "metric_ids": ["KPI-002"],
                "source_resource_ids": [source_resource_id],
                "sql_path": "reports/agent/10_presentation/matplotlib/sql_verification/020_rate.sql",
                "description": "Completion rate trend query",
            },
            {
                "query_id": "Q-volume_card",
                "metric_ids": ["KPI-001"],
                "source_resource_ids": [source_resource_id],
                "sql_path": "reports/agent/10_presentation/matplotlib/sql_verification/010_volume.sql",
                "description": "Volume card query",
            },
            {
                "query_id": "Q-completion_card",
                "metric_ids": ["KPI-002"],
                "source_resource_ids": [source_resource_id],
                "sql_path": "reports/agent/10_presentation/matplotlib/sql_verification/020_rate.sql",
                "description": "Completion card query",
            },
        ],
    }


def build_proof_registry(
    volume_total: int,
    completion_rate: float,
    *,
    source_resource_id: str = "model.local.fct_events",
) -> dict:
    return {
        "version": "1",
        "proofs": [
            {
                "proof_id": "PROOF-010_volume",
                "metric_id": "KPI-001",
                "kpi_id": "KPI-001",
                "page_id": "executive_overview",
                "visual_ids": ["visual_volume_trend", "card_volume"],
                "query_id": "Q-volume_trend",
                "proof_path": "reports/agent/10_presentation/matplotlib/sql_verification/010_volume.sql",
                "source_resource_ids": [source_resource_id],
                "captured_value": str(volume_total),
                "displayed_value": f"{volume_total:,}",
                "formatting_rule": "integer",
                "proof_status": "PASS",
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "proof_id": "PROOF-020_rate",
                "metric_id": "KPI-002",
                "kpi_id": "KPI-002",
                "page_id": "executive_overview",
                "visual_ids": ["visual_completion_rate_trend", "card_completion"],
                "query_id": "Q-completion_rate",
                "proof_path": "reports/agent/10_presentation/matplotlib/sql_verification/020_rate.sql",
                "source_resource_ids": [source_resource_id],
                "captured_value": str(completion_rate),
                "displayed_value": f"{completion_rate * 100:.1f}%",
                "formatting_rule": "percent",
                "proof_status": "PASS",
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "proof_id": "PROOF-030_dq",
                "metric_id": "DQ-001",
                "kpi_id": "DQ-001",
                "page_id": "exceptions_and_data_quality",
                "visual_ids": [],
                "query_id": "Q-dq_orphan",
                "proof_path": "reports/agent/10_presentation/matplotlib/sql_verification/030_dq.sql",
                "source_resource_ids": [source_resource_id],
                "captured_value": "0.0",
                "displayed_value": "0.0%",
                "formatting_rule": "percent",
                "proof_status": "PASS",
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
        ],
    }


def build_metric_manifest(
    volume_total: int,
    completion_rate: float,
    *,
    freshness_timestamp: str,
    source_resource_id: str = "model.local.fct_events",
) -> dict:
    return {
        "version": "1",
        "freshness_timestamp": freshness_timestamp,
        "metrics": [
            {
                "metric_id": "KPI-001",
                "kpi_id": "KPI-001",
                "display_name": "Volume KPI",
                "page_ids": ["executive_overview"],
                "visual_ids": ["visual_volume_trend", "card_volume"],
                "chart_ids": ["volume_trend"],
                "card_ids": ["volume_card"],
                "table_ids": [],
                "query_ids": ["Q-volume_trend", "Q-volume_card"],
                "proof_ids": ["PROOF-010_volume"],
                "source_resource_ids": [source_resource_id],
                "source_resource_unique_id": source_resource_id,
                "catalog_refs": ["business_measure_catalog:event_count"],
                "time_intelligence_refs": ["KPI-001"],
                "dom_item_ids": ["card_volume", "chart_volume_trend"],
                "captured_value": str(volume_total),
                "displayed_value": f"{volume_total:,}",
                "formatted_value": f"{volume_total:,}",
                "formatting_rule": "integer",
                "format": "integer",
                "unit": "events",
                "period_label": "Current month",
                "refresh_timestamp": freshness_timestamp,
                "trust_level": "TRUSTED",
                "validation_status": "PASS",
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "metric_id": "KPI-002",
                "kpi_id": "KPI-002",
                "display_name": "Completion rate KPI",
                "page_ids": ["executive_overview"],
                "visual_ids": ["visual_completion_rate_trend", "card_completion"],
                "chart_ids": ["completion_rate_trend"],
                "card_ids": ["completion_card"],
                "table_ids": [],
                "query_ids": ["Q-completion_rate", "Q-completion_card"],
                "proof_ids": ["PROOF-020_rate"],
                "source_resource_ids": [source_resource_id],
                "source_resource_unique_id": source_resource_id,
                "catalog_refs": ["business_metric_catalog:completion_rate"],
                "time_intelligence_refs": ["KPI-002"],
                "dom_item_ids": ["card_completion", "chart_completion_rate_trend"],
                "captured_value": str(completion_rate),
                "displayed_value": f"{completion_rate * 100:.1f}%",
                "formatted_value": f"{completion_rate * 100:.1f}%",
                "formatting_rule": "percent",
                "format": "percent",
                "period_label": "Current month",
                "refresh_timestamp": freshness_timestamp,
                "trust_level": "TRUSTED",
                "validation_status": "PASS",
                "technical_validation_status": "PASS",
                "business_approval_status": "APPROVED",
            },
            {
                "metric_id": "KPI-PENDING-001",
                "kpi_id": "KPI-PENDING-001",
                "display_name": "Draft exploratory metric",
                "page_ids": ["all_metrics"],
                "visual_ids": [],
                "chart_ids": [],
                "card_ids": [],
                "table_ids": [],
                "query_ids": [],
                "proof_ids": [],
                "source_resource_ids": [source_resource_id],
                "source_resource_unique_id": source_resource_id,
                "catalog_refs": [],
                "time_intelligence_refs": [],
                "dom_item_ids": [],
                "captured_value": None,
                "displayed_value": "Pending",
                "formatted_value": "Pending",
                "formatting_rule": "decimal",
                "format": "decimal",
                "period_label": "Not approved",
                "refresh_timestamp": freshness_timestamp,
                "trust_level": "DRAFT",
                "validation_status": "PENDING",
                "technical_validation_status": "PENDING",
                "business_approval_status": "PENDING",
                "pending_label": "Pending approval",
            },
        ],
        "measure_board": [
            {
                "id": "event_count",
                "display_name": "Event count",
                "value": volume_total,
                "formatted_value": f"{volume_total:,}",
                "group": "Volume",
                "format": "integer",
                "unit": "events",
            }
        ],
        "metric_board": [
            {
                "id": "completion_rate",
                "display_name": "Completion rate",
                "value": completion_rate,
                "formatted_value": f"{completion_rate * 100:.1f}%",
                "group": "Performance",
                "format": "percent",
            },
            {
                "id": "draft_exploratory",
                "display_name": "Draft exploratory metric",
                "value": None,
                "formatted_value": "Pending",
                "group": "Draft",
                "format": "decimal",
                "business_approval_status": "PENDING",
            },
        ],
    }


def build_contracts_markdown(registry: dict, manifest: dict) -> str:
    rows = [
        "# Chart Interactivity Contracts (TEST FIXTURE)",
        "",
        "| Chart ID | Visual ID | Page | Chart Type | Metric IDs | Proof IDs | Hover Fields | Validation |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for chart in registry.get("charts", []):
        hover = ", ".join(chart.get("hover_fields") or [])
        rows.append(
            f"| {chart['chart_id']} | {chart.get('visual_id', '')} | {chart['page_id']} | {chart['chart_type']} | "
            f"{', '.join(chart.get('metric_ids', []))} | {', '.join(chart.get('proof_ids', []))} | "
            f"{hover} | {chart.get('validation_status', 'PENDING')} |"
        )
    rows.extend(
        [
            "",
            "## Metric manifest mapping",
            "",
            "| Metric ID | Display Name | Visual IDs | Proof IDs | Formatted Value | Trust | Business Approval |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for metric in manifest.get("metrics", []):
        rows.append(
            f"| {metric['metric_id']} | {metric['display_name']} | "
            f"{', '.join(metric.get('visual_ids', []))} | {', '.join(metric.get('proof_ids', []))} | "
            f"{metric.get('formatted_value', '')} | {metric.get('trust_level', '')} | "
            f"{metric.get('business_approval_status', '')} |"
        )
    return "\n".join(rows) + "\n"


def write_interactive_presentation(
    matplotlib: Path,
    *,
    volume_total: int,
    completion_rate: float,
    source_resource_id: str = "model.local.fct_events",
) -> None:
    """Write interactive presentation files and stable-ID registries."""
    matplotlib.mkdir(parents=True, exist_ok=True)
    presentation = matplotlib.parent
    static_dir = matplotlib / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    freshness = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    page_registry = build_page_registry()
    chart_registry = build_chart_registry(
        volume_total, completion_rate, source_resource_id=source_resource_id
    )
    query_registry = build_query_registry(source_resource_id=source_resource_id)
    proof_registry = build_proof_registry(
        volume_total, completion_rate, source_resource_id=source_resource_id
    )
    manifest = build_metric_manifest(
        volume_total,
        completion_rate,
        freshness_timestamp=freshness,
        source_resource_id=source_resource_id,
    )
    contracts = build_contracts_markdown(chart_registry, manifest)

    # Offline Plotly vendor (or SVG-fallback marker)
    vendor_js = ensure_offline_plotly_vendor(matplotlib)

    # Static Matplotlib PNG/PDF fallbacks for every chart
    for chart in chart_registry.get("charts") or []:
        png = export_static_image(chart, static_dir / f"{chart['chart_id']}.png")
        if png is not None:
            chart["static_fallback_path"] = f"static/{png.name}"
            chart["static_fallback_exists"] = True
            chart["static_pdf_path"] = f"static/{png.with_suffix('.pdf').name}"
        else:
            chart["static_fallback_path"] = f"static/{chart['chart_id']}.png"
            chart["static_fallback_exists"] = False
        chart["offline_dependency"] = "vendor/plotly.min.js"
        chart["offline_dependency_exists"] = bool(vendor_js and vendor_js.exists())

    # Canonical registries at presentation root
    for name, payload in (
        ("page_registry.json", page_registry),
        ("chart_registry.json", chart_registry),
        ("query_registry.json", query_registry),
        ("proof_registry.json", proof_registry),
        ("rendered_metric_manifest.json", manifest),
    ):
        (presentation / name).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Mirror chart + manifest for matplotlib-scoped validators
    (matplotlib / "chart_registry.json").write_text(
        json.dumps(chart_registry, indent=2, default=str), encoding="utf-8"
    )
    (matplotlib / "rendered_metric_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
    (presentation / "chart_interactivity_contracts.md").write_text(contracts, encoding="utf-8")

    # Self-contained renderer beside the report (no Plotly calls in business pages)
    shutil.copy2(SCRIPTS / "lib_chart_renderer.py", matplotlib / "chart_renderer.py")
    for name in ("report.html", "serve_report.py", "data_access.py", "report_builder.py"):
        src = TEMPLATES / name
        if src.exists():
            shutil.copy2(src, matplotlib / name)

    data_access = matplotlib / "data_access.py"
    data_access.write_text(
        f'''"""TEST FIXTURE ONLY — board payloads with display names and formatted values."""
MEASURE_BOARD = {json.dumps(manifest["measure_board"], indent=4)}
METRIC_BOARD = {json.dumps(manifest["metric_board"], indent=4)}

def format_value(value, fmt):
    if fmt == "percent":
        return f"{{value * 100:.1f}}%"
    if fmt == "integer":
        return f"{{int(value):,}}"
    return str(value)
''',
        encoding="utf-8",
    )

    report_builder = matplotlib / "report_builder.py"
    report_builder.write_text(
        '''# TEST FIXTURE ONLY
TABS = ["Executive Overview", "Exceptions and Data Quality", "Pipeline Health", "All Measures", "All Metrics", "Dimensions"]
PAGE_IDS = ["executive_overview", "exceptions_and_data_quality", "pipeline_health", "all_measures", "all_metrics", "all_dimensions"]
RENDER_MODE = "interactive_html"
STATIC_EXPORT_MODE = "static_image"
''',
        encoding="utf-8",
    )

    report_html = matplotlib / "report.html"
    if report_html.exists():
        html = report_html.read_text(encoding="utf-8")
        slim_charts = []
        for c in chart_registry.get("charts") or []:
            slim_charts.append(
                {
                    key: c.get(key)
                    for key in (
                        "chart_id",
                        "page_id",
                        "chart_type",
                        "title",
                        "metric_ids",
                        "query_id",
                        "validation_status",
                        "business_approval_status",
                        "accessible_name",
                        "accessible_description",
                        "data",
                        "hover_fields",
                        "tooltip_template",
                        "static_fallback_path",
                        "proof_ids",
                        "format",
                        "unit",
                        "currency",
                        "series",
                        "x_field",
                        "y_fields",
                        "period_label",
                        "mobile_tap_enabled",
                        "interactive_html",
                    )
                }
            )
        injection = (
            "<script>\n"
            f"window.MEASURE_BOARD = {json.dumps(manifest['measure_board'])};\n"
            f"window.METRIC_BOARD = {json.dumps(manifest['metric_board'])};\n"
            f"window.PAGE_REGISTRY = {json.dumps(page_registry)};\n"
            f"window.RENDERED_METRIC_MANIFEST = {json.dumps({'metrics': manifest['metrics']}, default=str)};\n"
            "window.__REPORT_METRIC_MANIFEST__ = window.RENDERED_METRIC_MANIFEST;\n"
            f"window.__REPORT_CHART_REGISTRY__ = {json.dumps({'version': chart_registry.get('version'), 'freshness_timestamp': chart_registry.get('freshness_timestamp'), 'charts': slim_charts}, default=str)};\n"
            f"window.__REPORT_DATA_VERSION__ = {json.dumps(chart_registry.get('data_version') or freshness)};\n"
            "window.__REPORT_REFRESH_STATUS__ = 'bootstrapping';\n"
            "</script>\n"
        )
        marker = "<!-- FIXTURE_REPORT_HOOKS -->"
        if marker in html:
            # Replace existing hooks block
            start = html.index(marker)
            end = html.index("</script>", start) + len("</script>")
            html = html[:start] + marker + "\n" + injection + html[end:]
        else:
            html = html.replace("</body>", f"{marker}\n{injection}</body>")
        report_html.write_text(html, encoding="utf-8")
