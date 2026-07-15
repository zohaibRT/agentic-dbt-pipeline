# Consolidated Migration Guide

This guide indexes all production analytics migration paths for
`agentic-dbt-pipeline`. Use it when upgrading an existing generated project or
reviewing Batches 1–7 changes.

## Authority order

1. Executable validators under `scripts/`
2. `project.config.yml` production policy blocks
3. `SKILL.md` / `AGENTS.md` / `.cursor/rules/`
4. `references/` and `docs/`

When documentation and validators disagree, **validators win** until docs are
updated. Do not weaken final-phase validators for legacy compatibility.

## Migration documents

| Topic | Document |
|---|---|
| Process coverage vs fixed counts (P1) | [analytics-gate-p1-migration.md](analytics-gate-p1-migration.md) |
| Analytics product completeness | [analytics-product-completeness-migration.md](analytics-product-completeness-migration.md) |
| Manifest `unique_id` identity | [manifest-resource-identity-migration.md](manifest-resource-identity-migration.md) |
| KPI contracts + human approval | [kpi-contract-human-approval-migration.md](kpi-contract-human-approval-migration.md) |
| P2 interactive charts / gates | [production_analytics_p2_migration.md](production_analytics_p2_migration.md) |

## Breaking final-phase rules (do not weaken)

| Rule | Behavior |
|---|---|
| Resource identity | Prefer dbt manifest `unique_id`. Ambiguous name-only **fails**. Unambiguous name-only **fails at `--phase final`** when a manifest exists. |
| Warning policy | `acceptance_policy.final_fail_on_warning` + `require_explicit_warning_acceptance`. Unaccepted warnings fail final. |
| Technical vs business | Technical `PASS` is never business approval. |
| Presentation | Tooltip, static fallback, accessible table, offline dependency, and live browser validation are policy-gated; defaults are strict. |
| Synthetic approvals | Allowed only under `fixtures/` paths; independent verifier rejects them elsewhere. |
| Empty coverage | Empty denominators are `NOT_APPLICABLE` / fail — never report 100% for empty sets. |

## Legacy compatibility (allowed only pre-final)

- Filesystem inventory when `target/manifest.json` is missing
- Unambiguous name-only classification rows (migration **warning** before final)
- Advisory measure/metric targets under `completion_mode: process_coverage` (WARN only)

Legacy parsers in older scripts must not bypass these rules. Prefer
`scripts/lib_gate_common.py` (`parse_markdown_tables`, `table_dicts`,
`build_resource_inventory`, `resolve_named_resource`).

## Policy coverage

Run:

```bash
python scripts/check_policy_implementation_coverage.py --root .
```

Every production policy key must be **USED**. The report is written to
`reports/agent/POLICY_IMPLEMENTATION_COVERAGE.md`.

## Recommended upgrade sequence

1. `dbt parse` so `target/manifest.json` exists
2. Stamp classification / fact / exposure docs with `unique_id`
3. Align `project.config.yml` with current skill defaults (remove
   `analytics_policy.fail_on_warning_at_final` if present)
4. Run presentation validators, live browser, independent verifier
5. Run `python scripts/run_acceptance_gate.py --root <project> --phase final --strict`
