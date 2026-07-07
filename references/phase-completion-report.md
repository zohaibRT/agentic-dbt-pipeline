# Phase Completion Report

Use this after every phase that performs discovery, changes files, runs dbt commands, or builds warehouse objects.

## Core rule

After each phase, create or update a Markdown report that tells the user what happened, what is correct, what is warning or wrong, and what needs review. Also apply [reporting-standards.md](reporting-standards.md): every report must include context and strategy, key performance indicators, trend analysis and variance, insights and attribution, and recommendations and next steps when relevant. If a pillar is not supported yet, mark it `Not applicable`, `Not available yet`, or `Deferred` with the reason.

Read [report-artifact-organization.md](report-artifact-organization.md) before writing files. Use the managed folder layout there for new projects.

Root control-plane folder:

```text
<project.root>/reports/agent/
```

If `{project.root}` does not exist yet, use the current workspace/run root:

```text
<workspace.root>/reports/agent/
```

Root control-plane files:

```text
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
reports/agent/NEXT_PHASE_PROMPT.md
reports/agent/REPORT_INDEX.md
reports/agent/HUMAN_VERIFICATION_GUIDE.md
```

Phase reports should be written to the canonical phase folder from [report-artifact-organization.md](report-artifact-organization.md). Examples:

```text
reports/agent/00_discovery/discovery_report.md
reports/agent/00_discovery/requirements.md
reports/agent/01_setup/setup_report.md
reports/agent/02_sources/sources_report.md
reports/agent/03_bronze/bronze_report.md
reports/agent/04_silver/silver_report.md
reports/agent/05_gold/gold_report.md
reports/agent/06_semantic/semantic_report.md
reports/agent/07_evaluator/evaluator_report.md
reports/agent/08_documentation/docs_report.md
reports/agent/09_analytics_insights/analytics_insight_reporting_report.md
reports/agent/10_presentation/presentation_report.md
reports/agent/10_presentation/powerbi_model_plan.md
reports/agent/10_presentation/dashboard_pages.md
reports/agent/10_presentation/dax_measures.md
reports/agent/final_delivery.md
reports/agent/11_operations/ci_report.md
reports/agent/11_operations/agents_schema_report.md
reports/agent/NEXT_PHASE_PROMPT.md
```

For existing projects that already use a flat `reports/agent/` layout, do not move files without user approval. Create `REPORT_INDEX.md`, keep reading legacy files when canonical files are absent, and write new artifacts to the canonical folders unless the user asks to preserve the old layout.

For new projects, do not create phase-specific files directly under `reports/agent/`. If a phase-specific file is accidentally written at the root, copy or move it to the canonical phase folder before reporting completion, then update `REPORT_INDEX.md` with the canonical path. Keep only the root control-plane files at the root.

## Discovery report exception

`reports/agent/00_discovery/discovery_report.md` must be project-oriented, not setup-oriented. Use discovery sections such as:

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

Do not lead discovery reports with setup details such as `.env` creation, profile search, virtual environment, package installation, git, continuous integration, or project setup tasks. Mention configuration only as brief input context at the end.

Discovery reports are mandatory even before dbt project initialization. Write the file first, then summarize it in chat with the file path.

`reports/agent/00_discovery/requirements.md` is also mandatory for initial discovery. It must capture source-derived requirements, evidence, confidence, recommended defaults, open questions, user-provided requirements, and deferred or blocked scope. Do not hide requirements only in chat.

## Chat result summary

After every completed or blocked checkpoint, send a short visible Markdown chat summary in a normal assistant message in addition to writing the report files. This summary is the user's quick control panel; it must show what changed, whether validation passed, exactly what the next approval would allow, and the exact next-phase prompt. Do not only say "the exact prompt is in `NEXT_PHASE_PROMPT.md`"; paste the runnable prompt or exact prompt section in chat before asking approval. Do not show only a native/clickable question card, and do not put the whole summary only inside the question widget; the summary must appear as a separate assistant message directly above the question so the user can tell the phase finished intentionally.

Use this format for discovery, project setup and configuration, sources, bronze/staging, silver/intermediate, gold/marts, semantic layer, evaluator, documentation, presentation layer, continuous integration, Agents Schema, commits, and blocked checkpoints. Omit a section only when it is truly not applicable, and write `None` for empty open decisions.

```markdown
<Phase friendly name> <complete / blocked / awaiting approval>

Current checkpoint: <checkpoint name>
Status: <PASS / WARN / FAIL / BLOCKED / awaiting approval>
Report: `<reports/agent/<phase_folder>/<phase>_report.md>`

Goal:
<one sentence describing the phase goal>

What was completed:
- <completed action or result>

What was built or changed:
| Item | Detail |
|---|---|
| <project/model/schema/file/package/workflow> | <short detail> |

Validation:
| Check | Result |
|---|---|
| <command or validation query> | <PASS/WARN/FAIL/SKIPPED plus short evidence> |

Included:
- <tables/models/files/scope included>

Not included:
- <explicitly excluded or deferred scope>

Open decisions:
- <decision, warning, or risk requiring review; or None>

Next checkpoint: <phase name>
Next goal: <one sentence>
Next includes: <short scope>
Next does not include: <short non-scope>
Next-phase prompt file: `reports/agent/NEXT_PHASE_PROMPT.md`
The next phase prompt I will use is:
```text
<paste the exact prompt from reports/agent/NEXT_PHASE_PROMPT.md>
```
Approval needed: ask with a native interactive question when available.
- Question: Do you want me to run this next-phase prompt as written?
- Recommended option: Yes, run this prompt
- Other options: Tell me what to change; Not now
- Text fallback: Reply Yes to proceed, or tell me what to change.
```

Do not replace the summary with a one-line status such as `Silver complete - gold/marts approval pending`. The summary must include what was completed, what passed/warned/failed, what is recommended next, what the next phase will and will not include, and the exact prompt to be approved.

For project setup and configuration, the summary must make clear that setup was automatic/setup-only and did not approve source YAML or model builds.

For layer phases, add the important data verification results directly in chat, not only in the report. Include row counts, unexpected empty models, grain/key result, relationship result, and any blocker before asking for the next approval.

For phase plans awaiting approval, use the same shape but write `What will be built or changed` and `Planned validation` instead of completed/built/validation results.

## What to include

Every phase report must include:

- Phase name and date/time
- Why this report exists
- How to use this report
- What the data engineer should verify
- What to do next after verification
- Context and strategy: objective, scope, audience, target, benchmark, or why the phase matters
- Approval status and approved plan reference
- Files created or changed
- Warehouse schemas/tables/views created or changed
- Models, seeds, semantic files, workflows, or documentation created
- Source YAML location for the Sources phase; generated or curated source YAML must be under `models/sources/`
- Commands run
- Validation results: pass, warn, fail, skipped
- Data verification results after bronze/staging, silver/intermediate, and gold/marts builds
- SQL proof files for every phase that ran warehouse discovery, source profiling, model validation, metric verification, evaluator checks, or reporting verification
- Cardinality and grain validation results when joins, relationships, final models, or Power BI relationships are in scope
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
- Analytics insight reporting files: `analytics_insight_report.md`, `reporting_catalog.md`, `kpi_catalog.md`, `dashboard_spec.md`, `insight_backlog.md`, `reporting_readiness_scorecard.md`
- Presentation-layer artifacts when approved, such as `presentation_layer_report.md`, `powerbi_model_plan.md`, `dashboard_pages.md`, `dax_measures.md`, and `final_delivery.md`
- Metric verification results for any implemented key performance indicator, including expected versus actual numerator, denominator, and final result
- Key performance indicator reconciliation results for any approved or implemented key performance indicator, including proof files, source-to-final variance, first failing layer, and cardinality/grain proof
- Trend analysis and variance when supported, such as row-count movement, period movement, target variance, baseline variance, or validation deltas
- Insights and attribution: what the evidence suggests, likely drivers, anomalies, outliers, blockers, and confidence
- Recommendations and next steps: actionable next phase, data engineer decision, risk, resource need, or approval checkpoint
- Assumptions used
- Open questions or user decisions
- Commit status
- Next recommended phase
- Exact next-phase execution prompt and `reports/agent/NEXT_PHASE_PROMPT.md` path
- Approved next-phase context bundle that must be reloaded before executing `NEXT_PHASE_PROMPT.md`
- Files/reports that will be created in the next phase
- What is included and not included in the next phase
- Known caveats or deferred items for the next phase
- Interactive approval question from [next-phase-prompt.md](next-phase-prompt.md), or the text fallback when interactive questions are unavailable

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

## Context and Strategy
- Objective: <why this phase or report matters>
- Scope: <what was reviewed or changed>
- Target or benchmark: <target/baseline if known, or Not available yet with reason>

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

## SQL Proof Files
| Proof File | What It Proves | Captured Result Summary | Status |
|---|---|---|---|
| `reports/agent/<phase>/sql_proofs/<proof>.sql` | <row count, grain, relationship, metric, or quality proof> | <small result summary captured in the file header> | <PASS/WARN/FAIL/BLOCKED/SKIPPED> |

## Profile Target Schema Hygiene
| Profile | Adapter | Database | Target Schema | Source Schema | Safe? | Evidence / Action |
|---|---|---|---|---|---|---|
| <profile> | <adapter> | <database> | <target_schema> | <source_schema> | <PASS/WARN/BLOCKED/SKIPPED> | <routing or required change> |

## Key Performance Indicator Definitions
| Key Performance Indicator | Business Meaning | Source Model | Grain | Numerator | Denominator | Filters | Time Field | Result / Caveat | Approval |
|---|---|---|---|---|---|---|---|---|---|
| <name> | <meaning> | <model> | <grain> | <numerator> | <denominator or not applicable> | <filters> | <date field> | <validation/caveat> | <approved/deferred/blocked> |

## Metric Verification Results
| Key Performance Indicator | Layer Checked | Expected Numerator | Actual Numerator | Expected Denominator | Actual Denominator | Expected Result | Actual Result | Status | Evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| <metric> | <gold/semantic/presentation> | <value> | <value> | <value or not applicable> | <value or not applicable> | <value> | <value> | <PASS/WARN/FAIL/BLOCKED> | <query, command, or report reference> |

## Key Performance Indicator Reconciliation Results
| Key Performance Indicator | First Layer Result | Final Layer Result | Variance | Variance Percentage | First Failing Layer | Proof Files | Status |
|---|---:|---:|---:|---:|---|---|---|
| <name> | <value> | <value> | <difference> | <percent> | <layer or Not applicable> | <paths> | <PASS/WARN/FAIL/BLOCKED> |

## Cardinality And Grain Validation Results
| Model Or Join | Expected Grain/Cardinality | Observed Result | Row Multiplier | Row Loss | Status | Evidence |
|---|---|---|---:|---:|---|---|
| <model/join> | <expected> | <observed> | <value> | <value> | <PASS/WARN/FAIL/BLOCKED> | <query/report> |

## Trend Analysis and Variance
| Item | Current Result | Comparison / Target | Variance | Evidence | Status |
|---|---|---|---|---|---|
| <metric, row count, validation result, or trend> | <current> | <prior/baseline/target or Not available yet> | <difference or Not applicable> | <query/report/check> | <PASS/WARN/FAIL/SKIPPED> |

## Insights and Attribution
- Insight: <what the evidence suggests>
- Attribution or driver: <likely cause, dimension, source behavior, data quality issue, or Not available yet>
- Confidence: <high/medium/low plus why>

## Recommendations and Next Steps
- Recommendation: <what should happen next>
- Action needed: <approval, business input, fix, follow-up build, or None>
- Risk/resource note: <risk, dependency, or None>

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

## Next Phase Prompt
Path: `reports/agent/NEXT_PHASE_PROMPT.md`

Summary:
- Recommended next phase: <next_phase>
- Included: <short scope>
- Not included: <short non-scope>
- Known caveats: <deferred or uncertain items>
- Approval question: Use a native interactive question when available, but only after the visible Markdown control-panel summary has already been sent as a normal assistant message. Keep the widget text short: Do you want me to run this next-phase prompt as written? Recommended option: Yes, run this prompt. Text fallback: Reply Yes to proceed, or tell me what to change.
- Context bundle before execution: `SKILL.md`, `prompt.md`, phase references, `AGENT_PLAN.md`, `PIPELINE_STATUS.md`, `CONTEXT_TREE.md`, `requirements.md` when present, latest phase report, and `NEXT_PHASE_PROMPT.md`.
```

## Pipeline status file

Update `reports/agent/PIPELINE_STATUS.md` after every phase:

```markdown
# Pipeline Status

| Phase | Status | Report | Commit |
|---|---|---|---|
| Discovery | PASS | reports/agent/00_discovery/discovery_report.md; reports/agent/00_discovery/requirements.md | n/a |
| Project setup and configuration | PASS | reports/agent/01_setup/setup_report.md | <hash or pending> |
```

## Context tree

Update `reports/agent/CONTEXT_TREE.md` after every phase using [context-tree.md](context-tree.md). The context tree should summarize the phase input, output, decisions, report link, status, and next action.

## Next phase prompt

After every completed or blocked checkpoint, read [next-phase-prompt.md](next-phase-prompt.md), write/update `reports/agent/NEXT_PHASE_PROMPT.md`, share the required chat control-panel summary, show the exact prompt in chat, and ask the interactive approval question from that file when available. If the user asks for changes, revise the next-phase prompt and `AGENT_PLAN.md` before proceeding.

## Commit behavior

Include the phase report, `PIPELINE_STATUS.md`, `CONTEXT_TREE.md`, and `NEXT_PHASE_PROMPT.md` in the same phase commit when commit approval is granted.

Do not commit reports that contain secrets, passwords, tokens, or sensitive record samples.
