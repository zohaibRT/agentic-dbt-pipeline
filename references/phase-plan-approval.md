# Phase Plan Approval

Use this before every non-setup phase that creates models, seeds, snapshots, semantic files, documentation files, workflow files, or warehouse objects. Run [discovery-requirements.md](discovery-requirements.md) first for a new/full-pipeline request.

Project setup and configuration is handled by [bootstrap.md](bootstrap.md). It auto-runs as setup-only after the discovery requirements checkpoint is accepted, unless a setup safety gate requires user approval.

Discovery acceptance is not build approval. Interpret user responses by the active workflow checkpoint. At the discovery checkpoint, approval moves only to resolved source confirmation and automatic project setup and configuration. After setup, stop at the next phase plan and ask for approval before generating source YAML, building bronze/staging, or moving into any later phase.

## Core rule

Before implementation, run phase-specific discovery from [phased-discovery.md](phased-discovery.md), add the agent recommendation from [recommendation-and-review.md](recommendation-and-review.md), explain the phase plan in Markdown, and wait for user approval. Include the data-engineering decision check from [data-engineer-decision-gate.md](data-engineer-decision-gate.md) so the design is reviewed before build.

Default plan file:

```text
<project.root>/AGENT_PLAN.md
```

The same Markdown should also be summarized in chat so the user can approve without opening files.

Do not create or modify models, seeds, snapshots, workflows, semantic files, documentation files, or warehouse schemas for a phase until the user approves that phase plan.

One approval authorizes only the current checkpoint or named phase. It never authorizes the whole remaining pipeline unless the user explicitly approves multiple named future phases in the same response. Even then, complete each phase report, validation, and next-phase prompt before starting the next approved phase.

## Applies to these phases

- Packages and source YAML
- Bronze / staging
- Silver / intermediate
- Gold / marts
- Semantic layer
- Project evaluator
- Docs
- Analytics insight reporting
- Presentation layer and Power BI or business intelligence handoff
- CI
- Agents Schema
- Refactors, cleanup, or schema behavior changes

Initialization/project setup belongs to automatic project setup and configuration only when it stays inside the setup-only boundary. If setup would overwrite files, change profile behavior, create warehouse objects, or alter schema behavior, stop and ask before continuing.

Read-only discovery commands are allowed before approval when they are needed to make the plan accurate, such as `dbt debug`, `dbt ls`, metadata queries, row counts, or file inspection. Keep discovery lightweight and summarize what was learned.

## What the plan must explain

For each phase, include:

- Phase name and goal
- Phase-specific discovery findings and report path
- Inputs used: domain, profile, source schema, source tables, project rules
- What will be created or changed
- Target folders, files, and warehouse schemas
- Planned models, grains, materializations, and naming
- Planned joins, mappings, metrics, and privacy handling when relevant
- Project knowledge used from `project_rules`, `AGENT_KNOWLEDGE.md`, `docs/dbt_knowledge.md`, `docs/business_rules.md`, `.agents/project_knowledge.md`, or `reports/agent/CONTEXT_TREE.md`
- Sensitive fields and unclear coded fields, with the agent's recommended safe default
- Agent recommendation: recommended path, evidence, what looks right, what is not ready yet, confidence, and what requires data engineer approval
- Data-engineering decisions, evidence, and which choices need user approval
- Unknown or unproven source tables, relationships, business processes, required metrics, data quality rules, required output models, or reporting needs, plus what work is blocked or deferred because of them
- Tests and documentation to add
- Mermaid diagrams to add or update, plus verification method when relevant
- dbt packages/macros involved
- Validation commands to run after changes
- Commit boundary for the phase
- Assumptions, risks, and open questions

## Approval wording

Approval is based on the displayed active checkpoint plan or next-phase prompt, not a magic phrase.

For a phase plan before implementation, end with:

```text
Approval needed before build.
Do you want me to run this phase plan as written? Reply Yes to proceed, or tell me what to change.
```

When the agent runtime supports native questions, buttons, choice prompts, or approval widgets, ask the approval as an interactive question instead of only plain text. In Codex, use `request_user_input` or the current native question/approval UI when that tool is available in the active mode.

Recommended question:

```text
Do you want me to run this phase plan as written?
```

Recommended options:

- Yes, run this phase plan (Recommended) - approves only the displayed active checkpoint plan.
- Tell me what to change - pauses so the user can revise scope, models, metrics, privacy, validation, or files.
- Not now - pauses without starting the phase.

Do not set an automatic approval timeout. If interactive questions are unavailable, use the text fallback above.

Natural approval responses count as approval for the displayed plan only:

- Yes
- Proceed
- Approved
- Continue
- Run this prompt
- Looks good
- Go ahead
- Yes, run this
- Approved as written

The active checkpoint is the control mechanism: discovery, setup, sources, bronze/staging, silver/intermediate, gold/marts, semantic layer, evaluator, documentation, analytics insight reporting, presentation layer, continuous integration, Agents Schema, commit, and push are separate checkpoints. Any approval that does not explicitly name additional future phases applies only to the active checkpoint.

Silence is never approval. If the user changes scope, models, key performance indicators, privacy, schema, validation, materialization, or files, update `AGENT_PLAN.md`, show the revised plan, and ask again before proceeding.

## Markdown template

````markdown
# dbt Agent Plan

## Current Phase: <phase>

### Goal
<what this phase will accomplish>

### Inputs
- Domain: <domain>
- dbt profile: <profile>
- Source schema: <source_schema>
- Source name: <source_name>
- Layer/schema target: <target_schema_or_layer>

### What I Will Build
| Item | Type | Grain / purpose | Target |
|---|---|---|---|
| <name> | <model/source/seed/workflow> | <grain or purpose> | <folder/schema> |

### Layer Folder Convention
- Active physical layer folders: `models/<layer_1_name>/`, `models/<layer_2_name>/`, `models/<layer_3_name>/`
- Role names: staging, intermediate, marts
- Duplicate alias folders found? <yes/no; if yes, stop and ask which convention is canonical>

### Rules I Will Follow
- <source/ref rule>
- <schema isolation rule>
- <privacy or mapping rule>
- <materialization rule>

### Agent Recommendation
- Recommended path: <what I recommend for this phase>
- Why: <evidence from discovery, source profiling, dbt files, or validation>

### What Looks Right
- <safe or well-supported choice>

### What Is Not Ready Yet
- <risk, missing data, ambiguous field, or weak assumption>

### Confidence
- Confident about: <validated facts, stable grains/keys/relationships, or safe technical defaults>
- Less confident about: <business meaning, privacy choices, ambiguous fields, metric dates, rebuild/refactor choices, or anything not proven yet>

### Needs Data Engineer Approval
- <business-impacting choice that must be approved before build>

### Unknowns That Cannot Be Assumed
| Area | What is unclear | Impact | Recommendation | Action before build |
|---|---|---|---|---|
| <source tables / relationships / business process / metrics / data quality / output models / reporting> | <unknown item> | <models, tests, metrics, or presentation affected> | <safe default or defer> | <ask / block / proceed only for independent scope> |

### Not Deciding Alone
- <privacy, metric, mapping, grain, schema, cost, or production behavior I will not choose silently>

### Sensitive And Unclear Fields
| Field | Source table | Concern | Recommended default | Needs User Approval? |
|---|---|---|---|---|
| <field_name> | <table_name> | <sensitive/unclear/business meaning unknown> | <exclude/mask/hash/pass through raw/defer mapping> | <yes/no> |

### Project Knowledge Used
| Source | Rule / Knowledge | Applied How | Conflict? |
|---|---|---|---|
| <file or prompt> | <rule> | <implementation or plan impact> | <none / needs approval> |

### Data Engineer Decision Check
| Decision | Choice | Evidence | Needs User Approval? |
|---|---|---|---|
| Grain | <one row per ...> | <source/profile evidence> | <yes/no> |
| Keys | <key columns/tests> | <uniqueness/null checks> | <yes/no> |
| Joins | <join/cardinality plan> | <relationship/profile evidence> | <yes/no> |
| Bridge tables | <needed / not needed / deferred> | <many-to-many profiling and BI relationship evidence> | <yes/no> |
| Privacy | <include/exclude/mask fields> | <column names/rules> | <yes/no> |
| Materialization | <view/table/incremental> | <volume/use case> | <yes/no> |

### Validation
```powershell
<commands>
```

### Mermaid Diagrams
| Diagram | Mermaid type | Purpose | Verification plan |
|---|---|---|---|
| <file or section> | <erDiagram/flowchart/etc.> | <what it shows> | <viewer or Mermaid CLI check> |

### Commit Boundary
<what files belong in the phase commit>

### Assumptions And Questions
- <assumption or question>

### Approval Needed Before Build
Use a native interactive approval question when available:

- Question: Do you want me to run this phase plan as written?
- Recommended option: Yes, run this phase plan
- Other options: Tell me what to change; Not now

Text fallback: Do you want me to run this phase plan as written? Reply Yes to proceed, or tell me what to change.
````

## After approval

After the user approves:

1. Implement only the approved phase.
2. Run the promised validation.
3. Update `AGENT_PLAN.md` with a short result section for the phase.
4. Create/update the phase report in `reports/agent/` using [phase-completion-report.md](phase-completion-report.md).
5. Update `reports/agent/CONTEXT_TREE.md` using [context-tree.md](context-tree.md).
6. Summarize actual files/models built, test results, assumptions used, open decisions, report path, and context tree update.
7. Ask for commit approval according to [git-workflow.md](git-workflow.md).
8. Read [next-phase-prompt.md](next-phase-prompt.md), write/update `reports/agent/NEXT_PHASE_PROMPT.md` with the exact recommended next-phase prompt, show it to the user, and ask the interactive approval question when available before running the next phase.

If the user has not approved the displayed next-phase prompt, stop after reporting the completed phase. Do not infer approval from a prior discovery, setup, or layer approval.

## Do not

- Treat approval for one phase as approval for all future phases.
- Require exact magic phrases such as `approve sources`, `approve bronze`, `approve silver`, or `approve gold` after a prompt has been shown.
- Proceed from a natural response unless the next-phase prompt or phase plan was shown first.
- Hide important business logic in code without explaining it first.
- Build gold marts or semantic metrics before the user understands the planned facts, dimensions, metrics, and privacy handling.
- Guess source tables, relationships, business processes, required metrics, data quality rules, required output models, or reporting needs when they are unclear.
- Continue after the plan changes materially; update the plan and ask again.
