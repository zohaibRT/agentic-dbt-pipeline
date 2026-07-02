#!/usr/bin/env python3
"""Detect the locally installed Power BI Desktop executable and version.

The presentation layer uses this as evidence only. It does not prove a PBIP
opens; Desktop or MCP validation still has to run when available.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def candidate_paths() -> list[Path]:
    candidates: list[Path] = []
    env_vars = ["LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"]
    suffixes = [
        "Microsoft Power BI Desktop/bin/PBIDesktop.exe",
        "Microsoft Power BI Desktop/bin/PBIDesktopStore.exe",
        "WindowsApps/Microsoft.MicrosoftPowerBIDesktop_8wekyb3d8bbwe/bin/PBIDesktop.exe",
    ]
    for env_var in env_vars:
        root = os.environ.get(env_var)
        if not root:
            continue
        for suffix in suffixes:
            candidates.append(Path(root) / suffix)
    return candidates


def powershell_file_version(path: Path) -> str | None:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"(Get-Item -LiteralPath {json.dumps(str(path))}).VersionInfo.ProductVersion",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        return None
    version = completed.stdout.strip()
    return version or None


def appx_versions() -> list[dict[str, str]]:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-AppxPackage -Name Microsoft.MicrosoftPowerBIDesktop | "
        "Select-Object Name, Version, InstallLocation | ConvertTo-Json -Compress",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    results: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        results.append({key: str(item.get(key, "")) for key in ["Name", "Version", "InstallLocation"]})
    return results


def main() -> int:
    detections: list[dict[str, str]] = []
    for path in candidate_paths():
        if not path.exists():
            continue
        version = powershell_file_version(path)
        detections.append(
            {
                "source": "file",
                "path": str(path),
                "product_version": version or "",
            }
        )

    for item in appx_versions():
        detections.append(
            {
                "source": "appx",
                "path": item.get("InstallLocation", ""),
                "product_version": item.get("Version", ""),
            }
        )

    result = {
        "found": bool(detections),
        "detections": detections,
        "note": "Use this for version evidence only; still run Desktop open validation when available.",
    }
    print(json.dumps(result, indent=2))
    return 0 if detections else 1


if __name__ == "__main__":
    raise SystemExit(main())
