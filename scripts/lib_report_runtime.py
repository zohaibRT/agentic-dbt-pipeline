#!/usr/bin/env python3
"""DuckDB-first warehouse-backed report runtime execution.

Resolves exact unique_id → manifest relation, executes registered SQL, and
regenerates chart/metric payloads. Non-DuckDB adapters return BLOCKED.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib_gate_common import load_manifest, load_presentation_policy, reconcile_numeric
from lib_llm_playwright_review import is_under_fixtures
from lib_manifest_relation import (
    infer_project_root_from_report_dir,
    load_active_profile_target,
    resolve_unique_id,
    sha256_file,
)

SQL_COMMENT_RE = re.compile(r"^\s*--")
SELECT_RE = re.compile(r"\b(select|with)\b", re.I)
REF_RE = re.compile(r"\{\{\s*ref\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}")
EXPECTED_RESULT_RE = re.compile(
    r"(?:^|\n)\s*--\s*expected\s+result\s*[:=|-]\s*([^\n]+)", re.I
)
CAPTURED_RESULT_RE = re.compile(
    r"(?:^|\n)\s*--\s*captured\s+result\s*[:=|-]\s*([^\n]+)", re.I
)
TOLERANCE_RE = re.compile(r"(?:^|\n)\s*--\s*tolerance\s*[:=|-]\s*([^\n]+)", re.I)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def extract_runnable_sql(sql_text: str) -> str:
    """Return executable SQL, stripping leading proof comment headers."""
    lines = []
    for line in sql_text.splitlines():
        if SQL_COMMENT_RE.match(line) and not SELECT_RE.search(line):
            continue
        lines.append(line)
    body = "\n".join(lines).strip().rstrip(";")
    if not SELECT_RE.search(body):
        raise ValueError("no runnable SELECT/WITH statement found")
    return body + ";"


def load_query_registry(root: Path, report_dir: Path) -> list[dict[str, Any]]:
    candidates = [
        report_dir / "query_registry.json",
        root / "reports" / "agent" / "10_presentation" / "query_registry.json",
        root / "reports" / "agent" / "10_presentation" / "matplotlib" / "query_registry.json",
    ]
    for path in candidates:
        data = _load_json(path)
        queries = data.get("queries")
        if isinstance(queries, list) and queries:
            return [q for q in queries if isinstance(q, dict)]
    return []


def execute_duckdb_sql(
    *,
    connection_path: str,
    sql: str,
) -> tuple[list[tuple[Any, ...]], list[str]]:
    import duckdb  # type: ignore

    con = duckdb.connect(connection_path, read_only=True)
    try:
        cursor = con.execute(sql)
        columns = [d[0] for d in (cursor.description or [])]
        rows = cursor.fetchall()
        return list(rows), columns
    finally:
        con.close()


def execute_registered_query(
    root: Path,
    query: dict[str, Any],
    *,
    profile_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one query_registry entry against the resolved exact relation."""
    meta = profile_meta if profile_meta is not None else load_active_profile_target(root)
    adapter = str(meta.get("adapter") or "").strip().lower()
    query_id = str(query.get("query_id") or "")
    sql_path_raw = str(query.get("sql_path") or "")
    source_ids = [str(x) for x in (query.get("source_resource_ids") or []) if x]
    if query.get("source_resource_id"):
        source_ids.insert(0, str(query.get("source_resource_id")))
    unique_id = source_ids[0] if source_ids else ""

    result: dict[str, Any] = {
        "query_id": query_id,
        "unique_id": unique_id,
        "relation_name": None,
        "sql_path": sql_path_raw,
        "query_hash": "",
        "result_hash": "",
        "row_count": 0,
        "scalar_value": None,
        "columns": [],
        "rows": [],
        "executed_at": _utc_now(),
        "execution_id": str(uuid.uuid4()),
        "status": "FAIL",
        "error": "",
    }

    if adapter not in {"", "duckdb"}:
        result["status"] = "BLOCKED"
        result["error"] = f"live query execution unsupported for adapter={adapter or 'unknown'}"
        return result
    if not meta.get("connection_path"):
        result["status"] = "BLOCKED"
        result["error"] = "duckdb connection path unavailable"
        return result
    if not unique_id:
        result["error"] = "query missing exact source_resource_ids unique_id"
        return result

    resolved = resolve_unique_id(root, unique_id, require_physical=True, profile_meta=meta)
    result["relation_name"] = resolved.get("relation_name")
    if resolved.get("status") != "PASS":
        result["status"] = str(resolved.get("status") or "FAIL")
        result["error"] = str(resolved.get("execution_error") or resolved.get("notes") or "relation resolution failed")
        return result

    sql_path = root / sql_path_raw if sql_path_raw else None
    if sql_path is None or not sql_path.exists():
        result["error"] = f"sql_path missing: {sql_path_raw}"
        return result
    try:
        sql = extract_runnable_sql(sql_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        result["error"] = str(exc)
        return result
    result["query_hash"] = _sha256_text(sql)

    try:
        rows, columns = execute_duckdb_sql(connection_path=str(meta["connection_path"]), sql=sql)
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        return result

    result["columns"] = columns
    result["row_count"] = len(rows)
    # Keep a compact serializable sample (not full dumps for large results).
    sample = []
    for row in rows[:50]:
        sample.append([_jsonable(v) for v in row])
    result["rows"] = sample
    if rows and len(rows[0]) == 1:
        result["scalar_value"] = _jsonable(rows[0][0])
    result["result_hash"] = _sha256_text(json.dumps({"columns": columns, "rows": sample}, sort_keys=True))
    result["status"] = "PASS"
    return result


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # noqa: BLE001
            return str(value)
    return str(value)


def _format_metric_value(value: Any, *, format_rule: str = "") -> str:
    if value is None:
        return ""
    rule = (format_rule or "").lower()
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    if "percent" in rule:
        if abs(num) <= 1.5:
            return f"{num * 100:.2f}%"
        return f"{num:.2f}%"
    if num == int(num):
        return str(int(num))
    return f"{num:.4g}"


def apply_execution_to_payloads(
    report_dir: Path,
    executions: list[dict[str, Any]],
    *,
    data_version: str,
    freshness_timestamp: str,
) -> dict[str, Any]:
    """Update chart/metric JSON from successful executions."""
    chart_path = report_dir / "chart_registry.json"
    metric_path = report_dir / "rendered_metric_manifest.json"
    charts = _load_json(chart_path)
    metrics = _load_json(metric_path)

    by_query = {str(e.get("query_id")): e for e in executions if e.get("status") == "PASS"}
    metric_by_id: dict[str, Any] = {}
    for row in metrics.get("metrics") or []:
        if isinstance(row, dict) and row.get("metric_id"):
            metric_by_id[str(row["metric_id"])] = row

    updated_metrics = 0
    for query_id, execution in by_query.items():
        scalar = execution.get("scalar_value")
        # Find queries' metric ids from chart/metric links
        for chart in charts.get("charts") or []:
            if not isinstance(chart, dict):
                continue
            if str(chart.get("query_id") or "") != query_id:
                continue
            chart["freshness_timestamp"] = freshness_timestamp
            chart["data_version"] = data_version
            chart["runtime_execution_id"] = execution.get("execution_id")
            chart["runtime_result_hash"] = execution.get("result_hash")
            chart["source_relation_name"] = execution.get("relation_name")
            if scalar is not None:
                # Update last non-missing datapoint formatted_value when present
                data_rows = chart.get("data") if isinstance(chart.get("data"), list) else []
                for row in reversed(data_rows):
                    if isinstance(row, dict) and not row.get("missing_period"):
                        fmt = str(row.get("format") or chart.get("format") or "")
                        row["value"] = scalar
                        if "volume" in (chart.get("y_fields") or []) or chart.get("chart_id") == "volume_trend":
                            row["volume"] = scalar
                        row["formatted_value"] = _format_metric_value(scalar, format_rule=fmt)
                        break
            for mid in chart.get("metric_ids") or []:
                metric = metric_by_id.get(str(mid))
                if metric is not None and scalar is not None:
                    metric["value"] = scalar
                    metric["formatted_value"] = _format_metric_value(
                        scalar, format_rule=str(metric.get("format") or "")
                    )
                    metric["data_version"] = data_version
                    metric["runtime_execution_id"] = execution.get("execution_id")
                    updated_metrics += 1

        for board_key in ("measure_board", "metric_board"):
            for card in metrics.get(board_key) or []:
                if not isinstance(card, dict):
                    continue
                if str(card.get("query_id") or "") == query_id and scalar is not None:
                    card["value"] = scalar
                    card["formatted_value"] = _format_metric_value(
                        scalar, format_rule=str(card.get("format") or "")
                    )
                    card["data_version"] = data_version
                    updated_metrics += 1

    charts["freshness_timestamp"] = freshness_timestamp
    charts["data_version"] = data_version
    metrics["freshness_timestamp"] = freshness_timestamp
    metrics["data_version"] = data_version
    _write_json(chart_path, charts)
    _write_json(metric_path, metrics)
    return {"updated_metrics": updated_metrics, "charts_path": str(chart_path), "metrics_path": str(metric_path)}


def report_runtime_exempt(root: Path) -> bool:
    """Fixture-only synthetic reports may skip warehouse-backed refresh."""
    policy = load_presentation_policy(root)
    applicability = str(policy.get("report_runtime_applicability") or "required").strip().lower()
    return applicability == "not_applicable_fixture" and is_under_fixtures(root)


def refresh_report_from_warehouse(
    root: Path,
    report_dir: Path,
) -> dict[str, Any]:
    """Execute registered queries and regenerate report payloads (DuckDB-first)."""
    report_dir = report_dir.resolve()
    root = root.resolve()
    meta = load_active_profile_target(root)
    queries = load_query_registry(root, report_dir)
    freshness_timestamp = _utc_now()
    data_version = f"dv-{uuid.uuid4().hex[:12]}"
    execution_id = f"exec-{uuid.uuid4().hex[:12]}"

    payload: dict[str, Any] = {
        "status": "FAIL",
        "execution_id": execution_id,
        "data_version": data_version,
        "freshness_timestamp": freshness_timestamp,
        "profile_name": meta.get("profile_name"),
        "target": meta.get("target"),
        "adapter": meta.get("adapter"),
        "connection_path": meta.get("connection_path"),
        "manifest_path": str(root / "target" / "manifest.json"),
        "manifest_checksum": (
            sha256_file(root / "target" / "manifest.json")
            if (root / "target" / "manifest.json").exists()
            else None
        ),
        "queries": [],
        "execution_ids": [],
        "result_hashes": [],
        "errors": [],
    }

    if report_runtime_exempt(root):
        # Synthetic analytics fixtures: stamp freshness only; never claim warehouse truth.
        freshness = {
            "freshness_timestamp": freshness_timestamp,
            "data_version": data_version,
            "execution_id": execution_id,
            "status": "refreshed",
            "fixture_runtime_exempt": True,
        }
        _write_json(report_dir / "freshness.json", freshness)
        charts = _load_json(report_dir / "chart_registry.json")
        if charts:
            charts["freshness_timestamp"] = freshness_timestamp
            charts["data_version"] = data_version
            _write_json(report_dir / "chart_registry.json", charts)
        payload["status"] = "PASS"
        payload["execution_ids"] = [f"fixture-exempt-{execution_id}"]
        payload["result_hashes"] = [f"fixture-exempt-{_sha256_text(data_version)}"]
        payload["errors"] = []
        payload["notes"] = "report_runtime_applicability=not_applicable_fixture"
        _write_json(report_dir / "runtime_execution.json", payload)
        return payload

    if not queries:
        payload["status"] = "BLOCKED"
        payload["errors"].append("no query_registry entries found for live refresh")
        _write_json(report_dir / "runtime_execution.json", payload)
        return payload

    executions: list[dict[str, Any]] = []
    for query in queries:
        row = execute_registered_query(root, query, profile_meta=meta)
        executions.append(row)
        if row.get("status") == "PASS":
            payload["execution_ids"].append(row.get("execution_id"))
            payload["result_hashes"].append(row.get("result_hash"))
        else:
            payload["errors"].append(
                f"{row.get('query_id')}: {row.get('error') or row.get('status')}"
            )

    payload["queries"] = executions
    if any(e.get("status") != "PASS" for e in executions):
        # Do not rewrite chart/metric payloads on partial/failed execution.
        if any(e.get("status") == "BLOCKED" for e in executions) and all(
            e.get("status") in {"BLOCKED", "PASS"} for e in executions
        ):
            payload["status"] = "BLOCKED"
        else:
            payload["status"] = "FAIL"
        _write_json(report_dir / "runtime_execution.json", payload)
        return payload

    apply_execution_to_payloads(
        report_dir,
        executions,
        data_version=data_version,
        freshness_timestamp=freshness_timestamp,
    )
    freshness = {
        "freshness_timestamp": freshness_timestamp,
        "data_version": data_version,
        "execution_id": execution_id,
        "status": "refreshed",
    }
    _write_json(report_dir / "freshness.json", freshness)
    payload["status"] = "PASS"
    _write_json(report_dir / "runtime_execution.json", payload)
    return payload


def project_root_from_report_dir(report_dir: Path) -> Path:
    return infer_project_root_from_report_dir(report_dir)


def materialize_dbt_refs(root: Path, sql: str) -> str:
    """Replace {{ ref('model') }} with schema.alias from the dbt manifest."""
    if "{{" not in sql:
        return sql
    manifest = load_manifest(root) or {}
    nodes = manifest.get("nodes") if isinstance(manifest.get("nodes"), dict) else {}
    by_name: dict[str, dict[str, Any]] = {}
    for node in nodes.values():
        if not isinstance(node, dict):
            continue
        if str(node.get("resource_type") or "") != "model":
            continue
        for key in ("name", "alias"):
            value = str(node.get(key) or "").strip()
            if value:
                by_name[value] = node

    def _repl(match: re.Match[str]) -> str:
        name = match.group(1)
        node = by_name.get(name)
        if node is None:
            raise ValueError(f"cannot resolve ref('{name}') against manifest")
        schema = str(node.get("schema") or "main").strip() or "main"
        alias = str(node.get("alias") or node.get("name") or name).strip()
        return f"{schema}.{alias}"

    return REF_RE.sub(_repl, sql)


def parse_proof_comment_values(sql_text: str) -> dict[str, str]:
    expected = EXPECTED_RESULT_RE.search(sql_text)
    captured = CAPTURED_RESULT_RE.search(sql_text)
    tolerance = TOLERANCE_RE.search(sql_text)
    return {
        "expected": (expected.group(1).strip() if expected else ""),
        "captured": (captured.group(1).strip() if captured else ""),
        "tolerance": (tolerance.group(1).strip() if tolerance else "0"),
    }


def execute_kpi_proof_sql(
    root: Path,
    proof_path: Path,
    *,
    profile_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a KPI proof SELECT on DuckDB and reconcile vs expected/captured."""
    meta = profile_meta if profile_meta is not None else load_active_profile_target(root)
    adapter = str(meta.get("adapter") or "").strip().lower()
    result: dict[str, Any] = {
        "proof_path": str(proof_path),
        "status": "FAIL",
        "adapter": adapter or None,
        "live_value": None,
        "expected": "",
        "captured": "",
        "error": "",
        "executed_at": _utc_now(),
    }
    if adapter not in {"", "duckdb"}:
        result["status"] = "BLOCKED"
        result["error"] = f"live KPI proof execution unsupported for adapter={adapter or 'unknown'}"
        return result
    if not meta.get("connection_path"):
        result["status"] = "BLOCKED"
        result["error"] = "duckdb connection path unavailable for live KPI proof execution"
        return result
    try:
        text = proof_path.read_text(encoding="utf-8")
        comments = parse_proof_comment_values(text)
        result["expected"] = comments["expected"]
        result["captured"] = comments["captured"]
        sql = extract_runnable_sql(materialize_dbt_refs(root, text))
        rows, _columns = execute_duckdb_sql(connection_path=str(meta["connection_path"]), sql=sql)
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        return result
    if not rows:
        result["error"] = "proof SQL returned zero rows"
        return result
    live = rows[0][0]
    result["live_value"] = _jsonable(live)
    live_text = str(result["live_value"])
    tol = comments["tolerance"] or "0"
    for label, baseline in (("expected", comments["expected"]), ("captured", comments["captured"])):
        if not baseline:
            result["error"] = f"proof missing {label} result for live reconcile"
            return result
        recon = reconcile_numeric(baseline, live_text, tol)
        if not recon.get("within_tolerance"):
            result["error"] = (
                f"live KPI proof mismatch vs {label}: expected={baseline!r} live={live_text!r}"
            )
            result["reconcile"] = {
                "against": label,
                "calculated_status": recon.get("calculated_status"),
                "abs_diff": str(recon.get("abs_diff")),
            }
            return result
    result["status"] = "PASS"
    return result


def run_live_kpi_proof_execution(root: Path, proof_files: list[Path]) -> dict[str, Any]:
    """Run live DuckDB execution for referenced KPI proofs when policy requires it."""
    policy = load_presentation_policy(root)
    required = bool(policy.get("require_live_kpi_proof_execution", True))
    summary: dict[str, Any] = {
        "required": required,
        "status": "SKIPPED",
        "executions": [],
        "errors": [],
    }
    if not required:
        return summary
    if report_runtime_exempt(root):
        summary["status"] = "NOT_APPLICABLE"
        summary["notes"] = "report_runtime_applicability=not_applicable_fixture"
        return summary
    meta = load_active_profile_target(root)
    executions: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in proof_files:
        row = execute_kpi_proof_sql(root, path, profile_meta=meta)
        executions.append(row)
        if row.get("status") != "PASS":
            errors.append(
                f"{path.as_posix()}: {row.get('error') or row.get('status')}"
            )
    summary["executions"] = executions
    summary["errors"] = errors
    if not proof_files:
        summary["status"] = "PASS"
        summary["notes"] = "no proof files to execute"
        return summary
    if any(e.get("status") == "BLOCKED" for e in executions):
        summary["status"] = "BLOCKED"
    elif errors:
        summary["status"] = "FAIL"
    else:
        summary["status"] = "PASS"
    return summary
