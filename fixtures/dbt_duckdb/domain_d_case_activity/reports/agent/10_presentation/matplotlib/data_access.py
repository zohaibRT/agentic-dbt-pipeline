# TEST FIXTURE ONLY — illustrates required board payload shape
MEASURE_BOARD = [
    {"id": "event_count", "display_name": "Event count", "value": 5, "formatted_value": "5", "group": "Volume", "format": "integer"},
]
METRIC_BOARD = [
    {"id": "completion_rate", "display_name": "Completion rate", "value": 0.4, "formatted_value": "40.0%", "group": "Performance", "format": "percent"},
]

def format_value(value, fmt):
    if fmt == "percent":
        return f"{value * 100:.1f}%"
    return str(value)
