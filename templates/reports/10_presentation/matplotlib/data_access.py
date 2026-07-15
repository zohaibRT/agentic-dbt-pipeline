"""Data access helpers for presentation boards and chart payloads."""

from __future__ import annotations

from chart_renderer import format_display_value

MEASURE_BOARD = [
    {
        "id": "event_count",
        "display_name": "Event count",
        "value": 100,
        "formatted_value": "100",
        "group": "Volume",
        "format": "integer",
        "unit": "events",
    },
    {
        "id": "completed_count",
        "display_name": "Completed count",
        "value": 80,
        "formatted_value": "80",
        "group": "Volume",
        "format": "integer",
        "unit": "events",
    },
]

METRIC_BOARD = [
    {
        "id": "completion_rate",
        "display_name": "Completion rate",
        "value": 0.8,
        "formatted_value": "80.0%",
        "group": "Performance",
        "format": "percent",
        "unit": None,
    },
    {
        "id": "mom_volume_change",
        "display_name": "Month-over-month volume change",
        "value": 0.05,
        "formatted_value": "5.0%",
        "group": "Performance",
        "format": "percent",
        "unit": None,
    },
]


def format_value(value: float | int, fmt: str, *, unit: str | None = None) -> str:
    return format_display_value(value, fmt, unit=unit)


def build_volume_trend_data() -> list[dict]:
    rows = [
        {"period": "Jan", "volume": 90, "period_label": "January"},
        {"period": "Feb", "volume": 95, "period_label": "February"},
        {"period": "Mar", "volume": 100, "period_label": "March"},
    ]
    for row in rows:
        row["formatted_value"] = format_display_value(row["volume"], "integer", unit="events")
        row["tooltip_text"] = f"{row['period_label']}: {row['formatted_value']}"
    return rows


def build_completion_rate_data() -> list[dict]:
    rows = [
        {"period": "Jan", "rate": 0.75, "period_label": "January"},
        {"period": "Feb", "rate": 0.78, "period_label": "February"},
        {"period": "Mar", "rate": 0.8, "period_label": "March"},
    ]
    for row in rows:
        row["formatted_value"] = format_display_value(row["rate"], "percent")
        row["tooltip_text"] = f"{row['period_label']}: {row['formatted_value']}"
    return rows
