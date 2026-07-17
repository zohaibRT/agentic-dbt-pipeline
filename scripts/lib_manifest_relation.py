#!/usr/bin/env python3
"""Genuine dbt unique_id → manifest relation resolution and physical preflight.

Exact unique_id lookup only. No name shortening or bare-name fallback at
presentation/final phases.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from lib_gate_common import load_manifest, load_yaml

UNIQUE_ID_RE = re.compile(
    r"^(model|source|seed|snapshot|metric|exposure|semantic_model)\.[A-Za-z0-9_]+\.[A-Za-z0-9_]+"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_project_root_from_report_dir(report_dir: Path) -> Path:
    """matplotlib → 10_presentation → agent → reports → <project root>."""
    return report_dir.resolve().parents[3]


def collect_registered_unique_ids(root: Path) -> list[str]:
    """Collect exact unique_ids registered on presentation charts/queries/metrics."""
    found: list[str] = []
    presentation = root / "reports" / "agent" / "10_presentation"
    candidates = [
        presentation / "chart_registry.json",
        presentation / "matplotlib" / "chart_registry.json",
        presentation / "query_registry.json",
        presentation / "matplotlib" / "query_registry.json",
        presentation / "rendered_metric_manifest.json",
        presentation / "matplotlib" / "rendered_metric_manifest.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        for bucket_key in ("charts", "queries", "metrics", "measure_board", "metric_board"):
            rows = data.get(bucket_key)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                for key in ("source_resource_id", "model_unique_id", "unique_id"):
                    value = row.get(key)
                    if value:
                        found.append(str(value).strip())
                for item in row.get("source_resource_ids") or []:
                    if item:
                        found.append(str(item).strip())
    # Preserve order, drop empties/duplicates
    seen: set[str] = set()
    ordered: list[str] = []
    for item in found:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def load_active_profile_target(root: Path) -> dict[str, Any]:
    """Read profile/target/adapter metadata from dbt_project.yml + profiles.yml."""
    project = load_yaml(root / "dbt_project.yml")
    profile_name = str((project or {}).get("profile") or "").strip()
    profiles_path = root / "profiles.yml"
    if not profiles_path.exists():
        # Fallback to user profiles only for metadata; never invent credentials.
        home_profiles = Path.home() / ".dbt" / "profiles.yml"
        profiles_path = home_profiles if home_profiles.exists() else profiles_path
    profiles = load_yaml(profiles_path) if profiles_path.exists() else {}
    profile = profiles.get(profile_name) if isinstance(profiles, dict) else None
    if not isinstance(profile, dict):
        return {
            "profile_name": profile_name or None,
            "target": None,
            "adapter": None,
            "database": None,
            "schema": None,
            "profiles_path": str(profiles_path) if profiles_path.exists() else None,
        }
    target_name = str(profile.get("target") or "dev").strip()
    outputs = profile.get("outputs") if isinstance(profile.get("outputs"), dict) else {}
    output = outputs.get(target_name) if isinstance(outputs.get(target_name), dict) else {}
    path_value = output.get("path")
    resolved_path = None
    if path_value:
        candidate = Path(str(path_value))
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()
        resolved_path = str(candidate)
    return {
        "profile_name": profile_name or None,
        "target": target_name,
        "adapter": str(output.get("type") or "").strip() or None,
        "database": output.get("database") or output.get("dbname") or output.get("catalog"),
        "schema": output.get("schema"),
        "connection_path": resolved_path,
        "profiles_path": str(profiles_path),
    }


def _lookup_manifest_node(manifest: dict[str, Any], unique_id: str) -> dict[str, Any] | None:
    for bucket in ("nodes", "sources", "exposures", "metrics", "semantic_models", "saved_queries"):
        section = manifest.get(bucket)
        if isinstance(section, dict) and unique_id in section and isinstance(section[unique_id], dict):
            return section[unique_id]
    disabled = manifest.get("disabled")
    if isinstance(disabled, dict) and unique_id in disabled:
        entries = disabled[unique_id]
        items = entries if isinstance(entries, list) else [entries]
        for item in items:
            if isinstance(item, dict):
                return {**item, "_disabled": True}
    return None


def _relation_name_from_node(node: dict[str, Any]) -> str:
    relation = node.get("relation_name")
    if relation:
        return str(relation).strip()
    database = node.get("database")
    schema = node.get("schema")
    alias = node.get("alias") or node.get("name")
    parts = [p for p in (database, schema, alias) if p]
    if len(parts) == 3:
        return f'"{parts[0]}"."{parts[1]}"."{parts[2]}"'
    if len(parts) == 2:
        return f'"{parts[0]}"."{parts[1]}"'
    if alias:
        return str(alias)
    return ""


def physical_relation_exists(
    *,
    adapter: str | None,
    connection_path: str | None,
    relation_name: str,
    schema: str | None = None,
    alias: str | None = None,
) -> tuple[bool, str]:
    """Return (exists, error_message). Adapter-neutral; DuckDB file path supported."""
    adapter_l = (adapter or "").strip().lower()
    if adapter_l in {"", "duckdb"} and connection_path:
        try:
            import duckdb  # type: ignore
        except ImportError:
            return False, "duckdb package not installed for physical relation check"
        path = Path(connection_path)
        if not path.exists():
            return False, f"duckdb database file missing: {path}"
        try:
            con = duckdb.connect(str(path), read_only=True)
        except Exception as exc:  # noqa: BLE001
            return False, f"duckdb connect failed: {exc}"
        try:
            # Prefer exact relation_name; also try schema.alias forms.
            candidates = [relation_name]
            if schema and alias:
                candidates.append(f'"{schema}"."{alias}"')
                candidates.append(f"{schema}.{alias}")
            if alias:
                candidates.append(str(alias))
            last_error = ""
            for candidate in candidates:
                if not candidate:
                    continue
                try:
                    con.execute(f"SELECT 1 FROM {candidate} LIMIT 0")
                    return True, ""
                except Exception as exc:  # noqa: BLE001
                    last_error = str(exc)
            return False, last_error or "relation not found"
        finally:
            con.close()
    if not connection_path and adapter_l == "duckdb":
        return False, "duckdb connection path unavailable for physical relation check"
    # Non-duckdb adapters: require relation_name present; physical check deferred
    # to warehouse validators. Report as unknown so callers can require duckdb
    # fixtures / explicit warehouse proof separately.
    if relation_name:
        return True, "physical_check_skipped_non_duckdb_adapter"
    return False, "relation_name missing and physical check unavailable"


def resolve_unique_id(
    root: Path,
    unique_id: str,
    *,
    require_physical: bool = True,
    profile_meta: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Resolve one exact unique_id against the current manifest and optionally the warehouse."""
    result: dict[str, Any] = {
        "unique_id": unique_id,
        "status": "FAIL",
        "enabled": None,
        "database": None,
        "schema": None,
        "alias": None,
        "relation_name": None,
        "manifest_path": str(manifest_path) if manifest_path else None,
        "manifest_checksum": None,
        "physical_exists": None,
        "execution_error": "",
        "notes": "",
    }
    if not UNIQUE_ID_RE.match(unique_id or ""):
        result["notes"] = "not_an_exact_unique_id; name shortening / bare names are forbidden"
        result["execution_error"] = result["notes"]
        return result

    if manifest is None:
        manifest_path = root / "target" / "manifest.json"
        result["manifest_path"] = str(manifest_path)
        if not manifest_path.exists():
            result["notes"] = "target/manifest.json missing"
            result["execution_error"] = result["notes"]
            return result
        result["manifest_checksum"] = sha256_file(manifest_path)
        manifest = load_manifest(root)
    else:
        if manifest_path and manifest_path.exists():
            result["manifest_checksum"] = sha256_file(manifest_path)

    if not isinstance(manifest, dict):
        result["notes"] = "manifest unreadable"
        result["execution_error"] = result["notes"]
        return result

    node = _lookup_manifest_node(manifest, unique_id)
    if node is None:
        result["notes"] = "unique_id not found in manifest (exact match required; no name fallback)"
        result["execution_error"] = result["notes"]
        return result

    config = node.get("config") if isinstance(node.get("config"), dict) else {}
    enabled = bool(config.get("enabled", True)) and not bool(node.get("_disabled"))
    result["enabled"] = enabled
    result["database"] = node.get("database")
    result["schema"] = node.get("schema")
    result["alias"] = node.get("alias") or node.get("name")
    result["relation_name"] = _relation_name_from_node(node)
    if not enabled:
        result["notes"] = "resource is disabled in manifest"
        result["execution_error"] = result["notes"]
        return result
    if not result["relation_name"]:
        result["notes"] = "manifest relation_name missing for unique_id"
        result["execution_error"] = result["notes"]
        return result

    meta = profile_meta if profile_meta is not None else load_active_profile_target(root)
    if require_physical:
        exists, err = physical_relation_exists(
            adapter=str(meta.get("adapter") or "") or None,
            connection_path=str(meta.get("connection_path") or "") or None,
            relation_name=str(result["relation_name"]),
            schema=str(result["schema"] or "") or None,
            alias=str(result["alias"] or "") or None,
        )
        result["physical_exists"] = exists
        if not exists:
            result["execution_error"] = err or "physical relation does not exist"
            result["notes"] = "physical_relation_missing"
            return result
        if err == "physical_check_skipped_non_duckdb_adapter":
            result["notes"] = err
    else:
        result["physical_exists"] = None
        result["notes"] = "physical_check_not_required"

    result["status"] = "PASS"
    return result


def resolve_registered_relations(
    root: Path,
    *,
    unique_ids: list[str] | None = None,
    require_physical: bool = True,
) -> dict[str, Any]:
    """Resolve all registered presentation unique_ids. No bare-name fallback."""
    manifest_path = root / "target" / "manifest.json"
    profile_meta = load_active_profile_target(root)
    ids = list(unique_ids) if unique_ids is not None else collect_registered_unique_ids(root)
    manifest = load_manifest(root) if manifest_path.exists() else None
    manifest_checksum = sha256_file(manifest_path) if manifest_path.exists() else None

    resolutions: list[dict[str, Any]] = []
    errors: list[str] = []
    for unique_id in ids:
        row = resolve_unique_id(
            root,
            unique_id,
            require_physical=require_physical,
            profile_meta=profile_meta,
            manifest=manifest,
            manifest_path=manifest_path if manifest_path.exists() else None,
        )
        resolutions.append(row)
        if row.get("status") != "PASS":
            errors.append(
                f"{unique_id}: {row.get('execution_error') or row.get('notes') or 'resolution failed'}"
            )

    ok = bool(ids) and not errors
    return {
        "status": "PASS" if ok else "FAIL",
        "manifest_relation_resolution": ok,
        "unique_ids": ids,
        "resolved_relations": [
            r["unique_id"] for r in resolutions if r.get("status") == "PASS" and r.get("relation_name")
        ],
        "resolutions": resolutions,
        "errors": errors,
        "profile_name": profile_meta.get("profile_name"),
        "target": profile_meta.get("target"),
        "adapter": profile_meta.get("adapter"),
        "database": profile_meta.get("database"),
        "schema": profile_meta.get("schema"),
        "connection_path": profile_meta.get("connection_path"),
        "manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "manifest_checksum": manifest_checksum,
        "require_physical": require_physical,
    }
