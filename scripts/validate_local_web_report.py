#!/usr/bin/env python3
"""Validate that a generated local web report serves live data, not just HTML."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from lib_gate_common import add_output_json_arg, print_results
except ImportError:  # pragma: no cover
    add_output_json_arg = None  # type: ignore[assignment]
    print_results = None  # type: ignore[assignment]


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(url: str, timeout: float) -> tuple[int, bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "agentic-dbt-pipeline-validator"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        content_type = str(response.headers.get("Content-Type") or "")
        return int(response.status), body, content_type


def wait_for_response(url: str, process: subprocess.Popen[str], timeout_seconds: float) -> tuple[int, bytes, str]:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None

    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=2)
            raise RuntimeError(
                "Server process exited before serving content.\n"
                f"Exit code: {process.returncode}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            )
        try:
            return fetch(url, timeout=3)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = str(exc)
            time.sleep(0.5)

    raise TimeoutError(f"Timed out waiting for {url}. Last error: {last_error}")


def validate_body(body: bytes, expected_text: str | None) -> None:
    if len(body) < 200:
        raise RuntimeError(f"Response body is too small ({len(body)} bytes); page may be empty.")

    lower_body = body[:5000].lower()
    if b"<html" not in lower_body and b"<!doctype html" not in lower_body:
        raise RuntimeError("Response did not look like an HTML page.")

    if expected_text and expected_text.lower().encode("utf-8") not in body.lower():
        raise RuntimeError(f"Expected text not found in page: {expected_text}")


def _json_payload(body: bytes) -> dict[str, Any]:
    data = json.loads(body.decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("JSON payload was not an object")
    if data.get("error") or data.get("errors") or data.get("query_error"):
        raise RuntimeError(f"structured query error in payload: {data.get('error') or data.get('errors')}")
    return data


def validate_live_endpoints(base_url: str, report_dir: Path, details: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    charts_url = f"{base_url}/api/charts.json"
    metrics_url = f"{base_url}/api/metrics.json"
    refresh_url = f"{base_url}/api/refresh"

    try:
        status, body, _ctype = fetch(charts_url, timeout=5)
        details["charts_http_status"] = status
        if status != 200:
            errors.append(f"charts endpoint returned HTTP {status}")
        else:
            payload = _json_payload(body)
            charts = payload.get("charts") if isinstance(payload.get("charts"), list) else []
            details["charts_count"] = len(charts)
            details["charts_payload_ok"] = len(charts) > 0
            if not charts:
                errors.append("charts endpoint returned no charts")
            # Domain-neutral relation resolution evidence from registry metadata
            resolved = []
            for chart in charts:
                if not isinstance(chart, dict):
                    continue
                for key in ("source_resource_id", "relation_name", "model_unique_id", "unique_id"):
                    if chart.get(key):
                        resolved.append(str(chart.get(key)))
                for item in chart.get("source_resource_ids") or []:
                    if item:
                        resolved.append(str(item))
            details["resolved_relations"] = sorted(set(resolved))
            details["manifest_relation_resolution"] = bool(resolved)
            if not resolved:
                errors.append(
                    "manifest relation resolution failed: no source_resource_id/unique_id on chart payloads"
                )
    except Exception as exc:  # noqa: BLE001
        errors.append(f"charts endpoint failed: {exc}")
        details["charts_payload_ok"] = False

    try:
        status, body, _ctype = fetch(metrics_url, timeout=5)
        details["metrics_http_status"] = status
        if status != 200:
            errors.append(f"metrics endpoint returned HTTP {status}")
        else:
            payload = _json_payload(body)
            metrics = payload.get("metrics") if isinstance(payload.get("metrics"), list) else []
            boards = []
            if isinstance(payload.get("measure_board"), list):
                boards.extend(payload["measure_board"])
            if isinstance(payload.get("metric_board"), list):
                boards.extend(payload["metric_board"])
            details["metrics_count"] = len(metrics)
            details["board_count"] = len(boards)
            details["metrics_payload_ok"] = bool(metrics or boards)
            if not metrics and not boards:
                errors.append("metrics endpoint returned empty KPI payloads")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"metrics endpoint failed: {exc}")
        details["metrics_payload_ok"] = False

    try:
        status, body, _ctype = fetch(refresh_url, timeout=5)
        details["refresh_http_status"] = status
        if status != 200:
            errors.append(f"refresh endpoint returned HTTP {status}")
            details["refresh_ok"] = False
        else:
            payload = _json_payload(body)
            details["refresh_payload"] = {
                key: payload.get(key) for key in ("status", "freshness_timestamp", "error") if key in payload
            }
            if payload.get("error") or str(payload.get("status") or "").lower() in {"error", "fail", "failed"}:
                errors.append(f"refresh endpoint reported failure: {payload}")
                details["refresh_ok"] = False
            else:
                details["refresh_ok"] = True
    except Exception as exc:  # noqa: BLE001
        errors.append(f"refresh endpoint failed: {exc}")
        details["refresh_ok"] = False

    details["runtime_preflight"] = not errors
    details["initial_data_load"] = bool(details.get("charts_payload_ok") and details.get("metrics_payload_ok"))
    details["refresh_validation"] = bool(details.get("refresh_ok"))
    details["manifest_relation_resolution"] = bool(details.get("manifest_relation_resolution"))
    return errors


def write_runtime_preflight(report_dir: Path, details: dict[str, Any], errors: list[str]) -> Path:
    payload = {
        "status": "PASS" if not errors else "FAIL",
        "runtime_preflight": details.get("runtime_preflight"),
        "manifest_relation_resolution": details.get("manifest_relation_resolution"),
        "initial_data_load": details.get("initial_data_load"),
        "refresh_validation": details.get("refresh_validation"),
        "resolved_relations": details.get("resolved_relations") or [],
        "charts_payload_ok": details.get("charts_payload_ok"),
        "metrics_payload_ok": details.get("metrics_payload_ok"),
        "refresh_ok": details.get("refresh_ok"),
        "errors": list(errors),
    }
    path = report_dir / "runtime_preflight.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate live local web report data endpoints.")
    parser.add_argument("--report-dir", required=True, help="Directory containing serve_report.py.")
    parser.add_argument("--port", type=int, default=0, help="Port to use. Defaults to an available port.")
    parser.add_argument("--path", default="/", help="URL path to validate.")
    parser.add_argument("--expected-text", default=None, help="Text expected in the returned HTML.")
    parser.add_argument("--timeout-seconds", type=float, default=30)
    parser.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        help="Optional custom command. Use {port} as a placeholder for the selected port.",
    )
    if add_output_json_arg is not None:
        add_output_json_arg(parser)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {}

    report_dir = Path(args.report_dir).resolve()
    if not report_dir.exists():
        errors.append(f"report directory does not exist: {report_dir}")
        if print_results is not None:
            return print_results(
                "Local web report validation",
                errors,
                warnings,
                output_json=getattr(args, "output_json", None),
                validator_id=Path(__file__).stem,
            )
        print(f"ERROR: report directory does not exist: {report_dir}", file=sys.stderr)
        return 1

    port = args.port or find_free_port()
    path = args.path if args.path.startswith("/") else f"/{args.path}"
    base_url = f"http://127.0.0.1:{port}"
    url = f"{base_url}{path}"
    details["url"] = url
    details["report_dir"] = str(report_dir)

    if args.command:
        command = [part.format(port=port) for part in args.command]
    else:
        serve_report = report_dir / "serve_report.py"
        if not serve_report.exists():
            errors.append(f"missing {serve_report}")
            if print_results is not None:
                return print_results(
                    "Local web report validation",
                    errors,
                    warnings,
                    output_json=getattr(args, "output_json", None),
                    validator_id=Path(__file__).stem,
                )
            print(f"ERROR: missing {serve_report}", file=sys.stderr)
            return 1
        command = [
            sys.executable,
            str(serve_report),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]

    process = subprocess.Popen(
        command,
        cwd=str(report_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    body = b""
    try:
        status, body, _ctype = wait_for_response(url, process, args.timeout_seconds)
        details["http_status"] = status
        details["body_bytes"] = len(body)
        if status != 200:
            raise RuntimeError(f"Expected HTTP 200 but got HTTP {status}.")
        validate_body(body, args.expected_text)
        # HTTP 200/title alone is not enough for a live report.
        endpoint_errors = validate_live_endpoints(base_url, report_dir, details)
        errors.extend(endpoint_errors)
        preflight_path = write_runtime_preflight(report_dir, details, endpoint_errors)
        details["runtime_preflight_path"] = str(preflight_path)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"local web report validation failed for {url}: {exc}")
        details["runtime_preflight"] = False
        details["initial_data_load"] = False
        details["refresh_validation"] = False
        write_runtime_preflight(report_dir, details, errors)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    if print_results is not None:
        return print_results(
            "Local web report validation",
            errors,
            warnings,
            output_json=getattr(args, "output_json", None),
            validator_id=Path(__file__).stem,
            details=details,
        )

    if errors:
        print(f"ERROR: {errors[0]}", file=sys.stderr)
        return 1
    print(f"Local web report validation passed: {url} returned {len(body)} bytes of HTML with live data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
