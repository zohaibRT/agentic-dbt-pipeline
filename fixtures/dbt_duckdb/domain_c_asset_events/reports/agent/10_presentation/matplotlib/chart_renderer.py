#!/usr/bin/env python3
"""Domain-neutral chart renderer: ChartSpec + Plotly interactive + Matplotlib static.

Business-page code should call build_chart_spec / render_* only — never Plotly APIs directly.
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

RENDER_MODE = "auto"  # auto | interactive_html | static_image
VALID_RENDER_MODES = frozenset({"auto", "interactive_html", "static_image"})

VALID_CHART_TYPES = frozenset(
    {
        "line",
        "multi_line",
        "bar",
        "grouped_bar",
        "stacked_bar",
        "area",
        "scatter",
        "histogram",
        "box",
        "heatmap",
        "funnel",
        "table",
        "kpi_card",
    }
)

CHARTSPEC_FIELDS = (
    "chart_id",
    "page_id",
    "chart_type",
    "title",
    "subtitle",
    "business_question",
    "metric_ids",
    "series",
    "x_field",
    "y_fields",
    "date_role",
    "date_grain",
    "dimensions",
    "filters",
    "unit",
    "currency",
    "precision",
    "aggregation_behavior",
    "hover_fields",
    "tooltip_template",
    "query_id",
    "proof_ids",
    "source_resource_ids",
    "freshness_timestamp",
    "partial_period_behavior",
    "empty_state_behavior",
    "validation_status",
    "business_approval_status",
)

DEFAULT_HOVER_FIELDS = [
    "metric_display_name",
    "series_display_name",
    "period_label",
    "formatted_value",
    "unit",
    "currency",
    "prior_formatted_value",
    "abs_change_formatted",
    "pct_change_formatted",
    "target_formatted",
    "target_variance_formatted",
    "status_label",
    "partial_period_note",
    "freshness_timestamp",
    "metric_definition_link",
]

DEFAULT_TOOLTIP_TEMPLATE = (
    "{metric_display_name}"
    "{series_suffix}"
    "\n{period_label}"
    "\n{formatted_value}"
    "{prior_block}"
    "{change_block}"
    "{target_block}"
    "{status_block}"
    "{partial_block}"
    "{freshness_block}"
)


def format_display_value(
    value: float | int | str | None,
    fmt: str,
    *,
    unit: str | None = None,
    currency: str | None = None,
    precision: int | None = None,
) -> str:
    """Format for display only — never mutate the underlying numeric value."""
    if value is None:
        return "—"
    if isinstance(value, str):
        return value

    number = float(value)
    fmt_l = (fmt or "decimal").lower()

    if fmt_l == "percent":
        digits = precision if precision is not None else 2
        text = f"{number * 100:.{digits}f}%"
    elif fmt_l == "currency":
        digits = precision if precision is not None else 2
        symbol = (currency or "").strip()
        body = f"{number:,.{digits}f}"
        # ISO currency codes (e.g. SAR, USD) keep a space; symbols (e.g. $, €) do not.
        if symbol and len(symbol) >= 3 and symbol.replace(".", "").isalpha():
            text = f"{symbol} {body}"
        elif symbol:
            text = f"{symbol}{body}"
        else:
            text = body
    elif fmt_l == "integer":
        text = f"{int(round(number)):,}"
    elif fmt_l == "duration":
        total_minutes = int(round(number))
        hours, minutes = divmod(max(total_minutes, 0), 60)
        text = f"{hours}h {minutes}m"
    elif fmt_l == "decimal":
        digits = precision if precision is not None else 2
        text = f"{number:,.{digits}f}"
    else:
        text = str(value)

    if unit and fmt_l not in {"percent", "currency", "duration"}:
        return f"{text} {unit}"
    return text


def build_tooltip_text(row: dict[str, Any], spec: dict[str, Any] | None = None) -> str:
    """Compose an exact-value hover/tap string from row + ChartSpec metadata."""
    spec = spec or {}
    if row.get("tooltip_text"):
        return str(row["tooltip_text"])

    metric_name = row.get("metric_display_name") or spec.get("title") or "Metric"
    series_name = row.get("series_display_name") or row.get("series_name")
    period = row.get("period_label") or row.get(spec.get("x_field") or "period") or ""
    formatted = row.get("formatted_value")
    if formatted is None:
        y_field = (spec.get("y_fields") or ["value"])[0]
        formatted = format_display_value(
            row.get(y_field),
            str(spec.get("format") or row.get("format") or "decimal"),
            unit=spec.get("unit") or row.get("unit"),
            currency=spec.get("currency") or row.get("currency"),
            precision=spec.get("precision"),
        )

    lines = [str(metric_name)]
    if series_name:
        lines[0] = f"{metric_name} — {series_name}"
    if period:
        lines.append(str(period))
    lines.append(str(formatted))

    if row.get("prior_formatted_value"):
        lines.append(f"Previous: {row['prior_formatted_value']}")
    if row.get("abs_change_formatted"):
        change = str(row["abs_change_formatted"])
        if row.get("pct_change_formatted"):
            change = f"{change} ({row['pct_change_formatted']})"
        lines.append(f"Change: {change}")
    if row.get("target_formatted"):
        lines.append(f"Target: {row['target_formatted']}")
    if row.get("target_variance_formatted"):
        lines.append(f"Variance: {row['target_variance_formatted']}")
    if row.get("status_label"):
        lines.append(f"Status: {row['status_label']}")
    if row.get("partial_period_note") or row.get("is_partial_period"):
        note = row.get("partial_period_note") or "Partial period — incomplete"
        lines.append(str(note))
    if row.get("freshness_timestamp") or spec.get("freshness_timestamp"):
        lines.append(f"Fresh as of: {row.get('freshness_timestamp') or spec.get('freshness_timestamp')}")
    if row.get("metric_definition_link"):
        lines.append(f"Definition: {row['metric_definition_link']}")
    if row.get("missing_period"):
        lines.append("Missing period — value not interpolated")

    return "\n".join(lines)


def enrich_series_rows(
    rows: list[dict[str, Any]],
    *,
    y_field: str,
    fmt: str,
    unit: str | None = None,
    currency: str | None = None,
    precision: int | None = None,
    metric_display_name: str | None = None,
    series_display_name: str | None = None,
    freshness_timestamp: str | None = None,
    connect_missing: bool = False,
) -> list[dict[str, Any]]:
    """Attach formatted values, prior/change, and partial/missing markers.

    Missing periods keep null y values and are never filled when connect_missing is False.
    """
    enriched: list[dict[str, Any]] = []
    prev_raw: float | None = None
    for idx, raw in enumerate(rows):
        row = dict(raw)
        value = row.get(y_field)
        missing = value is None or row.get("missing_period") is True
        if missing and not connect_missing:
            row["missing_period"] = True
            row[y_field] = None
            row["formatted_value"] = "—"
        else:
            row["formatted_value"] = format_display_value(
                value, fmt, unit=unit, currency=currency, precision=precision
            )
            if prev_raw is not None and value is not None:
                abs_change = float(value) - prev_raw
                row["prior_value"] = prev_raw
                row["prior_formatted_value"] = format_display_value(
                    prev_raw, fmt, unit=unit, currency=currency, precision=precision
                )
                row["abs_change"] = abs_change
                row["abs_change_formatted"] = format_display_value(
                    abs_change, fmt, unit=unit, currency=currency, precision=precision
                )
                if prev_raw != 0:
                    pct = abs_change / prev_raw
                    row["pct_change"] = pct
                    row["pct_change_formatted"] = format_display_value(pct, "percent", precision=2)
            if value is not None:
                prev_raw = float(value)

        if metric_display_name:
            row.setdefault("metric_display_name", metric_display_name)
        if series_display_name:
            row.setdefault("series_display_name", series_display_name)
        if freshness_timestamp:
            row.setdefault("freshness_timestamp", freshness_timestamp)

        if row.get("is_partial_period") and not row.get("partial_period_note"):
            row["partial_period_note"] = "Partial period — incomplete"

        if row.get("target") is not None and row.get("target_formatted") is None:
            row["target_formatted"] = format_display_value(
                row["target"], fmt, unit=unit, currency=currency, precision=precision
            )
            if value is not None:
                variance = float(value) - float(row["target"])
                row["target_variance"] = variance
                row["target_variance_formatted"] = format_display_value(
                    variance, fmt, unit=unit, currency=currency, precision=precision
                )

        row["tooltip_text"] = build_tooltip_text(
            row,
            {
                "title": metric_display_name,
                "y_fields": [y_field],
                "format": fmt,
                "unit": unit,
                "currency": currency,
                "precision": precision,
                "freshness_timestamp": freshness_timestamp,
                "x_field": "period",
            },
        )
        # Preserve original index for gap detection in tests
        row.setdefault("point_index", idx)
        enriched.append(row)
    return enriched


def build_chart_spec(**fields: Any) -> dict[str, Any]:
    """Build a full ChartSpec dict with required metadata for interactive + static paths."""
    required = ("chart_id", "page_id", "chart_type", "title")
    missing = [key for key in required if not fields.get(key)]
    if missing:
        raise ValueError(f"build_chart_spec missing required fields: {', '.join(missing)}")

    chart_type = str(fields["chart_type"]).lower()
    if chart_type not in VALID_CHART_TYPES:
        raise ValueError(f"unsupported chart_type: {chart_type}")

    hover_fields = list(fields.get("hover_fields") or DEFAULT_HOVER_FIELDS)
    tooltip_template = fields.get("tooltip_template") or DEFAULT_TOOLTIP_TEMPLATE

    data = list(fields.get("data") or [])
    fmt = str(fields.get("format") or "decimal")
    y_fields = list(fields.get("y_fields") or (["value"] if chart_type != "kpi_card" else []))
    series = list(fields.get("series") or [])
    if not fields.get("skip_enrich"):
        if data and y_fields:
            data = enrich_series_rows(
                data,
                y_field=y_fields[0],
                fmt=fmt,
                unit=fields.get("unit"),
                currency=fields.get("currency"),
                precision=fields.get("precision"),
                metric_display_name=fields.get("metric_display_name") or fields.get("title"),
                series_display_name=(series[0].get("display_name") if series else None)
                or fields.get("series_display_name"),
                freshness_timestamp=fields.get("freshness_timestamp"),
                connect_missing=bool(fields.get("connect_missing")),
            )
        enriched_series = []
        for item in series:
            item = dict(item)
            series_rows = list(item.get("data") or [])
            y_field = item.get("y_field") or (y_fields[0] if y_fields else "value")
            if series_rows:
                item["data"] = enrich_series_rows(
                    series_rows,
                    y_field=y_field,
                    fmt=fmt,
                    unit=fields.get("unit"),
                    currency=fields.get("currency"),
                    precision=fields.get("precision"),
                    metric_display_name=fields.get("metric_display_name") or fields.get("title"),
                    series_display_name=item.get("display_name") or item.get("name"),
                    freshness_timestamp=fields.get("freshness_timestamp"),
                    connect_missing=bool(fields.get("connect_missing")),
                )
            enriched_series.append(item)
        series = enriched_series

    spec: dict[str, Any] = {
        "chart_id": str(fields["chart_id"]),
        "visual_id": str(fields.get("visual_id") or f"visual_{fields['chart_id']}"),
        "visual_type": str(fields.get("visual_type") or f"{chart_type}_chart"),
        "page_id": str(fields["page_id"]),
        "chart_type": chart_type,
        "title": str(fields["title"]),
        "display_name": str(fields.get("display_name") or fields["title"]),
        "subtitle": fields.get("subtitle"),
        "business_question": fields.get("business_question"),
        "metric_ids": list(fields.get("metric_ids") or []),
        "series": series,
        "x_field": str(fields.get("x_field") or "period"),
        "y_fields": y_fields,
        "date_role": fields.get("date_role"),
        "date_grain": fields.get("date_grain"),
        "dimensions": list(fields.get("dimensions") or []),
        "filters": list(fields.get("filters") or []),
        "format": fmt,
        "unit": fields.get("unit"),
        "currency": fields.get("currency"),
        "precision": fields.get("precision"),
        "aggregation_behavior": fields.get("aggregation_behavior") or "sum_additive",
        "hover_fields": hover_fields,
        "tooltip_template": tooltip_template,
        "proof_ids": list(fields.get("proof_ids") or []),
        "query_id": fields.get("query_id"),
        "source_resource_ids": list(fields.get("source_resource_ids") or []),
        "freshness_timestamp": fields.get("freshness_timestamp"),
        "partial_period_behavior": fields.get("partial_period_behavior") or "label_and_include",
        "empty_state_behavior": fields.get("empty_state_behavior") or "show_empty_message",
        "validation_status": str(fields.get("validation_status") or "PENDING"),
        "technical_validation_status": str(
            fields.get("technical_validation_status") or fields.get("validation_status") or "PENDING"
        ),
        "business_approval_status": str(fields.get("business_approval_status") or "PENDING"),
        "period_label": fields.get("period_label"),
        "accessible_name": str(fields.get("accessible_name") or fields["title"]),
        "accessible_description": str(
            fields.get("accessible_description")
            or fields.get("business_question")
            or f"Interactive chart for {fields['title']}"
        ),
        "mobile_tap_enabled": bool(fields.get("mobile_tap_enabled", True)),
        "hover_mode": fields.get("hover_mode") or ("x unified" if chart_type == "multi_line" else "closest"),
        "connect_missing": bool(fields.get("connect_missing", False)),
        "static_fallback_path": fields.get("static_fallback_path"),
        "static_fallback_exists": bool(fields.get("static_fallback_exists", False)),
        "accessible_data_table": bool(fields.get("accessible_data_table", True)),
        "offline_dependency": fields.get("offline_dependency") or "vendor/plotly.min.js",
        "renderer": fields.get("renderer") or "auto",
        "data": data,
    }
    return spec


def plotly_available() -> bool:
    try:
        import plotly.graph_objects as go  # noqa: F401

        return True
    except ImportError:
        return False


def matplotlib_available() -> bool:
    try:
        import matplotlib.pyplot as plt  # noqa: F401

        return True
    except ImportError:
        return False


def find_plotly_js() -> Path | None:
    """Locate plotly.min.js from an installed plotly package."""
    try:
        import plotly
    except ImportError:
        return None
    root = Path(plotly.__file__).resolve().parent
    candidates = [
        root / "package_data" / "plotly.min.js",
        root / "package_data" / "plotly.min.js.gz",
        *root.rglob("plotly.min.js"),
    ]
    for path in candidates:
        if path.is_file() and path.stat().st_size > 1000:
            return path
    return None


def ensure_offline_plotly_vendor(output_dir: Path) -> Path | None:
    """Copy plotly.min.js into output_dir/vendor for offline / restricted networks."""
    vendor = output_dir / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    dest = vendor / "plotly.min.js"
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest
    src = find_plotly_js()
    if src is None:
        # Marker file so validators can detect intent; SVG path still works offline.
        dest.write_text(
            "/* plotly not installed — interactive charts use offline SVG fallback */\n",
            encoding="utf-8",
        )
        return dest
    if src.suffix == ".gz":
        import gzip

        dest.write_bytes(gzip.decompress(src.read_bytes()))
    else:
        shutil.copy2(src, dest)
    return dest


def _chart_data_attrs(spec: dict[str, Any]) -> str:
    metric_ids = ",".join(str(m) for m in (spec.get("metric_ids") or []))
    return (
        f'data-chart-id="{html.escape(str(spec["chart_id"]))}" '
        f'data-page-id="{html.escape(str(spec.get("page_id") or ""))}" '
        f'data-metric-ids="{html.escape(metric_ids)}" '
        f'data-query-id="{html.escape(str(spec.get("query_id") or ""))}" '
        f'data-validation-status="{html.escape(str(spec.get("validation_status") or "PENDING"))}" '
        f'data-business-approval-status="{html.escape(str(spec.get("business_approval_status") or "PENDING"))}"'
    )


def _data_table_html(spec: dict[str, Any], data: list[dict[str, Any]]) -> str:
    x_field = spec.get("x_field") or "period"
    y_field = (spec.get("y_fields") or ["value"])[0]
    title = html.escape(str(spec.get("accessible_name") or spec.get("title") or "chart"))
    rows = []
    for row in data:
        period = html.escape(str(row.get("period_label") or row.get(x_field) or ""))
        value = html.escape(str(row.get("formatted_value") or row.get(y_field) or "—"))
        series = html.escape(str(row.get("series_display_name") or ""))
        note = html.escape(str(row.get("partial_period_note") or ("Missing" if row.get("missing_period") else "")))
        rows.append(f"<tr><td>{period}</td><td>{series}</td><td>{value}</td><td>{note}</td></tr>")
    return (
        f'<table class="chart-data-table" tabindex="0" aria-label="{title} data table">'
        "<thead><tr><th>Period / category</th><th>Series</th><th>Value</th><th>Notes</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _render_plotly_chart(
    spec: dict[str, Any],
    data: list[dict[str, Any]],
    *,
    include_plotlyjs: bool | str = False,
) -> str:
    import plotly.graph_objects as go

    chart_type = spec["chart_type"]
    x_field = spec["x_field"]
    y_fields = spec["y_fields"] or ["value"]
    title = spec["title"]
    hovermode = spec.get("hover_mode") or "closest"
    connect_gaps = bool(spec.get("connect_missing", False))

    fig = go.Figure()
    series_list = list(spec.get("series") or [])

    def add_series(y_field: str, name: str, rows: list[dict[str, Any]]) -> None:
        x_vals = [row.get(x_field, "") for row in rows]
        y_vals = [row.get(y_field) for row in rows]
        hover_text = [build_tooltip_text(row, spec) for row in rows]
        common = dict(
            name=name,
            text=hover_text,
            hovertext=hover_text,
            hovertemplate="%{hovertext}<extra></extra>",
            connectgaps=connect_gaps,
        )
        if chart_type in {"bar", "grouped_bar"}:
            fig.add_bar(x=x_vals, y=y_vals, **common)
        elif chart_type == "stacked_bar":
            fig.add_bar(x=x_vals, y=y_vals, **common)
        elif chart_type == "area":
            fig.add_scatter(x=x_vals, y=y_vals, mode="lines+markers", fill="tozeroy", **common)
        elif chart_type == "scatter":
            fig.add_scatter(x=x_vals, y=y_vals, mode="markers", **common)
        elif chart_type == "funnel":
            fig.add_funnel(x=y_vals, y=x_vals, **{k: v for k, v in common.items() if k != "connectgaps"})
        else:
            # line / multi_line default
            fig.add_scatter(x=x_vals, y=y_vals, mode="lines+markers", **common)

    if series_list and any("data" in s for s in series_list):
        for series in series_list:
            rows = list(series.get("data") or data)
            y_field = series.get("y_field") or y_fields[0]
            name = series.get("display_name") or series.get("name") or y_field
            add_series(y_field, name, rows)
    elif chart_type == "multi_line" and len(y_fields) > 1:
        for y_field in y_fields:
            add_series(y_field, y_field, data)
    elif chart_type == "histogram":
        y_field = y_fields[0]
        fig.add_histogram(x=[row.get(y_field) for row in data], name=title)
    elif chart_type == "box":
        y_field = y_fields[0]
        fig.add_box(y=[row.get(y_field) for row in data], name=title)
    elif chart_type == "heatmap":
        # Expect rows with x, y, z fields when provided
        xs = sorted({row.get("x") for row in data})
        ys = sorted({row.get("y") for row in data})
        zmap = {(row.get("x"), row.get("y")): row.get("z") for row in data}
        z = [[zmap.get((x, y)) for x in xs] for y in ys]
        fig.add_heatmap(x=xs, y=ys, z=z)
    elif chart_type in {"table", "kpi_card"}:
        # Rendered as HTML table / card below; keep empty figure marker
        pass
    else:
        add_series(y_fields[0], series_list[0].get("display_name") if series_list else y_fields[0], data)

    if chart_type == "stacked_bar":
        fig.update_layout(barmode="stack")
    elif chart_type == "grouped_bar":
        fig.update_layout(barmode="group")

    fig.update_layout(
        title=title,
        hovermode=hovermode,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h"),
    )

    # Mobile-friendly: click/tap activates same hover info
    config = {
        "displayModeBar": False,
        "responsive": True,
        "scrollZoom": False,
    }
    inner = fig.to_html(
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        div_id=f"plotly-{spec['chart_id']}",
        config=config,
    )
    attrs = _chart_data_attrs(spec)
    name = html.escape(str(spec.get("accessible_name") or title))
    desc = html.escape(str(spec.get("accessible_description") or ""))
    approval = html.escape(str(spec.get("business_approval_status") or "PENDING"))
    status_badge = ""
    if approval.upper() in {"PENDING", "DRAFT"}:
        status_badge = f'<span class="status-badge status-pending" aria-label="Approval {approval}">Pending approval</span>'

    table = _data_table_html(spec, data) if spec.get("accessible_data_table", True) else ""
    return (
        f'<div class="interactive-chart plotly-chart" {attrs} '
        f'id="chart-{html.escape(spec["chart_id"])}" role="figure" '
        f'aria-label="{name}" aria-description="{desc}" data-mobile-tap="true">'
        f"<h3 class=\"chart-title\">{html.escape(title)}</h3>"
        f"{status_badge}"
        f"{inner}"
        f'<div class="chart-tooltip" role="tooltip" aria-live="polite" hidden></div>'
        f"{table}"
        f"</div>"
    )


def _svg_point_coords(
    index: int,
    count: int,
    value: float,
    min_val: float,
    max_val: float,
    *,
    width: int = 480,
    height: int = 220,
    padding: int = 36,
) -> tuple[float, float]:
    span = max(max_val - min_val, 1e-9)
    x = padding + (index / max(count - 1, 1)) * (width - 2 * padding)
    y = height - padding - ((value - min_val) / span) * (height - 2 * padding)
    return x, y


def _render_svg_chart(spec: dict[str, Any], data: list[dict[str, Any]]) -> str:
    """Offline interactive fallback — no CDN, works without Plotly JS."""
    chart_id = html.escape(str(spec["chart_id"]))
    title = html.escape(str(spec["title"]))
    x_field = spec["x_field"]
    y_field = (spec["y_fields"] or ["value"])[0]
    chart_type = spec["chart_type"]
    width, height, padding = 480, 220, 36
    attrs = _chart_data_attrs(spec)
    name = html.escape(str(spec.get("accessible_name") or spec["title"]))
    desc = html.escape(str(spec.get("accessible_description") or ""))

    if chart_type in {"table", "kpi_card"}:
        table = _data_table_html(spec, data)
        value = html.escape(str((data[0].get("formatted_value") if data else "—")))
        body = (
            f'<div class="kpi-card-value">{value}</div>{table}'
            if chart_type == "kpi_card"
            else table
        )
        return (
            f'<div class="interactive-chart svg-chart" {attrs} id="chart-{chart_id}" '
            f'role="figure" aria-label="{name}" aria-description="{desc}" data-mobile-tap="true">'
            f'<h3 class="chart-title">{title}</h3>{body}</div>'
        )

    # Only plot non-missing points; do not interpolate gaps in the line path
    plot_rows = list(data)
    numeric_values = [
        float(row[y_field])
        for row in plot_rows
        if row.get(y_field) is not None and not row.get("missing_period")
    ]
    min_val = min(numeric_values) if numeric_values else 0.0
    max_val = max(numeric_values) if numeric_values else 1.0
    # Bar charts need a zero baseline so the smallest category is still hoverable
    if chart_type in {"bar", "grouped_bar", "stacked_bar"} and min_val >= 0:
        min_val = 0.0
    if min_val == max_val:
        min_val -= 1
        max_val += 1

    shapes: list[str] = []
    marks: list[str] = []
    count = len(plot_rows)
    last_good_idx: int | None = None

    for idx, row in enumerate(plot_rows):
        raw_value = row.get(y_field)
        missing = raw_value is None or row.get("missing_period")
        tooltip = html.escape(build_tooltip_text(row, spec))
        x_label = html.escape(str(row.get(x_field, "")))
        period = html.escape(str(row.get("period_label") or row.get(x_field, "")))

        if missing:
            # Gap marker — no connecting line across missing periods
            x, _ = _svg_point_coords(idx, count, min_val, min_val, max_val)
            marks.append(
                f'<circle class="chart-point chart-missing" cx="{x:.1f}" cy="{height - padding:.1f}" '
                f'r="4" fill="none" stroke="#94a3b8" stroke-dasharray="2 2" '
                f'data-tooltip="{tooltip}" data-x="{x_label}" data-period="{period}" '
                f'tabindex="0" role="button" aria-label="{period}: missing"/>'
            )
            continue

        value = float(raw_value)
        x, y = _svg_point_coords(idx, count, value, min_val, max_val)
        partial_class = " chart-partial" if row.get("is_partial_period") else ""

        if chart_type in {"bar", "grouped_bar", "stacked_bar"}:
            bar_width = (width - 2 * padding) / max(count, 1) * 0.6
            bar_x = x - bar_width / 2
            bar_height = height - padding - y
            marks.append(
                f'<rect class="chart-bar{partial_class}" x="{bar_x:.1f}" y="{y:.1f}" '
                f'width="{bar_width:.1f}" height="{bar_height:.1f}" data-tooltip="{tooltip}" '
                f'data-x="{x_label}" data-period="{period}" tabindex="0" role="button" '
                f'aria-label="{period}: {tooltip}"/>'
            )
        else:
            marks.append(
                f'<circle class="chart-point{partial_class}" cx="{x:.1f}" cy="{y:.1f}" r="5" '
                f'data-tooltip="{tooltip}" data-x="{x_label}" data-period="{period}" '
                f'tabindex="0" role="button" aria-label="{period}: {tooltip}"/>'
            )
            if last_good_idx is not None and chart_type in {
                "line",
                "multi_line",
                "area",
                "scatter",
            }:
                # Only connect consecutive non-missing points (no silent interpolation)
                if idx == last_good_idx + 1:
                    prev = plot_rows[last_good_idx]
                    prev_x, prev_y = _svg_point_coords(
                        last_good_idx, count, float(prev[y_field]), min_val, max_val
                    )
                    shapes.append(
                        f'<line x1="{prev_x:.1f}" y1="{prev_y:.1f}" x2="{x:.1f}" y2="{y:.1f}" '
                        f'stroke="#2563eb" stroke-width="2"/>'
                    )
        last_good_idx = idx

    axis = (
        f'<line x1="{padding}" y1="{height - padding}" x2="{width - padding}" '
        f'y2="{height - padding}" stroke="#94a3b8"/>'
        f'<line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}" '
        f'stroke="#94a3b8"/>'
    )
    table = _data_table_html(spec, data) if spec.get("accessible_data_table", True) else ""
    payload = html.escape(json.dumps(data, ensure_ascii=False, default=str))
    approval = str(spec.get("business_approval_status") or "PENDING").upper()
    status_badge = ""
    if approval in {"PENDING", "DRAFT"}:
        status_badge = (
            f'<span class="status-badge status-pending" aria-label="Approval {approval}">'
            "Pending approval</span>"
        )

    return f"""
<div class="interactive-chart svg-chart" {attrs} id="chart-{chart_id}"
     role="figure" aria-label="{name}" aria-description="{desc}"
     data-mobile-tap="true" data-chart-payload="{payload}">
  <h3 class="chart-title">{title}</h3>
  {status_badge}
  <svg class="chart-svg" viewBox="0 0 {width} {height}" width="100%" height="{height}"
       aria-hidden="true">
    {axis}
    {''.join(shapes)}
    {''.join(marks)}
  </svg>
  <div class="chart-tooltip" role="tooltip" aria-live="polite" hidden></div>
  {table}
</div>
""".strip()


def render_interactive_chart(
    spec: dict[str, Any],
    data: list[dict[str, Any]] | None = None,
    *,
    mode: str | None = None,
    include_plotlyjs: bool | str = False,
) -> str:
    """Render interactive HTML for a ChartSpec (Plotly when available, else offline SVG)."""
    rows = data if data is not None else list(spec.get("data") or [])
    active = (mode or RENDER_MODE or "auto").lower()
    if active not in VALID_RENDER_MODES:
        raise ValueError(f"unsupported render mode: {active}")
    if active == "static_image":
        raise ValueError("static_image mode should use export_static_image()")

    prefer_plotly = active in {"auto", "interactive_html"} and plotly_available()
    if prefer_plotly and spec.get("chart_type") not in {"table"}:
        try:
            return _render_plotly_chart(spec, rows, include_plotlyjs=include_plotlyjs)
        except Exception:
            return _render_svg_chart(spec, rows)
    return _render_svg_chart(spec, rows)


def export_static_image(spec: dict[str, Any], output_path: Path) -> Path | None:
    """Export a Matplotlib PNG (and optional PDF sibling) for print/offline static use."""
    if not matplotlib_available():
        return None
    import matplotlib.pyplot as plt

    data = list(spec.get("data") or [])
    if not data and spec.get("chart_type") not in {"kpi_card", "table"}:
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    x_field = spec.get("x_field") or "period"
    y_field = (spec.get("y_fields") or ["value"])[0]
    chart_type = spec.get("chart_type") or "line"

    fig, ax = plt.subplots(figsize=(7, 3.5))
    xs = [row.get("period_label") or row.get(x_field, "") for row in data]
    ys = [row.get(y_field) if not row.get("missing_period") else None for row in data]

    if chart_type in {"bar", "grouped_bar", "stacked_bar"}:
        plot_x = [x for x, y in zip(xs, ys) if y is not None]
        plot_y = [y for y in ys if y is not None]
        ax.bar(plot_x, plot_y, color="#2563eb")
    elif chart_type == "scatter":
        ax.scatter(
            [x for x, y in zip(xs, ys) if y is not None],
            [y for y in ys if y is not None],
            color="#2563eb",
        )
    else:
        # Draw segments without connecting across None (no silent interpolation)
        seg_x: list[Any] = []
        seg_y: list[Any] = []
        for x, y in zip(xs, ys):
            if y is None:
                if seg_x:
                    ax.plot(seg_x, seg_y, marker="o", color="#2563eb")
                    seg_x, seg_y = [], []
            else:
                seg_x.append(x)
                seg_y.append(y)
        if seg_x:
            ax.plot(seg_x, seg_y, marker="o", color="#2563eb")

    ax.set_title(spec.get("title") or spec.get("chart_id"))
    if spec.get("subtitle"):
        ax.set_xlabel(str(spec["subtitle"]))
    ylabel = spec.get("unit") or spec.get("currency") or (spec.get("y_fields") or [""])[0]
    if ylabel:
        ax.set_ylabel(str(ylabel))
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    pdf_path = output_path.with_suffix(".pdf")
    fig.savefig(pdf_path)
    plt.close(fig)
    return output_path


def render_chart(
    spec: dict[str, Any],
    *,
    mode: str = "auto",
    static_dir: Path | None = None,
) -> dict[str, Any]:
    """Unified renderer entrypoint returning HTML and/or static paths."""
    result: dict[str, Any] = {"chart_id": spec.get("chart_id"), "mode": mode}
    if mode in {"auto", "interactive_html"}:
        result["html"] = render_interactive_chart(spec, mode=mode, include_plotlyjs=False)
    if mode in {"auto", "static_image"} and static_dir is not None:
        out = static_dir / f"{spec['chart_id']}.png"
        path = export_static_image(spec, out)
        result["static_image_path"] = str(path.name) if path else None
        result["static_pdf_path"] = str(out.with_suffix(".pdf").name) if path else None
    return result
