#!/usr/bin/env python3
"""Local HTTP server for interactive presentation reports with live DuckDB refresh."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


def _discover_scripts_dir(report_dir: Path) -> Path | None:
    # matplotlib → 10_presentation → agent → reports → <project root>
    project_root = report_dir.resolve().parents[3]
    candidate = project_root / "scripts"
    if (candidate / "lib_report_runtime.py").exists():
        return candidate
    # Skill-repo layout: fixtures/.../matplotlib → walk upward for scripts/
    for parent in report_dir.resolve().parents:
        scripts = parent / "scripts"
        if (scripts / "lib_report_runtime.py").exists():
            return scripts
    return None


def _load_runtime(report_dir: Path):
    scripts = _discover_scripts_dir(report_dir)
    if scripts is None:
        raise RuntimeError("lib_report_runtime.py not found on scripts path")
    scripts_s = str(scripts)
    if scripts_s not in sys.path:
        sys.path.insert(0, scripts_s)
    from lib_report_runtime import project_root_from_report_dir, refresh_report_from_warehouse

    return project_root_from_report_dir, refresh_report_from_warehouse


class ReportHandler(SimpleHTTPRequestHandler):
    report_dir: Path = Path(".")
    freshness_file: Path = Path("freshness.json")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/api/charts.json":
            self._serve_json(self.report_dir / "chart_registry.json")
            return
        if route == "/api/metrics.json":
            self._serve_json(self.report_dir / "rendered_metric_manifest.json")
            return
        if route == "/api/refresh":
            self._handle_refresh()
            return

        if route in {"/", "/report.html"}:
            self.path = "/report.html"
        return super().do_GET()

    def _serve_json(self, path: Path) -> None:
        if not path.exists():
            self.send_error(404, f"Missing {path.name}")
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_refresh(self) -> None:
        try:
            project_root_from_report_dir, refresh_report_from_warehouse = _load_runtime(self.report_dir)
            root = project_root_from_report_dir(self.report_dir)
            result = refresh_report_from_warehouse(root, self.report_dir)
        except Exception as exc:  # noqa: BLE001
            result = {
                "status": "FAIL",
                "error": str(exc),
                "execution_ids": [],
                "result_hashes": [],
            }

        status = str(result.get("status") or "FAIL").upper()
        http_status = 200 if status == "PASS" else 500
        body_obj = {
            "status": "success" if status == "PASS" else status.lower(),
            "freshness_timestamp": result.get("freshness_timestamp"),
            "data_version": result.get("data_version"),
            "execution_id": result.get("execution_id"),
            "execution_ids": result.get("execution_ids") or [],
            "result_hashes": result.get("result_hashes") or [],
            "errors": result.get("errors") or ([] if status == "PASS" else [result.get("error") or status]),
        }
        if status != "PASS":
            body_obj["error"] = "; ".join(str(e) for e in body_obj["errors"] if e)

        body = json.dumps(body_obj).encode("utf-8")
        self.send_response(http_status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--report-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()

    report_dir = args.report_dir.resolve()
    if not (report_dir / "report.html").exists():
        raise SystemExit(f"Missing report.html in {report_dir}")

    handler = ReportHandler
    handler.report_dir = report_dir
    handler.freshness_file = report_dir / "freshness.json"

    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving report from {report_dir} at http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
