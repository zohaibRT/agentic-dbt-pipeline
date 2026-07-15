# Matplotlib Presentation Layer

Use this when the user approves a presentation layer and chooses **Matplotlib** as the presentation technology, or when the user approves the default presentation layer without naming another technology.

Also read [presentation-layer.md](presentation-layer.md), [analytics-insight-reporting.md](analytics-insight-reporting.md), [universal-analytics-framework.md](universal-analytics-framework.md), [report-artifact-organization.md](report-artifact-organization.md), [reporting-standards.md](reporting-standards.md), [kpi-definitions.md](kpi-definitions.md), [metric-verification.md](metric-verification.md), and [mapping-seeds.md](mapping-seeds.md) when code-to-label mappings are needed.

Official documentation: [Matplotlib User Guide](https://matplotlib.org/stable/users/index)

## Purpose

Generate a validated, business-facing, browser-viewable analytics report from approved gold/marts data and analytics insight reporting files. Matplotlib is the **Python visual rendering engine**, but the final default presentation deliverable is a refreshable rich tabbed web report, not a folder of loose images. Matplotlib is the **recommended default** presentation technology because it is:

- Version-controlled and reproducible in the dbt project repository
- Runnable without Power BI Desktop or proprietary report project files
- Easy to validate with SQL-backed Python scripts
- Suitable for executive summaries, trend pages, breakdown charts, operational detail views, and tabbed web report pages
- Viewable in a browser through a local refreshable web report with classified tabs/pages, plus optional static export and Windows launchers

Matplotlib outputs are not a replacement for governed semantic models. They consume the same trusted key performance indicators and page scope defined during analytics insight reporting.

## Refreshable browser report

Matplotlib delivery is not complete with PNG files alone, and PNGs embedded in HTML are not the default. The agent must produce a **refreshable, richly styled web report** so a data engineer or business user can review current values from the validated data layer.

Default behavior:

- `serve_report.py` starts a local web server and queries or reloads validated data on page load, browser refresh, or an approved auto-refresh interval.
- Charts are rendered as inline SVG/HTML fragments from Python/Matplotlib, or as browser-native charts from refreshed JSON data when another approved charting library is used.
- PNG files are optional exports for download, documentation, or offline snapshots only. Do not use PNG as the only chart rendering path.
- `report.html` is the web shell and can be served by `serve_report.py`; a fully static `report.html` is acceptable only as an explicit export/snapshot mode.

Why this matters: Matplotlib does not execute inside the browser. To reflect changed values automatically, the browser must either call a Python-backed endpoint that re-runs the queries and renders fresh SVG/HTML, or use a browser chart library that redraws from refreshed JSON data.

### Primary review experience

| Artifact | Purpose |
|---|---|
| `serve_report.py` | Starts the local refreshable web report server, runs read-only data refresh, and serves chart endpoints or refreshed HTML |
| `report.html` | Main browser shell with tabbed navigation, chart grouping, key performance indicator summaries, blocked/deferred notes, and report metadata |
| `open_report.bat` | Windows launcher that starts `serve_report.py` and opens the local report URL |
| `open_report.sh` | Optional Unix launcher for the same behavior |
| `generate_report.py` | Optional static export command that can create offline HTML/SVG/PNG snapshots, never the only live path |
| `data_cache/` | Optional local cache of query results used only when live warehouse access is unavailable or explicitly requested |

Expected user flow on Windows:

1. Double-click `reports/agent/10_presentation/matplotlib/open_report.bat`, or run `python reports/agent/10_presentation/matplotlib/serve_report.py`.
2. The browser opens the local report URL, usually `http://127.0.0.1:<port>/`.
3. Refresh the browser, click the refresh control, or wait for the approved auto-refresh interval to see changed values after the underlying data changes.

Do not require Power BI, Jupyter, or a notebook server for normal review.

### HTML report structure

`report.html` must use a clear multi-tab layout aligned to `dashboard_spec.md` and the five reporting pillars when supported. Do not deliver a single long image gallery when multiple pages or business sections exist.

Default tab or section order:

| Tab / section | Content |
|---|---|
| Overview | Report purpose, audience, data source, refresh time, caveats, and navigation |
| Executive key performance indicators | Trusted strategic key performance indicators from `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, and `kpi_catalog.md` (top 5–8 cards) |
| **All Measures** | **Required when gold has 3+ facts:** live board of **50+** measure values (cards and/or table) from `measure_catalog.md` via warehouse SQL — not catalog counts alone |
| **All Metrics** | **Required when gold has 3+ facts:** live board of **50+** metric values from `metric_catalog.md` |
| Trends and variance | Time showcase, period comparisons, and variance views |
| Operations and activity | Volumes, statuses, workflow movement, and operational metrics |
| Segmentation and performance | Department, product, provider, location, channel, or other approved dimensions |
| Financial or value | Amount, revenue, payment, cost, or value views when supported |
| Exceptions and data quality | Coverage gaps, blocked visuals, mapping gaps, and validation notes |
| Blocked and deferred | Items from `insight_backlog.md` and unreconciled metrics |
| Report information | Metric definitions, filters, privacy handling, SQL verification summary |

Do **not** ship an Overview with only eight executive cards when `measure_catalog.md` lists 50+. Humans must open the browser and *see* the full measure/metric surface. See Rule 5b in [reporting-coverage-requirements.md](reporting-coverage-requirements.md).

Each tab or section must:

- Show business-facing titles, not technical file names
- Render current chart output from live endpoints, inline SVG, or approved browser-native chart components
- Include rich HTML context: short page purpose, key questions answered, key metric cards where relevant, figure captions, caveats, and validation status
- List the metrics included on that page
- Mark unsupported or blocked content visibly instead of hiding it

`serve_report.py` must keep the browser view in sync with current query results and `kpi_figure_coverage.md`. If `generate_report.py` is provided for static exports, it must be clearly labeled as snapshot/export mode.

### Rich web report requirements

The web report must feel like a polished review surface, not a plain file index.

Required `report.html` behavior:

- Use a sticky or prominent header with report title, generated timestamp, data source summary, and validation status.
- Use clickable tabs for multiple report pages. A sectioned layout is acceptable only when there is one page.
- Use colorful active/inactive tab styling from `report_theme.py`; do not use browser default tab/button styling.
- Use key performance indicator cards, chart cards, callout panels, and blocked/deferred panels with consistent spacing and rounded corners.
- Render current charts inside chart cards with readable captions and SQL proof links or references.
- Include a visible refresh timestamp and a refresh control when the report is served locally.
- Include a Report Information tab with purpose, audience, data source, refresh details, key performance indicator definitions, caveats, privacy handling, and validation summary.
- Use responsive CSS so the report remains readable on laptop and wide desktop screens.
- Avoid plain unstyled HTML tables as the main experience; use tables only for definitions, coverage, or detail sections where useful.

### Chart rendering modes

Use this priority order:

1. **Live Matplotlib SVG**: Query current data in Python, render Matplotlib figures to inline SVG with `FigureCanvasSVG` or equivalent, and serve the SVG/HTML fragment to the browser.
2. **Browser-native charts from refreshed JSON**: Use Plotly, Chart.js, Vega-Lite, or another approved library only when the project needs richer browser interactivity. Data must still come from validated SQL queries or approved cached results.
3. **Static export**: Generate SVG/PNG/PDF snapshots only for offline handoff or documentation. Static exports must not be presented as automatically updating.

Do not use base64 PNGs or direct PNG files as the primary web report rendering path. PNG is acceptable only as a download/export fallback, an email/report snapshot, or when SVG/browser-native rendering is blocked and the blocker is documented.

### Refresh behavior

The report must document and implement one refresh mode:

| Mode | Behavior |
|---|---|
| Manual refresh | Browser refresh button or in-page refresh control re-runs read-only queries and redraws charts |
| Timed refresh | Approved interval refreshes JSON/SVG endpoints and updates the page |
| Snapshot export | Static `report.html` and image files generated at a point in time; clearly labeled as not live |

Default to manual refresh. Use timed refresh only when the data engineer approves the interval and warehouse cost is acceptable.

## When to recommend Matplotlib

Recommend Matplotlib as the default when:

- Analytics insight reporting is complete and trusted metrics exist
- The user wants a portable Python-backed web report with optional static exports checked into the repository
- The team prefers Python-based reporting over a business intelligence desktop workflow
- The project needs fast, testable visualization without PBIP/TMDL complexity

Recommend Power BI instead when the user explicitly needs interactive slicers, drill-through, governed enterprise semantic models, or a PBIP handoff. See [powerbi-thin-model-template.md](powerbi-thin-model-template.md).

## Inputs from analytics insight reporting

| Analytics insight output | Matplotlib use |
|---|---|
| `reports/agent/09_analytics_insights/dashboard_spec.md` | Page and figure plan |
| `reports/agent/09_analytics_insights/kpis/measure_catalog.md` | Raw and supporting measures for summary panels and detail charts |
| `reports/agent/09_analytics_insights/kpis/metric_catalog.md` | Contextual metrics that should become charts or summary values |
| `reports/agent/09_analytics_insights/kpis/kpi_discovery_matrix.md` | Recommended key performance indicator candidates, confidence, and blocked/deferred reasoning |
| `reports/agent/09_analytics_insights/kpis/kpi_reconciliation_report.md` | Proof that trusted key performance indicators reconcile across layers |
| `reports/agent/09_analytics_insights/kpis/kpi_catalog.md` | Trusted strategic key performance indicators and formulas |
| `reports/agent/KPI_DEFINITION_CONTRACTS.md` | Key performance indicator business contracts, approval status, expected result, actual result, and proof file |
| `reports/agent/METRIC_VERIFICATION_MATRIX.md` | Measure, metric, and key performance indicator reconciliation from source proof to mart, semantic, and presentation proof |
| `reports/agent/09_analytics_insights/business_process_catalog.md` | Business areas, business processes, source evidence, facts, entities, and recommended report pages |
| `reports/agent/09_analytics_insights/fact_catalog.md` | Fact/event models, grains, row counts, date/status/amount fields, supported measures, and relationship safety |
| `reports/agent/09_analytics_insights/dimension_catalog.md` | Safe slicers, labels, drill-down fields, related facts, and privacy status |
| `reports/agent/09_analytics_insights/reporting_catalog.md` | Report/page scope |
| `reports/agent/09_analytics_insights/insight_backlog.md` | Deferred or blocked visuals |
| `reports/agent/09_analytics_insights/reporting_readiness_scorecard.md` | Readiness gate |
| `reports/agent/09_analytics_insights/analytics_insight_report.md` | Business rationale |

Do not invent pages, metrics, or chart types that bypass analytics insight outputs unless the user explicitly overrides them. Use the business process, fact, and dimension catalogs to choose page tabs, slicers, drill-downs, captions, and detail sections.

## Key performance indicator and measure coverage

Matplotlib must include **all recommended analytics insight outputs**, not only a small executive subset.

Build a coverage table in `report_spec.md` that maps every recommended measure and key performance indicator to a Matplotlib output or an explicit blocked/deferred note.

| Source file | Matplotlib coverage rule |
|---|---|
| `measure_catalog.md` | Include every measure marked `recommended`, `trusted`, or equivalent supported status in at least one summary value, trend visual, distribution visual, or supporting detail panel |
| `metric_catalog.md` | Include every metric marked `recommended`, `trusted`, or equivalent supported status in at least one chart, summary value, or matrix-style figure |
| `kpi_discovery_matrix.md` | Include every row with `HIGH` confidence or user-approved `MEDIUM` confidence in the figure plan; mark `LOW`, `BLOCKED`, and unreconciled rows as deferred with the reason from the matrix |
| `kpi_catalog.md` | Include every trusted strategic key performance indicator in the executive summary area, a dedicated key performance indicator page, or a clearly labeled supporting panel |
| `KPI_DEFINITION_CONTRACTS.md` | Include only key performance indicators with acceptable approval and verification status; render `FAIL` or `BLOCKED` rows only as blocked/deferred notes |
| `METRIC_VERIFICATION_MATRIX.md` | Use expected result, actual result, difference, and proof file references to validate and caption rendered values |
| `dashboard_spec.md` | Every approved page and visual in the dashboard spec must have a matching figure group or blocked note |
| `insight_backlog.md` | Deferred or blocked items must appear in the coverage table as `BLOCKED` or `DEFERRED`; do not omit them silently |

Required coverage artifacts:

| File | Purpose |
|---|---|
| `kpi_figure_coverage.md` | Row-by-row mapping from measure/metric/key performance indicator name to figure file, chart type, SQL proof file, and status (`RENDERED`, `BLOCKED`, `DEFERRED`) |
| `report_spec.md` | Page plan plus the same coverage rules in summary form |

Hard coverage rules:

- **Every key performance indicator in `kpi_catalog.md` and `KPI_DEFINITION_CONTRACTS.md`** must appear in `kpi_figure_coverage.md` as `RENDERED`, `BLOCKED`, or `DEFERRED`.
- Do not skip a recommended measure or metric just because the visual would be repetitive; combine related items on one page when appropriate, but keep every `kpi_catalog.md` row visible in `kpi_figure_coverage.md`.
- Executive summary pages should prioritize `kpi_catalog.md` items that also pass `KPI_DEFINITION_CONTRACTS.md` and `METRIC_VERIFICATION_MATRIX.md`, but supporting measures from `measure_catalog.md` and `metric_catalog.md` must still be represented somewhere in the pack when they are marked recommended or trusted.
- Standard time showcase visuals from [presentation-layer.md](presentation-layer.md) still apply when validated date fields exist.

## Python environment and dependency installation

Before generating figures, verify the Matplotlib stack is available in the active Python environment. If any required package is missing, install it and record the command in `README.md` and `reports/agent/10_presentation/presentation_report.md`.

Required packages:

| Package | Role |
|---|---|
| `matplotlib` | Python chart rendering to inline SVG/HTML and optional static exports |
| `numpy` | Numeric arrays used by Matplotlib |
| `pandas` | Tabular query results and chart-ready data frames |
| `flask` or standard library HTTP server | Local refreshable report server when live browser refresh is approved; prefer the standard library for simple projects, Flask for route/API clarity |
| Optional browser chart library | Plotly, Chart.js, Vega-Lite, or similar only when explicitly useful for interactivity; document why it was added |
| Warehouse/query helper | Use the project's existing dbt profile adapter client when available, such as `psycopg2` or `psycopg2-binary` for PostgreSQL/Redshift, `snowflake-connector-python` for Snowflake, `google-cloud-bigquery` for BigQuery, or `databricks-sql-connector` for Databricks |

### Connection rule (no hardcodes)

Presentation Python must **not** hardcode:

- passwords / `pass` / tokens
- host, user, or database string defaults copied from another machine
- absolute paths like `C:\codebase\...` or `/Users/...`
- schema names copied from a different `agentic_dbt_*` project

Resolve connection from:

1. `DBT_PROFILE_NAME` in workspace `.env` or `profile:` in `dbt_project.yml`
2. `~/.dbt/profiles.yml` (or `DBT_PROFILES_DIR`) for host/port/user/dbname/`pass`
3. Non-secret `DBT_GOLD_SCHEMA` / `PRESENTATION_GOLD_SCHEMA` when the gold schema is not derivable

Run `python <skill>/scripts/check_presentation_hardcodes.py --root <project.root>` before marking presentation complete.

Install workflow:

1. Detect the active environment: prefer the project `.venv` when it exists; otherwise use the current `python` on PATH.
2. Run an import check:

```powershell
python -c "import matplotlib, numpy, pandas"
```

3. If the import check fails, install the missing base packages:

```powershell
python -m pip install --upgrade pip
python -m pip install matplotlib numpy pandas
```

4. If warehouse query execution from Python is required and the adapter package is missing, install only the package that matches the active dbt profile adapter. Do not install every warehouse client by default.
5. Write or update `requirements-matplotlib.txt` under `reports/agent/10_presentation/matplotlib/` with the exact packages installed for this project.
6. Re-run the import check, `python reports/agent/10_presentation/matplotlib/serve_report.py --smoke-test` when implemented, and the local browser page validation command before marking the phase complete.

Do not mark Matplotlib presentation work complete if `matplotlib`, `numpy`, or `pandas` are still missing and chart rendering or server smoke testing was skipped without documenting the blocker.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Completed analytics insight reporting outputs, validated gold/marts access, reconciled key performance indicators, privacy decisions |
| Allowed changes | Python visualization scripts, figure assets, Matplotlib report spec, README, validation evidence under `reports/agent/10_presentation/matplotlib/` |
| Not allowed | Guessed metrics, synthetic chart data, sensitive-field exposure without approval, Power BI files unless Power BI was separately approved |
| Commands to run | Environment import check; install missing Matplotlib prerequisites when needed; read-only warehouse queries or approved cache/export queries; server smoke test; local browser page HTTP validation; Python script execution to render live SVG/HTML or browser-native charts; optional static export; optional `python -m py_compile` on generated scripts |
| Completion criteria | All recommended measures and key performance indicators from analytics insight catalogs are mapped in `kpi_figure_coverage.md`, approved page set renders through the local web report or is explicitly blocked with evidence, the report URL returns HTTP 200 with non-empty HTML in validation, SQL reconciliation recorded, refresh mode documented, prerequisites installed or blocker documented, presentation report updated |
| Report required | `reports/agent/10_presentation/presentation_report.md`, Matplotlib artifacts under `reports/agent/10_presentation/matplotlib/`, updated `PIPELINE_STATUS.md` and `CONTEXT_TREE.md` |

## Required deliverables

Write new Matplotlib artifacts under:

```text
reports/agent/10_presentation/matplotlib/
  README.md
  requirements-matplotlib.txt
  report_spec.md
  kpi_figure_coverage.md
  label_dictionary.md
  report_theme.md
  report_theme.py
  serve_report.py
  generate_report.py
  report_builder.py
  data_access.py
  report_pages/
  report.html
  open_report.bat
  open_report.sh
  data_cache/
  figures/
  sql_verification/
```

| File | Purpose |
|---|---|
| `README.md` | How to regenerate figures, open the browser report, install packages, data source notes, and privacy caveats |
| `requirements-matplotlib.txt` | Exact Python packages required for this report pack, including Matplotlib prerequisites and any warehouse client used |
| `report_spec.md` | Page list, chart list, metrics per chart, filters, dimensions, blocked visuals, tab mapping, and coverage summary |
| `kpi_figure_coverage.md` | Row-by-row mapping from `measure_catalog.md`, `metric_catalog.md`, `kpi_discovery_matrix.md`, `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, and `kpi_catalog.md` to figure files and status |
| `label_dictionary.md` | Approved code-to-business-label mappings used on charts, tables, legends, and HTML report text |
| `report_theme.md` | Color palette, typography, spacing, optional logo/image usage, and eye-comfort design notes |
| `report_theme.py` | Shared theme constants for chart colors, fonts, figure size, and export DPI |
| `serve_report.py` | Primary entry script: starts the local web report, refreshes data, serves chart/API routes, supports smoke testing |
| `generate_report.py` | Optional snapshot/export script: query data, render static exports, build static `report.html` only when snapshot mode is requested |
| `report_builder.py` | HTML assembly, tab/section layout, chart card layout, and live endpoint wiring |
| `data_access.py` | Read-only warehouse query helpers, cache helpers, and SQL verification utilities |
| `report_pages/` | One Python module per classified report page/tab, for example `executive.py`, `trends.py`, `segmentation.py`, `exceptions.py` |
| `report.html` | Browser-viewable multi-tab report for business review |
| `open_report.bat` | Windows launcher for `report.html` |
| `open_report.sh` | Optional launcher for macOS/Linux |
| `data_cache/` | Optional cached query results for offline review or static export; must be clearly labeled with generated timestamp |
| `figures/` | Optional exported SVG/PNG charts aligned to `dashboard_spec.md`; not the primary live rendering path |
| `sql_verification/` | Exact queries and captured results for **every** RENDERED chart and for All Measures / All Metrics board values; include `_proof_index.md` |

### Local browser page validation

Do not rely on `open_report.bat` existing, and do not treat `serve_report.py --smoke-test` as enough by itself. Before marking Matplotlib presentation complete, prove that the browser page itself responds.

Preferred validation command:

```powershell
python <path-to-installed-skill-or-workspace>\scripts\validate_local_web_report.py `
  --report-dir reports\agent\10_presentation\matplotlib `
  --expected-text "<report title or known page heading>"
```

The generated `serve_report.py` should support `--host 127.0.0.1` and `--port <port>`. If it does not, fix it before delivery or run the validator with a custom command:

```powershell
python <path-to-installed-skill-or-workspace>\scripts\validate_local_web_report.py `
  --report-dir reports\agent\10_presentation\matplotlib `
  --command python serve_report.py --port {port}
```

The validation must prove:

- The server process stays alive long enough to serve the page.
- `http://127.0.0.1:<port>/` returns HTTP 200.
- The response body is not empty and looks like HTML.
- The expected report title or known page heading appears in the response when practical.

If validation fails with symptoms such as `ERR_EMPTY_RESPONSE`, empty response body, connection reset, or the server process exiting early, mark presentation as `FAIL` or `BLOCKED`, capture stdout/stderr in `presentation_report.md`, fix `serve_report.py` or `open_report.bat`, and rerun validation.

### Python file organization

Organize generation code by report page classification instead of one unstructured script.

Recommended pattern:

```text
serve_report.py             # starts local server and live refresh routes
generate_report.py          # optional static export/snapshot command
data_access.py              # read-only queries and optional cache
report_builder.py           # shared HTML shell, nav tabs, styles, chart route wiring
report_pages/
  overview.py
  executive_kpis.py
  trends.py
  operations.py
  segmentation.py
  financial.py
  exceptions.py
  blocked.py
  report_info.py
```

Each `report_pages/*.py` module should:

- Own one tab or section in `report.html`
- Declare the business-facing page title and included metrics
- Call shared helpers for SQL load, label mapping, figure save, and verification logging
- Return the HTML fragment or chart route definitions for that section

Use one `Figure` or figure group per chart, but group related charts under the same page module when they belong to the same business tab. Prefer returning SVG/HTML strings or JSON chart specs for the browser over writing PNG files.

## Business-friendly labels (no raw codes on charts)

Charts must use **business-facing names**, not raw warehouse codes, unless the code itself is the approved business label.

Do not plot axis labels, legends, bar categories, or table rows using:

- Status codes such as `A`, `P`, `C`, `1`, `2`
- Type codes, reason codes, department codes, or plan codes
- Surrogate keys, hash keys, or technical column names
- Abbreviations that only engineers understand

Instead, resolve labels from approved sources in this order:

| Label source | Use for |
|---|---|
| `KPI_DEFINITION_CONTRACTS.md`, `METRIC_VERIFICATION_MATRIX.md`, `kpi_catalog.md`, and `metric_catalog.md` | Metric titles, card labels, chart titles, proof status, expected result, and actual result |
| Gold dimension name/description columns | Entity, product, provider, department, location, and status names |
| Mapping seeds and reference tables from dbt | Code-to-label translations |
| `label_dictionary.md` | Explicit code-to-business-label mappings used by the report pack |
| User-approved requirements or business rules | Company names, brand names, and approved terminology |

Maintain `label_dictionary.md` with columns such as:

| field_name | raw_code | business_label | source | confidence |
|---|---|---|---|---|
| status_code | A | Active | seed `status_mapping` | HIGH |

Hard label rules:

- If a code has no approved business label, do not render that category on a business-facing chart. Move it to Blocked/Deferred with the reason `Missing business label mapping`.
- If only some codes are mapped, show mapped categories only and list unmapped codes in the Exceptions tab.
- Chart titles, axis labels, legends, HTML tab names, and KPI cards must use the same business label wording.
- Company, client, department, product, provider, and status names must come from governed dimension fields or approved mappings, not from raw code values.
- Technical field names may appear only in `sql_verification/` or Report Information, not on business-facing chart axes.

Before saving a figure or HTML section, run a label check:

1. Every categorical axis value has a mapped business label or the chart is deferred.
2. Every metric name matches `kpi_catalog.md`, `metric_catalog.md`, or an approved alias in `report_spec.md`.
3. `label_dictionary.md` documents any code translation used in the report pack.
4. Categorical labels are **trimmed** before plotting (`strip()` in Python, `trim()`/`btrim()` in SQL). Fixed-width `char`/`varchar` fields from Postgres often return padded values that push matplotlib tick labels off-chart and look blank in the browser.

### Generator script location

Keep presentation generator, refresh, and validation helper scripts under `<project.root>/scripts/presentation/` (or another `scripts/` subfolder). Do not store `.py` helpers under `reports/agent/10_presentation/` — that folder is for markdown reports, SQL proofs, HTML/SVG assets, and launchers only. See [report-artifact-organization.md](report-artifact-organization.md).

## Visual comfort and colorful design

Matplotlib reports must be **visually comfortable and engaging**, not dull gray defaults. Business users should be able to review charts for longer periods without eye strain.

Design goals:

- Colorful enough to distinguish categories, trends, and key performance indicator states quickly
- Calm enough for executive review: no neon overload, no harsh black-on-white glare
- Consistent across figures, HTML tabs, and key performance indicator cards
- Accessible: readable contrast, color plus label meaning, and no color-only critical signals

### Required visual treatment

| Area | Requirement |
|---|---|
| Chart colors | Use a deliberate multi-color categorical palette for bars, lines, and areas; avoid leaving charts in default gray |
| Trend visuals | Use colored lines or soft gradient area fills with readable markers sparingly |
| Key performance indicator cards | Use color accents for status: positive, warning, negative, and neutral |
| HTML report | Use a soft page background, white content cards, colorful tab accents, and comfortable spacing |
| Typography | Use readable font sizes; titles larger than axis labels; avoid tiny text |
| Figure export | Optional only; save SVG first and PNG second when static export is requested |
| Whitespace | Leave padding around titles, legends, and chart edges; do not crowd labels |
| Gridlines | Use light, muted gridlines only when they improve reading |
| Images | Optional approved logo, icon, or header image in `report.html` when the user provides brand assets; do not invent branding |

Document the chosen theme in `report_theme.md` and apply it from shared helpers in `report_builder.py` or `report_theme.py`.

### Recommended comfortable palette

Use this palette unless the user supplies approved brand colors:

| Purpose | Color | Use |
|---|---|---|
| Page background | `#F4F7FB` | HTML report background |
| Card surface | `#FFFFFF` | KPI cards and figure containers |
| Primary text | `#1F2937` | Titles and main labels |
| Secondary text | `#6B7280` | Notes and captions |
| Primary accent | `#2563EB` | Main series and active tab |
| Secondary accent | `#7C3AED` | Secondary series |
| Teal | `#0D9488` | Supporting trend or comparison series |
| Amber | `#D97706` | Warning or attention |
| Green | `#16A34A` | Positive movement or success |
| Red | `#DC2626` | Negative movement or risk |
| Coral | `#F97316` | Additional categorical series |
| Sky | `#0EA5E9` | Additional categorical series |
| Rose | `#E11D48` | Additional categorical series |

Recommended categorical series order for multi-series charts:

`#2563EB`, `#0D9488`, `#7C3AED`, `#F97316`, `#0EA5E9`, `#16A34A`, `#E11D48`, `#D97706`

### Eye-comfort rules

- Do not use matplotlib default styling as the final design.
- Do not make every chart a different random palette; keep one theme across the report pack.
- Do not use fully saturated neon colors across the whole page.
- Do not rely on color alone for meaning; pair color with labels, values, or icons in HTML cards.
- Use soft backgrounds and colored accents instead of large solid bright blocks.
- For dense category charts, prefer horizontal bars with alternating subtle fills or distinct series colors.
- Add short chart subtitles or callout text when a figure needs context.
- If company logo or approved imagery exists, place it in the HTML header only; do not embed sensitive or unapproved images.

### Optional theme files

| File | Purpose |
|---|---|
| `report_theme.md` | Human-readable theme notes: palette, typography, spacing, logo/image usage, and accessibility caveats |
| `report_theme.py` | Shared constants for colors, fonts, figure size, and DPI used by `report_pages/` modules |

## Matplotlib implementation knowledge

Use the official [Matplotlib User Guide](https://matplotlib.org/stable/users/index) when structure or API behavior is uncertain.

### Core concepts to apply

| Topic | Use in this skill |
|---|---|
| Figures and backends | Create one `Figure` per page or logical chart group; render live chart output as SVG/HTML through the local server; use `Agg` only for static export fallback |
| Axes and subplots | Use `subplots` or subplot mosaics for executive summary pages with multiple key performance indicator and trend panels |
| Artists | Keep line, bar, area, and table artists explicit; avoid unnecessary chart decoration |
| Colors | Use the comfortable colorful palette from `report_theme.md`; distinguish series and key performance indicator states with intentional color |
| Text and annotations | Add titles, axis labels, units, caveats, and source notes on every chart |
| Plotting dates | Use explicit date parsing and time-axis formatting for trend visuals |
| Legends | Show series meaning clearly; avoid duplicate or unreadable legends |
| rcParams and style sheets | Use one shared theme via `report_theme.py`, rcParams, or a style sheet so all figures and HTML cards match |
| Figure quality | Prefer inline SVG for crisp browser viewing; export PNG at `dpi=150` or higher only for snapshots |

### Chart selection rules

| Business question | Preferred visual |
|---|---|
| Trend over time | Line or area chart |
| Category comparison | Bar or horizontal bar chart |
| Part-to-whole when few categories | Bar chart; avoid pie charts unless the user explicitly requests them |
| Distribution or spread | Histogram or box plot when supported and meaningful |
| Operational detail | Table export or matrix-style figure only when row volume is safe and non-sensitive |

Every chart must answer one business question from `reporting_catalog.md` or `dashboard_spec.md`.

## Hard rules

- Do not plot metrics that are `LOW`, `BLOCKED`, or unreconciled in analytics insight key performance indicator files.
- Do not fabricate data, targets, benchmarks, or trend lines without evidence.
- Reconcile every plotted aggregate to SQL before marking the chart trusted.
- Do not expose secrets, passwords, OTP, full bank/IBAN dumps, national IDs, or protected health information in chart labels, tables, or annotations unless the user explicitly asks.
- When the user has opted out of privacy minimization, **do** show reporting attributes from gold on presentation tabs when useful. Discover columns from this project — do not assume industry field lists. Do not add “this report avoids identifiers” caveats after opt-out.
- Do not put raw codes, surrogate keys, or technical column names on business-facing chart axes, legends, or HTML tab content.
- Prefer a small set of high-value charts over many weak charts.
- Maximum means maximum useful business insight supported by validated data, not maximum number of figures.
- Use full wording in titles, labels, and report text.

## Validation before handoff

Before marking Matplotlib presentation work complete:

1. Verify `matplotlib`, `numpy`, and `pandas` import successfully or document the exact install blocker and commands attempted.
2. Verify `requirements-matplotlib.txt` exists and matches the installed packages.
3. Verify `kpi_figure_coverage.md` includes **every row** from `measure_catalog.md`, `metric_catalog.md`, `kpi_catalog.md`, and `KPI_DEFINITION_CONTRACTS.md` (supported/recommended/trusted or contract rows), each with `RENDERED`, `BLOCKED`, or `DEFERRED` status. See [reporting-coverage-requirements.md](reporting-coverage-requirements.md).
4. Verify `serve_report.py --smoke-test` or the documented server smoke test runs without error.
5. Verify the local report page itself with `scripts/validate_local_web_report.py --report-dir <matplotlib_dir>`, proving that `http://127.0.0.1:<port>/` returns HTTP 200 and non-empty HTML. This catches browser failures such as `ERR_EMPTY_RESPONSE`.
6. Verify the **data refresh path** used by the report (refresh control / data API / chart JSON endpoint). Run live warehouse SQL for every `RENDERED` chart. A missing relation such as `schema.fct_* does not exist` is presentation `FAIL`, not a tip for the user.
7. If `generate_report.py` exists for snapshot export, verify it runs without error or document the exact blocker.
8. Verify the local web report contains the classified tabs/sections defined in `report_spec.md`.
9. Verify `open_report.bat` exists on Windows-focused projects or document the equivalent open command, and confirm it points to the same validated server entrypoint.
10. Verify every `RENDERED` row in `kpi_figure_coverage.md` appears in the correct HTML tab/section through SVG/HTML/JSON chart output, measure/metric board cards, or has a documented static export fallback.
10b. Verify the live report includes **All Measures** and **All Metrics** boards (or equivalent named tabs) with **visible live values**: smoke-test must report `measure_cards >= 50` and `metric_cards >= 50` when gold has 3+ facts. Catalog markdown alone does not satisfy this check.
11. Verify `label_dictionary.md` exists and every categorical chart uses mapped **business labels** on axes/legends. Blank x-axis ticks on `RENDERED` charts are a validation `FAIL`.
12. Verify `report_theme.md` exists and charts/HTML use the comfortable colorful theme, not default gray matplotlib styling.
13. Verify every plotted aggregate **and every All Measures / All Metrics board card** has a matching **executed** SQL proof in `sql_verification/` with captured result and `PASS`, and `_proof_index.md` maps RENDERED items to those proofs. One KPI-card proof file is not enough when 50+ measures/metrics are visible.
14. Verify chart scope matches `dashboard_spec.md` and does not include deferred items from `insight_backlog.md` without a visible blocked note.
15. Run `python <skill>/scripts/check_presentation_coverage.py --root <project.root>` when available.
16. Record pass/fail evidence in `reports/agent/10_presentation/presentation_report.md`.

HTML shell load alone is never enough to mark presentation complete.

## Done gate

```text
Presentation layer: COMPLETE

Presentation technology: Matplotlib
Browser report server: reports/agent/10_presentation/matplotlib/serve_report.py
Browser report shell: reports/agent/10_presentation/matplotlib/report.html
Launcher: reports/agent/10_presentation/matplotlib/open_report.bat or documented equivalent
Refresh mode: manual / timed / snapshot export
Coverage map: reports/agent/10_presentation/matplotlib/kpi_figure_coverage.md
Label dictionary: reports/agent/10_presentation/matplotlib/label_dictionary.md
Python prerequisites: PASS or BLOCKED with install commands attempted
Report spec: reports/agent/10_presentation/matplotlib/report_spec.md
Figure generation: PASS or BLOCKED with reason
Local page validation: PASS with URL and response size, or BLOCKED with stdout/stderr
SQL verification: PASS or BLOCKED with reason
Report: reports/agent/10_presentation/presentation_report.md
Pipeline status: reports/agent/PIPELINE_STATUS.md
```

Do not claim figures are validated if SQL reconciliation was not recorded.

## Commit guidance

When commit mode allows, include only reproducible Matplotlib assets and exclude generated secrets, local credentials, or environment-specific cache files.
