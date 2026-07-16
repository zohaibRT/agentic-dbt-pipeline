# Final production enforcement migration

This document describes the P0 final-enforcement contract for validator
statuses, human-approval coverage, live browser gates, and reconciliation
waivers.

## Machine-readable validator results

Every production validator invoked by `run_acceptance_gate.py` supports
`--output-json <path>` and writes a `ValidatorResult` with
`schema_version: "1.0"`.

Statuses:

- `PASS` — no errors, no warnings
- `WARN` — warnings only (exit code may still be 0)
- `FAIL` / `BLOCKED` — errors present
- `SKIPPED` — legitimate non-applicable check

Parents must read the JSON status. Exit code 0 must not be treated as PASS when
JSON status is WARN or SKIPPED.

Warnings carry stable `warning_id` values. Final/strict warning acceptance
matches **warning IDs**, not arbitrary message substrings.

## Human approval denominator

`discover_production_kpi_obligations()` builds the denominator from contracts,
catalogs, rendered manifests, page registries, and trusted/executive artifacts.

Coverage = validly approved production obligations / all production obligations.

Technical PASS never counts as business approval.

## Live browser at final

With `presentation_policy.require_live_browser_at_final: true` (default), an
interactive report at phase `final` or `--strict` requires Playwright desktop,
tablet, and mobile validation. `--skip-live` and auto `--allow-skip` are
rejected. Browser SKIPPED is FAIL.

## Reconciliation waivers

Calculated reconciliation FAIL remains FAIL. A valid row in
`reports/agent/RECONCILIATION_WAIVER_REGISTER.md` may yield
`governance_disposition=APPROVED_WAIVER` without converting technical status to
PASS. WARN alone is not a waiver.
