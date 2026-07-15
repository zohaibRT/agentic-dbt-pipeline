# Reporting Coverage Requirements

Use this for gold, analytics insight reporting, semantic layer, presentation layer, and final delivery.

These requirements are **hard defaults** whenever the user states them (or pastes them as project rules). They also define the skill’s intended rich-reporting behavior.

## User-stated reporting requirements (binding)

When the user provides rules like the following, apply them for the whole run and write them into `reports/agent/00_discovery/requirements.md`, `CONTEXT_TREE.md`, and `AGENT_PLAN.md`:

```text
1. Maximize supported KPIs/metrics from validated gold — target 50+ in measure/metric catalogs.
2. Build conformed dimensions (partner, program, product/SKU, date, status) for slicing.
3. Do NOT apply privacy minimization unless I explicitly request it.
4. Use label_dictionary.md — every chart axis must show business names, not blank or raw codes.
5. Presentation must map every measure_catalog + metric_catalog + kpi_catalog row in kpi_figure_coverage.md.
6. Run live SQL for every RENDERED chart before marking presentation complete.
```

Treat that block as approved requirements. Do not re-ask for privacy minimization after the user opts out. Do not silently shrink catalogs to three to five executive KPIs.

## Rule 1 — Maximum useful measures and metrics (50+ target)

| Catalog | Target when gold has multiple facts and dims | Hard rule |
|---|---|---|
| `measure_catalog.md` | **50+ supported** rows when evidence allows | Do not stop at 3–5 |
| `metric_catalog.md` | **30+ supported** contextual metrics when evidence allows | Promote measures with time/dim/ratio context |
| `kpi_catalog.md` | Strategic subset (often 10–25) | Decision KPIs only, but still rich |
| Presentation | Render measures + metrics + KPIs across tabs | Executive tab shows top 5–8; other tabs show the rest |

If catalogs fall below the target while many gold facts/dims have unmapped counts/amounts/status mixes:

1. Document the shortfall in `insight_backlog.md` and analytics report with exact missing proofs
2. Mark analytics / presentation status `WARN` or `BLOCKED`
3. Re-warn on the Attention Board / Gap Register with an agent recommendation to expand coverage
4. Acceptance gate must run `scripts/check_analytics_coverage.py` — **FAIL** when gold has 3+ facts/marts and catalogs are below target (unless shortfall is explicitly documented as impossible)

`kpi_catalog` staying smaller is fine. Thin `measure_catalog` / `metric_catalog` while gold can support more is not. Do not treat a 10–15 measure executive list as analytics complete.

Also read [kpi-discovery-framework.md](kpi-discovery-framework.md) and [universal-analytics-framework.md](universal-analytics-framework.md).

## Rule 2 — Conformed dimensions for slicing

When source/bronze/silver evidence exists, gold must evaluate and preferably **BUILD** these classes:

| Dimension class | Examples |
|---|---|
| Partner / channel | channel partners, stores, sales channels |
| Program / corporate | programs, corporate companies, employee programs |
| Product / SKU | master SKUs, partner SKUs, plans, durations |
| Date | date dimension / time spine from fact dates |
| Status / lifecycle | order, subscription, payment, invoice statuses (code dims or mapped labels) |

Do not deliver fact-only gold with blank categorical charts. Prefer dimensions over dropping slicers. See [gold-dimension-completeness.md](gold-dimension-completeness.md).

If a class cannot be built, register `BLOCKED` / `DEFERRED` with proof — still list the blocked KPIs/slices on the Gap Register.

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
| Documentation | Record opt-out in requirements, Context Tree, gold plan, and presentation caveats |
| Recommend, don't block | Mention residual risk once; do not block gold dims for privacy after opt-out |
| Attention Board | Close privacy rows for tier-2 identifiers; no OPEN `Exclude phone/IMEI/serial/...` blockers |
| Gap Register | No OPEN `PRIVACY` blockers for tier-2 identifiers when opt-out is recorded |

Still document tier-1 exclusions once as `CARRY_FORWARD` (secrets, OTP, full IBAN/bank dumps, national IDs, PHI). Do not treat tier-1 as OPEN blockers that stop gold dims or KPI catalogs unless presentation would expose them without user ask.

Still ask once if national IDs, bank accounts, OTP, or medical identifiers would be placed on presentation charts — recommend exclude those columns even under opt-out. Everything else used for slicing proceeds.

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

## Rule 6 — Live SQL for every RENDERED chart

Before marking presentation complete:

1. Confirm the gold object exists in the warehouse (`information_schema` / `\dt` / adapter equivalent)
2. Execute the **exact** presentation SQL used by the chart refresh path
3. Capture actual row counts / aggregates in `sql_verification/` with PASS
4. Hit the report refresh/data endpoint (not only HTML shell `/`) and assert no SQL error
5. Record evidence in `presentation_report.md`

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
| Gold | Missing partner/program/product/date/status dims without BLOCKED register |
| Analytics | `measure_catalog` thin vs available gold; coverage not attempted |
| Presentation | Catalog rows missing from `kpi_figure_coverage.md` |
| Presentation | Blank categorical axes on RENDERED charts |
| Presentation | Live SQL / refresh API not proven for RENDERED charts |
| Final delivery | User opt-out of privacy ignored; dims still privacy-blocked without ask |
| Final delivery | OPEN Attention Board / Gap Register privacy rows for phone/IMEI/serial/fingerprint under recorded opt-out |

## Related references

- [kpi-discovery-framework.md](kpi-discovery-framework.md)
- [gold-dimension-completeness.md](gold-dimension-completeness.md)
- [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md)
- [matplotlib-presentation-layer.md](matplotlib-presentation-layer.md)
- [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md)
- [stakeholder-layer-and-presentation-guide.md](stakeholder-layer-and-presentation-guide.md)
