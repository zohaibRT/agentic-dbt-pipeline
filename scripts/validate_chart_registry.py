#!/usr/bin/env python3
"""Validate chart_registry.json and rendered_metric_manifest.json.

Static structural checks only — does not claim live browser hover verification
(that belongs to validate_live_report_dom.py).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from lib_gate_common import add_output_json_arg, load_presentation_policy, print_results, read_text

REQUIRED_CHART_FIELDS = (
    "chart_id",
    "page_id",
    "chart_type",
    "title",
    "metric_ids",
    "proof_ids",
    "query_id",
    "hover_fields",
    "tooltip_template",
    "validation_status",
    "business_approval_status",
    "accessible_name",
)


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(read_text(path))


def normalize_id(value: str) -> str:
    return value.strip().lower()


def looks_like_tech_id(label: str) -> bool:
    text = (label or "").strip()
    if not text:
        return False
    if re.fullmatch(r"[a-z][a-z0-9_]*", text) and "_" in text:
        return True
    if text.startswith(("model.", "source.", "metric.", "exposure.")):
        return True
    return False


def _resolve_static_path(matplotlib: Path, static_path: str) -> Path:
    candidate = Path(static_path)
    if candidate.is_absolute():
        return candidate
    return matplotlib / static_path


def validate_registry(
    registry: dict,
    errors: list[str],
    matplotlib: Path,
    *,
    policy: dict | None = None,
) -> dict[str, dict]:
    charts_by_id: dict[str, dict] = {}
    charts = registry.get("charts") or []
    if not charts:
        errors.append("chart_registry.json has no charts")
        return charts_by_id

    policy = policy or {}
    require_tooltip = bool(policy.get("require_tooltip_contract", True))
    require_static = bool(policy.get("require_static_fallback", True))
    require_a11y_table = bool(policy.get("require_accessible_data_table", True))
    require_offline = bool(policy.get("require_offline_interactive_dependency", True))
    expected_interactive = str(policy.get("interactive_renderer") or "plotly").lower()
    expected_static = str(policy.get("static_renderer") or "matplotlib").lower()
    allowed_modes = {str(m).lower() for m in (policy.get("render_modes") or [])}

    for chart in charts:
        chart_id = chart.get("chart_id")
        if not chart_id:
            errors.append("chart missing chart_id")
            continue
        if chart_id in charts_by_id:
            errors.append(f"duplicate chart_id: {chart_id}")
        charts_by_id[chart_id] = chart

        for field in REQUIRED_CHART_FIELDS:
            if chart.get(field) in (None, "", []):
                errors.append(f"chart {chart_id}: missing {field}")

        if not chart.get("page_id"):
            errors.append(f"chart {chart_id}: missing page mapping")

        metric_ids = chart.get("metric_ids") or []
        proof_ids = chart.get("proof_ids") or []
        if not metric_ids:
            errors.append(f"chart {chart_id}: missing metric_ids")
        if not proof_ids:
            errors.append(f"chart {chart_id}: missing proof_ids / proof mapping")

        hover_fields = chart.get("hover_fields") or []
        tooltip_template = chart.get("tooltip_template")
        if require_tooltip:
            if not hover_fields:
                errors.append(f"chart {chart_id}: missing tooltip hover_fields contract")
            if not tooltip_template:
                errors.append(f"chart {chart_id}: missing tooltip_template contract")

        if not chart.get("format"):
            errors.append(f"chart {chart_id}: missing display format from metric contract")

        static_path = chart.get("static_fallback_path")
        if require_static:
            if not static_path:
                errors.append(f"chart {chart_id}: missing static_fallback_path")
            else:
                candidate = _resolve_static_path(matplotlib, str(static_path))
                if not candidate.exists() and not chart.get("static_fallback_exists"):
                    errors.append(f"chart {chart_id}: static fallback file missing: {static_path}")
                elif chart.get("static_fallback_exists") and not candidate.exists():
                    errors.append(f"chart {chart_id}: static_fallback_exists true but file missing")

        if not chart.get("accessible_name"):
            errors.append(f"chart {chart_id}: missing accessible chart name")
        if require_a11y_table and chart.get("accessible_data_table") is False:
            errors.append(f"chart {chart_id}: accessible data table/details required")

        if require_offline:
            offline = chart.get("offline_dependency") or "vendor/plotly.min.js"
            offline_path = matplotlib / str(offline)
            if not offline_path.exists():
                errors.append(f"chart {chart_id}: offline interactive dependency missing: {offline}")

        render_mode = str(chart.get("render_mode") or chart.get("mode") or "auto").lower()
        if allowed_modes and render_mode not in allowed_modes:
            errors.append(
                f"chart {chart_id}: render_mode {render_mode!r} not in presentation_policy.render_modes"
            )

        # Only compare when chart explicitly declares a renderer override
        if chart.get("interactive_renderer"):
            declared = str(chart.get("interactive_renderer")).lower()
            if declared != expected_interactive:
                errors.append(
                    f"chart {chart_id}: interactive_renderer {declared!r} != "
                    f"policy {expected_interactive!r}"
                )
        if chart.get("static_renderer"):
            declared = str(chart.get("static_renderer")).lower()
            if declared != expected_static:
                errors.append(
                    f"chart {chart_id}: static_renderer {declared!r} != policy {expected_static!r}"
                )

        if chart.get("mobile_tap_enabled") is False:
            errors.append(f"chart {chart_id}: mobile_tap_enabled must be true for interactive charts")

        for label_key in ("title", "display_name", "accessible_name"):
            label = chart.get(label_key)
            if label and looks_like_tech_id(str(label)):
                errors.append(
                    f"chart {chart_id}: {label_key} looks like a technical id, not a business label: {label}"
                )

        data = chart.get("data") or []
        if not data:
            errors.append(f"chart {chart_id}: missing data points for hover validation")
        else:
            for idx, row in enumerate(data):
                if row.get("missing_period"):
                    continue
                if not (row.get("formatted_value") or row.get("tooltip_text")):
                    errors.append(
                        f"chart {chart_id}: data point {idx} missing formatted_value/tooltip_text"
                    )
                tip = str(row.get("tooltip_text") or "")
                metric_name = row.get("metric_display_name") or chart.get("title")
                if metric_name and metric_name not in tip and not row.get("formatted_value"):
                    errors.append(
                        f"chart {chart_id}: data point {idx} tooltip missing metric display name"
                    )

    return charts_by_id


def validate_manifest(
    manifest: dict,
    charts_by_id: dict[str, dict],
    errors: list[str],
) -> dict[str, dict]:
    metrics_by_id: dict[str, dict] = {}
    metrics = manifest.get("metrics") or []
    if not metrics:
        errors.append("rendered_metric_manifest.json has no metrics")
        return metrics_by_id

    chart_refs: dict[str, list[str]] = {}
    for metric in metrics:
        metric_id = metric.get("metric_id")
        if not metric_id:
            errors.append("metric missing metric_id")
            continue
        key = normalize_id(metric_id)
        if key in metrics_by_id:
            errors.append(f"duplicate metric_id: {metric_id}")
        metrics_by_id[key] = metric

        approval = str(metric.get("business_approval_status") or "").upper()
        if approval in {"PENDING", "DRAFT"}:
            label = str(metric.get("formatted_value") or metric.get("displayed_value") or "").lower()
            pending_label = str(metric.get("pending_label") or "").lower()
            if "pending" not in label and "pending" not in pending_label:
                errors.append(f"metric {metric_id}: pending KPI must be labelled as pending")

        display_name = metric.get("display_name")
        if display_name and looks_like_tech_id(str(display_name)):
            errors.append(
                f"metric {metric_id}: display_name looks like a technical id: {display_name}"
            )

        for chart_id in metric.get("chart_ids") or []:
            chart_refs.setdefault(chart_id, []).append(metric_id)
            if chart_id not in charts_by_id:
                errors.append(f"metric {metric_id}: orphan chart_id {chart_id}")

        if metric.get("chart_ids"):
            if not metric.get("proof_ids"):
                errors.append(f"metric {metric_id}: rendered metric missing proof mapping")

        if not metric.get("display_name"):
            errors.append(f"metric {metric_id}: missing display_name")
        if not metric.get("formatted_value"):
            errors.append(f"metric {metric_id}: missing formatted_value")

    for chart_id, chart in charts_by_id.items():
        metric_ids = chart.get("metric_ids") or []
        manifest_hits = chart_refs.get(chart_id, [])
        for metric_id in metric_ids:
            if metric_id not in manifest_hits:
                errors.append(
                    f"chart {chart_id}: metric_id {metric_id} not mapped in rendered_metric_manifest"
                )

    return metrics_by_id


def validate_report_hooks(matplotlib: Path, errors: list[str], warnings: list[str]) -> None:
    """Confirm live-browser hooks are present in report.html (static presence only)."""
    report = matplotlib / "report.html"
    if not report.exists():
        warnings.append("report.html missing — skip hook presence checks")
        return
    text = read_text(report)
    for hook in (
        "__REPORT_READY__",
        "__REPORT_CHART_REGISTRY__",
        "__REPORT_METRIC_MANIFEST__",
        "__REPORT_DATA_VERSION__",
        "__REPORT_REFRESH_STATUS__",
    ):
        if hook not in text:
            errors.append(f"report.html missing live-report hook: window.{hook}")
    for attr in (
        "data-chart-id",
        "data-page-id",
        "data-metric-ids",
        "data-query-id",
        "data-validation-status",
        "data-business-approval-status",
    ):
        if attr not in text:
            errors.append(f"report.html missing chart container attribute hook: {attr}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report-dir", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    policy = load_presentation_policy(root)
    matplotlib = (
        args.report_dir.resolve()
        if args.report_dir
        else root / "reports" / "agent" / "10_presentation" / "matplotlib"
    )

    errors: list[str] = []
    warnings: list[str] = []

    if not matplotlib.exists():
        print("SKIPPED: no matplotlib presentation folder")
        return 0

    registry_path = matplotlib / "chart_registry.json"
    manifest_path = matplotlib / "rendered_metric_manifest.json"
    has_charts = registry_path.exists() or (matplotlib / "report.html").exists()

    if not has_charts:
        print("SKIPPED: no interactive charts")
        return 0

    if not registry_path.exists():
        errors.append("missing chart_registry.json")
        return print_results("Chart registry validation", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)

    registry = load_json(registry_path)
    if not isinstance(registry, dict):
        errors.append("chart_registry.json must be an object")
        return print_results("Chart registry validation", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)

    charts_by_id = validate_registry(registry, errors, matplotlib, policy=policy)

    if not manifest_path.exists():
        errors.append("missing rendered_metric_manifest.json")
    else:
        manifest = load_json(manifest_path)
        if not isinstance(manifest, dict):
            errors.append("rendered_metric_manifest.json must be an object")
        else:
            validate_manifest(manifest, charts_by_id, errors)

    validate_report_hooks(matplotlib, errors, warnings)

    print(f"Chart registry validation: charts={len(charts_by_id)} errors={len(errors)}")
    return print_results("Chart registry validation", errors, warnings, output_json=getattr(args, "output_json", None), validator_id=Path(__file__).stem)


if __name__ == "__main__":
    raise SystemExit(main())
