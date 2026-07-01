#!/usr/bin/env python3
"""Generate a Power BI PBIP/TMDL project from the bundled neutral template.

This command is the public entrypoint for agents. It creates the PBIP shell,
regenerates project-specific IDs through the template copier, validates the
result, and records which planning inputs were available. Agents still add
project-specific tables, relationships, measures, pages, and visuals from
validated dbt gold and semantic evidence after this scaffold is created.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import create_powerbi_pbip_from_template


PLANNING_FILES = [
    "reports/agent/dashboard_spec.md",
    "reports/agent/kpi_catalog.md",
    "reports/agent/reporting_catalog.md",
    "reports/agent/analytics_insight_report.md",
    "reports/agent/reporting_readiness_scorecard.md",
    "reports/agent/insight_backlog.md",
    "target/manifest.json",
    "target/catalog.json",
    "target/semantic_manifest.json",
]


def write_generation_report(project_root: Path, pbip_folder: Path, planning_status: list[tuple[str, bool]]) -> None:
    reports_dir = project_root / "reports" / "agent"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "powerbi_template_generation_report.md"
    lines = [
        "# Power BI Template Generation Report",
        "",
        "## Generated Artifact",
        f"- PBIP folder: `{pbip_folder}`",
        "- Source template: `assets/powerbi/pbip_template/`",
        "- Generator: `scripts/generate_powerbi_pbip.py`",
        "",
        "## Planning Inputs",
        "| File | Status |",
        "|---|---|",
    ]
    for relative_path, exists in planning_status:
        lines.append(f"| `{relative_path}` | {'FOUND' if exists else 'MISSING'} |")
    lines.extend(
        [
            "",
            "## Notes",
            "- This step creates a neutral PBIP shell only.",
            "- The generator does not create linguistic metadata by default; bundled template linguistic metadata is preserved and validated.",
            "- Never write JSON such as `{ \"Version\": \"1.0.0\" }` into XML-typed linguistic metadata. If metadata content type cannot be guaranteed, omit linguistic metadata.",
            "- Project-specific tables, relationships, measures, report pages, visuals, and source partitions must be generated from validated dbt gold/semantic evidence before presentation delivery.",
            "- Do not mark presentation complete until `scripts/validate_powerbi_pbip.py`, Power BI Modeling MCP when available, and Power BI Desktop open validation when available are recorded in `reports/agent/presentation_report.md`.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def run_validator(repo_root: Path, pbip_folder: Path) -> int:
    validator = repo_root / "scripts" / "validate_powerbi_pbip.py"
    if not validator.exists():
        print(f"WARN: validator not found: {validator}", file=sys.stderr)
        return 0
    completed = subprocess.run(
        [sys.executable, str(validator), str(pbip_folder)],
        cwd=str(repo_root),
        check=False,
    )
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Power BI PBIP project from dbt presentation planning artifacts")
    parser.add_argument("--name", required=True, help="Filesystem-safe PBIP project base name")
    parser.add_argument("--output-dir", type=Path, help="Parent output folder. Defaults to <project-root>/reports/powerbi")
    parser.add_argument("--display-name", help="Human-facing report display name")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="dbt project root or workspace root")
    parser.add_argument("--skip-validation", action="store_true", help="Create the PBIP shell without running static validation")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    project_root = args.project_root.resolve()
    output_dir = (args.output_dir or (project_root / "reports" / "powerbi")).resolve()
    template_root = repo_root / "assets" / "powerbi" / "pbip_template"

    create_args = argparse.Namespace(
        name=args.name,
        output_dir=output_dir,
        display_name=args.display_name,
        template_root=template_root,
    )
    project_name = create_args.name.strip()
    if any(char in project_name for char in "\\/:*?\"<>| "):
        print("ERROR: --name must be a filesystem-safe base name without spaces or path separators", file=sys.stderr)
        return 2
    display_name = create_args.display_name or create_powerbi_pbip_from_template.slug_to_title(project_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    pbip_path = create_powerbi_pbip_from_template.copy_template(template_root, output_dir / project_name, project_name, display_name)
    pbip_folder = pbip_path.parent
    print(f"Created PBIP project: {pbip_path}")

    planning_status = []
    for relative_path in PLANNING_FILES:
        planning_status.append((relative_path, (project_root / relative_path).exists()))
    write_generation_report(project_root, pbip_folder, planning_status)

    if args.skip_validation:
        print("Skipped static validation by request")
        return 0
    return run_validator(repo_root, pbip_folder)


if __name__ == "__main__":
    raise SystemExit(main())
