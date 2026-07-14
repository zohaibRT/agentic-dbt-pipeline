# Gold Dimension Completeness

Use this during gold/marts discovery and build. Also read [marts-spec.md](marts-spec.md), [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md), and [cardinality-validation.md](cardinality-validation.md).

## Problem this prevents

A gold layer with only facts and a bridge is **not** a complete star schema. If bronze has accounts, partners, programs, SKUs, payment methods, or other entities, gold must either:

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

| Class | Typical sources | Default when evidence exists |
|---|---|---|
| Entity dimensions | accounts, customers, subscribers, partners, programs, companies | `BUILD_PRIVACY_SAFE` if PII; else `BUILD` |
| Product / offer dimensions | SKUs, products, pricing plans, durations, protection plans | `BUILD` when unique grain proven; else `BLOCKED` with proof |
| Method / channel dimensions | payment methods, sales channels | `BUILD` when unique |
| Status / type dimensions | low-cardinality codes used by facts | `BUILD` as code dimensions, or keep as degenerate attributes with note |
| Date dimension | any fact date/timestamp | `BUILD` when any fact has usable dates |
| Degenerate dimensions | invoice numbers, order numbers kept on fact | Document as degenerate; not a separate dim |

## Privacy-safe dimension pattern (mandatory option)

When entity keys are sensitive but structurally unique:

1. Do **not** drop the dimension entirely as the first choice.
2. Prefer `BUILD_PRIVACY_SAFE`:
   - surrogate or hashed business key
   - exclude clear-text names, phones, emails, national ids, bank details, addresses, device identifiers
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

If silver has facts but omitted partners/programs/SKUs that were included in discovery, gold planning must call that out as a silver gap before “no dimensions available.”

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
