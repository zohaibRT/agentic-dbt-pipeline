# Phase Completion Report

Use this after every phase that performs discovery, changes files, runs dbt commands, or builds warehouse objects.

## Core rule

After each phase, create or update a Markdown report that tells the user what happened, what is correct, what is warning or wrong, and what needs review.

Default folder:

```text
<project.root>/reports/agent/
```

If `{project.root}` does not exist yet, use the current workspace/run root:

```text
<workspace.root>/reports/agent/
```

Default files:

```text
reports/agent/<phase>_report.md
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
```

Examples:

```text
reports/agent/discovery_report.md
reports/agent/sources_discovery.md
reports/agent/bronze_discovery.md
reports/agent/silver_discovery.md
reports/agent/gold_discovery.md
reports/agent/setup_report.md
reports/agent/sources_report.md
reports/agent/bronze_report.md
reports/agent/silver_report.md
reports/agent/gold_report.md
reports/agent/semantic_report.md
reports/agent/evaluator_report.md
reports/agent/docs_report.md
reports/agent/ci_report.md
reports/agent/agents_schema_report.md
```

## Discovery report exception

`reports/agent/discovery_report.md` must be project-oriented, not setup-oriented. Use discovery sections such as:

- Project/domain summary
- Source tables and row counts
- Entities and relationships
- Mermaid discovery diagrams, including entity relationship diagram when credible relationships exist
- Candidate business processes
- Candidate facts, dimensions, and metrics
- Data quality and completeness notes
- Privacy/sensitive-field observations
- Recommended medallion direction for sources, bronze/staging, silver/intermediate, and gold/marts
- Agent recommendation
- What looks right
- What is not ready yet
- Items needing data engineer approval
- Open modeling decisions for the data engineer
- Inputs used: domain, dbt profile name without credentials, source schema, source tables inspected

Do not lead discovery reports with setup details such as `.env` creation, profile search, virtual environment, package installation, git, continuous integration, or bootstrap tasks. Mention configuration only as brief input context at the end.

Discovery reports are mandatory even before dbt project initialization. Write the file first, then summarize it in chat with the file path.

## What to include

Every phase report must include:

- Phase name and date/time
- Approval status and approved plan reference
- Files created or changed
- Warehouse schemas/tables/views created or changed
- Models, seeds, semantic files, workflows, or documentation created
- Source YAML location for the Sources phase; generated or curated source YAML must be under `models/sources/`
- Commands run
- Validation results: pass, warn, fail, skipped
- Data verification results after bronze/staging, silver/intermediate, and gold/marts builds
- Agent recommendation followed, changed, or deferred
- Project knowledge used and whether it was applied, deferred, or conflicted
- What looks correct
- What looks wrong or risky
- Confidence: what is proven vs what still needs confirmation
- Data-engineering decisions implemented, inferred, or still open
- Mermaid diagrams added/changed and visibility verification status
- Data quality notes
- Privacy/sensitive-field notes
- Profile target schema hygiene for project setup and configuration
- Key performance indicator definitions for gold/marts, semantic layer, presentation layer, and final delivery
- Assumptions used
- Open questions or user decisions
- Commit status
- Next recommended phase

## Status labels

Use these labels consistently:

| Label | Meaning |
|---|---|
| `PASS` | Completed and validated |
| `WARN` | Works, but user should review |
| `FAIL` | Failed validation or unsafe to continue |
| `SKIPPED` | Intentionally not run |
| `BLOCKED` | Waiting on user/external action |

## Phase report template

```markdown
# <Phase> Report

## Status
Overall: <PASS | WARN | FAIL | SKIPPED | BLOCKED>

## What Was Done
- <action>

## Files Changed
| File | Purpose |
|---|---|
| <path> | <why changed> |

## Warehouse Changes
| Object | Type | Purpose |
|---|---|---|
| <schema.object> | <table/view/schema> | <why created/changed> |

## Validation Results
| Check | Result | Notes |
|---|---|---|
| <command/check> | <PASS/WARN/FAIL/SKIPPED> | <important output> |

## Data Verification Results
| Layer | Model | Row Count | Expected Evidence | Grain Check | Relationship Check | Measure Check | Result | Notes |
|---|---:|---:|---|---|---|---|---|---|
| <layer> | <model> | <row_count> | <source/upstream comparison> | <PASS/WARN/FAIL/SKIPPED> | <PASS/WARN/FAIL/SKIPPED> | <PASS/WARN/FAIL/SKIPPED> | <PASS/WARN/FAIL/BLOCKED> | <important finding> |

## Profile Target Schema Hygiene
| Profile | Adapter | Database | Target Schema | Source Schema | Safe? | Evidence / Action |
|---|---|---|---|---|---|---|
| <profile> | <adapter> | <database> | <target_schema> | <source_schema> | <PASS/WARN/BLOCKED/SKIPPED> | <routing or required change> |

## Key Performance Indicator Definitions
| Key Performance Indicator | Business Meaning | Source Model | Grain | Numerator | Denominator | Filters | Time Field | Result / Caveat | Approval |
|---|---|---|---|---|---|---|---|---|---|
| <name> | <meaning> | <model> | <grain> | <numerator> | <denominator or not applicable> | <filters> | <date field> | <validation/caveat> | <approved/deferred/blocked> |

## Advanced Data Engineering Review
| Area | Status | Evidence | Action Needed |
|---|---|---|---|
| <area> | <PASS/WARN/FAIL/BLOCKED/SKIPPED> | <evidence> | <next action or none> |

## Mermaid Diagrams
| Diagram | Mermaid type | Verification | Notes |
|---|---|---|---|
| <file or section> | <erDiagram/flowchart/etc.> | <PASS/WARN/FAIL/SKIPPED> | <visibility/parse notes or omitted relationships> |

## Agent Recommendation Outcome
| Recommendation | Outcome | Evidence / Reason |
|---|---|---|
| <recommended action> | <followed/changed/deferred> | <why> |

## Project Knowledge Used
| Source | Rule / Knowledge | Applied How | Conflict? |
|---|---|---|---|
| <file or prompt> | <rule> | <implementation or report impact> | <none / resolved / needs approval> |

## What Looks Correct
- <confirmed-good point>

## What Is Not Ready Yet
- <warning/risk/question>

## Confidence
- Confident about: <validated facts, passing tests, proven relationships, or safe technical defaults>
- Less confident about: <business meaning, privacy choices, ambiguous fields, metric dates, rebuild/refactor choices, or anything not proven yet>

## Needs Data Engineer Approval
- <open approval item, or "None">

## Data Engineer Decisions
| Decision | Implemented Choice | Evidence / Validation | Still Open? |
|---|---|---|---|
| <grain/key/join/privacy/materialization/etc.> | <choice> | <check/result> | <yes/no> |

## Assumptions
- <assumption>

## Open Decisions
- <decision needed, or "None">

## Commit Status
<not asked / skipped / committed <hash> / pushed>

## Next Step
<recommended next phase>
```

## Pipeline status file

Update `reports/agent/PIPELINE_STATUS.md` after every phase:

```markdown
# Pipeline Status

| Phase | Status | Report | Commit |
|---|---|---|---|
| Discovery | PASS | reports/agent/discovery_report.md | n/a |
| Project setup and configuration | PASS | reports/agent/setup_report.md | <hash or pending> |
```

## Context tree

Update `reports/agent/CONTEXT_TREE.md` after every phase using [context-tree.md](context-tree.md). The context tree should summarize the phase input, output, decisions, report link, status, and next action.

## Commit behavior

Include the phase report, `PIPELINE_STATUS.md`, and `CONTEXT_TREE.md` in the same phase commit when commit approval is granted.

Do not commit reports that contain secrets, passwords, tokens, or sensitive record samples.
