# Reporting Coverage Requirements

Use this for gold, analytics insight reporting, semantic layer, presentation layer, and final delivery.

These requirements are **hard defaults** whenever the user states them (or pastes them as project rules). They also define the skill’s intended rich-reporting behavior.

## User-stated reporting requirements (binding)

When the user provides rules like the following, apply them for the whole run and write them into `reports/agent/00_discovery/requirements.md`, `CONTEXT_TREE.md`, and `AGENT_PLAN.md`:

```text
1. Maximize supported KPIs/metrics from validated gold — target 50+ in measure/metric catalogs.
2. Build conformed dimensions present in THIS warehouse (entity, date, status, and any channel/product/geography tables with evidence) for slicing.
3. Do NOT apply privacy minimization unless I explicitly request it.
4. Use label_dictionary.md — every chart axis must show business names, not blank or raw codes.
5. Presentation must map every measure_catalog + metric_catalog + kpi_catalog row in kpi_figure_coverage.md.
6. Run live SQL for every RENDERED chart before marking presentation complete.
```

If the user names **project-specific** dimension types (for example partners or SKUs), apply those names for that run only. Do **not** treat any industry’s entity list as a global skill default.

Treat the block as approved requirements when the user states it. Do not re-ask for privacy minimization after the user opts out. Do not silently shrink catalogs to three to five executive KPIs.

## Rule 1 — Maximum useful measures and metrics (50+ target)

| Catalog | Target when gold has multiple facts and dims | Hard rule |
|---|---|---|
| `measure_catalog.md` | **50+ supported** rows when evidence allows | Do not stop at 3–5 |
| `metric_catalog.md` | **50+ supported** contextual metrics when evidence allows | Promote measures with time/dim/ratio/share/trend context |
| `kpi_catalog.md` | Strategic subset (often 10–25) | Decision KPIs only, but still rich |
| Presentation | **Visible** measures + metrics + KPIs in the live browser report | Executive tab shows top 5–8; dedicated **All Measures** and **All Metrics** tabs show **50+ live values each** when gold supports it |

Thin catalogs with rich gold are a **FAIL**. Cataloguing 50+ rows in Markdown while the browser only shows ~8 executive cards is also a **FAIL**.

If catalogs fall below the target while many gold facts/dims have unmapped counts/amounts/status mixes:

1. Document the shortfall in `insight_backlog.md` and analytics report with exact missing proofs
2. Mark analytics / presentation status `WARN` or `BLOCKED`
3. Re-warn on the Attention Board / Gap Register with an agent recommendation to expand coverage
4. Acceptance gate must run `scripts/check_analytics_coverage.py` — **FAIL** when gold has 3+ facts/marts and catalogs are below target (unless shortfall is explicitly documented as impossible)

`kpi_catalog` staying smaller is fine. Thin `measure_catalog` / `metric_catalog` while gold can support more is not. Do not treat a 10–15 measure executive list as analytics complete.

Also read [kpi-discovery-framework.md](kpi-discovery-framework.md) and [universal-analytics-framework.md](universal-analytics-framework.md).

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

## Rule 5 — Full catalog coverage in presentation

`kpi_figure_coverage.md` must contain **every** row from:

- `measure_catalog.md` (supported/recommended/trusted)
- `metric_catalog.md` (supported/recommended/trusted)
- `kpi_catalog.md`
- `KPI_DEFINITION_CONTRACTS.md` rows that are APPROVED or BLOCKED/DEFERRED

Each row: `RENDERED` | `BLOCKED` | `DEFERRED` with reason and (for RENDERED) SQL proof path.

Do not only map the executive KPI cards. Supporting tabs must absorb measures and metrics.

## Rule 5b — Visible density in the live browser report (hard)

Catalogs and `kpi_figure_coverage.md` alone are **not** enough. The refreshable web report the human opens must **show** the coverage:

| Surface | Minimum when gold has 3+ facts/marts |
|---|---|
| Executive / Overview | Top strategic KPIs (cards) |
| **All Measures** tab (or equivalent) | **50+** live measure values as cards and/or a filterable table (name + value + group) |
| **All Metrics** tab (or equivalent) | **50+** live metric values as cards and/or a table |
| Charts | Status/partner/product/time visuals plus quality callouts |

Required implementation pattern:

1. `data_access.py` (or equivalent) runs live SQL that returns a **measure board** list of 50+ `{name, value, group}` rows and a **metric board** of 30+ rows.
2. `report_builder.py` / HTML renders those boards in dedicated tabs the user can click — not only buried in Report Info prose.
3. `serve_report.py --smoke-test` asserts visible card/table counts (`measure_cards >= 50`, `metric_cards >= 50`) before presentation passes.
4. `check_presentation_coverage.py` **FAIL**s when the presentation Python/HTML has no All Measures / All Metrics board, or smoke density checks fail.

Forbidden:

- “75 measures in measure_catalog.md” while Overview still shows only 8 cards
- Marking presentation complete because `kpi_figure_coverage.md` lists RENDERED rows that are not visible in the browser
- Only printing catalog counts in Report Info without live values

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

A single KPI-card proof is **not** enough when 50+ measures and 50+ metrics are RENDERED. `check_presentation_coverage.py` **FAIL**s when RENDERED board density is high and `sql_verification/` has too few executed proofs with captured results.

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
| Presentation | Catalogs hit 50+/50+ but live HTML still shows only executive KPI cards (no All Measures / All Metrics boards) |
| Presentation | Privacy opt-out recorded but report still says it avoids/hides identifiers or applies privacy minimization |

## Related references

- [kpi-discovery-framework.md](kpi-discovery-framework.md)
- [gold-dimension-completeness.md](gold-dimension-completeness.md)
- [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md)
- [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md)
- [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md)
- [stakeholder-layer-and-presentation-guide.md](stakeholder-layer-and-presentation-guide.md)
