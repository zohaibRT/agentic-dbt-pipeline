#!/usr/bin/env python3
"""Check that a dbt profile target has a credential key without printing secrets.

dbt commonly stores the warehouse password under `pass`. Some connectors look for
`password`. This script reports which non-secret key names exist so agents do not
false-block discovery when only `pass` is present.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any


try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


SECRET_KEYS = ("pass", "password", "token", "key", "private_key", "client_secret")
ENV_VAR_RE = re.compile(r"env_var\(\s*['\"]([^'\"]+)['\"]")


def profiles_path() -> Path:
    override = os.environ.get("DBT_PROFILES_DIR")
    if override:
        return Path(override) / "profiles.yml"
    return Path.home() / ".dbt" / "profiles.yml"


def load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: python -m pip install pyyaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"{path} did not parse as a YAML mapping")
    return data


def resolve_target(profile: dict[str, Any], target_name: str | None) -> tuple[str, dict[str, Any]]:
    outputs = profile.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise RuntimeError("profile has no outputs")
    selected = target_name or profile.get("target") or next(iter(outputs))
    target = outputs.get(selected)
    if not isinstance(target, dict):
        raise RuntimeError(f"target '{selected}' is missing or invalid")
    return str(selected), target


def credential_findings(target: dict[str, Any]) -> dict[str, Any]:
    present_keys = [key for key in ("pass", "password") if key in target]
    findings: dict[str, Any] = {
        "present_keys": present_keys,
        "env_var_refs": [],
        "has_direct_value": False,
        "has_env_var_ref": False,
    }
    for key in present_keys:
        value = target.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        match = ENV_VAR_RE.search(text)
        if match:
            findings["has_env_var_ref"] = True
            findings["env_var_refs"].append({"key": key, "env_var": match.group(1)})
        elif "{{" not in text:
            findings["has_direct_value"] = True
        else:
            # Other Jinja; treat as configured reference without expanding.
            findings["has_env_var_ref"] = True
            findings["env_var_refs"].append({"key": key, "env_var": "(jinja-ref)"})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="dbt profile name from profiles.yml")
    parser.add_argument("--target", default=None, help="Optional output target name")
    parser.add_argument(
        "--profiles-file",
        type=Path,
        default=None,
        help="Optional explicit profiles.yml path",
    )
    args = parser.parse_args()

    path = args.profiles_file.resolve() if args.profiles_file else profiles_path()
    if not path.exists():
        print(f"FAIL | profiles file not found: {path}")
        print("Ask the user to create ~/.dbt/profiles.yml. Do not request the password in chat.")
        return 1

    try:
        data = load_yaml(path)
        if args.profile not in data:
            print(f"FAIL | profile not found: {args.profile}")
            print(f"Available profiles: {', '.join(sorted(k for k in data if not str(k).startswith('.')))}")
            return 1
        profile = data[args.profile]
        if not isinstance(profile, dict):
            print(f"FAIL | profile '{args.profile}' is invalid")
            return 1
        target_name, target = resolve_target(profile, args.target)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL | could not read profile safely: {exc}")
        return 1

    adapter = str(target.get("type") or "unknown")
    findings = credential_findings(target)
    print(f"Profile: {args.profile}")
    print(f"Target: {target_name}")
    print(f"Adapter: {adapter}")
    print(f"Credential keys present (names only): {', '.join(findings['present_keys']) or '(none)'}")
    if findings["env_var_refs"]:
        refs = ", ".join(
            f"{item['key']}->env:{item['env_var']}" for item in findings["env_var_refs"]
        )
        print(f"Env-var style refs detected (names only): {refs}")

    if findings["has_direct_value"] or findings["has_env_var_ref"]:
        mapped = "pass" if "pass" in findings["present_keys"] else "password"
        print(
            "PASS | credential key found. "
            f"For direct connectors, map profile field `{mapped}` to the connector password parameter. "
            "Never print the secret value."
        )
        if "pass" in findings["present_keys"] and "password" not in findings["present_keys"]:
            print(
                "NOTE | dbt uses `pass`. Do not report 'password missing' only because the key is not named `password`."
            )
        return 0

    print(
        "FAIL | no usable `pass` or `password` key found on the selected target. "
        "Ask the user to add dbt's `pass` field in ~/.dbt/profiles.yml or choose another profile. "
        "Do not ask them to paste the password in chat."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
