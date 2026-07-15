#!/usr/bin/env python3
"""Minimal local HTTP server for interactive presentation reports."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


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
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = {"freshness_timestamp": timestamp, "status": "refreshed"}
        self.freshness_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        registry_path = self.report_dir / "chart_registry.json"
        if registry_path.exists():
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["freshness_timestamp"] = timestamp
            registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
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
