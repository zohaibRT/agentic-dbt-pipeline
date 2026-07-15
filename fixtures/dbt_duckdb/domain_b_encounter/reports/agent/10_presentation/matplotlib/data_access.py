"""TEST FIXTURE ONLY — board payloads with display names and formatted values."""
MEASURE_BOARD = [
    {
        "id": "event_count",
        "display_name": "Event count",
        "value": 5,
        "formatted_value": "5",
        "group": "Volume",
        "format": "integer",
        "unit": "events"
    }
]
METRIC_BOARD = [
    {
        "id": "completion_rate",
        "display_name": "Completion rate",
        "value": 0.4,
        "formatted_value": "40.0%",
        "group": "Performance",
        "format": "percent"
    },
    {
        "id": "draft_exploratory",
        "display_name": "Draft exploratory metric",
        "value": null,
        "formatted_value": "Pending",
        "group": "Draft",
        "format": "decimal",
        "business_approval_status": "PENDING"
    }
]

def format_value(value, fmt):
    if fmt == "percent":
        return f"{value * 100:.1f}%"
    if fmt == "integer":
        return f"{int(value):,}"
    return str(value)
