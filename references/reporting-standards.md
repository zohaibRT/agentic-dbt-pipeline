# Reporting Standards

Use this before writing discovery reports, phase reports, analytics insight reporting files, presentation reports, final handoffs, dashboard designs, and Power BI report plans.

For analytics insight reporting design rules and deliverables, read [analytics-insight-reporting.md](analytics-insight-reporting.md). This file defines the five report pillars, Matplotlib visual standards, and Power BI canvas standards; analytics insight reporting decides what is useful to show, and the presentation layer implements the approved design.

## Core rule

Every report must be actionable. Do not only list data, files, models, or charts. A good report tells the data engineer and business user what happened, why it matters, what changed, what is uncertain, and what should happen next.

When a section is not supported by validated data, include it as `Not available yet` or `Deferred` with the reason. Do not invent targets, benchmarks, root causes, or recommendations that are not supported by evidence.

## Five report pillars

Every report should include these pillars when relevant:

| Pillar | Purpose | Required content |
|---|---|---|
| Context and strategy | Explain why the work or numbers matter | Objective, business process, audience, scope, baseline, target, benchmark, or why the metric exists |
| Key performance indicators | Show the current state | Primary measures, leading indicators, lagging indicators, business definition, source model, grain, filters, time field, and caveats |
| Trend analysis and variance | Show direction and gap | Historical trend, period comparison, target variance, baseline variance, month-over-month, year-over-year, year to date, or last 12 months when supported |
| Insights and attribution | Explain why performance changed | Drivers, root-cause hypotheses, anomalies, outliers, segment changes, data quality explanations, and confidence level |
| Recommendations and next steps | Drive action | Actionable next steps, owner or decision needed when known, risk, resource need, blocked item, and next approval checkpoint |

## Report behavior

- Start with a short executive summary before details.
- Separate evidence from interpretation.
- Use validated metrics and source-backed findings first.
- Treat key performance indicator reconciliation, first failing layer, and cardinality/grain proof as part of the metric evidence.
- State targets and benchmarks only when provided, discovered, or safely derived from approved baseline logic.
- When no target exists, recommend that the data engineer or business owner define one.
- Include both leading and lagging indicators when the data supports them.
- Use `kpi_discovery_matrix.md` to separate supported, uncertain, and blocked metrics before selecting report content.
- Include variance from target or baseline when a target or baseline exists.
- Include anomaly and outlier notes when distributions, trends, or data validation show unusual values.
- Include limitations and confidence notes so users can trust what is proven and see what is still uncertain.
- Use full wording in headings and summaries.

## Presentation report behavior

For business-facing presentation layers, the report design must show more than key performance indicator cards and trends. It should include:

- Context and strategy page or section.
- Executive Overview page.
- Key performance indicator scorecard with leading and lagging measures when supported.
- Trends and variance page.
- Driver, segmentation, attribution, or root-cause page when dimensions support it.
- Exceptions, anomalies, and data quality page when issues exist.
- Recommendations and next steps page or section.

If targets, benchmarks, attribution dimensions, or next-step owners are missing, include a visible `Needs business input` note instead of leaving the pillar out silently.

## Matplotlib visual standard

Use this standard for every generated Matplotlib refreshable web report unless the user provides a stronger company template. Official reference: [Matplotlib User Guide](https://matplotlib.org/stable/users/index).

Every Matplotlib chart must be readable, business-facing, SQL-verified, and rendered through a polished local web report:

| Rule | Requirement |
|---|---|
| Figure structure | One clear business question per figure; use `subplots` or subplot mosaics for multi-panel pages |
| Labels | Title, axis labels, units, and source/caveat notes on every chart |
| Colors | Use a comfortable colorful palette across charts, KPI cards, and HTML tabs; distinguish categories and states with intentional color while keeping readable contrast |
| Visual comfort | Soft backgrounds, white content cards, readable font sizes, generous spacing, light gridlines, and crisp SVG/browser rendering |
| Theme files | Document palette and styling in `report_theme.md`; apply shared constants from `report_theme.py` |
| Images | Optional approved logo or header image in `report.html` when brand assets are provided |
| Dates | Explicit date parsing and readable time-axis formatting for trend visuals |
| Legends | Clear series meaning; avoid duplicate or unreadable legends |
| Live output | Serve charts through `serve_report.py` as Matplotlib SVG/HTML endpoints or approved browser-native charts from refreshed JSON |
| Static output | Optional only; save SVG/PNG files under `figures/` for snapshots or exports, clearly labeled as not automatically updating |
| Browser review | Build a rich local `report.html` shell with colorful classified tabs, summary cards, chart cards, captions, caveats, validation status, refresh timestamp/control, and provide `open_report.bat` or `serve_report.py --open` |
| Page modules | Organize generation code in `report_pages/` by business tab, not one unstructured script |
| Labels | Use business names from dimensions, mappings, and `label_dictionary.md`; never raw codes on chart axes or legends |
| Validation | Every plotted aggregate must reconcile to SQL in `sql_verification/` before the chart is marked trusted |
| Coverage | Every recommended measure, metric, and key performance indicator from analytics insight catalogs must appear in `kpi_figure_coverage.md` as `RENDERED`, `BLOCKED`, or `DEFERRED` |
| Prerequisites | Install missing `matplotlib`, `numpy`, and `pandas` before chart generation; record commands in `requirements-matplotlib.txt` |
| Style | Use one shared colorful theme via `report_theme.py`, rcParams, or a style sheet so outputs look like one comfortable report system |

Do not use decorative chart junk, unlabeled axes, raw warehouse codes on business-facing charts, default gray-only matplotlib styling, unstyled browser-default HTML, PNG-only delivery, loose image-only delivery, or synthetic trend lines without evidence.

## Power BI canvas standard

Use this fixed layout standard for every generated Power BI report unless the user provides a stronger company template.

Every Power BI report must feel like an interactive dashboard canvas, not a static table dump. Each main report page should include these elements when supported:

| Layer | Required content | Purpose |
|---|---|---|
| Header and navigation | Report title, page title, company or project branding when available, last refreshed timestamp, reset filters button, and page navigation buttons | Keep the user oriented and make the report feel consistent |
| Key performance indicator summary | The most important executive key performance indicators near the top, usually three to five for readability; all other validated key performance indicators belong in a dedicated key performance indicator details area, scorecard page, or Report Information page | Show current state quickly without hiding useful metrics |
| Interactive slicers | Date range plus important dimensions such as region, department, category, product, provider, customer, status, or channel when available | Let users filter without cluttering the page |
| Trends and comparisons | Line or area charts for time series, bar or column charts for category comparisons, and drill-down when a date hierarchy or hierarchy dimension exists | Show direction, variance, and drivers |
| Detail layer | Matrix or detail table at the bottom of the page or on a separate details page, with conditional formatting for outliers when useful | Support operational investigation |
| Tooltips and drill-throughs | Report page tooltips and drill-through pages for important entities or data points when the model supports safe row-level investigation | Keep pages clean while preserving depth |

Default top-to-bottom canvas order:

1. Header/navigation bar.
2. Key performance indicator card row.
3. Primary trends and comparison visuals.
4. Secondary driver, attribution, or segmentation visuals.
5. Matrix/detail table or drill-through entry point.

## Visual Theme And Color Standard

Do not use default Power BI styling as the final report design. Every generated presentation layer must use a deliberate, professional visual theme that supports fast reading, hierarchy, and accessibility.

Use these rules unless the user provides brand guidelines:

- Choose a restrained enterprise palette with a neutral background, dark readable text, one primary accent, one secondary accent, and one warning/exception color.
- Avoid one-note palettes where the entire report is only blue, purple, beige, brown, or gray.
- Use color to encode meaning consistently: positive/pass, warning, failure, selected state, muted context, and categorical series.
- Keep key performance indicator cards visually prominent, but do not overuse saturated colors on every card.
- Use muted gridlines, clear labels, and sufficient contrast for text, axes, legends, and data labels.
- Use conditional formatting in matrices and exception visuals when it helps users detect outliers or risk.
- Use consistent page headers, navigation treatment, slicer styling, card styling, chart colors, and detail table formatting across every page.
- If company branding, logo, or brand colors are available and approved, use them. If not, create a neutral professional theme and document it in the presentation report.
- Document theme choices, color meanings, and any accessibility limitations in `reports/agent/10_presentation/presentation_report.md`, or the legacy presentation report path when the project uses the flat layout.

Recommended generic palette:

| Purpose | Color |
|---|---|
| Background | `#F7F8FA` |
| Surface | `#FFFFFF` |
| Primary text | `#1F2933` |
| Secondary text | `#5B677A` |
| Primary accent | `#2563EB` |
| Secondary accent | `#0F766E` |
| Positive | `#16A34A` |
| Warning | `#D97706` |
| Failure | `#DC2626` |
| Neutral series | `#64748B` |

## Key performance indicator coverage

The agent must analyze the maximum useful key performance indicators the validated model can support. Do not limit analysis to only three to five metrics.

Use this split:

- Executive key performance indicator row: show the highest-priority three to five measures that a business user should see first.
- Supporting key performance indicators: include additional useful measures in a scorecard page, details section, tooltip, drill-through, or Report Information page when they are supported and not overwhelming.
- Deferred key performance indicators: list metrics that are useful but blocked by missing definitions, missing targets, empty facts, ambiguous grain, or privacy concerns.

For every proposed or implemented key performance indicator, keep the definition visible somewhere in the report experience or companion report: business meaning, source model, grain, numerator, denominator, filters, time field, caveat, and validation status.

Key performance indicator coverage must come from the domain-neutral discovery framework, not from hardcoded domain templates. Prioritize `HIGH` confidence and approved `MEDIUM` confidence metrics only when reconciliation and cardinality proof are available. Put `LOW`, `BLOCKED`, and unreconciled metrics in the deferred key performance indicator list with the exact missing business rule, mapping, grain, source data, cardinality proof, reconciliation proof, or privacy decision.

## Report Information page

Every generated Power BI report must include a Report Information, Report Settings, or About This Report page unless the user explicitly asks to omit it.

The Report Information page should include:

- Report purpose, audience, and business process.
- Data source and dbt gold/mart schema used, without secrets.
- Refresh timestamp and refresh notes.
- Page list and what each page is for.
- Key performance indicator definitions and formulas in user-friendly wording.
- Slicer/filter definitions and default filter behavior.
- Metric caveats, data quality notes, expected-empty facts, and known limitations.
- Privacy handling and hidden technical fields.
- Relationship/grain summary for the semantic model.
- Validation summary and link/path to `reports/agent/10_presentation/presentation_report.md`.
- Open decisions, missing targets or benchmarks, and recommended next steps.

Power BI page rules:

- Use native page navigation buttons for multi-page reports.
- Include a Report Information or Report Settings page in navigation.
- Include a reset filters button on main report pages when supported by the chosen PBIP/report format.
- Include a last refreshed timestamp measure or equivalent metadata visual when the model can support it.
- Keep primary slicers visible and put secondary filters in the filter pane or a dedicated filter area.
- Use line or area charts for time series, not pie-heavy trend pages.
- Use bar or column charts for ranked comparison across categories.
- Use matrix visuals for operational detail and apply conditional formatting when it helps users spot exceptions.
- Add report page tooltips for important charts when the PBIP/report format supports them.
- Add drill-through pages for important entities such as customer, patient, provider, product, location, department, account, or order when safe and useful.
- Hide technical fields from the report canvas and report view unless they are needed for investigation.
- Document any missing layout element in `reports/agent/10_presentation/presentation_report.md` with the reason, such as unsupported by current PBIP generation, missing dimension, or privacy risk.

## Required report sections

Use these headings, or equivalent full wording, in reports and handoffs:

```markdown
## Context and Strategy

## Key Performance Indicators

## Trend Analysis and Variance

## Insights and Attribution

## Recommendations and Next Steps
```

For technical phase reports, these sections may be brief, but they must still orient the user:

- Context and Strategy: why the phase exists and what business or data-engineering goal it supports.
- Key Performance Indicators: implemented or deferred metrics, or `Not applicable for this technical phase`.
- Trend Analysis and Variance: validation movement, row-count movement, or `Not applicable yet`.
- Insights and Attribution: what the checks suggest about data behavior, blockers, or quality.
- Recommendations and Next Steps: the next checkpoint and exact approval needed.
