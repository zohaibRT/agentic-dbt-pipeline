# Matplotlib Presentation Layer

Use this when the user approves a presentation layer and chooses **Matplotlib** as the presentation technology, or when the user approves the default presentation layer without naming another technology.

Also read [presentation-layer.md](presentation-layer.md), [analytics-insight-reporting.md](analytics-insight-reporting.md), [report-artifact-organization.md](report-artifact-organization.md), [reporting-standards.md](reporting-standards.md), [kpi-definitions.md](kpi-definitions.md), [metric-verification.md](metric-verification.md), and [mapping-seeds.md](mapping-seeds.md) when code-to-label mappings are needed.

Official documentation: [Matplotlib User Guide](https://matplotlib.org/stable/users/index)

## Purpose

Generate validated, business-facing static analytics outputs from approved gold/marts data and analytics insight reporting files. Matplotlib is the **recommended default** presentation technology because it is:

- Version-controlled and reproducible in the dbt project repository
- Runnable without Power BI Desktop or proprietary report project files
- Easy to validate with SQL-backed Python scripts
- Suitable for executive summaries, trend pages, breakdown charts, and operational detail views
- Viewable in a browser through a generated HTML report with classified tabs/pages, plus optional Windows batch launcher

Matplotlib outputs are not a replacement for governed semantic models. They consume the same trusted key performance indicators and page scope defined during analytics insight reporting.

## Browser-viewable report pack

Matplotlib delivery is not complete with PNG files alone. The agent must also produce a **browser-openable HTML report** so a data engineer or business user can review all charts without hunting through loose image files.

### Primary review experience

| Artifact | Purpose |
|---|---|
| `report.html` | Main browser report with tabbed or sectioned navigation, chart grouping, key performance indicator summaries, blocked/deferred notes, and report metadata |
| `open_report.bat` | Windows launcher that opens `report.html` in the default browser |
| `open_report.sh` | Optional Unix launcher for the same behavior |
| `generate_report.py` | Regenerates figures, rebuilds `report.html`, and may open the browser when run with `--open` |

Expected user flow on Windows:

1. Run `python reports/agent/10_presentation/matplotlib/generate_report.py`
2. Double-click `reports/agent/10_presentation/matplotlib/open_report.bat`
3. Review classified tabs/pages in the browser

Do not require Power BI, Jupyter, or a notebook server for normal review.

### HTML report structure

`report.html` must use a clear multi-page or multi-tab layout aligned to `dashboard_spec.md` and the five reporting pillars when supported.

Default tab or section order:

| Tab / section | Content |
|---|---|
| Overview | Report purpose, audience, data source, refresh time, caveats, and navigation |
| Executive key performance indicators | Trusted strategic key performance indicators from `kpi_catalog.md` |
| Trends and variance | Time showcase, period comparisons, and variance views |
| Operations and activity | Volumes, statuses, workflow movement, and operational metrics |
| Segmentation and performance | Department, product, provider, location, channel, or other approved dimensions |
| Financial or value | Amount, revenue, payment, cost, or value views when supported |
| Exceptions and data quality | Coverage gaps, blocked visuals, mapping gaps, and validation notes |
| Blocked and deferred | Items from `insight_backlog.md` and unreconciled metrics |
| Report information | Metric definitions, filters, privacy handling, SQL verification summary |

Each tab or section must:

- Show business-facing titles, not technical file names
- Embed or link the related PNG figures from `figures/`
- List the metrics included on that page
- Mark unsupported or blocked content visibly instead of hiding it

`generate_report.py` must rebuild `report.html` every time figures are regenerated so the browser view stays in sync with `kpi_figure_coverage.md`.

## When to recommend Matplotlib

Recommend Matplotlib as the default when:

- Analytics insight reporting is complete and trusted metrics exist
- The user wants portable charts, PDFs, or PNGs checked into the repository
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
| `reports/agent/09_analytics_insights/reporting_catalog.md` | Report/page scope |
| `reports/agent/09_analytics_insights/insight_backlog.md` | Deferred or blocked visuals |
| `reports/agent/09_analytics_insights/reporting_readiness_scorecard.md` | Readiness gate |
| `reports/agent/09_analytics_insights/analytics_insight_report.md` | Business rationale |

Do not invent pages, metrics, or chart types that bypass analytics insight outputs unless the user explicitly overrides them.

## Key performance indicator and measure coverage

Matplotlib must include **all recommended analytics insight outputs**, not only a small executive subset.

Build a coverage table in `report_spec.md` that maps every recommended measure and key performance indicator to a Matplotlib output or an explicit blocked/deferred note.

| Source file | Matplotlib coverage rule |
|---|---|
| `measure_catalog.md` | Include every measure marked `recommended`, `trusted`, or equivalent supported status in at least one summary value, trend visual, distribution visual, or supporting detail panel |
| `metric_catalog.md` | Include every metric marked `recommended`, `trusted`, or equivalent supported status in at least one chart, summary value, or matrix-style figure |
| `kpi_discovery_matrix.md` | Include every row with `HIGH` confidence or user-approved `MEDIUM` confidence in the figure plan; mark `LOW`, `BLOCKED`, and unreconciled rows as deferred with the reason from the matrix |
| `kpi_catalog.md` | Include every trusted strategic key performance indicator in the executive summary area, a dedicated key performance indicator page, or a clearly labeled supporting panel |
| `dashboard_spec.md` | Every approved page and visual in the dashboard spec must have a matching figure group or blocked note |
| `insight_backlog.md` | Deferred or blocked items must appear in the coverage table as `BLOCKED` or `DEFERRED`; do not omit them silently |

Required coverage artifacts:

| File | Purpose |
|---|---|
| `kpi_figure_coverage.md` | Row-by-row mapping from measure/metric/key performance indicator name to figure file, chart type, SQL proof file, and status (`RENDERED`, `BLOCKED`, `DEFERRED`) |
| `report_spec.md` | Page plan plus the same coverage rules in summary form |

Hard coverage rules:

- Do not skip a recommended measure or key performance indicator just because the figure would be repetitive; combine related items on one page when appropriate, but keep every item visible in `kpi_figure_coverage.md`.
- Do not plot `LOW`, `BLOCKED`, or unreconciled items; show them in a blocked/deferred section of the report pack instead.
- Executive summary pages should prioritize `kpi_catalog.md` items, but supporting measures from `measure_catalog.md` and `metric_catalog.md` must still be represented somewhere in the pack when they are marked recommended or trusted.
- Standard time showcase visuals from [presentation-layer.md](presentation-layer.md) still apply when validated date fields exist.

## Python environment and dependency installation

Before generating figures, verify the Matplotlib stack is available in the active Python environment. If any required package is missing, install it and record the command in `README.md` and `reports/agent/10_presentation/presentation_report.md`.

Required packages:

| Package | Role |
|---|---|
| `matplotlib` | Static chart rendering |
| `numpy` | Numeric arrays used by Matplotlib |
| `pandas` | Tabular query results and chart-ready data frames |
| Warehouse/query helper | Use the project's existing dbt profile adapter client when available, such as `psycopg2` or `psycopg2-binary` for PostgreSQL/Redshift, `snowflake-connector-python` for Snowflake, `google-cloud-bigquery` for BigQuery, or `databricks-sql-connector` for Databricks |

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
6. Re-run the import check and `python reports/agent/10_presentation/matplotlib/generate_report.py` before marking the phase complete.

Do not mark Matplotlib presentation work complete if `matplotlib`, `numpy`, or `pandas` are still missing and figure generation was skipped without documenting the blocker.

## Phase contract

| Area | Contract |
|---|---|
| Inputs required | Completed analytics insight reporting outputs, validated gold/marts access, reconciled key performance indicators, privacy decisions |
| Allowed changes | Python visualization scripts, figure assets, Matplotlib report spec, README, validation evidence under `reports/agent/10_presentation/matplotlib/` |
| Not allowed | Guessed metrics, synthetic chart data, sensitive-field exposure without approval, Power BI files unless Power BI was separately approved |
| Commands to run | Environment import check; install missing Matplotlib prerequisites when needed; read-only warehouse queries or approved export queries; Python script execution to render figures; optional `python -m py_compile` on generated scripts |
| Completion criteria | All recommended measures and key performance indicators from analytics insight catalogs are mapped in `kpi_figure_coverage.md`, approved page set rendered or explicitly blocked with evidence, SQL reconciliation recorded, prerequisites installed or blocker documented, presentation report updated |
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
  generate_report.py
  report_builder.py
  report_pages/
  report.html
  open_report.bat
  open_report.sh
  figures/
  sql_verification/
```

| File | Purpose |
|---|---|
| `README.md` | How to regenerate figures, open the browser report, install packages, data source notes, and privacy caveats |
| `requirements-matplotlib.txt` | Exact Python packages required for this report pack, including Matplotlib prerequisites and any warehouse client used |
| `report_spec.md` | Page list, chart list, metrics per chart, filters, dimensions, blocked visuals, tab mapping, and coverage summary |
| `kpi_figure_coverage.md` | Row-by-row mapping from `measure_catalog.md`, `metric_catalog.md`, `kpi_discovery_matrix.md`, and `kpi_catalog.md` to figure files and status |
| `label_dictionary.md` | Approved code-to-business-label mappings used on charts, tables, legends, and HTML report text |
| `generate_report.py` | Entry script: query data, render figures, build `report.html`, optional `--open` browser launch |
| `report_builder.py` | HTML assembly, tab/section layout, and figure embedding logic |
| `report_pages/` | One Python module per classified report page/tab, for example `executive.py`, `trends.py`, `segmentation.py`, `exceptions.py` |
| `report.html` | Browser-viewable multi-tab report for business review |
| `open_report.bat` | Windows launcher for `report.html` |
| `open_report.sh` | Optional launcher for macOS/Linux |
| `figures/` | Exported PNG charts aligned to `dashboard_spec.md` |
| `sql_verification/` | Exact queries and expected values used to validate each chart aggregate |

### Python file organization

Organize generation code by report page classification instead of one unstructured script.

Recommended pattern:

```text
generate_report.py          # orchestrates query -> figure -> html
report_builder.py           # shared HTML shell, nav tabs, styles
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
- Return the HTML fragment for that section

Use one `Figure` or figure group per chart, but group related charts under the same page module when they belong to the same business tab.

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
| `kpi_catalog.md` and `metric_catalog.md` | Metric titles, card labels, and chart titles |
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

## Matplotlib implementation knowledge

Use the official [Matplotlib User Guide](https://matplotlib.org/stable/users/index) when structure or API behavior is uncertain.

### Core concepts to apply

| Topic | Use in this skill |
|---|---|
| Figures and backends | Create one `Figure` per page or logical chart group; save static outputs with a non-interactive backend such as `Agg` for reproducible files |
| Axes and subplots | Use `subplots` or subplot mosaics for executive summary pages with multiple key performance indicator and trend panels |
| Artists | Keep line, bar, area, and table artists explicit; avoid unnecessary chart decoration |
| Colors | Use a consistent accessible palette; document color meaning in `report_spec.md` |
| Text and annotations | Add titles, axis labels, units, caveats, and source notes on every chart |
| Plotting dates | Use explicit date parsing and time-axis formatting for trend visuals |
| Legends | Show series meaning clearly; avoid duplicate or unreadable legends |
| rcParams and style sheets | Use one project style for all figures so outputs look like one report system |

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
- Do not expose direct identifiers, personally identifiable information, or protected health information in chart labels, tables, or annotations unless approved.
- Do not put raw codes, surrogate keys, or technical column names on business-facing chart axes, legends, or HTML tab content.
- Prefer a small set of high-value charts over many weak charts.
- Maximum means maximum useful business insight supported by validated data, not maximum number of figures.
- Use full wording in titles, labels, and report text.

## Validation before handoff

Before marking Matplotlib presentation work complete:

1. Verify `matplotlib`, `numpy`, and `pandas` import successfully or document the exact install blocker and commands attempted.
2. Verify `requirements-matplotlib.txt` exists and matches the installed packages.
3. Verify `kpi_figure_coverage.md` includes every recommended measure, metric, and key performance indicator from analytics insight catalogs, with `RENDERED`, `BLOCKED`, or `DEFERRED` status for each row.
4. Verify `generate_report.py` runs without error in the project environment or document the exact blocker.
5. Verify `report.html` exists, opens in a browser, and contains the classified tabs/sections defined in `report_spec.md`.
6. Verify `open_report.bat` exists on Windows-focused projects or document the equivalent open command.
7. Verify every `RENDERED` row in `kpi_figure_coverage.md` has a matching figure file under `figures/` and appears in the correct HTML tab/section.
8. Verify `label_dictionary.md` exists and every categorical chart uses mapped business labels, not raw codes.
9. Verify every plotted aggregate has a matching SQL proof in `sql_verification/`.
10. Verify chart scope matches `dashboard_spec.md` and does not include deferred items from `insight_backlog.md` without a visible blocked note.
11. Record pass/fail evidence in `reports/agent/10_presentation/presentation_report.md`.

## Done gate

```text
Presentation layer: COMPLETE

Presentation technology: Matplotlib
Browser report: reports/agent/10_presentation/matplotlib/report.html
Launcher: reports/agent/10_presentation/matplotlib/open_report.bat or documented equivalent
Coverage map: reports/agent/10_presentation/matplotlib/kpi_figure_coverage.md
Label dictionary: reports/agent/10_presentation/matplotlib/label_dictionary.md
Python prerequisites: PASS or BLOCKED with install commands attempted
Report spec: reports/agent/10_presentation/matplotlib/report_spec.md
Figure generation: PASS or BLOCKED with reason
SQL verification: PASS or BLOCKED with reason
Report: reports/agent/10_presentation/presentation_report.md
Pipeline status: reports/agent/PIPELINE_STATUS.md
```

Do not claim figures are validated if SQL reconciliation was not recorded.

## Commit guidance

When commit mode allows, include only reproducible Matplotlib assets and exclude generated secrets, local credentials, or environment-specific cache files.
