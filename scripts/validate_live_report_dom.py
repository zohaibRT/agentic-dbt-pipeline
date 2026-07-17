#!/usr/bin/env python3
"""Live Playwright DOM validation for interactive presentation reports.

Verifies report readiness, pages, tooltips, responsive behavior, accessibility
hooks, refresh, API health, and DOM↔registry/proof traceability.

Browser PASS does not grant business approval — technical and business statuses
remain separate fields in the live report.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib_gate_common import add_output_json_arg, compare_formatted_values, print_results

VIEWPORTS: dict[str, dict[str, int]] = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
}

DECLARED_ENDPOINTS = ("/api/charts.json", "/api/metrics.json", "/api/refresh")
SQL_ERROR_RE = re.compile(
    r"("
    r"sql\s*error|psycopg2|sqlalchemy|duckdb\.Error|"
    r"syntax error at|database error|odbc|"
    r"relation does not exist|table does not exist|no such table|"
    r"catalog error|binder error|query failed|"
    r"internal server error|traceback"
    r")",
    re.I,
)
TECH_ID_RE = re.compile(r"^(model|source|metric|exposure|seed|snapshot)\.|^[a-z][a-z0-9]*(_[a-z0-9]+)+$")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def playwright_installed() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def looks_like_tech_id(label: str) -> bool:
    text = (label or "").strip()
    if not text:
        return False
    return bool(TECH_ID_RE.match(text))


def expected_tooltip_values(chart: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for row in chart.get("data") or []:
        token = row.get("tooltip_text") or row.get("formatted_value")
        if token:
            values.append(str(token))
    return values


def tooltip_matches_registry(tooltip_text: str, expected_values: list[str]) -> bool:
    cleaned = (tooltip_text or "").strip()
    if not cleaned:
        return False
    return any(value in cleaned for value in expected_values)


def pick_valid_data_point(chart: dict[str, Any]) -> dict[str, Any] | None:
    for row in chart.get("data") or []:
        if row.get("missing_period"):
            continue
        if row.get("formatted_value") or row.get("tooltip_text"):
            return row
    return None


def pick_critical_period_rows(chart: dict[str, Any]) -> list[dict[str, Any]]:
    """Return first, middle, last non-missing rows plus one partial-period row when present."""
    rows = [
        r
        for r in (chart.get("data") or [])
        if isinstance(r, dict)
        and not r.get("missing_period")
        and (r.get("formatted_value") or r.get("tooltip_text"))
    ]
    if not rows:
        return []
    selected: list[dict[str, Any]] = []
    first = rows[0]
    last = rows[-1]
    middle = rows[len(rows) // 2]
    for row in (first, middle, last):
        if row not in selected:
            selected.append(row)
    for row in rows:
        if row.get("is_partial_period") or row.get("partial_period_note"):
            if row not in selected:
                selected.append(row)
            break
    return selected


def _interact_chart_point(
    page: Any,
    container: Any,
    point: Any,
    viewport_name: str,
    *,
    chart_id: str,
) -> str:
    """Hover/tap a point and return tooltip text. Raises on failure."""
    tooltip = container.locator(".chart-tooltip")
    if viewport_name == "mobile":
        try:
            point.tap(timeout=5000)
        except Exception:
            box = point.bounding_box()
            if box:
                page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            else:
                point.click(timeout=5000, force=True)
        page.wait_for_timeout(250)
    else:
        try:
            point.hover(timeout=5000)
        except Exception:
            point.hover(timeout=5000, force=True)
        page.wait_for_timeout(150)
    page.wait_for_function(
        """(sel) => {
          const tip = document.querySelector(sel + ' .chart-tooltip');
          if (!tip) return false;
          if (tip.hasAttribute('hidden')) return false;
          const style = window.getComputedStyle(tip);
          return style.display !== 'none' && style.visibility !== 'hidden' && tip.textContent.trim().length > 0;
        }""",
        arg=f'[data-chart-id="{chart_id}"]',
        timeout=3000,
    )
    if tooltip.count() == 0:
        raise RuntimeError("missing tooltip element")
    return tooltip.inner_text(timeout=1500) or ""


def _find_target_for_row(targets: Any, row: dict[str, Any], chart: dict[str, Any]) -> Any | None:
    label = str(row.get("period_label") or row.get(chart.get("x_field") or "period") or "")
    short = str(row.get(chart.get("x_field") or "period") or "")
    series = str(row.get("series_display_name") or row.get("series_name") or "")
    formatted = str(row.get("formatted_value") or "")
    best = None
    for idx in range(targets.count()):
        candidate = targets.nth(idx)
        box = candidate.bounding_box()
        if not box or box.get("width", 0) <= 1 or box.get("height", 0) <= 1:
            continue
        period_attr = candidate.get_attribute("data-period") or candidate.get_attribute("data-x") or ""
        series_attr = candidate.get_attribute("data-series") or candidate.get_attribute("data-series-name") or ""
        tip = candidate.get_attribute("data-tooltip") or ""
        if period_attr and period_attr not in {label, short}:
            continue
        if series and series_attr and series_attr != series:
            continue
        if formatted and formatted in tip:
            return candidate
        if period_attr or not label:
            best = best or candidate
    if best is not None:
        return best
    # Fallback: first visible target
    for idx in range(targets.count()):
        candidate = targets.nth(idx)
        box = candidate.bounding_box()
        if box and box.get("width", 0) > 1 and box.get("height", 0) > 1:
            return candidate
    return targets.first if targets.count() else None


def expected_tooltip_assertions(chart: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    """Build assertion tokens for a single chart data point."""
    series = row.get("series_display_name") or row.get("series_name")
    if not series:
        series_list = chart.get("series") or []
        if series_list:
            series = series_list[0].get("display_name") or series_list[0].get("name")
    return {
        "metric_display_name": row.get("metric_display_name") or chart.get("title") or chart.get("display_name"),
        "formatted_value": row.get("formatted_value"),
        "period_label": row.get("period_label") or row.get(chart.get("x_field") or "period"),
        "series_display_name": series,
        "unit": chart.get("unit") or row.get("unit"),
        "currency": chart.get("currency") or row.get("currency"),
        "partial_period_note": row.get("partial_period_note")
        if row.get("is_partial_period") or row.get("partial_period_note")
        else None,
        "tooltip_text": row.get("tooltip_text"),
    }


def assert_tooltip_content(tooltip_text: str, expected: dict[str, Any], *, chart_id: str) -> list[str]:
    """Return error messages for missing tooltip expectations."""
    errors: list[str] = []
    text = tooltip_text or ""
    if not text.strip():
        return [f"chart {chart_id}: tooltip did not appear or was empty"]

    metric = expected.get("metric_display_name")
    if metric:
        if looks_like_tech_id(str(metric)):
            errors.append(f"chart {chart_id}: metric display name looks technical: {metric}")
        elif str(metric) not in text:
            errors.append(f"chart {chart_id}: tooltip missing metric display name {metric!r}")

    formatted = expected.get("formatted_value")
    if formatted and str(formatted) not in text and not tooltip_matches_registry(text, [str(formatted)]):
        # Allow formatted value to appear without unit suffix duplication
        core = str(formatted).split(" ")[0]
        if core not in text:
            errors.append(f"chart {chart_id}: tooltip missing exact formatted value {formatted!r}")

    period = expected.get("period_label")
    if period and str(period) not in text:
        errors.append(f"chart {chart_id}: tooltip missing date/category {period!r}")

    series = expected.get("series_display_name")
    if series and str(series) not in text:
        errors.append(f"chart {chart_id}: multi-series tooltip missing series name {series!r}")

    unit = expected.get("unit")
    if unit and str(unit) not in text and str(unit) not in str(formatted or ""):
        errors.append(f"chart {chart_id}: tooltip missing unit {unit!r}")

    currency = expected.get("currency")
    if currency and str(currency) not in text and str(currency) not in str(formatted or ""):
        errors.append(f"chart {chart_id}: tooltip missing currency {currency!r}")

    partial = expected.get("partial_period_note")
    if partial and "partial" not in text.lower():
        errors.append(f"chart {chart_id}: tooltip missing partial-period note")

    # Technical IDs must not appear as primary label (first line)
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    if looks_like_tech_id(first_line):
        errors.append(f"chart {chart_id}: technical id shown as primary tooltip label: {first_line}")

    return errors


def validate_page_contracts_static(
    page_registry: dict[str, Any],
    chart_registry: dict[str, Any],
    result: ValidationResult,
) -> dict[str, dict]:
    pages = page_registry.get("pages") or []
    by_id: dict[str, dict] = {}
    for page in pages:
        page_id = page.get("page_id")
        if not page_id:
            result.fail("page registry entry missing page_id")
            continue
        if page_id in by_id:
            result.fail(f"duplicate page_id: {page_id}")
        by_id[page_id] = page
        if not page.get("page_name") and not page.get("title"):
            result.fail(f"page {page_id}: missing page title/name")

    chart_pages = {c.get("page_id") for c in (chart_registry.get("charts") or []) if c.get("page_id")}
    for page_id in chart_pages:
        if page_id not in by_id:
            result.fail(f"orphan chart page_id not in page registry: {page_id}")

    return by_id


def response_has_sql_error(payload: Any, body_text: str = "") -> str | None:
    blob = body_text
    if isinstance(payload, dict):
        for key in ("sql_error", "error", "message", "detail"):
            val = payload.get(key)
            if isinstance(val, str) and SQL_ERROR_RE.search(val):
                return val
        blob = json.dumps(payload)
    match = SQL_ERROR_RE.search(blob or "")
    return match.group(0) if match else None


def wait_http_ready(url: str, process: subprocess.Popen[str], timeout: float) -> None:
    started = time.monotonic()
    while time.monotonic() - started < timeout:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=2)
            raise RuntimeError(f"serve_report exited early ({process.returncode})\n{stdout}\n{stderr}")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {url}")


def validate_declared_endpoints(base_url: str, result: ValidationResult) -> dict[str, Any]:
    details: dict[str, Any] = {}
    for route in DECLARED_ENDPOINTS:
        url = base_url.rstrip("/") + route
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                body = response.read().decode("utf-8", errors="replace")
                status = response.status
                payload: Any
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    payload = None
                details[route] = {"status": status, "ok": status == 200}
                if status != 200:
                    result.fail(f"endpoint {route} returned HTTP {status}")
                sql_err = response_has_sql_error(payload, body)
                if sql_err:
                    result.fail(f"endpoint {route} returned SQL error: {sql_err}")
        except urllib.error.HTTPError as exc:
            result.fail(f"endpoint {route} failed: HTTP {exc.code}")
            details[route] = {"status": exc.code, "ok": False}
        except Exception as exc:  # noqa: BLE001
            result.fail(f"endpoint {route} failed: {exc}")
            details[route] = {"status": None, "ok": False, "error": str(exc)}
    return details


def stop_server(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def capture_failure_artifacts(
    page: Any,
    context: Any,
    artifacts_dir: Path,
    label: str,
) -> dict[str, str]:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", label)[:80]
    shot = artifacts_dir / "screenshots" / f"{safe}.png"
    shot.parent.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    try:
        page.screenshot(path=str(shot), full_page=True)
        paths["screenshot"] = str(shot)
    except Exception as exc:  # noqa: BLE001
        paths["screenshot_error"] = str(exc)
    try:
        trace_path = artifacts_dir / "traces" / f"{safe}.zip"
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        context.tracing.stop(path=str(trace_path))
        paths["trace"] = str(trace_path)
    except Exception as exc:  # noqa: BLE001
        paths["trace_error"] = str(exc)
    return paths


def _tooltip_box_in_bounds(page: Any, tooltip_locator: Any, chart_locator: Any) -> bool:
    """Tooltip must stay within the viewport or at least the chart container."""
    if tooltip_locator.count() == 0:
        return False
    box = tooltip_locator.bounding_box()
    if not box:
        return True  # hidden or not laid out yet
    viewport = page.viewport_size or VIEWPORTS["desktop"]
    in_viewport = (
        box["x"] >= -2
        and box["y"] >= -2
        and box["x"] + box["width"] <= viewport["width"] + 2
        and box["y"] + box["height"] <= viewport["height"] + 2
    )
    if in_viewport:
        return True
    chart_box = chart_locator.bounding_box() if chart_locator.count() else None
    if not chart_box:
        return False
    # Allow tooltips clipped to the chart card on narrow mobile layouts
    return (
        box["x"] + box["width"] >= chart_box["x"] - 2
        and box["y"] + box["height"] >= chart_box["y"] - 2
        and box["x"] <= chart_box["x"] + chart_box["width"] + 2
        and box["y"] <= chart_box["y"] + chart_box["height"] + 2
    )


def validate_viewport(
    *,
    url: str,
    viewport_name: str,
    viewport: dict[str, int],
    timeout_ms: int,
    page_registry: dict[str, Any],
    chart_registry: dict[str, Any],
    metric_manifest: dict[str, Any],
    proof_registry: dict[str, Any],
    artifacts_dir: Path,
    result: ValidationResult,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    details: dict[str, Any] = {
        "viewport": viewport_name,
        "charts": [],
        "pages": [],
        "console_errors": [],
        "page_errors": [],
        "failed_requests": [],
        "refresh": {},
        "accessibility": {},
        "artifacts": {},
    }
    console_errors: list[str] = []
    page_errors: list[str] = []
    failed_requests: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=viewport,
            has_touch=viewport_name == "mobile",
            is_mobile=viewport_name == "mobile",
        )
        context.tracing.start(screenshots=True, snapshots=True, sources=False)
        page = context.new_page()

        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        def on_response(response: Any) -> None:
            req = response.request
            if "/api/" not in req.url:
                return
            if response.status >= 400:
                failed_requests.append(f"{req.method} {req.url} -> {response.status}")
            try:
                # Avoid consuming body for non-json; best-effort text check
                if "json" in (response.headers.get("content-type") or ""):
                    body = response.text()
                    if SQL_ERROR_RE.search(body or ""):
                        failed_requests.append(f"SQL error body from {req.url}")
            except Exception:
                pass

        page.on("response", on_response)

        try:
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            page.wait_for_function("window.__REPORT_READY__ === true", timeout=timeout_ms)
        except Exception as exc:  # noqa: BLE001
            result.fail(f"{viewport_name}: report ready failed: {exc}")
            details["artifacts"] = capture_failure_artifacts(page, context, artifacts_dir, f"{viewport_name}_ready")
            browser.close()
            return details

        ready = page.evaluate("window.__REPORT_READY__ === true")
        data_version = page.evaluate("window.__REPORT_DATA_VERSION__")
        details["report_ready"] = ready
        details["data_version"] = data_version
        details["report_url"] = url
        if not ready:
            result.fail(f"{viewport_name}: window.__REPORT_READY__ != true")
        if data_version is None or not str(data_version).strip():
            result.fail(f"{viewport_name}: nonblank window.__REPORT_DATA_VERSION__ required")
        error_panel = page.locator(".error-panel, .report-error, [data-report-error='true']")
        if error_panel.count() and error_panel.first.is_visible():
            result.fail(f"{viewport_name}: visible error panel present")

        for err in console_errors:
            result.fail(f"{viewport_name}: console error: {err}")
        for err in page_errors:
            result.fail(f"{viewport_name}: JavaScript exception: {err}")
        for err in failed_requests:
            result.fail(f"{viewport_name}: failed report API request: {err}")

        details["console_errors"] = list(console_errors)
        details["page_errors"] = list(page_errors)
        details["failed_requests"] = list(failed_requests)
        details["initial_data_load"] = ready and bool(data_version) and not failed_requests

        # --- Page validation ---
        pages = page_registry.get("pages") or []
        for page_meta in pages:
            page_id = page_meta.get("page_id")
            if not page_id:
                continue
            section = page.locator(f"section#{page_id}")
            page_detail = {"page_id": page_id, "exists": section.count() > 0}
            if section.count() == 0:
                result.fail(f"{viewport_name}: missing page section: {page_id}")
                details["pages"].append(page_detail)
                continue

            # Navigate to page
            nav = page.locator(f'nav a[data-page="{page_id}"]')
            if nav.count():
                nav.first.click()
                page.wait_for_timeout(100)

            title = section.locator("h2").first
            page_detail["title"] = title.inner_text() if title.count() else ""
            if not page_detail["title"]:
                result.fail(f"{viewport_name}: page {page_id} missing title")

            # Contracted visuals
            for visual_id in page_meta.get("visual_ids") or []:
                # visual_id may map to chart visual_id attribute or chart_id
                chart_match = None
                for chart in chart_registry.get("charts") or []:
                    if chart.get("visual_id") == visual_id or chart.get("chart_id") == visual_id:
                        chart_match = chart
                        break
                if chart_match:
                    cid = chart_match["chart_id"]
                    if page.locator(f'[data-chart-id="{cid}"]').count() == 0:
                        # Cards may not be charts
                        if not str(visual_id).startswith("card_"):
                            result.fail(
                                f"{viewport_name}: page {page_id} contracted visual missing in DOM: {visual_id}"
                            )

            details["pages"].append(page_detail)

        # Orphan DOM pages (sections not in registry) — warn for known extras only if registry present
        if pages:
            registry_ids = {p.get("page_id") for p in pages}
            for section in page.locator("section.page").all():
                sid = section.get_attribute("id")
                if sid and sid not in registry_ids:
                    result.fail(f"{viewport_name}: orphan page in DOM without contract: {sid}")

        # Freshness / period / trust status visibility
        if page.locator(".freshness-label").count() == 0:
            result.fail(f"{viewport_name}: freshness timestamp not visible")
        if page.locator("[data-reporting-period], .period-label").count() == 0:
            result.fail(f"{viewport_name}: reporting period not visible")
        if page.locator("[data-technical-validation-status]").count() == 0:
            result.fail(f"{viewport_name}: technical verification status not visible")
        if page.locator("[data-business-approval-status]").count() == 0:
            result.fail(f"{viewport_name}: business approval status not visible")

        # Pending approval must remain pending (browser must not rewrite to APPROVED)
        for metric in metric_manifest.get("metrics") or []:
            approval = str(metric.get("business_approval_status") or "").upper()
            if approval in {"PENDING", "DRAFT", "PENDING_REVIEW"}:
                # Ensure DOM still exposes pending somewhere for draft metrics
                pending_visible = page.locator(".status-badge.status-pending, [data-business-approval-status]").count()
                if pending_visible == 0:
                    result.warn(f"{viewport_name}: pending metric {metric.get('metric_id')} has no visible pending cue")
                # Never convert business status via automation — check window manifest unchanged
                live_manifest = page.evaluate("window.__REPORT_METRIC_MANIFEST__ || {}")
                for live in live_manifest.get("metrics") or []:
                    if live.get("metric_id") == metric.get("metric_id"):
                        live_approval = str(live.get("business_approval_status") or "").upper()
                        if live_approval == "APPROVED" and approval != "APPROVED":
                            result.fail(
                                f"{viewport_name}: browser PASS converted pending metric "
                                f"{metric.get('metric_id')} to APPROVED"
                            )

        # Horizontal overflow / nav accessibility
        overflow = page.evaluate(
            """() => {
              const doc = document.documentElement;
              return {
                scrollWidth: doc.scrollWidth,
                clientWidth: doc.clientWidth,
                navCount: document.querySelectorAll('nav a[data-page]').length
              };
            }"""
        )
        if overflow["scrollWidth"] > overflow["clientWidth"] + 8:
            result.fail(f"{viewport_name}: unexpected horizontal scrolling required")
        if overflow["navCount"] == 0:
            result.fail(f"{viewport_name}: navigation inaccessible")

        # --- Chart / tooltip validation ---
        charts = chart_registry.get("charts") or page.evaluate(
            "(window.__REPORT_CHART_REGISTRY__ && window.__REPORT_CHART_REGISTRY__.charts) || []"
        )
        for chart in charts:
            chart_id = chart.get("chart_id")
            chart_detail: dict[str, Any] = {"chart_id": chart_id, "viewport": viewport_name}
            if not chart_id:
                result.fail(f"{viewport_name}: registry chart missing chart_id")
                continue

            # Ensure executive page for charts
            page_id = chart.get("page_id")
            if page_id:
                nav = page.locator(f'nav a[data-page="{page_id}"]')
                if nav.count():
                    nav.first.click()
                    page.wait_for_timeout(80)

            container = page.locator(f'[data-chart-id="{chart_id}"]')
            if container.count() == 0:
                result.fail(f"{viewport_name}: missing chart: {chart_id}")
                chart_detail["missing"] = True
                details["charts"].append(chart_detail)
                continue

            # Overflow check
            overflow_chart = container.evaluate(
                """el => {
                  const parent = el.parentElement;
                  if (!parent) return false;
                  return el.scrollWidth > parent.clientWidth + 4;
                }"""
            )
            if overflow_chart:
                result.fail(f"{viewport_name}: chart {chart_id} overflows container")

            # Accessible name
            accessible_name = container.get_attribute("aria-label") or ""
            chart_detail["accessible_name"] = accessible_name
            expected_name = chart.get("accessible_name") or chart.get("title")
            if not accessible_name:
                result.fail(f"{viewport_name}: chart {chart_id} missing accessible name")
            elif expected_name and accessible_name != expected_name and expected_name not in accessible_name:
                result.warn(
                    f"{viewport_name}: chart {chart_id} accessible name {accessible_name!r} "
                    f"differs from registry {expected_name!r}"
                )

            # Data table alternative
            table = container.locator("table.chart-data-table")
            if table.count() == 0:
                result.fail(f"{viewport_name}: chart {chart_id} missing accessible data table")
            else:
                chart_detail["data_table"] = True

            sample_rows = pick_critical_period_rows(chart)
            targets = container.locator(".chart-point, .chart-bar")
            if targets.count() == 0:
                result.fail(f"{viewport_name}: chart {chart_id}: no hover/tap targets found")
                details["charts"].append(chart_detail)
                continue

            # Multi-series (≥2): genuine interaction with one DOM point per series
            series_list = [
                s for s in (chart.get("series") or []) if isinstance(s, dict)
            ]
            series_targets: list[tuple[str, Any, dict[str, Any]]] = []
            if len(series_list) >= 2:
                for series in series_list:
                    sname = str(series.get("display_name") or series.get("name") or "").strip()
                    if not sname:
                        continue
                    series_rows = [r for r in (series.get("data") or []) if isinstance(r, dict)]
                    if not series_rows and series is series_list[0]:
                        series_rows = [
                            r for r in (chart.get("data") or []) if isinstance(r, dict)
                        ]
                    srow = pick_valid_data_point(
                        {
                            "data": [
                                {**r, "series_display_name": sname, "series_name": sname}
                                for r in series_rows
                            ],
                            **{k: chart.get(k) for k in ("title", "x_field", "unit", "currency")},
                        }
                    )
                    matched = None
                    for idx in range(targets.count()):
                        candidate = targets.nth(idx)
                        box = candidate.bounding_box()
                        if not box or box.get("width", 0) <= 1 or box.get("height", 0) <= 1:
                            continue
                        series_attr = (
                            candidate.get_attribute("data-series")
                            or candidate.get_attribute("data-series-name")
                            or ""
                        )
                        if series_attr == sname:
                            matched = candidate
                            break
                    if matched is None:
                        result.fail(
                            f"{viewport_name}: chart {chart_id}: multi-series requires a "
                            f"hover/tap target with data-series={sname!r}"
                        )
                        continue
                    if srow:
                        series_targets.append((sname, matched, srow))

            if not sample_rows and not series_targets:
                result.fail(f"{viewport_name}: chart {chart_id}: no valid data point for tooltip check")
                details["charts"].append(chart_detail)
                continue

            tooltip_text = ""
            expected: dict[str, Any] = {}
            interactions: list[dict[str, Any]] = []

            def _run_interaction(point: Any, row: dict[str, Any]) -> None:
                nonlocal tooltip_text, expected
                expected = expected_tooltip_assertions(chart, row)
                try:
                    tip = _interact_chart_point(
                        page, container, point, viewport_name, chart_id=chart_id
                    )
                except Exception as exc:  # noqa: BLE001
                    diagnostic = point.get_attribute("data-tooltip") or ""
                    result.fail(
                        f"{viewport_name}: chart {chart_id}: genuine hover/tap failed ({exc}); "
                        f"data-tooltip diagnostic={'present' if diagnostic else 'missing'} "
                        f"(not accepted as PASS)"
                    )
                    return
                tooltip_text = tip
                if not tip.strip():
                    result.fail(f"{viewport_name}: chart {chart_id}: missing tooltip")
                else:
                    for msg in assert_tooltip_content(tip, expected, chart_id=chart_id):
                        result.fail(f"{viewport_name}: {msg}")
                interactions.append(
                    {
                        "period": expected.get("period_label"),
                        "series": expected.get("series_display_name"),
                        "tooltip": tip[:200],
                    }
                )

            for row in sample_rows:
                point = _find_target_for_row(targets, row, chart)
                if point is None:
                    result.fail(
                        f"{viewport_name}: chart {chart_id}: no hover/tap target for period sample"
                    )
                    continue
                _run_interaction(point, row)

            for _sname, matched, srow in series_targets:
                _run_interaction(matched, srow)

            tooltip = container.locator(".chart-tooltip")
            if tooltip.count() and not tooltip.is_hidden():
                if not _tooltip_box_in_bounds(page, tooltip.first, container):
                    result.fail(f"{viewport_name}: chart {chart_id}: tooltip leaves viewport")

            chart_detail["tooltip_text"] = tooltip_text
            chart_detail["expected"] = expected
            chart_detail["interactions"] = interactions
            chart_detail["sampled_points"] = len(interactions)
            details["charts"].append(chart_detail)

        # --- Accessibility (practical automated checks; not legal certification) ---
        a11y = {
            "has_nav_landmark": page.locator("nav").count() > 0,
            "has_main_or_pages": page.locator("section.page, main").count() > 0,
            "heading_count": page.locator("h1, h2, .site-title").count(),
            "focusable_charts": page.locator(".chart-point, .chart-bar, .chart-data-table").count(),
            "status_text_beyond_color": page.locator(".status-badge, [data-status-kind]").count() > 0,
            "disclaimer": "Automated checks only — not a full legal accessibility certification",
        }
        details["accessibility"] = a11y
        if not a11y["has_nav_landmark"]:
            result.fail(f"{viewport_name}: missing navigation landmark")
        if a11y["heading_count"] == 0:
            result.fail(f"{viewport_name}: missing headings")
        if a11y["focusable_charts"] == 0:
            result.fail(f"{viewport_name}: no keyboard-focusable chart inspection targets")
        if not a11y["status_text_beyond_color"]:
            result.fail(f"{viewport_name}: status indicators lack text beyond colour")

        # Visible focus check
        focusable = page.locator(".chart-point, .chart-bar, .chart-data-table, nav a").first
        if focusable.count():
            focusable.focus()
            focused = page.evaluate("document.activeElement && document.activeElement.tagName")
            if not focused:
                result.fail(f"{viewport_name}: keyboard focus not applied")

        # --- Refresh validation ---
        prior_version = page.evaluate("window.__REPORT_DATA_VERSION__")
        refresh_btn = page.locator(".refresh-data")
        refresh_detail: dict[str, Any] = {"prior_version": prior_version}
        if refresh_btn.count() == 0:
            result.fail(f"{viewport_name}: Refresh Data control missing")
        else:
            refresh_btn.click()
            page.wait_for_timeout(400)
            status = page.evaluate("window.__REPORT_REFRESH_STATUS__")
            new_version = page.evaluate("window.__REPORT_DATA_VERSION__")
            status_text = page.locator(".refresh-status").inner_text() if page.locator(".refresh-status").count() else ""
            refresh_detail.update(
                {
                    "status": status,
                    "status_text": status_text,
                    "new_version": new_version,
                }
            )
            if status == "error" or "fail" in status_text.lower():
                # Failed refresh must be visible and stale labelled
                stale = page.evaluate(
                    "document.body.classList.contains('stale-data') || "
                    "!!document.querySelector('.freshness-label[data-stale=\"true\"]')"
                )
                if not stale:
                    result.fail(f"{viewport_name}: refresh failure retained stale data without warning")
                refresh_detail["failed_visible"] = True
            else:
                if status != "success":
                    result.fail(
                        f"{viewport_name}: expected window.__REPORT_REFRESH_STATUS__ == 'success' "
                        f"after refresh, got {status!r}"
                    )
                if not new_version or not str(new_version).strip():
                    result.fail(f"{viewport_name}: nonblank __REPORT_DATA_VERSION__ required after refresh")
                # Chart registry consistency after refresh
                live_registry = page.evaluate("window.__REPORT_CHART_REGISTRY__ || {}")
                live_ids = {c.get("chart_id") for c in (live_registry.get("charts") or [])}
                expected_ids = {c.get("chart_id") for c in (chart_registry.get("charts") or [])}
                if expected_ids - live_ids:
                    result.fail(f"{viewport_name}: chart registry inconsistent after refresh")
                refresh_detail["refresh_validation"] = status == "success"

            # Forced failure path: intercept refresh and ensure stale warning
            page.route(
                "**/api/refresh",
                lambda route: route.fulfill(
                    status=500,
                    content_type="application/json",
                    body=json.dumps({"status": "error", "error": "forced refresh failure"}),
                ),
            )
            prior2 = page.evaluate("window.__REPORT_DATA_VERSION__")
            refresh_btn.click()
            page.wait_for_timeout(400)
            status2 = page.evaluate("window.__REPORT_REFRESH_STATUS__")
            version2 = page.evaluate("window.__REPORT_DATA_VERSION__")
            stale2 = page.evaluate(
                "document.body.classList.contains('stale-data') || "
                "!!document.querySelector('.freshness-label[data-stale=\"true\"]')"
            )
            status_text2 = page.locator(".refresh-status").inner_text() if page.locator(".refresh-status").count() else ""
            refresh_detail["forced_failure"] = {
                "status": status2,
                "stale_labelled": stale2,
                "version_unchanged": version2 == prior2,
                "status_text": status_text2,
            }
            if status2 != "error" and "fail" not in status_text2.lower():
                result.fail(f"{viewport_name}: refresh failure was not reported")
            if not stale2:
                result.fail(f"{viewport_name}: stale data without warning after failed refresh")
            if version2 != prior2:
                result.fail(
                    f"{viewport_name}: old data silently presented as newly refreshed "
                    f"(version changed on failed refresh)"
                )
            page.unroute("**/api/refresh")

        details["refresh"] = refresh_detail

        # --- Traceability: DOM card values vs manifest/proofs ---
        for metric in metric_manifest.get("metrics") or []:
            metric_id = metric.get("metric_id")
            if not metric_id:
                continue
            if not metric.get("chart_ids") and not metric.get("card_ids"):
                continue
            displayed = metric.get("formatted_value") or metric.get("displayed_value")
            card = page.locator(f'[data-metric-id="{metric_id}"] .value')
            if card.count():
                dom_value = card.first.inner_text().strip()
                ok, reason = compare_formatted_values(
                    dom_value,
                    str(displayed or ""),
                    format_rule=str(metric.get("format") or metric.get("formatting_rule") or ""),
                )
                if not ok:
                    result.fail(
                        f"{viewport_name}: live DOM value for {metric_id} differs from manifest "
                        f"({dom_value!r} vs {displayed!r}): {reason}"
                    )

            # Proof comparison
            for proof in proof_registry.get("proofs") or []:
                if proof.get("metric_id") != metric_id and proof.get("kpi_id") != metric_id:
                    continue
                proven = proof.get("displayed_value") or proof.get("captured_value")
                if displayed and proven:
                    ok, reason = compare_formatted_values(
                        str(displayed),
                        str(proven),
                        format_rule=str(proof.get("formatting_rule") or metric.get("format") or ""),
                    )
                    if not ok:
                        result.fail(
                            f"{viewport_name}: live/manifest value for {metric_id} differs from proof "
                            f"beyond formatting rules: {reason}"
                        )

        # Capture artifacts if this viewport accumulated errors
        viewport_errors = [e for e in result.errors if e.startswith(f"{viewport_name}:")]
        if viewport_errors:
            details["artifacts"] = capture_failure_artifacts(
                page, context, artifacts_dir, f"{viewport_name}_fail"
            )
        else:
            try:
                context.tracing.stop()
            except Exception:
                pass

        browser.close()

    return details


def write_reports(root: Path, payload: dict[str, Any], artifacts_dir: Path) -> tuple[Path, Path]:
    out_dir = root / "reports" / "agent" / "10_presentation"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "LIVE_REPORT_DOM_REPORT.json"
    md_path = out_dir / "LIVE_REPORT_DOM_REPORT.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Live Report DOM Validation",
        "",
        f"- Status: **{payload.get('status')}**",
        f"- Validated at: `{payload.get('validated_at')}`",
        f"- URL: `{payload.get('url')}`",
        f"- Viewports: {', '.join(payload.get('viewports') or [])}",
        "",
        "## Errors",
        "",
    ]
    errors = payload.get("errors") or []
    if not errors:
        lines.append("_None_")
    else:
        for err in errors:
            lines.append(f"- {err}")
    lines.extend(["", "## Warnings", ""])
    warnings = payload.get("warnings") or []
    if not warnings:
        lines.append("_None_")
    else:
        for warn in warnings:
            lines.append(f"- {warn}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Automated browser checks only — not a full legal accessibility certification.",
            "- Browser PASS does not grant business approval; technical and business statuses remain separate.",
            f"- Artifacts directory: `{artifacts_dir}`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_output_json_arg(parser)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report-dir", type=Path, default=None)
    parser.add_argument("--port", type=int, default=None, help="Fixed port (default: ephemeral)")
    parser.add_argument("--desktop", action="store_true", help="Include desktop viewport")
    parser.add_argument("--tablet", action="store_true", help="Include tablet viewport")
    parser.add_argument("--mobile", action="store_true", help="Include mobile viewport")
    parser.add_argument("--timeout-seconds", type=float, default=45)
    parser.add_argument(
        "--allow-skip",
        action="store_true",
        help="Exit 0 when playwright is not installed (non-CI only).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    matplotlib = (
        args.report_dir.resolve()
        if args.report_dir
        else root / "reports" / "agent" / "10_presentation" / "matplotlib"
    )
    presentation = matplotlib.parent
    artifacts_dir = presentation / "live_browser_artifacts"

    selected = [name for name in ("desktop", "tablet", "mobile") if getattr(args, name)]
    if not selected:
        selected = ["desktop", "tablet", "mobile"]

    if not (matplotlib / "report.html").exists():
        print("SKIPPED: no report.html")
        return 0

    if not playwright_installed():
        message = "playwright is not installed; run: pip install playwright && playwright install chromium"
        if args.allow_skip:
            print(f"SKIPPED: {message}")
            return 0
        print(f"ERROR: {message}")
        return 1

    serve_report = matplotlib / "serve_report.py"
    if not serve_report.exists():
        print(f"ERROR: missing {serve_report}")
        return 1

    chart_registry = load_json(matplotlib / "chart_registry.json") or load_json(presentation / "chart_registry.json")
    metric_manifest = load_json(matplotlib / "rendered_metric_manifest.json") or load_json(
        presentation / "rendered_metric_manifest.json"
    )
    page_registry = load_json(presentation / "page_registry.json")
    proof_registry = load_json(presentation / "proof_registry.json")

    result = ValidationResult()
    validate_page_contracts_static(page_registry, chart_registry, result)

    port = args.port or find_free_port()
    url = f"http://127.0.0.1:{port}/"
    timeout_ms = int(args.timeout_seconds * 1000)

    process = subprocess.Popen(
        [
            sys.executable,
            str(serve_report),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--report-dir",
            str(matplotlib),
        ],
        cwd=str(matplotlib),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    details: dict[str, Any] = {"viewports": {}, "endpoints": {}}
    try:
        wait_http_ready(url, process, args.timeout_seconds)
        details["endpoints"] = validate_declared_endpoints(url, result)

        for name in selected:
            vp_details = validate_viewport(
                url=url,
                viewport_name=name,
                viewport=VIEWPORTS[name],
                timeout_ms=timeout_ms,
                page_registry=page_registry,
                chart_registry=chart_registry,
                metric_manifest=metric_manifest,
                proof_registry=proof_registry,
                artifacts_dir=artifacts_dir,
                result=result,
            )
            details["viewports"][name] = vp_details
    except Exception as exc:  # noqa: BLE001
        result.fail(str(exc))
        details["exception"] = traceback.format_exc()
    finally:
        stop_server(process)

    payload = {
        "status": "FAIL" if result.errors else "PASS",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "viewports": selected,
        "errors": result.errors,
        "warnings": result.warnings,
        "details": details,
        "artifacts_dir": str(artifacts_dir),
        "notes": [
            "Automated browser checks only — not a full legal accessibility certification.",
            "Browser PASS does not grant business approval.",
        ],
    }
    json_path, md_path = write_reports(root, payload, artifacts_dir)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")

    # Avoid Windows console UnicodeEncodeError on tooltip glyphs
    safe_errors = [e.encode("ascii", "replace").decode("ascii") for e in result.errors]
    safe_warnings = [w.encode("ascii", "replace").decode("ascii") for w in result.warnings]
    # Surface handoff evidence flags for check_report_handoff_readiness.py
    first_vp = next(iter(details.get("viewports") or {}), None)
    vp0 = (details.get("viewports") or {}).get(first_vp) or {}
    details["initial_data_load"] = bool(vp0.get("initial_data_load")) or not result.errors
    details["refresh_validation"] = any(
        bool((vp.get("refresh") or {}).get("refresh_validation"))
        for vp in (details.get("viewports") or {}).values()
        if isinstance(vp, dict)
    )
    details["manifest_relation_resolution"] = any(
        bool(c.get("source_resource_id") or c.get("source_resource_ids") or c.get("unique_id"))
        for c in (chart_registry.get("charts") or [])
        if isinstance(c, dict)
    )
    details["report_url"] = url
    return print_results(
        "Live report DOM validation",
        safe_errors,
        safe_warnings,
        details=details,
        output_json=getattr(args, "output_json", None),
        validator_id=Path(__file__).stem,
    )


if __name__ == "__main__":
    raise SystemExit(main())
