# Phase Plan Approval

Use this before every phase that creates files, changes dbt behavior, or builds warehouse objects. Run [discovery-requirements.md](discovery-requirements.md) first for a new/full-pipeline request.

## Core rule

Before implementation, explain the phase plan in Markdown and wait for user approval. Include the data-engineering decision check from [data-engineer-decision-gate.md](data-engineer-decision-gate.md) so the design is reviewed before build.

Default plan file:

```text
<project.root>/AGENT_PLAN.md
```

The same Markdown should also be summarized in chat so the user can approve without opening files.

Do not create or modify models, seeds, snapshots, workflows, semantic files, or warehouse schemas for a phase until the user approves that phase plan.

## Applies to these phases

- Init / project setup
- Packages and source YAML
- Bronze / staging
- Silver / intermediate
- Gold / marts
- Semantic layer
- Project evaluator
- Docs
- CI
- Agents Schema
- Refactors, cleanup, or schema behavior changes

Read-only discovery commands are allowed before approval when they are needed to make the plan accurate, such as `dbt debug`, `dbt ls`, metadata queries, row counts, or file inspection. Keep discovery lightweight and summarize what was learned.

## What the plan must explain

For each phase, include:

- Phase name and goal
- Inputs used: domain, profile, source schema, source tables, project rules
- What will be created or changed
- Target folders, files, and warehouse schemas
- Planned models, grains, materializations, and naming
- Planned joins, mappings, metrics, and privacy handling when relevant
- Data-engineering decisions, evidence, and which choices need user approval
- Tests and documentation to add
- dbt packages/macros involved
- Validation commands to run after changes
- Commit boundary for the phase
- Assumptions, risks, and open questions

## Approval wording

End each phase plan with:

```text
Approval needed before build:
Reply "approve <phase>" to continue, or tell me what to change.
```

Examples:

```text
approve sources
approve bronze
approve silver
approve gold
approve semantic
approve evaluator
approve docs
```

If the user approves with plain language such as "yes", "go ahead", or "looks good", treat it as approval for the current phase only.

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

### Rules I Will Follow
- <source/ref rule>
- <schema isolation rule>
- <privacy or mapping rule>
- <materialization rule>

### Data Engineer Decision Check
| Decision | Choice | Evidence | Needs User Approval? |
|---|---|---|---|
| Grain | <one row per ...> | <source/profile evidence> | <yes/no> |
| Keys | <key columns/tests> | <uniqueness/null checks> | <yes/no> |
| Joins | <join/cardinality plan> | <relationship/profile evidence> | <yes/no> |
| Privacy | <include/exclude/mask fields> | <column names/rules> | <yes/no> |
| Materialization | <view/table/incremental> | <volume/use case> | <yes/no> |

### Validation
```powershell
<commands>
```

### Commit Boundary
<what files belong in the phase commit>

### Assumptions And Questions
- <assumption or question>

### Approval Needed Before Build
Reply `approve <phase>` to continue, or tell me what to change.
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
8. Move to the next phase and repeat the plan/approval process.

## Do not

- Treat approval for one phase as approval for all future phases.
- Hide important business logic in code without explaining it first.
- Build gold marts or semantic metrics before the user understands the planned facts, dimensions, metrics, and privacy handling.
- Continue after the plan changes materially; update the plan and ask again.
