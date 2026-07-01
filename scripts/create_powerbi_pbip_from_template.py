#!/usr/bin/env python3
"""Create a neutral Power BI PBIP project from the bundled template."""

from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from pathlib import Path


PLACEHOLDER_FILES = {
    ".pbip",
    ".json",
    ".pbir",
    ".platform",
    ".tmdl",
    ".md",
}


def slug_to_title(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("-", "_").split("_") if part)


def replace_text(path: Path, replacements: dict[str, str]) -> None:
    if path.suffix not in PLACEHOLDER_FILES and path.name not in {".platform", "README.md"}:
        return
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8", newline="\n")


def copy_template(template_root: Path, output_root: Path, project_name: str, display_name: str) -> Path:
    if output_root.exists():
        raise FileExistsError(f"{output_root} already exists; choose an empty output folder")

    shutil.copytree(template_root, output_root)

    replacements = {
        "__PBIP_PROJECT_NAME__": project_name,
        "__REPORT_DISPLAY_NAME__": display_name,
        "__SEMANTIC_DISPLAY_NAME__": f"{display_name} Semantic Model",
        "__REPORT_LOGICAL_ID__": str(uuid.uuid4()),
        "__SEMANTIC_LOGICAL_ID__": str(uuid.uuid4()),
        "__METRICS_LINEAGE_TAG__": str(uuid.uuid4()),
    }

    for path in sorted(output_root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if path.is_file():
            replace_text(path, replacements)
        if "Template" in path.name:
            target = path.with_name(path.name.replace("Template", project_name))
            path.rename(target)

    return output_root / f"{project_name}.pbip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Power BI PBIP project from the bundled neutral template")
    parser.add_argument("--name", required=True, help="PBIP project folder/file base name, for example hospital_analytics")
    parser.add_argument("--output-dir", required=True, type=Path, help="Parent folder where the PBIP project folder will be created")
    parser.add_argument("--display-name", help="Human-facing report display name")
    parser.add_argument(
        "--template-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets" / "powerbi" / "pbip_template",
        help="Template root. Defaults to the bundled neutral PBIP template.",
    )
    args = parser.parse_args()

    project_name = args.name.strip()
    if not project_name:
        print("ERROR: --name must not be empty", file=sys.stderr)
        return 2
    if any(char in project_name for char in "\\/:*?\"<>| "):
        print("ERROR: --name must be a filesystem-safe base name without spaces or path separators", file=sys.stderr)
        return 2

    template_root = args.template_root.resolve()
    if not template_root.exists():
        print(f"ERROR: template root not found: {template_root}", file=sys.stderr)
        return 2

    output_root = (args.output_dir.resolve() / project_name)
    display_name = args.display_name or slug_to_title(project_name)
    pbip_path = copy_template(template_root, output_root, project_name, display_name)
    print(f"Created PBIP project: {pbip_path}")
    print("Next: add project-specific tables, relationships, measures, pages, visuals, and run scripts/validate_powerbi_pbip.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
