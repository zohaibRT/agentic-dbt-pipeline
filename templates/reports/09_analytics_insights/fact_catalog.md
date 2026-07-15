# Fact Catalog

## Purpose

Document validated facts available for measures, metrics, key performance indicators, and reporting. Use manifest `unique_id` as the canonical identity.

| Fact ID | Unique ID | Resource Name | Package Name | Version | Fact Class | Business Process | Business Event | Grain | Counting Key | Primary Date | Secondary Date Roles | Measurable Fields | Supported Dimensions | Lifecycle or Snapshot Behavior | Source Models | Reconciliation Source | Machine Confidence | Business Approval Status | Approval Evidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <fact_id> | model.package.name | <name> | <package> | <version or blank> | event_fact / transaction_fact / ... | <process> | <event> | <grain> | <key> | <date> | <roles> | <fields> | <dims> | <behavior> | <sources> | <recon> | HIGH/MEDIUM/LOW | APPROVED/PENDING_REVIEW/... | <evidence> | PASS/WARN/BLOCKED/DEFERRED |

## Fact Caveats

| Unique ID | Caveat | Impact | Action |
|---|---|---|---|
| None | Not applicable | Not applicable | Not applicable |

Legacy name-only rows are accepted only when unambiguous. Ambiguous duplicate names require `unique_id`.
