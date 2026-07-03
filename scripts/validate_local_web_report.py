#!/usr/bin/env python3
"""Validate that a generated local web report actually serves browser content."""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(url: str, timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "agentic-dbt-pipeline-validator"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return int(response.status), response.read()


def wait_for_response(url: str, process: subprocess.Popen[str], timeout_seconds: float) -> tuple[int, bytes]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test a generated local web report.")
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
    args = parser.parse_args()

    report_dir = Path(args.report_dir).resolve()
    if not report_dir.exists():
        print(f"ERROR: report directory does not exist: {report_dir}", file=sys.stderr)
        return 1

    port = args.port or find_free_port()
    path = args.path if args.path.startswith("/") else f"/{args.path}"
    url = f"http://127.0.0.1:{port}{path}"

    if args.command:
        command = [part.format(port=port) for part in args.command]
    else:
        serve_report = report_dir / "serve_report.py"
        if not serve_report.exists():
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

    try:
        status, body = wait_for_response(url, process, args.timeout_seconds)
        if status != 200:
            raise RuntimeError(f"Expected HTTP 200 but got HTTP {status}.")
        validate_body(body, args.expected_text)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: local web report validation failed for {url}: {exc}", file=sys.stderr)
        return 1
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    print(f"Local web report validation passed: {url} returned {len(body)} bytes of HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
