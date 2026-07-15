# Gold Dimension Completeness

Use this during gold/marts discovery and build. Also read [marts-spec.md](marts-spec.md), [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md), and [cardinality-validation.md](cardinality-validation.md).

## Problem this prevents

A gold layer with only facts and a bridge is **not** a complete star schema. If bronze has entity/lookup tables that describe the facts (whatever that domain uses), gold must either:

1. Build privacy-safe dimensions, or
2. Register each missing dimension as `BLOCKED` / `DEFERRED` with proof and a required user decision

Do **not** mark gold complete as a silent fact-only slice without that register. Do not invent unsupported dimensions. Do not skip safe non-PII dimensions because sensitive ones are blocked.

## Mandatory dimension inventory

Before approving or completing gold, create this table in `gold_discovery.md` and `gold_report.md`:

| Candidate dimension | Source/bronze/silver evidence | Why it is a dimension | Decision | Privacy handling | Proof | Blocks complete star? |
|---|---|---|---|---|---|---|
| <entity> | <model/table> | <describes facts> | `BUILD` / `BUILD_PRIVACY_SAFE` / `DEFERRED` / `BLOCKED` / `NOT_NEEDED` | <hash/exclude attrs/n/a> | `<proof>` | <yes/no> |

Every included first-pass entity/lookup table from discovery should appear at least once.

## Default dimension classes to evaluate

Evaluate classes from **this warehouse’s evidence only**. Do not assume an industry shape.

| Class | Typical sources (examples only) | Default when evidence exists |
|---|---|---|
| Entity dimensions | accounts, customers, counterparties, vendors, employees, orgs | `BUILD_PRIVACY_SAFE` if PII; else `BUILD`. If user opted out of privacy minimization, prefer `BUILD` with slicing attributes |
| Channel / location / org | channels, sites, departments, regions — when present | `BUILD` with business name for chart labels |
| Product / offer / catalog | products, plans, SKUs, catalogs — when present | `BUILD` when unique grain proven; else `BLOCKED` with proof |
| Method / type dimensions | payment methods, transaction types, categories — when present | `BUILD` when unique |
| Status / type dimensions | low-cardinality codes used by facts | `BUILD` as code dimensions **with labels** for presentation, or keep as degenerate attributes with `label_dictionary.md` |
| Date dimension | any fact date/timestamp | `BUILD` when any fact has usable dates — mandatory for trend KPIs |
| Degenerate dimensions | document numbers, external ids kept on fact | Document as degenerate; not a separate dim |

Required when evidence exists: **entity (or equivalent), date, status/labels**, plus any other descriptive classes proven in discovery. See [reporting-coverage-requirements.md](reporting-coverage-requirements.md).

## Privacy-safe dimension pattern (mandatory option)

When entity keys are sensitive but structurally unique:

1. Do **not** drop the dimension entirely as the first choice.
2. Prefer `BUILD_PRIVACY_SAFE`:
   - surrogate or hashed business key
   - exclude clear-text direct identifiers and always-exclude classes (see [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md)); discover actual sensitive columns from this project
   - keep only safe descriptive attributes needed for slicing
3. Keep foreign keys on facts as hashed/pseudonymized keys that match the dimension key, or document an unknown-member row for unmatched keys.
4. Ask the user only when hashing policy or attribute allowlist is unclear.

Excluding all entity keys from facts **and** building zero dimensions leaves reporting without slicers. That is a WARN/BLOCKED incomplete star, not a finished gold layer.

## Silver prerequisite

Silver must not silently drop lookup/entity tables that discovery marked `included`.

| Silver treatment | When allowed |
|---|---|
| Promote to `int_*` entity/reference models | Default for included lookups/entities |
| Keep as reference-only | Temporary, with gold dimension plan pointing at them |
| Exclude from silver | Only with explicit defer/blocked reason and discovery alignment |

If silver has facts but omitted entity/lookup tables that discovery marked included, gold planning must call that out as a silver gap before “no dimensions available.”

## Fact-first builds

A temporary fact-first build is allowed only when:

1. The dimension inventory is written
2. Every missing dimension is `DEFERRED` or `BLOCKED` with proof
3. `PIPELINE_STATUS` says gold is incomplete for star-schema / analytics / presentation
4. Next prompt is dimensional resolution, not “gold complete → semantic KPIs”

Never describe fact-only gold as a complete marts layer.

## Completion rule

Gold/marts is incomplete when:

- Facts exist and dimension count is 0, and no dimension inventory register exists
- Included entity/lookup tables have no BUILD/DEFERRED/BLOCKED decision
- Date fields exist on facts and no date dimension / time-spine decision is recorded
- Privacy blocked entity dims, but no privacy-safe alternative was proposed
- Facts removed all dimension foreign keys with no unknown-member or hashed-key strategy
- KPIs/metrics are claimed ready without dimensions needed for those slices

## Checker

```powershell
python <skill>/scripts/check_gold_star_shape.py --root <project.root>
```

Fails when gold has `fct_` models, zero `dim_` models, and no dimension inventory section documenting deferred/blocked dimensions.
