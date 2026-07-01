# Power BI Official Project Documentation

Use this when creating, validating, or troubleshooting Power BI PBIP/PBIR/TMDL presentation artifacts.

## Official Microsoft References

- Power BI Desktop developer mode documentation: https://learn.microsoft.com/en-us/power-bi/developer/projects/
- Power BI Desktop projects overview: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview
- Power BI Desktop project semantic model folder: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset
- Power BI Desktop project report folder: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report

These pages are the source of truth for PBIP project layout, report folder layout, semantic model folder layout, required files, local-only files, and current preview limitations. When internet access is available and Power BI behavior is uncertain, check these Microsoft Learn pages before inventing structure.

## Rules To Apply

- PBIP is a preview feature. Treat generated artifacts as requiring validation in the current Power BI Desktop version.
- A Power BI project normally contains a `.pbip` file, a `.Report/` folder, and a `.SemanticModel/` folder.
- The `.pbip` file is a shortcut/pointer to a report folder. Opening it should open the targeted report and related semantic model when the report has a valid relative semantic model reference.
- The Report folder and SemanticModel folder are separate artifacts. Do not create a semantic-model-only project when the user approved a report.
- Keep local/cache files out of generated and committed artifacts, especially `.pbi/localSettings.json` and `.pbi/cache.abf`.
- Use UTF-8 without BOM for externally edited project files.
- Keep paths short enough for Windows Power BI Desktop path-length limits.
- Be cautious when editing project files outside Power BI Desktop; Microsoft warns unsupported external edits can prevent Desktop from opening the project.
- Do not edit or rely on undocumented preview files as stable generation targets unless a validated template and Desktop open test prove they work.
- Automatic date tables created by Power BI Desktop should not be generated or modified by the agent. Prefer an explicit dbt date dimension or validated time spine.
- Report Linguistic Schema is not supported with Power BI projects. Do not generate unsupported report linguistic schema files.
- Any Desktop open validation result must say which file was opened: `.pbip` or Report `definition.pbir`.

## How This Skill Uses The Docs

The bundled template and validator encode a safe subset of the documented PBIP/PBIR/TMDL project format. Agents should:

1. Start from `assets/powerbi/pbip_template/`.
2. Use `scripts/generate_powerbi_pbip.py`.
3. Validate with `scripts/validate_powerbi_pbip.py`.
4. Use Power BI Modeling Model Context Protocol validation when available.
5. Open in Power BI Desktop when available.
6. If Microsoft Learn has changed the supported format, update the template and validator instead of patching one generated project only.

## Report In Presentation Report

When Power BI is generated, `reports/agent/presentation_report.md` must record:

- Whether official Microsoft docs were checked or not checked.
- Which official doc URLs were used when checked.
- Any doc-driven constraints applied.
- Any reason a Microsoft-documented element was skipped, such as unsupported by current generator, no Desktop available, or blocked by validation.
