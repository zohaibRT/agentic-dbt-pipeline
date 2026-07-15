# Reporting Coverage Requirements

Use this for gold, analytics insight reporting, semantic layer, presentation layer, and final delivery.

These requirements are **hard defaults** whenever the user states them (or pastes them as project rules). They also define the skill’s intended rich-reporting behavior.

## User-stated reporting requirements (binding)

When the user provides rules like the following, apply them for the whole run and write them into `reports/agent/00_discovery/requirements.md`, `CONTEXT_TREE.md`, and `AGENT_PLAN.md`:

```text
1. Maximize useful KPIs/metrics from validated gold for each material business process (no fixed minimum count).
2. Build conformed dimensions present in THIS warehouse (entity, date, status, and any other dims with evidence) for slicing.
3. Do NOT apply privacy minimization unless I explicitly request it.
4. Use label_dictionary.md — every chart axis must show business names, not blank or raw codes.
5. Presentation must map published strategic KPIs and recommended business metrics in kpi_figure_coverage.md (dictionary-only rows optional) and use human-readable display names.
6. Run live SQL for every RENDERED chart before marking presentation complete.
```

If the user names **project-specific** dimension types (illustrative only — do not treat as required model names: partners, SKUs), apply those names for that run only. Do **not** treat any industry’s entity list as a global skill default.

Treat the block as approved requirements when the user states it. Do not re-ask for privacy minimization after the user opts out. Do not silently shrink catalogs to three to five executive KPIs.

## Rule 1 — Analytical completeness (process-driven, not fixed counts)

Analytics completion is based on **business-process and fact coverage**, not a fixed number of catalog rows.

Do **not** optimize for 50+, 100+, or any other arbitrary measure/metric count. Those numbers may appear only as **optional advisory examples** for medium/large projects when configured under `analytics_policy.advisory_*_target`.

| Catalog / artifact | Role | Hard rule |
|---|---|---|
| `business_process_catalog.md` | Processes drive metrics and pages | Required when analytics phase runs |
| `analytics_coverage_matrix.md` | Primary coverage gate | Process coverage target from `analytics_policy` (default >= 90%) |
| `fact_coverage_contracts.md` | Per-fact analytical evaluation | Critical fact coverage default 100% |
| `business_measure_catalog.md` / `measure_catalog.md` | Business measures only | Complete for material facts; no fixed row floor |
| `business_metric_catalog.md` / `metric_catalog.md` | Contextual metrics | Complete where questions exist; no fixed row floor |
| `kpi_catalog.md` | Strategic KPI subset | Every published KPI has a full contract |
| `data_quality_metric_catalog.md` | DQ family | Separate from business pages |
| `pipeline_health_metric_catalog.md` | Pipeline family | Separate from business pages |
| Presentation | Readable business pages | Rules 5b–5c; dictionary pages optional |

Thin catalogs that leave material facts without volume/value/status/time/quality evaluation are a **FAIL**. A small project with complete process coverage can PASS with far fewer than 50 metrics.

If coverage is incomplete:

1. Document gaps in `insight_backlog.md` and the coverage matrix with exact missing proofs
2. Mark analytics / presentation status `WARN` or `BLOCKED`
3. Re-warn on the Attention Board / Gap Register with an agent recommendation
4. Acceptance gate runs process/fact/KPI contract checkers — **not** a hardcoded 50+ row counter

Also read [analytics-product-completeness.md](analytics-product-completeness.md), [kpi-discovery-framework.md](kpi-discovery-framework.md), and [universal-analytics-framework.md](universal-analytics-framework.md).

## Rule 2 — Conformed dimensions for slicing

Gold must evaluate and preferably **BUILD** every dimension class that **this project’s** source/bronze/silver evidence supports. There is no universal industry entity list.

| Dimension class | When to build |
|---|---|
| Entity / party | Accounts, customers, counterparties, vendors, employees, or similar when evidence exists |
| Date | Date dimension / time spine whenever facts have usable dates |
| Status / lifecycle | Low-cardinality codes used by facts (with business labels) |
| Product / offer / catalog | Only when product/plan/SKU/catalog tables exist in scope |
| Channel / location / org | Only when channel, store, site, department, or org tables exist in scope |
| Other descriptive dims | Any included lookup/entity proven unique and useful for slicing |

Do not invent partner/program/SKU (or healthcare/retail) dimensions when the warehouse has none. Do not deliver fact-only gold with blank categorical charts when labels exist. See [gold-dimension-completeness.md](gold-dimension-completeness.md).

If a evidenced class cannot be built, register `BLOCKED` / `DEFERRED` with proof — still list the blocked KPIs/slices on the Gap Register.

## Rule 3 — Privacy minimization opt-out

Default skill privacy is still conservative **until** the user opts out.

When the user says any of:

- `Do NOT apply privacy minimization unless I explicitly request it`
- `no privacy until specifically asked`
- `keep dimensions / clear attributes for reporting`

Then:

| Action | Required |
|---|---|
| Gold entity dimensions | `BUILD` with descriptive attributes needed for slicing (partner name, program name, product name, etc.) |
| Clear-text vs hash | Do **not** force hash/exclude for non-national-id commercial attributes |
| Still never invent | Still do not expose secrets, passwords, OTP, full bank/IBAN dumps, or PHI without explicit ask |
| Documentation | Record opt-out once in requirements / Context Tree |
| Recommend, don't block | Do not block gold dims or presentation for privacy after opt-out |
| Attention Board | Close privacy-minimization rows for reporting attributes; no OPEN privacy blockers after opt-out |
| Gap Register | No OPEN `PRIVACY` minimization blockers for reporting attributes when opt-out is recorded |
| Presentation | **Show** reporting attributes that exist in gold; forbid copy that the report still avoids/hides identifiers after opt-out |
| Gates / scripts | Stay **domain-neutral** — discover fields and dims from project evidence; never hardcode industry column or brand names into checkers |

Still document always-exclude classes once as `CARRY_FORWARD` (secrets, OTP, full bank dumps, national IDs, PHI). Do not treat those as OPEN blockers that stop gold dims or KPI catalogs.

Under opt-out, do **not** re-ask whether reporting attributes from this warehouse may appear on presentation — they may when present in gold. Ask only about always-exclude classes (national IDs, bank dumps, OTP, PHI) if those would be placed on charts.

Update [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md) behavior: user opt-out overrides the gold “exclude/mask/hash by default” row for reporting dimensions.

## Rule 4 — Chart labels required (`label_dictionary.md`)

Every categorical Matplotlib / presentation chart:

| Required | Forbidden |
|---|---|
| Visible business names on every categorical tick / legend | Blank x-axis / unlabeled bars |
| Mapping documented in `label_dictionary.md` | Raw warehouse codes as the only label when a business name exists |
| Query selects the label column (partner name, status label), not only surrogate keys | Keys plotted without join to dimension/label |

If labels cannot be resolved:

- Status = `BLOCKED` / `DEFERRED` for that figure
- Do not mark the chart `RENDERED`
- Fail presentation validation

Presentation is incomplete when any `RENDERED` categorical chart has empty or missing tick labels.

## Rule 5 — Required presentation mapping (not every catalog row)

`kpi_figure_coverage.md` must map:

- **Every strategic KPI** from `kpi_catalog.md` / published `KPI_DEFINITION_CONTRACTS.md` rows (`APPROVED`, `BLOCKED`, or `DEFERRED`)
- **Every recommended/published business metric** intended for decision pages
- **Data-quality metrics** → Exceptions / Data Quality surfaces
- **Pipeline-health metrics** → Pipeline Health surfaces
- Deferred/backlog items may remain in dictionary/backlog without being RENDERED

Technical, exploratory, or dictionary-only catalog rows **may** stay on Metric Dictionary pages without forcing every raw measure onto executive boards. Do **not** pad boards with `dim_*_row_count` or other warehouse inventory as business measures.

Each mapped row: `RENDERED` | `BLOCKED` | `DEFERRED` with reason and (for RENDERED) SQL proof path.

Do not only map executive KPI cards while omitting published business metrics the report claims to support.

## Rule 5b — Visible density in the live browser report (hard)

Catalogs and `kpi_figure_coverage.md` alone are **not** enough. The refreshable web report the human opens must **show** the coverage:

| Surface | Minimum when gold has 3+ facts/marts |
|---|---|
| Executive / Overview | Top strategic KPIs (cards) with period/context |
| Process / business pages | Pages derived from discovered processes (not fixed industry titles) |
| **Metric Dictionary** (optional) | All Measures / All Metrics exploration pages with display names + formatting |
| **Dimensions** tab (or equivalent) | Readable tables per built gold dimension when dims exist |
| Charts | Status/entity/time visuals plus quality callouts |

Required implementation pattern:

1. `data_access.py` (or equivalent) returns boards as `{id, display_name, value, formatted_value, group, format}` — not raw SQL identifiers alone.
2. `report_builder.py` / HTML renders decision-oriented pages first; dictionary boards are secondary.
3. `serve_report.py --smoke-test` asserts pages render and formatted values appear for RENDERED items.
4. `check_presentation_coverage.py` **FAIL**s when business readability / proofs / page contracts are incomplete.

Forbidden:

- “75 measures in measure_catalog.md” while Overview still shows only 8 cards
- Marking presentation complete because `kpi_figure_coverage.md` lists RENDERED rows that are not visible in the browser
- Only printing catalog counts in Report Info without live values

## Rule 5c — Business-facing boards (not SQL dumps)

The live report is for **humans who are not data engineers**. All Measures / All Metrics / Dimensions must look like business reporting, not a warehouse query tool.

| Element | Required | Forbidden on business tabs |
|---|---|---|
| Measure / metric title | Sentence case or Title Case business name (`Active operating share`, `Average order amount (SAR)`) | Snake_case IDs (`active_operating_share_of_subscriptions`, `avg_order_amount_sar`) |
| Stable technical id | May exist in JSON/API payload as `id` for SQL/proof mapping | Shown as the only visible Name column |
| Values | Formatted for type: integers with thousands separators; rates/shares as `%` (1–2 decimals); amounts with currency/unit when known; averages rounded | Raw float dumps (`0.2611111111111111`, `4037.6045379548`) |
| Dimension coverage | Dedicated **Dimensions** tab: for each `dim_*` with business labels, show a small table of rows (key + business name/status label columns from gold) | Leading the All Measures board with `dim_programs_row_count`, `dim_dates_row_count`, etc. as if those were business KPIs |
| Engineering QA counts | Model row counts, null counts, orphan rates may live under **Exceptions / data quality** or Report Information | Dominating the first screen of All Measures |

Catalogs must carry a **Display name** (and preferably **Format**: `integer` / `percent` / `currency` / `decimal` / `count`) so presentation does not invent labels at render time from the technical id alone.

`check_presentation_coverage.py` **FAIL**s when:

- Builder/HTML board payloads lack `display_name` (or equivalent) alongside values
- No value-formatting helper is present (`format_value`, `formatted_value`, percent/currency formatting)
- Sampled board Name cells are mostly `snake_case` technical ids with no human title mapping

## Rule 6 — Live SQL for every RENDERED chart **and** measure/metric board

Before marking presentation complete:

1. Confirm the gold object exists in the warehouse (`information_schema` / `\dt` / adapter equivalent)
2. Execute the **exact** presentation SQL used by the chart refresh path **and** the All Measures / All Metrics board queries
3. Capture actual row counts / aggregates in `sql_verification/` with PASS headers (purpose, expected, captured result, status)
4. Hit the report refresh/data endpoint (not only HTML shell `/`) and assert no SQL error
5. Record evidence in `presentation_report.md`
6. Maintain `sql_verification/_proof_index.md` mapping every RENDERED measure/metric/KPI board card or chart to at least one proof file

Minimum proof set when All Measures / All Metrics boards exist:

| Proof artifact | Covers |
|---|---|
| `sql_verification/010_measure_board_*.sql` (or split by group) | Live measure board snapshot values |
| `sql_verification/020_metric_board_*.sql` (or split by group) | Live metric board rates/shares/averages |
| Chart-specific proofs | Each major chart SQL used by `serve_report` |
| `_proof_index.md` | Row → proof path → status |

A single KPI-card proof is **not** enough when many measures/metrics are RENDERED. `check_presentation_coverage.py` **FAIL**s when RENDERED board density is high and `sql_verification/` has too few executed proofs with captured results.

HTML shell HTTP 200 alone is **not** enough. A missing relation such as `schema.fct_prospect does not exist` is a presentation **FAIL**, not a user environment tip.

## Chat / Attention Board behavior

After analytics and presentation checkpoints, re-warn when:

- Supported measure/metric counts are below the target while gold can support more
- Required dim classes are missing
- Any RENDERED chart lacks labels
- Any RENDERED SQL was not executed live
- Privacy opt-out was ignored

Agent recommendation format: concrete expand/build/label/run-SQL action + Accept / Override / Defer.

## Completion checks

| Checkpoint | Incomplete when |
|---|---|
| Gold | Missing evidenced entity/date/status (or other discovered dim classes) without BLOCKED register |
| Analytics | `measure_catalog` thin vs available gold; coverage not attempted |
| Presentation | Catalog rows missing from `kpi_figure_coverage.md` |
| Presentation | Blank categorical axes on RENDERED charts |
| Presentation | Live SQL / refresh API not proven for RENDERED charts |
| Presentation | All Measures/Metrics boards RENDERED but `sql_verification/` missing proofs / `_proof_index.md` |
| Final delivery | User opt-out of privacy ignored; dims still privacy-blocked without ask |
| Final delivery | OPEN Attention Board / Gap Register privacy-minimization rows under recorded opt-out |
| Presentation | Rich catalogs exist but live HTML shows only executive cards without dictionary or process pages |
| Presentation | All Measures/Metrics show snake_case SQL ids or raw unformatted floats as the primary user-facing columns |
| Presentation | Gold dimensions exist but only appear as `dim_*_row_count` on measures — no Dimensions browse tables |
| Presentation | Privacy opt-out recorded but report still says it avoids/hides identifiers or applies privacy minimization |

## Related references

- [kpi-discovery-framework.md](kpi-discovery-framework.md)
- [gold-dimension-completeness.md](gold-dimension-completeness.md)
- [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md)
- [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md)
- [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md)
- [stakeholder-layer-and-presentation-guide.md](stakeholder-layer-and-presentation-guide.md)
