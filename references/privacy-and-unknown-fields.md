# Privacy And Unknown Field Policy

Use this when source discovery or phase discovery finds direct identifiers, sensitive fields, protected health information, personally identifiable information, or ambiguous, placeholder, abbreviated, or poorly named fields.

## Core rule

The agent must recommend a safe default instead of only asking the user what to do.

Do not infer private-field exposure or business-code meanings from column names or sample-looking values alone. If the source does not prove the meaning, keep the decision visible in the plan, report, and context tree.

## User privacy opt-out (binding)

When the user says any of: `Do NOT apply privacy minimization unless I explicitly request it`, `no privacy until specifically asked`, or equivalent project rules:

1. Do **not** exclude, hash, or drop reporting dimensions for privacy by default.
2. Build conformed dimensions with business labels (partner name, program name, product/SKU name, status labels) needed for charts and slicing.
3. Still exclude **only** secrets, passwords, OTP codes, full bank/IBAN dumps, national IDs, and PHI/medical identifiers from presentation unless the user explicitly asks to expose them — document once as `CARRY_FORWARD`.
4. Record the opt-out in `requirements.md` and `CONTEXT_TREE.md` (short note — not a recurring caution).
5. Do not re-ask for privacy minimization on every later phase after opt-out is recorded.
6. Do **not** keep OPEN Attention Board or KPI Gap Register rows that block gold/marts for phone, IMEI, serial, fingerprint, email, address, or other commercial/operational identifiers.
7. **Presentation under opt-out:** show the full reporting surface. Phone, IMEI, serial, fingerprint, email, address, and device attributes that exist in gold **may appear** on charts, tables, and detail tabs when useful. Do **not** hide them “to be safe,” and do **not** write Report Info lines like `this report avoids phone/IMEI on charts`.

Also read [reporting-coverage-requirements.md](reporting-coverage-requirements.md).

## Identifier tiers (use with opt-out)

| Tier | Examples | Under privacy opt-out | Without opt-out |
|---|---|---|---|
| **Always exclude** | secrets, passwords, OTP, API tokens, full IBAN/account dumps, national IDs, PHI/medical record numbers | Exclude from gold and presentation; document once as `CARRY_FORWARD`, not an OPEN blocker | Same |
| **Reporting operational** | phone, IMEI, serial, fingerprint, device id, email, address | **BUILD in gold and show on presentation** when present (ops/detail tabs, labels, device boards) | Exclude/mask/hash from gold by default |
| **Business descriptive** | partner name, program name, SKU name, status labels | **BUILD** in gold dimensions and charts | May use `BUILD_PRIVACY_SAFE` |

When opt-out is recorded, the agent must **not** recommend `Exclude phone/IMEI/serial/IBAN/fingerprint from gold` as an OPEN decision. Split the rule:

- **Full IBAN / bank dumps / OTP / secrets / national ID / PHI** → tier 1, exclude unless user explicitly asks.
- **Phone / IMEI / serial / fingerprint / email / address** → allowed in gold **and** on the presentation report; do not minimize.

Forbidden under opt-out:

- OPEN Attention Board row: `Direct identifiers | Exclude phone/IMEI/serial/... from gold | Privacy default`
- OPEN KPI Gap Register row with blocker type `PRIVACY` for commercial identifiers
- Re-asking the human to approve privacy minimization on every checkpoint
- Presentation copy such as “privacy minimization OFF; this report avoids phone/IMEI on charts”
- Silently stripping phone/IMEI/serial from charts/tables after the user opted out

Allowed under opt-out:

- One short `CARRY_FORWARD` note: user opted out of privacy minimization; only secrets/OTP/full IBAN/national ID/PHI stay off the report unless explicitly requested.
- Report Info may say: `Privacy minimization: OFF (user rule). Operational identifiers may appear on this report.` — then stop repeating privacy warnings.

## Safe default by layer

| Layer | Direct identifiers and sensitive fields | Unknown coded fields |
|---|---|---|
| Sources | Document the fields and source table only | Document values and frequency profile without claiming meaning |
| Bronze / staging | Preserve source-shaped fields when needed for traceability, but mark them as sensitive or unclear | Preserve as raw code columns with clear descriptions such as "raw unmapped code" |
| Silver / intermediate | Keep only when needed for joins, validation, or approved business logic | Join mapping seeds or reference tables only when definitions are provided |
| Gold / marts | Exclude, mask, or hash by default unless the user explicitly approves clear-text exposure **or** has opted out of privacy minimization for reporting (then tier-2 operational fields may proceed; tier-1 always excluded) | Exclude by default, or expose as raw audit fields only when the user explicitly approves |
| Semantic layer | Do not define metrics or dimensions on direct identifiers or unknown codes unless user opt-out / approval allows descriptive attributes | Do not create semantic dimensions from unknown code fields without definitions or label dictionaries |

## Privacy recommendation pattern

When fields such as patient names, member numbers, medical record numbers, email addresses, phone numbers, addresses, national identifiers, insurance identifiers, birth dates, or clinical identifiers are found, include a recommendation like:

```text
Recommendation (default, no opt-out): keep these fields available only in bronze/staging for traceability, keep them out of gold/marts by default, and use masked or hashed versions only when downstream analysis needs stable identifiers.

Recommendation (privacy opt-out recorded): build reporting dimensions with business labels; allow tier-2 operational identifiers in gold **and on the presentation report** when useful; exclude only tier-1 secrets/OTP/full IBAN/national ID/PHI unless the user explicitly requests exposure. Do not leave OPEN privacy blockers and do not write “this report avoids phone/IMEI”.

Needs your approval (only when opt-out is NOT recorded):
- Approve the safe default: exclude clear-text patient identifiers from gold/marts.
- Or tell me which identifiers may be exposed, masked, or hashed for this local development run.
```

For local development, clear-text exposure is still a user decision. If the user approves keeping sensitive fields as-is for local development, document that approval and do not carry it forward as a production default.

## Unknown code recommendation pattern

When ambiguous, placeholder, abbreviated, generic, system-looking, or poorly named fields have unclear meaning, include a recommendation like:

```text
Recommendation: pass these fields through bronze/staging as raw unmapped codes, do not rename them to business-friendly names, do not create mapping seeds yet, and exclude them from gold/marts until definitions are provided.

Needs your approval:
- Approve the safe default.
- Or provide definitions/mappings so I can create mapping seeds or reference joins in the intermediate layer.
```

Do not create guessed mappings such as `M = Male`, `P1 = Priority 1`, or `WEB = Web Channel` unless the source metadata, a reliable reference table, or the user confirms the meaning.

Do not present an `Agent guess` column for unclear coded fields. Use wording such as `Possible meaning, not confirmed` only when it is useful, and keep the recommended action as defer mapping until definitions are provided. Never let a possible meaning drive model names, mappings, tests, metrics, or gold/marts fields without confirmation.

Do not rename ambiguous or poorly named fields by default. Generic, abbreviated, placeholder, short unexplained code, or system-looking fields must keep their source column names in bronze/staging until the user provides definitions or explicitly asks the agent to suggest possible names. If the user asks for suggestions, first profile distinct values and patterns, propose candidate names with confidence and evidence, then stop for approval before changing model SQL or YAML. Suggested names are advisory only; they must not be implemented until the user approves the exact final names.

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
