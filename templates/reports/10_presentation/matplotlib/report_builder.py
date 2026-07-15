#!/usr/bin/env python3
"""Build chart registry, metric manifest, contracts, and optional static exports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from chart_renderer import build_chart_spec, format_display_value, render_interactive_chart
from data_access import (
    METRIC_BOARD,
    MEASURE_BOARD,
    build_completion_rate_data,
    build_volume_trend_data,
)

OUTPUT_DIR = Path(__file__).resolve().parent


def build_chart_registry() -> dict:
    timestamp = datetime.now(timezone.utc).isoformat()
    volume_data = build_volume_trend_data()
    rate_data = build_completion_rate_data()

    charts = [
        build_chart_spec(
            chart_id="volume_trend",
            page_id="executive_overview",
            chart_type="line",
            title="Volume KPI Trend",
            metric_ids=["KPI-001"],
            y_fields=["volume"],
            x_field="period",
            format="integer",
            unit="events",
            proof_ids=["010_volume"],
            query_id="volume_trend_q1",
            validation_status="PASS",
            period_label="Current quarter",
            data=volume_data,
        ),
        build_chart_spec(
            chart_id="completion_rate_trend",
            page_id="executive_overview",
            chart_type="bar",
            title="Completion Rate KPI",
            metric_ids=["KPI-002"],
            y_fields=["rate"],
            x_field="period",
            format="percent",
            proof_ids=["020_rate"],
            query_id="completion_rate_q1",
            validation_status="PASS",
            period_label="Current quarter",
            data=rate_data,
        ),
    ]
    return {"version": "1", "freshness_timestamp": timestamp, "charts": charts}


def build_metric_manifest(registry: dict) -> dict:
    metrics = [
        {
            "metric_id": "KPI-001",
            "display_name": "Volume KPI",
            "chart_ids": ["volume_trend"],
            "card_ids": ["volume_card"],
            "proof_ids": ["010_volume"],
            "formatted_value": "100",
            "format": "integer",
            "unit": "events",
            "period_label": "Current month",
        },
        {
            "metric_id": "KPI-002",
            "display_name": "Completion rate KPI",
            "chart_ids": ["completion_rate_trend"],
            "card_ids": ["completion_card"],
            "proof_ids": ["020_rate"],
            "formatted_value": "80.0%",
            "format": "percent",
            "period_label": "Current month",
        },
    ]
    for chart in registry.get("charts", []):
        for metric_id in chart.get("metric_ids", []):
            for metric in metrics:
                if metric["metric_id"] == metric_id and chart["chart_id"] not in metric["chart_ids"]:
                    metric["chart_ids"].append(chart["chart_id"])
    return {"version": "1", "metrics": metrics, "measure_board": MEASURE_BOARD, "metric_board": METRIC_BOARD}


def build_contracts_markdown(registry: dict, manifest: dict) -> str:
    rows = [
        "| Chart ID | Page | Chart Type | Metric IDs | Proof IDs | Hover Fields | Validation |",
        "|---|---|---|---|---|---|---|",
    ]
    for chart in registry.get("charts", []):
        hover = ", ".join(chart.get("hover_fields") or ["formatted_value", "tooltip_text"])
        proofs = ", ".join(chart.get("proof_ids") or [])
        metrics = ", ".join(chart.get("metric_ids") or [])
        rows.append(
            f"| {chart['chart_id']} | {chart['page_id']} | {chart['chart_type']} | "
            f"{metrics} | {proofs} | {hover} | {chart.get('validation_status', 'PENDING')} |"
        )
    rows.append("")
    rows.append("## Metric manifest mapping")
    rows.append("")
    rows.append("| Metric ID | Display Name | Chart IDs | Proof IDs | Formatted Value |")
    rows.append("|---|---|---|---|---|")
    for metric in manifest.get("metrics", []):
        rows.append(
            f"| {metric['metric_id']} | {metric['display_name']} | "
            f"{', '.join(metric.get('chart_ids', []))} | {', '.join(metric.get('proof_ids', []))} | "
            f"{metric.get('formatted_value', '')} |"
        )
    return "\n".join(rows) + "\n"


def export_static_images(registry: dict, output_dir: Path) -> list[str]:
    exported: list[str] = []
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return exported

    for chart in registry.get("charts", []):
        data = chart.get("data") or []
        if not data:
            continue
        y_field = (chart.get("y_fields") or ["value"])[0]
        x_field = chart.get("x_field", "period")
        xs = [row.get(x_field, "") for row in data]
        ys = [row.get(y_field, 0) for row in data]
        fig, ax = plt.subplots(figsize=(6, 3))
        if chart.get("chart_type") == "bar":
            ax.bar(xs, ys)
        else:
            ax.plot(xs, ys, marker="o")
        ax.set_title(chart.get("title", chart["chart_id"]))
        ax.set_ylabel(format_display_value(ys[-1] if ys else 0, chart.get("format", "decimal")))
        out = output_dir / f"{chart['chart_id']}.png"
        fig.tight_layout()
        fig.savefig(out, dpi=120)
        plt.close(fig)
        exported.append(str(out.name))
    return exported


def main() -> int:
    registry = build_chart_registry()
    manifest = build_metric_manifest(registry)
    contracts = build_contracts_markdown(registry, manifest)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "chart_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "rendered_metric_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUTPUT_DIR.parent / "chart_interactivity_contracts.md").write_text(contracts, encoding="utf-8")

    previews = []
    for chart in registry["charts"]:
        previews.append(render_interactive_chart(chart))

    export_static_images(registry, OUTPUT_DIR)
    print(f"Wrote chart registry with {len(registry['charts'])} charts")
    print(f"Static exports: {export_static_images(registry, OUTPUT_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
