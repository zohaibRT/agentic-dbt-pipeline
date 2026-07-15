# Stakeholder Layer And Presentation Guide

Use this when explaining progress to humans and when designing the presentation layer.

Also read [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md), [human-attention-reporting.md](human-attention-reporting.md), [reporting-standards.md](reporting-standards.md), and [presentation-layer.md](presentation-layer.md).

## Part A — Explain after every layer

Use this 7-point script in chat after every checkpoint:

1. **Status** — PASS / WARN / BLOCKED
2. **What we built** — models, tables, row counts
3. **What we proved** — short proof highlights
4. **What is trusted now** — safe for business use
5. **What is still blocked** — Attention Board IDs + KPI impact (re-warn every time)
6. **Agent recommends** — concrete preferred rule per OPEN ID + Accept / Override / Defer
7. **What next Yes allows / does not allow**
8. **Decision needed from you** — accept recommendations, override, or defer

Always re-warn: because of these blockers / missing data / unclear definitions, these KPIs stay missing until you accept or override the agent recommendations. See [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md) and [recommendation-and-review.md](recommendation-and-review.md).

| Audience | Open first |
|---|---|
| Business / exec | `HUMAN_ATTENTION_BOARD.md` + `KPI_GAP_REGISTER.md` |
| Data engineer | Phase report + `sql_proofs/_proof_index.md` |
| Auditor | `LAYER_VERIFICATION_LEDGER.md` + `KPI_DEFINITION_CONTRACTS.md` |

## Part B — Layer-by-layer talking points

### Discovery

Explain: processes found, included vs deferred tables, privacy/money/date/status risks, candidate vs blocked metrics.  
Show: `discovery_report.md`, `requirements.md`, Attention Board, Gap Register.  
Do not claim final KPIs or dashboards.

### Setup / Sources

Explain: project ready, schemas isolated, source YAML/tests.  
Show: setup/sources reports. No business KPIs yet.

### Bronze

Explain: 1:1 landing, row match, raw statuses/dates/PII preserved.  
Show: bronze report + row proofs. Say clearly: landing, not reporting.

### Silver

Explain: joins, orphan flags, what mappings were not applied.  
Show: silver + join safety. Say: no invented Active/churn/revenue rules.

### Gold

Explain: facts/dims/bridges, star completeness, privacy, measures vs KPIs.  
Show: gold report, Gap Register, Attention Board.  
Say: gold facts ≠ approved KPIs.

### Semantic / Insights

Explain: only approved contracts become live metrics; backlog remains blocked.  
Show: KPI contracts, catalogs, `dashboard_spec.md`, Gap Register.

### Presentation

Explain: only APPROVED KPIs on cards; blocked on Blocked / Needs input.  
Show: browser report or Power BI pages per Part C.

### Final delivery

Explain: ready vs deferred, remaining OPEN gaps, how to re-verify.  
Show: `final_delivery.md`, Attention Board, Gap Register, verification guide.

## Part C — What to show in a presentation

Use the five report pillars. Organize by business purpose, not table names.

Hard requirements from [reporting-coverage-requirements.md](reporting-coverage-requirements.md):

1. Maximize measures/metrics (50+/30+ targets when gold allows).
2. Build conformed dimensions present in this warehouse (entity, date, status, and any channel/product/org dims with evidence) for slicing.
3. Honor privacy opt-out when the user stated it.
4. Every categorical axis must show business names via `label_dictionary.md` — blank ticks are a FAIL.
5. Map every measure/metric/kpi catalog row in `kpi_figure_coverage.md`.
6. Live SQL for every RENDERED chart before presentation complete.

| Page / tab | Show | Do not show |
|---|---|---|
| Cover / context | Domain, date range, refresh, validation status | Schema dumps |
| Executive overview | 3–5 approved KPI cards + caveats | Blocked KPIs as live |
| KPI scorecard | Trusted KPIs with definition and reconciliation | Unreconciled metrics |
| Trends & variance | Proven date bases only | Ambiguous/empty dates |
| Drivers / segments | Approved safe dimensions only | Clear-text PII |
| Operations / exceptions | Orphans, failures, quality flags | Silent failure hiding |
| Blocked / Needs input | Gap Register OPEN rows + decisions needed | Fake near-ready KPI cards |
| Recommendations | Attention Board IDs and unlock impact | Vague “improve quality” only |
| Report information | Definitions, lineage, proof links | Secrets |

Canvas order on each main page: header → KPI cards → primary chart → drivers → detail.

## Part D — One-slide layer template

```text
Layer: ____________   Status: PASS / WARN / BLOCKED
Built: ____________
Trusted now: ____________
Blocked (Attention / Gap Register): ____________
→ Without this fix we cannot show: ____________
Evidence: reports/agent/KPI_GAP_REGISTER.md
Next Yes allows: ____________
Next Yes does NOT unlock blocked KPIs unless OPEN IDs are answered.
```
