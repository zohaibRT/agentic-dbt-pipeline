# Manifest Resource Identity Migration

## Old name-based behavior

Earlier gates treated model and fact **names** as primary keys. Classification rows, fact catalogs, and exposure docs often keyed only on `fct_*` / `dim_*` stems. Duplicate names across packages, versions, or resource types could silently collapse.

## New unique_id behavior

When `target/manifest.json` exists, **dbt `unique_id`** is the canonical resource key, for example:

- `model.package_name.model_name`
- `source.package_name.source_name.table_name`
- `snapshot.package_name.snapshot_name`
- `exposure.package_name.exposure_name`
- `metric.package_name.metric_name`
- `semantic_model.package_name.semantic_model_name`

Shared inventory in `scripts/lib_gate_common.py` normalizes nodes, sources, exposures, metrics, semantic models, saved queries, and disabled entries into resource records. Classification, fact discovery, and exposure coverage match on `unique_id` first.

## Fallback identity behavior

If the manifest is missing (pre-parse / early phases):

1. Inventory falls back to filesystem discovery.
2. Stable temporary IDs include package and relative path, e.g. `model.local.models.gold.activity_events` — **not** stem-only `model.local.activity_events`.
3. Gates emit a limited-evidence / migration warning.
4. When a manifest appears later, fallback IDs are replaced by manifest `unique_id` values for the same path/name.

## Duplicate-name handling

Identical names may exist in different packages, versions, folders, or resource types (for example a model and a snapshot both named `activity_events`).

- Never collapse resources solely because `name` matches.
- Name-only classification or fact-catalog rows **pass only when unambiguous** (pre-final phases).
- Ambiguous name-only rows **fail** and require `unique_id` (and optionally package / version / path).
- Unambiguous legacy name-only rows emit a **migration warning** before final.
- At `--phase final` with a manifest present, unambiguous name-only rows **fail** — migrate to `unique_id` before release.

## Classification migration

Update `reports/agent/09_analytics_insights/model_classification.md` to include:

| Unique ID | Model | Package | Class | … | Human Approval Status | Status |

Policy lives in `project.config.yml` under `resource_classification_policy`. Coverage denominators use unique_ids of in-scope enabled resources, not a set of names.

Machine recommendations may be recorded, but business classification approval remains human-in-the-loop.

## Fact-catalog migration

`fact_catalog.md` should include `fact_id`, `unique_id`, `resource_name`, `package_name`, and `fact_class`.

Fact discovery order:

1. Approved classification by unique_id  
2. Fact catalog by unique_id  
3. Manifest meta / tags  
4. Lineage / grain evidence  
5. `fct_` prefix fallback only  

Reporting marts are not automatically facts. Event-like names alone are not enough.

## Exposure migration

Prefer manifest exposures. YAML discovery searches models/snapshots/analyses for top-level `exposures:` blocks (not only `exposures.yml`).

Production exposures need owner, business purpose, criticality, refresh expectation, resolvable dependencies, technical validation, and (at final phase) non-stale business approval with real evidence.

Documentation-only coverage rows do **not** satisfy final production coverage when a dbt project and presentation exist.

## Human approval implications

- Technical validation and business approval are separate statuses.
- Fingerprint changes on business-significant exposure fields stale prior approval and force `PENDING_REVIEW`.
- Agents must not self-approve owners, criticality, audience, production status, or sensitive-data publication.
- Synthetic fixture approvals must be labelled (for example `SYNTHETIC_FIXTURE_APPROVAL:...`).
