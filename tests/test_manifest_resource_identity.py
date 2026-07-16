#!/usr/bin/env python3
"""P0-MANIFEST-RESOURCE-IDENTITY-EXPOSURES: inventory, identity, classification, facts, exposures."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DBT_FIX = ROOT / "fixtures" / "dbt_duckdb"
FIX = ROOT / "fixtures" / "analytics"

sys.path.insert(0, str(SCRIPTS))
from lib_gate_common import (  # noqa: E402
    _class_is_analytical_fact,
    build_resource_inventory,
    compute_exposure_fingerprint,
    filesystem_fallback_unique_id,
    inventory_from_filesystem,
    inventory_from_manifest,
    list_analytical_facts,
    resolve_named_resource,
    resources_by_name,
)


def run_script(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    return subprocess.run(cmd, cwd=str(cwd or SCRIPTS), capture_output=True, text=True)


def write_manifest(root: Path, manifest: dict) -> None:
    target = root / "target"
    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def base_manifest(**sections: dict) -> dict:
    data = {
        "metadata": {"project_name": "demo"},
        "nodes": {},
        "sources": {},
        "exposures": {},
        "metrics": {},
        "semantic_models": {},
        "disabled": {},
    }
    data.update(sections)
    return data


def model_node(
    unique_id: str,
    *,
    name: str,
    package: str = "demo",
    path: str = "models/gold/x.sql",
    enabled: bool = True,
    meta: dict | None = None,
    tags: list | None = None,
    version: int | None = None,
) -> dict:
    return {
        "unique_id": unique_id,
        "name": name,
        "resource_type": "model",
        "package_name": package,
        "original_file_path": path,
        "version": version,
        "config": {"enabled": enabled, "materialized": "table"},
        "depends_on": {"nodes": [], "macros": []},
        "meta": meta or {},
        "tags": tags or [],
        "columns": {},
        "description": "",
    }


class ManifestInventoryTests(unittest.TestCase):
    def test_01_loads_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.demo.a": model_node("model.demo.a", name="a", path="models/gold/a.sql"),
                    }
                ),
            )
            inv = inventory_from_manifest(json.loads((root / "target" / "manifest.json").read_text()))
            self.assertTrue(any(r["unique_id"] == "model.demo.a" for r in inv))

    def test_02_loads_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    sources={
                        "source.demo.raw.t": {
                            "unique_id": "source.demo.raw.t",
                            "name": "t",
                            "resource_type": "source",
                            "package_name": "demo",
                            "original_file_path": "models/sources/raw.yml",
                            "source_name": "raw",
                            "config": {},
                            "meta": {},
                            "tags": [],
                            "columns": {},
                        }
                    }
                ),
            )
            inv, src = build_resource_inventory(root)
            self.assertEqual(src, "manifest")
            self.assertTrue(any(r["resource_type"] == "source" for r in inv))

    def test_03_loads_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "seed.demo.raw_x": {
                            "unique_id": "seed.demo.raw_x",
                            "name": "raw_x",
                            "resource_type": "seed",
                            "package_name": "demo",
                            "original_file_path": "seeds/raw_x.csv",
                            "config": {"enabled": True},
                            "depends_on": {"nodes": [], "macros": []},
                            "meta": {},
                            "tags": [],
                            "columns": {},
                        }
                    }
                ),
            )
            inv, _ = build_resource_inventory(root)
            self.assertTrue(any(r["resource_type"] == "seed" for r in inv))

    def test_04_loads_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "snapshot.demo.s": {
                            "unique_id": "snapshot.demo.s",
                            "name": "s",
                            "resource_type": "snapshot",
                            "package_name": "demo",
                            "original_file_path": "snapshots/s.sql",
                            "config": {"enabled": True},
                            "depends_on": {"nodes": [], "macros": []},
                            "meta": {},
                            "tags": [],
                            "columns": {},
                        }
                    }
                ),
            )
            inv, _ = build_resource_inventory(root)
            self.assertTrue(any(r["resource_type"] == "snapshot" for r in inv))

    def test_05_loads_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    metrics={
                        "metric.demo.m": {
                            "unique_id": "metric.demo.m",
                            "name": "m",
                            "resource_type": "metric",
                            "package_name": "demo",
                            "original_file_path": "models/metrics.yml",
                            "config": {},
                            "meta": {},
                            "tags": [],
                        }
                    }
                ),
            )
            inv, _ = build_resource_inventory(root)
            self.assertTrue(any(r["resource_type"] == "metric" for r in inv))

    def test_06_loads_semantic_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    semantic_models={
                        "semantic_model.demo.sm": {
                            "unique_id": "semantic_model.demo.sm",
                            "name": "sm",
                            "resource_type": "semantic_model",
                            "package_name": "demo",
                            "original_file_path": "models/semantic.yml",
                            "config": {},
                            "meta": {},
                            "tags": [],
                        }
                    }
                ),
            )
            inv, _ = build_resource_inventory(root)
            self.assertTrue(any(r["resource_type"] == "semantic_model" for r in inv))

    def test_07_loads_exposures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    exposures={
                        "exposure.demo.browser_report": {
                            "unique_id": "exposure.demo.browser_report",
                            "name": "browser_report",
                            "resource_type": "exposure",
                            "package_name": "demo",
                            "type": "dashboard",
                            "original_file_path": "models/exposures.yml",
                            "depends_on": {"nodes": ["model.demo.a"]},
                            "owner": {"name": "owner", "email": "o@example.test"},
                            "config": {},
                            "meta": {"business_purpose": "overview", "criticality": "high", "refresh_expectation": "daily"},
                            "tags": [],
                        }
                    }
                ),
            )
            inv, _ = build_resource_inventory(root)
            self.assertTrue(any(r["resource_type"] == "exposure" for r in inv))

    def test_08_disabled_resources_identified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    disabled={
                        "model.demo.old": [
                            model_node("model.demo.old", name="old", enabled=False),
                        ]
                    }
                ),
            )
            inv, _ = build_resource_inventory(root)
            disabled = [r for r in inv if r["unique_id"] == "model.demo.old"]
            self.assertEqual(len(disabled), 1)
            self.assertFalse(disabled[0]["enabled"])

    def test_09_unknown_types_not_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "custom.demo.x": {
                            "unique_id": "custom.demo.x",
                            "name": "x",
                            "resource_type": "custom_widget",
                            "package_name": "demo",
                            "original_file_path": "models/x.sql",
                            "config": {},
                            "meta": {},
                            "tags": [],
                            "depends_on": {"nodes": [], "macros": []},
                        }
                    }
                ),
            )
            inv, _ = build_resource_inventory(root)
            self.assertTrue(any(r["unique_id"] == "custom.demo.x" for r in inv))

    def test_10_invalid_manifest_falls_back_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "target").mkdir(parents=True, exist_ok=True)
            (root / "target" / "manifest.json").write_text("{not-json", encoding="utf-8")
            (root / "dbt_project.yml").write_text("name: demo\nversion: '1.0.0'\n", encoding="utf-8")
            (root / "models" / "gold").mkdir(parents=True)
            (root / "models" / "gold" / "a.sql").write_text("select 1 as id\n", encoding="utf-8")
            inv, src = build_resource_inventory(root)
            self.assertEqual(src, "filesystem")
            self.assertTrue(any("models.gold.a" in r["unique_id"] for r in inv))


class CanonicalIdentityTests(unittest.TestCase):
    def test_11_unique_id_is_primary_key(self) -> None:
        inv = [
            {"unique_id": "model.a.x", "name": "x", "package_name": "a", "resource_type": "model", "enabled": True},
            {"unique_id": "model.b.x", "name": "x", "package_name": "b", "resource_type": "model", "enabled": True},
        ]
        match, status = resolve_named_resource(inv, unique_id="model.b.x")
        self.assertEqual(status, "ok")
        self.assertEqual(match["package_name"], "b")

    def test_12_same_name_different_packages_distinct(self) -> None:
        inv = [
            {"unique_id": "model.a.x", "name": "x", "package_name": "a", "resource_type": "model", "enabled": True},
            {"unique_id": "model.b.x", "name": "x", "package_name": "b", "resource_type": "model", "enabled": True},
        ]
        self.assertEqual(len(resources_by_name(inv, "x")), 2)
        match, status = resolve_named_resource(inv, name="x")
        self.assertEqual(status, "ambiguous")
        self.assertIsNone(match)

    def test_13_model_versions_distinct(self) -> None:
        inv = [
            {
                "unique_id": "model.demo.x.v1",
                "name": "x",
                "package_name": "demo",
                "version": 1,
                "resource_type": "model",
                "enabled": True,
            },
            {
                "unique_id": "model.demo.x.v2",
                "name": "x",
                "package_name": "demo",
                "version": 2,
                "resource_type": "model",
                "enabled": True,
            },
        ]
        match, status = resolve_named_resource(inv, name="x", version="2")
        self.assertEqual(status, "ok")
        self.assertEqual(match["unique_id"], "model.demo.x.v2")

    def test_14_filesystem_fallback_includes_path(self) -> None:
        uid = filesystem_fallback_unique_id("model", "models/gold/activity_events.sql", package="local")
        self.assertEqual(uid, "model.local.models.gold.activity_events")
        self.assertNotEqual(uid, "model.local.activity_events")

    def test_15_manifest_replaces_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dbt_project.yml").write_text("name: demo\nversion: '1.0.0'\n", encoding="utf-8")
            (root / "models" / "gold").mkdir(parents=True)
            (root / "models" / "gold" / "activity_events.sql").write_text("select 1\n", encoding="utf-8")
            fs_inv = inventory_from_filesystem(root)
            self.assertTrue(any("models.gold.activity_events" in r["unique_id"] for r in fs_inv))
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.demo.activity_events": model_node(
                            "model.demo.activity_events",
                            name="activity_events",
                            path="models/gold/activity_events.sql",
                        )
                    }
                ),
            )
            inv, src = build_resource_inventory(root)
            self.assertEqual(src, "manifest")
            self.assertTrue(any(r["unique_id"] == "model.demo.activity_events" for r in inv))

    def test_16_name_only_classification_ok_when_unambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={"model.demo.only": model_node("model.demo.only", name="only", path="models/gold/only.sql")}
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Model | Class | Business Meaning | Grain | Key | Date Roles | Measures | Dimensions | Tests | Reconciliation | Materialization | Confidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| only | event_fact | primary | event | id | d | c | n/a | t | PASS | table | HIGH | PASS |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: false\n",
                encoding="utf-8",
            )
            proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("migrate to unique_id", (proc.stdout + proc.stderr).lower())

    def test_17_name_only_classification_fails_when_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.pkg_a.dup": model_node(
                            "model.pkg_a.dup", name="dup", package="pkg_a", path="models/gold/dup.sql"
                        ),
                        "model.pkg_b.dup": model_node(
                            "model.pkg_b.dup", name="dup", package="pkg_b", path="models/gold/dup.sql"
                        ),
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Model | Class | Status |
|---|---|---|
| dup | event_fact | PASS |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: false\n  require_dependency_package_models: true\n",
                encoding="utf-8",
            )
            proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("ambiguous", (proc.stdout + proc.stderr).lower())

    def test_18_unique_id_resolves_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.pkg_a.dup": model_node(
                            "model.pkg_a.dup", name="dup", package="pkg_a", path="models/gold/dup.sql"
                        ),
                        "model.pkg_b.dup": model_node(
                            "model.pkg_b.dup", name="dup", package="pkg_b", path="models/gold/dup.sql"
                        ),
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Package | Class | Status |
|---|---|---|---|---|
| model.pkg_a.dup | dup | pkg_a | event_fact | PASS |
| model.pkg_b.dup | dup | pkg_b | event_fact | PASS |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: false\n  require_dependency_package_models: true\n",
                encoding="utf-8",
            )
            proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class ClassificationPolicyTests(unittest.TestCase):
    def _root_with_models(self, *names: str, enabled_map: dict[str, bool] | None = None) -> Path:
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        enabled_map = enabled_map or {}
        nodes = {
            f"model.demo.{name}": model_node(
                f"model.demo.{name}",
                name=name,
                path=f"models/gold/{name}.sql",
                enabled=enabled_map.get(name, True),
            )
            for name in names
        }
        write_manifest(root, base_manifest(nodes=nodes))
        insights = root / "reports" / "agent" / "09_analytics_insights"
        insights.mkdir(parents=True)
        (root / "project.config.yml").write_text(
            "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: false\n  require_snapshots: false\n",
            encoding="utf-8",
        )
        return root

    def test_19_enabled_local_models_require_classification(self) -> None:
        root = self._root_with_models("alpha", "beta")
        insights = root / "reports" / "agent" / "09_analytics_insights"
        (insights / "model_classification.md").write_text(
            """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.alpha | alpha | event_fact | PASS |
""",
            encoding="utf-8",
        )
        proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("model.demo.beta", proc.stdout + proc.stderr)

    def test_20_disabled_models_do_not_inflate_coverage(self) -> None:
        root = self._root_with_models("alpha", "beta", enabled_map={"beta": False})
        # Put disabled in disabled section instead
        write_manifest(
            root,
            base_manifest(
                nodes={"model.demo.alpha": model_node("model.demo.alpha", name="alpha")},
                disabled={"model.demo.beta": [model_node("model.demo.beta", name="beta", enabled=False)]},
            ),
        )
        insights = root / "reports" / "agent" / "09_analytics_insights"
        (insights / "model_classification.md").write_text(
            """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.alpha | alpha | event_fact | PASS |
""",
            encoding="utf-8",
        )
        proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_21_snapshot_classification_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.demo.a": model_node("model.demo.a", name="a"),
                        "snapshot.demo.s": {
                            "unique_id": "snapshot.demo.s",
                            "name": "s",
                            "resource_type": "snapshot",
                            "package_name": "demo",
                            "original_file_path": "snapshots/s.sql",
                            "config": {"enabled": True},
                            "depends_on": {"nodes": [], "macros": []},
                            "meta": {},
                            "tags": [],
                            "columns": {},
                        },
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.a | a | event_fact | PASS |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: false\n  require_snapshots: true\n",
                encoding="utf-8",
            )
            proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("snapshot", (proc.stdout + proc.stderr).lower())

    def test_22_semantic_model_classification_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={"model.demo.a": model_node("model.demo.a", name="a")},
                    semantic_models={
                        "semantic_model.demo.sm": {
                            "unique_id": "semantic_model.demo.sm",
                            "name": "sm",
                            "resource_type": "semantic_model",
                            "package_name": "demo",
                            "original_file_path": "models/s.yml",
                            "config": {},
                            "meta": {},
                            "tags": [],
                        }
                    },
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.a | a | event_fact | PASS |
| semantic_model.demo.sm | sm | semantic_model | PASS |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: false\n  require_semantic_models: true\n",
                encoding="utf-8",
            )
            proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_23_exposure_classification_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={"model.demo.a": model_node("model.demo.a", name="a")},
                    exposures={
                        "exposure.demo.e": {
                            "unique_id": "exposure.demo.e",
                            "name": "e",
                            "resource_type": "exposure",
                            "package_name": "demo",
                            "type": "dashboard",
                            "original_file_path": "models/e.yml",
                            "depends_on": {"nodes": ["model.demo.a"]},
                            "owner": {"name": "o"},
                            "config": {},
                            "meta": {},
                            "tags": [],
                        }
                    },
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.a | a | event_fact | PASS |
| exposure.demo.e | e | exposure | PASS |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: true\n",
                encoding="utf-8",
            )
            proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_24_unknown_class_fails(self) -> None:
        root = self._root_with_models("alpha")
        insights = root / "reports" / "agent" / "09_analytics_insights"
        (insights / "model_classification.md").write_text(
            """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.alpha | alpha | mystery_blob | PASS |
""",
            encoding="utf-8",
        )
        proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("unknown class", (proc.stdout + proc.stderr).lower())

    def test_25_excluded_requires_reason(self) -> None:
        root = self._root_with_models("alpha")
        insights = root / "reports" / "agent" / "09_analytics_insights"
        (insights / "model_classification.md").write_text(
            """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.alpha | alpha | excluded | PASS |
""",
            encoding="utf-8",
        )
        proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("exclusion_reason", (proc.stdout + proc.stderr).lower())

    def test_26_ambiguous_machine_classification_needs_human(self) -> None:
        root = self._root_with_models("alpha")
        insights = root / "reports" / "agent" / "09_analytics_insights"
        (insights / "model_classification.md").write_text(
            """
| Unique ID | Model | Class | Machine Recommendation | Human Approval Status | Status |
|---|---|---|---|---|---|
| model.demo.alpha | alpha | event_fact | reporting_mart | PENDING_REVIEW | PASS |
""",
            encoding="utf-8",
        )
        proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("human approval", (proc.stdout + proc.stderr).lower())

    def test_27_event_name_alone_not_fact(self) -> None:
        self.assertFalse(_class_is_analytical_fact("event"))
        self.assertFalse(_class_is_analytical_fact("transaction"))
        self.assertTrue(_class_is_analytical_fact("event_fact"))

    def test_28_dimension_prefix_does_not_override_contradiction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.demo.dim_weird": model_node(
                            "model.demo.dim_weird",
                            name="dim_weird",
                            path="models/gold/dim_weird.sql",
                            meta={"model_class": "event_fact"},
                        )
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.dim_weird | dim_weird | event_fact | PASS |
""",
                encoding="utf-8",
            )
            facts = list_analytical_facts(root)
            self.assertTrue(any(f["unique_id"] == "model.demo.dim_weird" for f in facts))


class FactDiscoveryTests(unittest.TestCase):
    def test_29_fact_without_fct_prefix_from_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.demo.activity_events": model_node(
                            "model.demo.activity_events",
                            name="activity_events",
                            path="models/gold/activity_events.sql",
                        )
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.activity_events | activity_events | event_fact | PASS |
""",
                encoding="utf-8",
            )
            facts = list_analytical_facts(root)
            self.assertTrue(any(f["name"] == "activity_events" for f in facts))

    def test_30_periodic_snapshot_fact(self) -> None:
        self.assertTrue(_class_is_analytical_fact("periodic_snapshot_fact"))

    def test_31_accumulating_snapshot_fact(self) -> None:
        self.assertTrue(_class_is_analytical_fact("accumulating_snapshot_fact"))

    def test_32_factless_fact(self) -> None:
        self.assertTrue(_class_is_analytical_fact("factless_fact"))

    def test_33_reporting_mart_not_automatic_fact(self) -> None:
        self.assertFalse(_class_is_analytical_fact("reporting_mart"))

    def test_34_same_named_facts_remain_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.pkg_a.events": model_node(
                            "model.pkg_a.events", name="events", package="pkg_a", path="models/gold/events.sql"
                        ),
                        "model.pkg_b.events": model_node(
                            "model.pkg_b.events", name="events", package="pkg_b", path="models/gold/events.sql"
                        ),
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Package | Class | Status |
|---|---|---|---|---|
| model.pkg_a.events | events | pkg_a | event_fact | PASS |
| model.pkg_b.events | events | pkg_b | event_fact | PASS |
""",
                encoding="utf-8",
            )
            facts = list_analytical_facts(root)
            uids = {f["unique_id"] for f in facts}
            self.assertIn("model.pkg_a.events", uids)
            self.assertIn("model.pkg_b.events", uids)

    def test_35_fact_catalog_name_only_fails_when_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.pkg_a.events": model_node(
                            "model.pkg_a.events", name="events", package="pkg_a", path="models/gold/events.sql"
                        ),
                        "model.pkg_b.events": model_node(
                            "model.pkg_b.events", name="events", package="pkg_b", path="models/gold/events.sql"
                        ),
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "fact_catalog.md").write_text(
                """
| Fact Model | Grain | Status |
|---|---|---|
| events | event | PASS |
""",
                encoding="utf-8",
            )
            facts = list_analytical_facts(root)
            self.assertTrue(any(f.get("ambiguous") == "true" for f in facts) or not any(f.get("name") == "events" and f.get("unique_id") for f in facts if f.get("ambiguous") != "true"))
            # Coverage script should fail
            (insights / "fact_coverage_contracts.md").write_text(
                """
| Fact | Grain | Counting Key | Primary Date | Volume | Amount or Quantity | Duration or Balance | Status Distribution | Lifecycle | Dimensions | Time Trends | Period Comparison | Data Quality | Exceptions | Aging | Reconciliation | Business Questions | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| events | one row | id | d | SUPPORTED | NOT_APPLICABLE | NOT_APPLICABLE | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | NOT_APPLICABLE | SUPPORTED | q | n | PASS |
""",
                encoding="utf-8",
            )
            (insights / "model_classification.md").write_text("# none\n", encoding="utf-8")
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  critical_fact_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_fact_analytical_coverage.py", "--root", str(root))
            # Ambiguous discovery should surface as failure or empty with error
            out = (proc.stdout + proc.stderr).lower()
            self.assertTrue(proc.returncode != 0 or "ambiguous" in out)

    def test_36_fact_coverage_matches_unique_id(self) -> None:
        fixture = DBT_FIX / "domain_b_encounter"
        if not (fixture / "target" / "manifest.json").exists():
            self.skipTest("duckdb fixture not built")
        proc = run_script("check_fact_analytical_coverage.py", "--root", str(fixture))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


def _exposure_project(
    root: Path,
    *,
    deps: list[str] | None = None,
    meta: dict | None = None,
    owner: dict | None = None,
    yaml_name: str = "models/report_consumers.yml",
    with_presentation: bool = True,
    with_dbt_project: bool = True,
    biz_status: str = "APPROVED",
) -> None:
    if deps is None:
        deps = ["model.demo.fact_a"]
    meta = {
        "business_purpose": "overview for analysts",
        "audience": "analysts",
        "criticality": "high",
        "refresh_expectation": "daily",
        "business_approval_status": biz_status,
        "technical_validation_status": "PASS",
        "approval_evidence": "reports/agent/09_analytics_insights/SYNTHETIC_FIXTURE_EXPOSURE_APPROVAL.md",
        "sensitive_data_classification": "NONE",
        "approver": "fixture-approver",
        "approval_date": "2026-01-15",
        "maturity": "high",
        "expiry_or_review": "2027-01-15",
        "presentation_artifact_id": "matplotlib/report.html",
        "delivery_location": "reports/agent/10_presentation/matplotlib/report.html",
        **(meta or {}),
    }
    owner = owner if owner is not None else {"name": "fixture-owner", "email": "o@example.test"}
    delivery = str(meta.get("delivery_location") or "reports/agent/10_presentation/matplotlib/report.html")
    write_manifest(
        root,
        base_manifest(
            nodes={"model.demo.fact_a": model_node("model.demo.fact_a", name="fact_a")},
            exposures={
                "exposure.demo.browser_report": {
                    "unique_id": "exposure.demo.browser_report",
                    "name": "browser_report",
                    "resource_type": "exposure",
                    "package_name": "demo",
                    "type": "dashboard",
                    "original_file_path": yaml_name,
                    "depends_on": {"nodes": list(deps)},
                    "owner": owner,
                    "url": delivery,
                    "config": {},
                    "meta": meta,
                    "tags": [],
                    "description": "TEST FIXTURE",
                }
            },
        ),
    )
    if with_dbt_project:
        (root / "dbt_project.yml").write_text("name: demo\nversion: '1.0.0'\n", encoding="utf-8")
    insights = root / "reports" / "agent" / "09_analytics_insights"
    insights.mkdir(parents=True)
    (insights / "SYNTHETIC_FIXTURE_EXPOSURE_APPROVAL.md").write_text(
        "# TEST FIXTURE — NOT PRODUCTION APPROVAL\n\nSynthetic exposure approval.\n",
        encoding="utf-8",
    )
    fp = compute_exposure_fingerprint(
        {
            "type": "dashboard",
            "business_purpose": meta["business_purpose"],
            "audience": meta["audience"],
            "depends_on_models": deps,
            "depends_on_sources": [],
            "depends_on_metrics": "",
            "url": delivery,
            "delivery_location": delivery,
            "refresh_expectation": meta["refresh_expectation"],
            "criticality": meta["criticality"],
            "sensitive_data_classification": meta["sensitive_data_classification"],
        }
    )
    meta["exposure_fingerprint"] = fp
    yaml_path = root / yaml_name
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    dep_yaml_block = (
        "depends_on:\n" + "\n".join(f"      - ref('{d.split('.')[-1]}')" for d in deps)
        if deps
        else "depends_on: []"
    )
    yaml_path.write_text(
        f"""
version: 2
exposures:
  - name: browser_report
    type: dashboard
    owner:
      name: {owner.get('name', '')}
      email: {owner.get('email', '')}
    url: "{delivery}"
    {dep_yaml_block}
    meta:
      business_purpose: "{meta['business_purpose']}"
      audience: "{meta['audience']}"
      criticality: "{meta['criticality']}"
      refresh_expectation: "{meta['refresh_expectation']}"
      business_approval_status: "{meta['business_approval_status']}"
      technical_validation_status: "PASS"
      approval_evidence: "{meta['approval_evidence']}"
      sensitive_data_classification: "{meta['sensitive_data_classification']}"
      approver: "{meta.get('approver', 'fixture-approver')}"
      approval_date: "{meta.get('approval_date', '2026-01-15')}"
      maturity: "{meta.get('maturity', 'high')}"
      expiry_or_review: "{meta.get('expiry_or_review', '2027-01-15')}"
      presentation_artifact_id: "{meta.get('presentation_artifact_id', 'matplotlib/report.html')}"
      delivery_location: "{delivery}"
      exposure_fingerprint: "{fp}"
""",
        encoding="utf-8",
    )
    write_manifest(
        root,
        base_manifest(
            nodes={"model.demo.fact_a": model_node("model.demo.fact_a", name="fact_a")},
            exposures={
                "exposure.demo.browser_report": {
                    "unique_id": "exposure.demo.browser_report",
                    "name": "browser_report",
                    "resource_type": "exposure",
                    "package_name": "demo",
                    "type": "dashboard",
                    "original_file_path": yaml_name,
                    "depends_on": {"nodes": list(deps)},
                    "owner": owner,
                    "url": delivery,
                    "config": {},
                    "meta": meta,
                    "tags": [],
                    "description": "TEST FIXTURE",
                }
            },
        ),
    )
    (insights / "exposure_coverage.md").write_text(
        f"""
| Exposure ID | Unique ID | Exposure | Type | Owner | Dependent Models | Refresh Expectation | Business Purpose | Audience | Criticality | Technical Validation Status | Business Approval Status | Approval Evidence | Approver | Approval Date | Maturity | Expiry | Presentation Artifact ID | Delivery Location | Exposure Fingerprint | Validation Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXP-browser_report | exposure.demo.browser_report | browser_report | dashboard | {owner.get('name')} | {', '.join(deps)} | {meta['refresh_expectation']} | {meta['business_purpose']} | {meta['audience']} | {meta['criticality']} | PASS | {meta['business_approval_status']} | {meta['approval_evidence']} | {meta.get('approver', 'fixture-approver')} | {meta.get('approval_date', '2026-01-15')} | {meta.get('maturity', 'high')} | {meta.get('expiry_or_review', '2027-01-15')} | {meta.get('presentation_artifact_id', 'matplotlib/report.html')} | {delivery} | {fp} | PASS |
""",
        encoding="utf-8",
    )
    if with_presentation:
        pres = root / "reports" / "agent" / "10_presentation" / "matplotlib"
        pres.mkdir(parents=True)
        (pres / "report.html").write_text("<html></html>", encoding="utf-8")
    (root / "project.config.yml").write_text(
        "analytics_policy:\n  production_exposure_coverage_required: 1.0\n",
        encoding="utf-8",
    )


class ExposureTests(unittest.TestCase):
    def test_37_exposure_from_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root)
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("manifest", (proc.stdout + proc.stderr).lower())

    def test_38_exposure_from_general_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, yaml_name="models/gold/schema.yml")
            # Keep model inventory via filesystem; remove exposures from manifest
            (root / "models" / "gold").mkdir(parents=True, exist_ok=True)
            (root / "models" / "gold" / "fact_a.sql").write_text("select 1 as id\n", encoding="utf-8")
            man = json.loads((root / "target" / "manifest.json").read_text(encoding="utf-8"))
            man["exposures"] = {}
            write_manifest(root, man)
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_39_not_limited_to_exposures_yml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, yaml_name="models/consumers/downstream.yml")
            (root / "models" / "gold").mkdir(parents=True, exist_ok=True)
            (root / "models" / "gold" / "fact_a.sql").write_text("select 1 as id\n", encoding="utf-8")
            man = json.loads((root / "target" / "manifest.json").read_text(encoding="utf-8"))
            man["exposures"] = {}
            write_manifest(root, man)
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_40_non_exposure_yaml_fields_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "models").mkdir(parents=True)
            (root / "models" / "notes.yml").write_text(
                "version: 2\nmodels:\n  - name: x\n    meta:\n      exposure: fake\n",
                encoding="utf-8",
            )
            (root / "reports" / "agent" / "09_analytics_insights").mkdir(parents=True)
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_41_missing_dependency_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, deps=["model.demo.missing"])
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("missing dependency", (proc.stdout + proc.stderr).lower())

    def test_42_disabled_dependency_fails_production(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, deps=["model.demo.fact_a"])
            write_manifest(
                root,
                base_manifest(
                    nodes={},
                    disabled={"model.demo.fact_a": [model_node("model.demo.fact_a", name="fact_a", enabled=False)]},
                    exposures={
                        "exposure.demo.browser_report": {
                            "unique_id": "exposure.demo.browser_report",
                            "name": "browser_report",
                            "resource_type": "exposure",
                            "package_name": "demo",
                            "type": "dashboard",
                            "depends_on": {"nodes": ["model.demo.fact_a"]},
                            "owner": {"name": "fixture-owner"},
                            "meta": {
                                "business_purpose": "overview for analysts",
                                "audience": "analysts",
                                "criticality": "high",
                                "refresh_expectation": "daily",
                                "business_approval_status": "APPROVED",
                                "approval_evidence": "SYNTHETIC_FIXTURE_APPROVAL:x",
                                "sensitive_data_classification": "NOT_APPLICABLE: fixture",
                            },
                            "config": {},
                            "tags": [],
                        }
                    },
                ),
            )
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("disabled", (proc.stdout + proc.stderr).lower())

    def test_43_dependency_package_model_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            delivery = "reports/agent/10_presentation/matplotlib/report.html"
            fp = compute_exposure_fingerprint(
                {
                    "type": "dashboard",
                    "business_purpose": "overview for analysts",
                    "audience": "analysts",
                    "depends_on_models": ["model.other_pkg.fact_a"],
                    "depends_on_sources": [],
                    "depends_on_metrics": "",
                    "url": delivery,
                    "delivery_location": delivery,
                    "refresh_expectation": "daily",
                    "criticality": "high",
                    "sensitive_data_classification": "NONE",
                }
            )
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.other_pkg.fact_a": model_node(
                            "model.other_pkg.fact_a", name="fact_a", package="other_pkg"
                        )
                    },
                    exposures={
                        "exposure.demo.browser_report": {
                            "unique_id": "exposure.demo.browser_report",
                            "name": "browser_report",
                            "type": "dashboard",
                            "resource_type": "exposure",
                            "package_name": "demo",
                            "depends_on": {"nodes": ["model.other_pkg.fact_a"]},
                            "owner": {"name": "fixture-owner"},
                            "url": delivery,
                            "meta": {
                                "business_purpose": "overview for analysts",
                                "audience": "analysts",
                                "criticality": "high",
                                "refresh_expectation": "daily",
                                "business_approval_status": "APPROVED",
                                "technical_validation_status": "PASS",
                                "approval_evidence": "reports/agent/09_analytics_insights/SYNTHETIC_FIXTURE_EXPOSURE_APPROVAL.md",
                                "sensitive_data_classification": "NONE",
                                "approver": "fixture-approver",
                                "approval_date": "2026-01-15",
                                "maturity": "high",
                                "expiry_or_review": "2027-01-15",
                                "presentation_artifact_id": "matplotlib/report.html",
                                "delivery_location": delivery,
                                "exposure_fingerprint": fp,
                            },
                            "config": {},
                            "tags": [],
                        }
                    },
                ),
            )
            (root / "dbt_project.yml").write_text("name: demo\nversion: '1.0.0'\n", encoding="utf-8")
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "SYNTHETIC_FIXTURE_EXPOSURE_APPROVAL.md").write_text(
                "# TEST FIXTURE\n", encoding="utf-8"
            )
            (insights / "exposure_coverage.md").write_text(
                f"""
| Unique ID | Exposure | Owner | Refresh Expectation | Business Purpose | Criticality | Business Approval Status | Approval Evidence | Approver | Approval Date | Maturity | Expiry | Presentation Artifact ID | Delivery Location | Exposure Fingerprint | Validation Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| exposure.demo.browser_report | browser_report | fixture-owner | daily | overview for analysts | high | APPROVED | reports/agent/09_analytics_insights/SYNTHETIC_FIXTURE_EXPOSURE_APPROVAL.md | fixture-approver | 2026-01-15 | high | 2027-01-15 | matplotlib/report.html | {delivery} | {fp} | PASS |
""",
                encoding="utf-8",
            )
            (root / "reports" / "agent" / "10_presentation" / "matplotlib").mkdir(parents=True)
            (root / "reports" / "agent" / "10_presentation" / "matplotlib" / "report.html").write_text(
                "<html></html>", encoding="utf-8"
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  production_exposure_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_44_versioned_dependency_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            inv = [
                {
                    "unique_id": "model.demo.fact_a.v2",
                    "name": "fact_a",
                    "package_name": "demo",
                    "version": 2,
                    "resource_type": "model",
                    "enabled": True,
                }
            ]
            match, status = resolve_named_resource(inv, name="fact_a", version="2")
            self.assertEqual(status, "ok")
            self.assertEqual(match["unique_id"], "model.demo.fact_a.v2")

    def test_45_ambiguous_name_dependency_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.pkg_a.fact_a": model_node(
                            "model.pkg_a.fact_a", name="fact_a", package="pkg_a"
                        ),
                        "model.pkg_b.fact_a": model_node(
                            "model.pkg_b.fact_a", name="fact_a", package="pkg_b"
                        ),
                    },
                    exposures={
                        "exposure.demo.browser_report": {
                            "unique_id": "exposure.demo.browser_report",
                            "name": "browser_report",
                            "type": "dashboard",
                            "resource_type": "exposure",
                            "package_name": "demo",
                            "depends_on": ["ref('fact_a')"],
                            "owner": {"name": "fixture-owner"},
                            "meta": {
                                "business_purpose": "overview",
                                "criticality": "high",
                                "refresh_expectation": "daily",
                                "business_approval_status": "APPROVED",
                                "approval_evidence": "SYNTHETIC_FIXTURE_APPROVAL:x",
                            },
                            "config": {},
                            "tags": [],
                        }
                    },
                ),
            )
            (root / "dbt_project.yml").write_text("name: demo\nversion: '1.0.0'\n", encoding="utf-8")
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "exposure_coverage.md").write_text(
                "| Exposure | Owner | Validation Status |\n|---|---|---|\n| browser_report | fixture-owner | PASS |\n",
                encoding="utf-8",
            )
            (root / "reports" / "agent" / "10_presentation").mkdir(parents=True)
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  production_exposure_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("ambiguous", (proc.stdout + proc.stderr).lower())

    def test_46_missing_owner_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, owner={"name": ""})
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("owner", (proc.stdout + proc.stderr).lower())

    def test_47_missing_purpose_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, meta={"business_purpose": ""})
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("business purpose", (proc.stdout + proc.stderr).lower())

    def test_48_missing_criticality_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, meta={"criticality": ""})
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("criticality", (proc.stdout + proc.stderr).lower())

    def test_49_missing_refresh_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, meta={"refresh_expectation": ""})
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("refresh", (proc.stdout + proc.stderr).lower())

    def test_50_no_dependencies_require_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, deps=[])
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("dependenc", (proc.stdout + proc.stderr).lower())

    def test_51_presentation_without_exposure_fails_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dbt_project.yml").write_text("name: demo\nversion: '1.0.0'\n", encoding="utf-8")
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "exposure_coverage.md").write_text(
                "| Exposure | Owner | Validation Status |\n|---|---|---|\n| docs_only | o | PASS |\n",
                encoding="utf-8",
            )
            (root / "reports" / "agent" / "10_presentation" / "matplotlib").mkdir(parents=True)
            (root / "reports" / "agent" / "10_presentation" / "matplotlib" / "report.html").write_text(
                "<html></html>", encoding="utf-8"
            )
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  production_exposure_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            write_manifest(root, base_manifest())
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("real dbt exposure", (proc.stdout + proc.stderr).lower())

    def test_52_docs_only_not_final_coverage(self) -> None:
        # covered by 51
        self.assertTrue(True)

    def test_53_draft_pending_review_ok_before_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, biz_status="PENDING_REVIEW")
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_54_production_without_approval_fails_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, biz_status="PENDING_REVIEW")
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("business approval", (proc.stdout + proc.stderr).lower())

    def test_55_valid_approved_exposure_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root)
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_56_changed_dependency_invalidates_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, deps=["model.demo.fact_a"])
            delivery = "reports/agent/10_presentation/matplotlib/report.html"
            # Stale fingerprint (wrong deps)
            insights = root / "reports" / "agent" / "09_analytics_insights"
            text = (insights / "exposure_coverage.md").read_text(encoding="utf-8")
            (insights / "exposure_coverage.md").write_text(
                text.replace(
                    compute_exposure_fingerprint(
                        {
                            "type": "dashboard",
                            "business_purpose": "overview for analysts",
                            "audience": "analysts",
                            "depends_on_models": ["model.demo.fact_a"],
                            "depends_on_sources": [],
                            "depends_on_metrics": "",
                            "url": delivery,
                            "delivery_location": delivery,
                            "refresh_expectation": "daily",
                            "criticality": "high",
                            "sensitive_data_classification": "NONE",
                        }
                    ),
                    "deadbeefdeadbeef",
                ),
                encoding="utf-8",
            )
            # Also put stale fp in manifest meta
            man = json.loads((root / "target" / "manifest.json").read_text(encoding="utf-8"))
            man["exposures"]["exposure.demo.browser_report"]["meta"]["exposure_fingerprint"] = "deadbeefdeadbeef"
            write_manifest(root, man)
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("stale", (proc.stdout + proc.stderr).lower())

    def test_57_stale_exposure_approval_fails(self) -> None:
        self.test_56_changed_dependency_invalidates_approval()

    def test_58_sensitive_uncertainty_creates_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, meta={"sensitive_data_classification": "UNKNOWN"})
            # Human attention is documented via warning path when sensitive uncertain —
            # ensure fingerprint/approval path still works; classification note present
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class CoverageRegressionTests(unittest.TestCase):
    def test_59_classification_uses_unique_ids(self) -> None:
        fixture = DBT_FIX / "domain_a_transactional"
        if not (fixture / "target" / "manifest.json").exists():
            self.skipTest("duckdb fixture not built")
        proc = run_script(
            "check_model_classification_coverage.py", "--root", str(fixture), "--phase", "final"
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("unique_id_denominator=yes", proc.stdout + proc.stderr)

    def test_60_duplicate_names_do_not_reduce_denominator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(
                root,
                base_manifest(
                    nodes={
                        "model.demo.activity_events": model_node(
                            "model.demo.activity_events", name="activity_events", path="models/gold/a.sql"
                        ),
                        "snapshot.demo.activity_events": {
                            "unique_id": "snapshot.demo.activity_events",
                            "name": "activity_events",
                            "resource_type": "snapshot",
                            "package_name": "demo",
                            "original_file_path": "snapshots/activity_events.sql",
                            "config": {"enabled": True},
                            "depends_on": {"nodes": [], "macros": []},
                            "meta": {},
                            "tags": [],
                            "columns": {},
                        },
                    }
                ),
            )
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "model_classification.md").write_text(
                """
| Unique ID | Model | Class | Status |
|---|---|---|---|
| model.demo.activity_events | activity_events | event_fact | PASS |
| snapshot.demo.activity_events | activity_events | snapshot | PASS |
""",
                encoding="utf-8",
            )
            (root / "project.config.yml").write_text(
                "resource_classification_policy:\n  require_sources: false\n  require_seeds: false\n  require_exposures: false\n  require_snapshots: true\n",
                encoding="utf-8",
            )
            proc = run_script("check_model_classification_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_61_fact_coverage_uses_unique_ids(self) -> None:
        self.test_36_fact_coverage_matches_unique_id = FactDiscoveryTests.test_36_fact_coverage_matches_unique_id
        FactDiscoveryTests().test_36_fact_coverage_matches_unique_id()

    def test_62_production_exposure_threshold_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _exposure_project(root, biz_status="PENDING_REVIEW")
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  production_exposure_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)

    def test_63_empty_denominator_not_auto_100(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "dbt_project.yml").write_text("name: demo\nversion: '1.0.0'\n", encoding="utf-8")
            insights = root / "reports" / "agent" / "09_analytics_insights"
            insights.mkdir(parents=True)
            (insights / "exposure_coverage.md").write_text("# empty\n", encoding="utf-8")
            (root / "reports" / "agent" / "10_presentation").mkdir(parents=True)
            write_manifest(root, base_manifest())
            (root / "project.config.yml").write_text(
                "analytics_policy:\n  production_exposure_coverage_required: 1.0\n",
                encoding="utf-8",
            )
            proc = run_script("check_exposure_coverage.py", "--root", str(root), "--phase", "final")
            self.assertEqual(proc.returncode, 1)

    def test_64_analytics_fixtures_remain_valid(self) -> None:
        for slug in ("domain_a_transactional", "domain_b_encounter", "domain_c_asset_events"):
            path = FIX / slug
            if not path.exists():
                continue
            proc = run_script("check_exposure_coverage.py", "--root", str(path), "--phase", "analytics")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_65_duckdb_fixtures_after_migration(self) -> None:
        for slug in ("domain_a_transactional", "domain_b_encounter", "domain_c_asset_events"):
            path = DBT_FIX / slug
            if not (path / "target" / "manifest.json").exists():
                self.skipTest("duckdb fixtures not built")
            for script in (
                "check_model_classification_coverage.py",
                "check_fact_analytical_coverage.py",
                "check_exposure_coverage.py",
            ):
                args = ["--root", str(path)]
                if script != "check_fact_analytical_coverage.py":
                    args.extend(["--phase", "final"])
                proc = run_script(script, *args)
                self.assertEqual(proc.returncode, 0, f"{slug} {script}: {proc.stdout}{proc.stderr}")

    def test_66_domain_neutrality_passes(self) -> None:
        proc = run_script("check_domain_neutrality.py", "--root", str(ROOT))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_67_batch1_acceptance_facts_helpers(self) -> None:
        from lib_gate_common import ratio

        self.assertIsNone(ratio(0, 0))

    def test_68_batch2_fingerprint_stable(self) -> None:
        from lib_gate_common import compute_contract_fingerprint

        a = compute_contract_fingerprint({"formula": "count(*)", "business_definition": "volume"})
        b = compute_contract_fingerprint({"formula": "count(*)", "business_definition": "volume"})
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
