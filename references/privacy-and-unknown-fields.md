# Privacy And Unknown Field Policy

Use this when source discovery or phase discovery finds direct identifiers, sensitive fields, protected health information, personally identifiable information, or unclear coded fields such as `field_1`, `field_2`, and `field_3`.

## Core rule

The agent must recommend a safe default instead of only asking the user what to do.

Do not infer private-field exposure or business-code meanings from column names or sample-looking values alone. If the source does not prove the meaning, keep the decision visible in the plan, report, and context tree.

## Safe default by layer

| Layer | Direct identifiers and sensitive fields | Unknown coded fields |
|---|---|---|
| Sources | Document the fields and source table only | Document values and frequency profile without claiming meaning |
| Bronze / staging | Preserve source-shaped fields when needed for traceability, but mark them as sensitive or unclear | Preserve as raw code columns with clear descriptions such as "raw unmapped code" |
| Silver / intermediate | Keep only when needed for joins, validation, or approved business logic | Join mapping seeds or reference tables only when definitions are provided |
| Gold / marts | Exclude, mask, or hash by default unless the user explicitly approves clear-text exposure | Exclude by default, or expose as raw audit fields only when the user explicitly approves |
| Semantic layer | Do not define metrics or dimensions on direct identifiers or unknown codes | Do not create semantic dimensions from unknown code fields |

## Privacy recommendation pattern

When fields such as patient names, member numbers, medical record numbers, email addresses, phone numbers, addresses, national identifiers, insurance identifiers, birth dates, or clinical identifiers are found, include a recommendation like:

```text
Recommendation: keep these fields available only in bronze/staging for traceability, keep them out of gold/marts by default, and use masked or hashed versions only when downstream analysis needs stable identifiers.

Needs your approval:
- Approve the safe default: exclude clear-text patient identifiers from gold/marts.
- Or tell me which identifiers may be exposed, masked, or hashed for this local development run.
```

For local development, clear-text exposure is still a user decision. If the user approves keeping sensitive fields as-is for local development, document that approval and do not carry it forward as a production default.

## Unknown code recommendation pattern

When columns such as `field_1`, `field_2`, `field_3`, short code columns, or system-looking values have unclear meaning, include a recommendation like:

```text
Recommendation: pass these fields through bronze/staging as raw unmapped codes, do not rename them to business-friendly names, do not create mapping seeds yet, and exclude them from gold/marts until definitions are provided.

Needs your approval:
- Approve the safe default.
- Or provide definitions/mappings so I can create mapping seeds or reference joins in the intermediate layer.
```

Do not create guessed mappings such as `M = Male`, `P1 = Priority 1`, or `WEB = Web Channel` unless the source metadata, a reliable reference table, or the user confirms the meaning.

Do not present an `Agent guess` column for unclear coded fields. Use wording such as `Possible meaning, not confirmed` only when it is useful, and keep the recommended action as defer mapping until definitions are provided. Never let a possible meaning drive model names, mappings, tests, metrics, or gold/marts fields without confirmation.

Do not rename unclear generic fields by default. Columns such as `field_1`, `field_2`, `field_3`, short unexplained code fields, or system-looking placeholders must keep their source column names in bronze/staging until the user provides definitions or explicitly asks the agent to suggest possible names. If the user asks for suggestions, first profile distinct values and patterns, propose candidate names with confidence and evidence, then stop for approval before changing model SQL or YAML. Suggested names are advisory only; they must not be implemented until the user approves the exact final names.

## Mapping seeds

Create mapping seeds only when:

- The user provides definitions.
- A reliable source reference table exists.
- Source metadata or documentation proves the mapping.

If mapping definitions are missing:

- Keep raw code fields in bronze/staging.
- Mention them in the silver/intermediate plan as deferred mappings.
- Exclude them from gold/marts by default.
- Add them to `reports/agent/CONTEXT_TREE.md` as open business definitions.

## Required reporting

In discovery reports, phase plans, phase reports, and final handoffs, include:

- Field name and source table.
- Why it is considered sensitive or unclear.
- Recommended default.
- User decision needed, if any.
- Whether the choice was approved, deferred, or implemented.

Never include full sensitive record samples in reports, commits, or final messages.
