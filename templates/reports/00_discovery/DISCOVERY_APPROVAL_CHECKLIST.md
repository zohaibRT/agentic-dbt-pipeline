# Discovery Approval Checklist

## Template Use

Use this file as the fixed structure for `reports/agent/00_discovery/DISCOVERY_APPROVAL_CHECKLIST.md`.
Replace `TODO` with `PASS`, `WARN`, `FAIL`, `BLOCKED`, or `N/A`.

## Required Outputs

| Check | Status | Evidence / Notes |
|---|---|---|
| Discovery report exists | TODO | `reports/agent/00_discovery/discovery_report.md` |
| Requirements file exists | TODO | `reports/agent/00_discovery/requirements.md` |
| Cardinality report exists | TODO | `reports/agent/00_discovery/cardinality_report.md` |
| Relationship profile exists | TODO | `reports/agent/00_discovery/relationship_profile.md` |
| SQL proof folder exists | TODO | `reports/agent/00_discovery/sql_proofs/` |
| Pipeline status updated | TODO | `reports/agent/PIPELINE_STATUS.md` |
| Context tree updated | TODO | `reports/agent/CONTEXT_TREE.md` |
| Requirements traceability matrix updated | TODO | `reports/agent/REQUIREMENTS_TRACEABILITY_MATRIX.md` |

## Source Scope

| Check | Status | Evidence / Notes |
|---|---|---|
| Correct dbt profile identified | TODO | |
| Correct adapter identified | TODO | |
| Correct database or catalog inspected | TODO | |
| Correct source schema inspected | TODO | |
| Source tables discovered from metadata, not guessed | TODO | |
| No alternate source profiled without approval | TODO | |

## Evidence Quality

| Check | Status | Evidence / Notes |
|---|---|---|
| Table inventory captured | TODO | |
| Row counts captured | TODO | |
| Key checks captured where possible | TODO | |
| Relationship/cardinality checks captured where possible | TODO | |
| Status/date/measure checks captured where possible | TODO | |
| Sensitive or ambiguous fields reviewed | TODO | |
| Open questions listed | TODO | |

## Final Discovery Decision

Decision: TODO

Allowed values:

- `APPROVED`
- `APPROVED WITH CONDITIONS`
- `NOT APPROVED`

Reason:

- <reason>

Required changes before next phase:

- <changes or "None">

Approved project rules to carry forward:

- <rules or "None">
