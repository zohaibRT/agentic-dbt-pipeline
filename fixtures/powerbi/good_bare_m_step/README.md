# Neutral Power BI PBIP Template

This template is bundled so the skill does not depend on finding a local project such as IHMS, ShopSphere, or Hospital on the user's machine.

Use it only as a structural starting point for approved Power BI PBIP/TMDL presentation layers. It intentionally contains no business tables, relationships, source connections, pages, measures, or branding beyond a neutral report information page.

Generation rules:

- Copy with `scripts/create_powerbi_pbip_from_template.py`.
- Regenerate report and semantic model logical IDs.
- Regenerate TMDL lineage tags.
- Replace placeholders before validation.
- Add project-specific tables, relationships, measures, pages, and visuals from validated dbt gold/semantic evidence.
- Run `scripts/validate_powerbi_pbip.py` after generation and after every modification.
- Use local PBIP projects only as optional references after showing the exact path and getting user approval.
