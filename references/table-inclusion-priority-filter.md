# Table Inclusion And Priority Filter

Use this during discovery whenever the source schema has more tables than a first-pass pipeline should model.

Also read [discovery-artifacts.md](discovery-artifacts.md), [discovery-requirements.md](discovery-requirements.md), and [discovery-status-vocabulary.md](discovery-status-vocabulary.md).

## Goal

Make table selection **visible, repeatable, and reviewable**.

Anyone opening discovery should be able to answer:

1. How many tables exist in the source schema?
2. Which tables are in v1 / first pass?
3. Why each table was included, deferred, or excluded?
4. Which tables got deep SQL proofs (`010+`, `020+`, `060+`)?

Do not silently filter tables. Do not create thousands of deep proof files without a documented scope.

## Reusable filter checklist (mandatory)

Use this checklist on every discovery run. Copy the same decisions into `discovery_report.md`, `requirements.md`, and `discovery_raw.json`.

| # | Rule | Required action | Pass condition |
|---|---|---|---|
| 1 | **Keep fact/event tables on the main process** | Identify the first-pass business process from evidence, then include its core facts/events | Every included fact/event is on the named process path |
| 2 | **Keep related dimensions/lookups** | For each included fact, include the minimum related entities and lookups needed for grain, joins, and metrics | Included facts are not orphaned from required parents/lookups |
| 3 | **Exclude audit/log/platform/empty** | Exclude platform, framework, audit, loader, sync, temp, backup, and empty tables unless the user explicitly needs them | Excluded groups are listed with reasons |
| 4 | **Require an `inclusion_reason` for every table** | Set `inclusion_status` = `included` / `deferred` / `excluded` and write `inclusion_reason` for every table in `discovery_raw.json` | No table is missing status or reason |
| 5 | **Ask the user if process scope is unclear** | If multiple processes are plausible, or scope would surprise the business, stop and ask before deep proofs / first-pass modeling | Scope is approved, or uncertainty is marked `BLOCKED` |

Hard rules:

- Do not mark a table `included` without a written `inclusion_reason`.
- Do not deep-proof excluded/deferred tables unless the user expands scope.
- Do not invent a first-pass process when evidence is weak; ask the user.

## Two proof layers

| Layer | Proof | Covers |
|---|---|---|
| Inventory | `001_source_table_inventory.sql` | **All** tables: name + row count |
| Priority / included deep proofs | `010+`, `020+`, `030+`, `040+`, `050+`, `060+` | Only **included** or **priority** tables |

Example for a large schema:

```text
001_source_table_inventory.sql      → 323 tables counted
010_priority_table_row_counts.sql   → 16 included tables recounted with business context
```

## Inclusion statuses

Use exactly these values in `discovery_raw.json` and discovery reports:

| Status | Meaning | Deep proofs? | Build in v1? |
|---|---|---|---|
| `included` | On the first-pass business process path | Yes | Yes, unless blocked |
| `deferred` | Relevant later, not required for first pass | No | No, until re-scoped |
| `excluded` | Outside scope for this project/process | No | No |

Every table must have an `inclusion_reason`.

## Required selection process

Run these steps in order and document them.

### Step 1 — Inventory everything

1. List every table in the confirmed source schema.
2. Capture exact or best-available row counts in `001_source_table_inventory.sql`.
3. Write every table into `discovery_raw.json.tables[]` with at least:
   - `table_name`
   - `row_count`
   - `inclusion_status`
   - `inclusion_reason`

### Step 2 — Identify the first-pass business process

State the process in plain language before filtering, for example:

- the first-pass business process named from warehouse evidence
- order-to-cash
- claims adjudication
- ticket lifecycle

Sources for the process:

1. User prompt / `project_rules` / `DBT_BUSINESS_DESCRIPTION`
2. Source evidence: table names, keys, statuses, dates, amounts, relationships
3. Domain label only as context, not proof

If the process is unclear, mark scope `BLOCKED` or ask before deep profiling.

### Step 3 — Classify each table

Score each table with this checklist:

| Signal | Prefer `included` when | Prefer `deferred` when | Prefer `excluded` when |
|---|---|---|---|
| Business process fit | Clearly on the first-pass process path | Adjacent process that may matter later | Unrelated process |
| Role | Fact/event, core entity, required lookup/bridge | Optional enrichment, secondary lookup | Technical only |
| Data presence | Non-empty and usable | Empty but structurally important later | Empty and not needed |
| Relationships | Joins to other included tables | Weak or unproven joins | No credible business join |
| Privacy / risk | Safe for bronze/staging with known handling | Sensitive and needs later approval | Out of reporting scope and unused |
| Naming / ownership | Domain tables (`crm_*`, `orders`, `payments_*`) | Shared utility tables with unclear ownership | Platform, audit, loader, sync, temp, backup tables |

Default exclude patterns unless the user explicitly needs them:

- audit / log / history dump tables that are not the business event of record
- platform / framework / agent metadata tables
- loader, sync, staging-temp, backup, archive-only tables
- empty tables with no modeling value for v1
- duplicate copies of the same entity already represented by an included table

### Step 4 — Keep supporting entities for included facts

If a fact/event table is included, also include the minimum related tables needed to model it safely:

- parent entities (account, customer, subscriber)
- child/detail lines (order items, invoice lines)
- required lookups evidenced for the facts (statuses, catalogs, pricing, etc.)
- payment or status companions on the same process path

Do not include every neighbor table. Include only what first-pass grain, joins, and metrics need.

### Step 5 — Document the filter decision

Write the decision in all of these places:

| Location | What to write |
|---|---|
| `discovery_report.md` | Process name, included count, deferred count, excluded count, filter rationale |
| `requirements.md` | Source inclusion requirement with evidence and confidence |
| `discovery_raw.json.scope` | Totals + `notes` describing the filter |
| `discovery_raw.json.tables[]` | Per-table `inclusion_status` + `inclusion_reason` |
| `sql_proofs/_proof_index.md` | Note that `001` covers all tables and deep proofs cover included/priority only |
| `CONTEXT_TREE.md` | Approved or proposed first-pass scope |

### Step 6 — Deep-proof only the included set

For included/priority tables, create the needed deeper proofs:

- row recount / priority row counts (`010+`)
- key checks (`020+`)
- status distributions (`030+`)
- date coverage (`040+`)
- numeric summaries (`050+`)
- relationship checks (`060+`)

For deferred/excluded tables, inventory count is enough unless the user expands scope.

## Required report section

Every discovery report must include:

```markdown
## Table Inclusion Filter

- First-pass business process: <process name>
- Total tables in schema: <count>
- Included (v1 / priority): <count>
- Deferred: <count>
- Excluded: <count>
- Filter rationale: <short explanation>
- Inventory proof: `sql_proofs/001_source_table_inventory.sql`
- Priority proof set: `sql_proofs/010_...` and related deep proofs
- User approval needed for scope? <yes/no and why>
```

Also keep the Source Inventory table with an inclusion column (`yes` / `defer` / `no`) that matches `discovery_raw.json`.

## Example rationale language

Good:

> First-pass process is <named from evidence>. Included 16 tables on that process path. Excluded 270 platform, audit, operational, or empty tables outside first pass. Deferred adjacent tables for later phase discovery.

Bad:

> Selected important tables.

## Ask the user when

Stop and ask before treating a table as included if:

- the first-pass business process is unclear
- multiple business processes are equally plausible
- a large sensitive table would enter gold/presentation
- excluding a non-empty core-looking table may surprise the business
- the user already named tables/processes that conflict with the inferred filter

If process scope is unclear, do not invent it. Ask the user, mark the scope decision `BLOCKED` until answered, and keep deep proofs limited to already-approved tables only.

## Scope lock and repeatability (mandatory)

Same profile, database, source schema, and first-pass business process must produce the **same included table set** unless the user explicitly re-scopes.

### Why this exists

Discovery judgment on borderline tables (agreements, credit notes, device conditions, addresses, attempts) can otherwise drift across runs (for example 28 vs 26). That makes it hard to know which discovery is “correct.”

Rule: **the approved first-pass scope is the source of truth.** Later runs reuse it. They do not invent a new count.

### Fingerprint

Build a scope fingerprint from:

| Field | Source |
|---|---|
| `profile` | `DBT_PROFILE_NAME` / `core_profile.json` |
| `database` | active profile database/catalog |
| `source_schema` | `DBT_SOURCE_SCHEMA` |
| `business_process` | named first-pass process from discovery |

If those four match a prior discovery, treat it as the same discovery target.

### Reuse order

1. If this project already has an **approved** scope lock (`first_pass_scope.json` with `lock_status: approved`, or an approved `DISCOVERY_APPROVAL_CHECKLIST.md` plus `discovery_raw.json`), **reuse that exact included/deferred/excluded set**.
2. If the user points at a prior project/run with the same fingerprint, compare with `scripts/compare_discovery_scope.py` and **reuse the approved prior included list** unless the user asks to re-scope.
3. Only invent a new inclusion set when no prior approved scope exists for this fingerprint.
4. If a fresh classification would change an existing approved included set, **stop and ask**. Do not silently move tables between included and deferred.

### Borderline table default (domain-neutral)

When no prior approved scope exists, classify borderline neighbors as **`deferred` by default**:

| Prefer `included` | Prefer `deferred` (until user asks) |
|---|---|
| Fact/event on the named process | Optional enrichment (conditions, attributes, notes) |
| Required parent of an included fact | Adjacent commercial docs (agreements, credit notes) unless named |
| Required child/detail line of an included fact | Secondary attempt/log companions that are not the event of record |
| Required lookup/bridge to test grain or joins | Nice-to-have slicing tables with no required FK for first-pass grain |

Do not flip these defaults between runs without user approval.

### Which discovery is correct?

| Situation | Correct scope |
|---|---|
| One run approved, later run differs | The **approved** run |
| Two fresh runs, neither approved | Neither is authoritative yet — compare with the script, apply borderline defaults, ask the user once |
| User explicitly re-scopes | The new user-approved list |

After approval, write/update:

```text
reports/agent/00_discovery/first_pass_scope.json
```

with fingerprint, `lock_status: approved`, sorted `included_tables`, `deferred_tables`, `excluded_count`, and the discovery report path.

### Proof filenames

Keep proof **bands** stable (`001`, `010`, `020`, … `080`). Do not rename bands between runs for the same fingerprint. Optional mid-band proofs (`025`, `035`) are allowed only when they support a warning already in the report; they must not change the included table set.

## Completion rule

Discovery is incomplete when:

- the reusable filter checklist items 1-5 are missing from the discovery report
- fact/event tables on the main process were dropped without reason
- included facts are missing required related dimensions/lookups
- audit/log/platform/empty tables were included without explicit user need
- any table lacks `inclusion_status` and `inclusion_reason` in `discovery_raw.json`
- process scope was unclear and the user was not asked
- deep proofs exist for tables never marked included/priority
- included tables are missing from priority proofs without explanation
- the discovery report has no Table Inclusion Filter section
- scope was narrowed but `001_source_table_inventory.sql` was skipped
- an approved same-fingerprint scope exists and this run changed included tables without user re-scope approval
- `first_pass_scope.json` is missing after discovery approval
- two discovery runs for the same fingerprint disagree and the agent did not stop to ask which scope to lock
