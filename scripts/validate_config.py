#!/usr/bin/env python3
"""Validate agentic dbt pipeline skill configuration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


REQUIRED_KEYS = [
    ("project", "name"),
    ("project", "root"),
    ("project", "profile"),
    ("database", "adapter"),
    ("database", "host"),
    ("database", "port"),
    ("database", "dbname"),
    ("database", "target_schema"),
    ("source", "name"),
    ("source", "schema"),
    ("schema_isolation", "source_read_only"),
    ("schema_isolation", "allow_dbt_outputs_in_source_schema"),
    ("agents", "schema"),
    ("agents", "github_secret"),
    ("git", "branch"),
]

FORBIDDEN_CONFIG_KEYS = {
    "password",
    "token",
    "private_key",
    "api_key",
}

REQUIRED_GITIGNORE = {
    ".venv/",
    "target/",
    "logs/",
    "dbt_packages/",
    ".env",
    "profiles.yml",
}

REQUIRED_REPO_FILES = {
    "requirements.txt",
    "scripts/create_report_skeleton.py",
    "scripts/run_acceptance_gate.py",
    "scripts/check_layer_proof_coverage.py",
    "scripts/check_requirement_traceability.py",
    "scripts/verify_metric_reconciliation.py",
    "scripts/validate_local_web_report.py",
    "scripts/validate_kpi_proofs.py",
    "docs/kpi_proof_standards.md",
    "agents/dbt-verifier-agent.md",
    "references/evidence-driven-dbt-process.md",
    "references/kpi-definition-contract.md",
    "references/metric-verification-checklist.md",
    "references/discovery-approval-checklist.md",
    "references/requirements-traceability-matrix.md",
    "references/layer-verification-ledger.md",
    "references/independent-verification-governance.md",
    "scripts/check_discovery_artifacts.py",
    "scripts/check_software_prerequisites.py",
    "scripts/compare_discovery_scope.py",
    "references/discovery-artifacts.md",
    "references/discovery-status-vocabulary.md",
    "references/table-inclusion-priority-filter.md",
    "references/software-prerequisites.md",
    "references/profile-credential-keys.md",
    "references/gold-dimension-completeness.md",
    "references/reporting-coverage-requirements.md",
    "scripts/check_profile_credential_keys.py",
    "scripts/check_gold_star_shape.py",
    "scripts/check_analytics_coverage.py",
    "scripts/check_presentation_coverage.py",
    "scripts/check_privacy_opt_out.py",
    "templates/reports/00_discovery/core_profile.json",
    "templates/reports/00_discovery/discovery_raw.json",
    "templates/reports/00_discovery/first_pass_scope.json",
    "templates/reports/00_discovery/README.md",
    "templates/reports/root/HUMAN_ATTENTION_BOARD.md",
    "templates/reports/root/KPI_GAP_REGISTER.md",
    "templates/reports/root/HUMAN_VERIFICATION_GUIDE.md",
    "references/human-attention-reporting.md",
    "references/kpi-gap-and-stakeholder-warnings.md",
    "references/stakeholder-layer-and-presentation-guide.md",
    "templates/reports/root/LAYER_VERIFICATION_LEDGER.md",
    "templates/reports/root/KPI_DEFINITION_CONTRACTS.md",
    "templates/reports/root/METRIC_VERIFICATION_MATRIX.md",
    "templates/reports/09_analytics_insights/business_process_catalog.md",
    "templates/reports/09_analytics_insights/fact_catalog.md",
    "templates/reports/09_analytics_insights/dimension_catalog.md",
    "templates/reports/09_analytics_insights/reporting_catalog.md",
    "templates/reports/09_analytics_insights/dashboard_spec.md",
    "templates/reports/09_analytics_insights/insight_backlog.md",
    "templates/reports/09_analytics_insights/reporting_readiness_scorecard.md",
    "docs/how-to-verify-generated-project.md",
    "templates/dbt/tests/README.md",
    ".github/workflows/dbt_acceptance_gate.yml",
}

FORBIDDEN_ENV_KEY_PARTS = (
    "PASSWORD",
    "TOKEN",
    "PRIVATE_KEY",
    "SECRET",
    "API_KEY",
)

REQUIRED_ENV_EXAMPLE_KEYS = {
    "DBT_DOMAIN",
    "DBT_BUSINESS_DESCRIPTION",
    "DBT_PROFILE_NAME",
    "DBT_SOURCE_SCHEMA",
}

PLACEHOLDER_ENV_EXAMPLE_KEYS = {
    "DBT_DOMAIN",
    "DBT_BUSINESS_DESCRIPTION",
    "DBT_PROFILE_NAME",
    "DBT_SOURCE_SCHEMA",
}


def get_nested(data: dict, path: tuple[str, ...]):
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def find_forbidden_keys(value, prefix=""):
    findings = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            child_path = f"{prefix}.{key}" if prefix else str(key)
            if key_text in FORBIDDEN_CONFIG_KEYS:
                findings.append(child_path)
            findings.extend(find_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_forbidden_keys(child, f"{prefix}[{index}]"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=".",
        help="Skill repository root. Defaults to current directory.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / "project.config.yml"
    gitignore_path = root / ".gitignore"
    env_example_path = root / ".env.example"

    errors = []

    for relative_path in sorted(REQUIRED_REPO_FILES):
        if not (root / relative_path).exists():
            errors.append(f"Missing required repo file: {relative_path}")

    if not config_path.exists():
        errors.append("Missing project.config.yml")
    else:
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"project.config.yml is invalid YAML: {exc}")
            config = None

        if isinstance(config, dict):
            for path in REQUIRED_KEYS:
                if get_nested(config, path) in (None, ""):
                    errors.append(f"Missing required config key: {'.'.join(path)}")

            forbidden = find_forbidden_keys(config)
            if forbidden:
                errors.append(
                    "Config contains secret-like keys that should not be stored: "
                    + ", ".join(forbidden)
                )

            source_schema = str(get_nested(config, ("source", "schema")) or "").lower()
            target_schema = str(
                get_nested(config, ("database", "target_schema")) or ""
            ).lower()
            if source_schema and target_schema and source_schema == target_schema:
                errors.append(
                    "database.target_schema must not equal source.schema; "
                    "source schemas are read-only inputs"
                )

            if get_nested(config, ("schema_isolation", "source_read_only")) is not True:
                errors.append("schema_isolation.source_read_only must be true")

            if (
                get_nested(
                    config, ("schema_isolation", "allow_dbt_outputs_in_source_schema")
                )
                is not False
            ):
                errors.append(
                    "schema_isolation.allow_dbt_outputs_in_source_schema must be false"
                )

            packages = config.get("packages")
            if isinstance(packages, list):
                for index, package in enumerate(packages, start=1):
                    if not isinstance(package, dict):
                        errors.append(f"packages[{index}] must be a mapping")
                        continue
                    name = package.get("package") or package.get("git") or f"#{index}"
                    version = str(package.get("version") or "").strip()
                    if not version:
                        errors.append(
                            f"Package {name} must pin an exact or range-bounded version"
                        )
                    if version.lower() in {"latest", "*"}:
                        errors.append(
                            f"Package {name} must not use floating version {version!r}"
                        )
            else:
                errors.append("project.config.yml packages must be a list")
        elif config is not None:
            errors.append("project.config.yml must contain a YAML mapping at top level")

    if not gitignore_path.exists():
        errors.append("Missing .gitignore")
    else:
        gitignore_entries = {
            line.strip()
            for line in gitignore_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        missing_entries = sorted(REQUIRED_GITIGNORE - gitignore_entries)
        if missing_entries:
            errors.append("Missing .gitignore entries: " + ", ".join(missing_entries))

    if env_example_path.exists():
        env_keys = set()
        for line_number, line in enumerate(
            env_example_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip().upper()
            value = value.strip()
            env_keys.add(key)
            if any(part in key for part in FORBIDDEN_ENV_KEY_PARTS):
                errors.append(
                    f".env.example contains secret-like key on line {line_number}: {key}"
                )
            if key in PLACEHOLDER_ENV_EXAMPLE_KEYS and value and not (
                value.startswith("<") and value.endswith(">")
            ):
                errors.append(
                    f".env.example key {key} should be blank or use a placeholder value like <...>"
                )

        missing_env_keys = sorted(REQUIRED_ENV_EXAMPLE_KEYS - env_keys)
        if missing_env_keys:
            errors.append(
                ".env.example is missing required keys: " + ", ".join(missing_env_keys)
            )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Config validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
