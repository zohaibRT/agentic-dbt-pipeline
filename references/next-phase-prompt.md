# Next Phase Prompt

Use this after every completed or blocked checkpoint when another phase is recommended.

The goal is to keep the data engineer in control without forcing exact magic phrases such as `approve sources`, `approve bronze`, `approve silver`, or `approve gold`.

## Core rule

After every completed phase, prepare the exact next-phase execution prompt, save it to `reports/agent/NEXT_PHASE_PROMPT.md`, show it in chat, and ask a simple approval question.

The user may approve naturally after seeing the prompt:

- Yes
- Proceed
- Approved
- Continue
- Run this prompt
- Looks good
- Go ahead
- Yes, run this
- Approved as written

Natural approval applies only to the displayed next-phase prompt and only to the active checkpoint. It does not approve later phases, commits, pushes, source switching, privacy changes, schema changes, or any hidden scope.

If the user asks for any change to scope, models, key performance indicators, privacy, schemas, validation, materialization, or files, revise `AGENT_PLAN.md` and `reports/agent/NEXT_PHASE_PROMPT.md`, show the revised prompt, and ask again before proceeding.

## Safety rules

- Do not proceed without explicit user approval.
- Do not treat silence as approval.
- Do not auto-run the next phase immediately after completing a phase.
- Do not hide the next-phase prompt.
- Do not ask only for `approve <phase>` without showing the exact prompt.
- Always show what will be run before asking approval.
- Always save the prompt under `reports/agent/NEXT_PHASE_PROMPT.md`.

## Required chat output after each phase

After every completed phase, the chat summary must include:

1. Short phase completion summary.
2. Validation results.
3. Next recommended phase.
4. Exact next-phase execution prompt.
5. Files/reports that will be created in the next phase.
6. What is included.
7. What is not included.
8. Known caveats or deferred items.
9. Approval question.

Use this approval question:

```text
Do you want me to run this next-phase prompt as written? Reply Yes to proceed, or tell me what to change.
```

## Required files

Minimum required file:

```text
reports/agent/NEXT_PHASE_PROMPT.md
```

Optional phase-specific prompt files:

```text
reports/agent/sources_prompt.md
reports/agent/staging_prompt.md
reports/agent/intermediate_prompt.md
reports/agent/marts_prompt.md
reports/agent/semantic_layer_prompt.md
reports/agent/docs_prompt.md
reports/agent/analytics_insight_reporting_prompt.md
reports/agent/presentation_layer_prompt.md
reports/agent/final_delivery_prompt.md
```

## Template

````markdown
# Next Phase Prompt

## Current completed phase

`<completed_phase>`

## Recommended next phase

`<next_phase>`

## Why this phase is next

<evidence from the completed phase, validation results, pipeline status, and context tree>

## Exact prompt to run

```text
Use the dbt Analytics Engineer skill (`agentic-dbt-pipeline`).
Continue from the completed `<completed_phase>` phase.
workflow_phase: `<next_phase>`

Project context:
- dbt project: `<project_name>`
- profile: `<profile_name>`
- database: `<database_name>`
- source schema: `<source_schema>`
- target schemas: `<target_schemas>`

Use these completed reports:
- reports/agent/PIPELINE_STATUS.md
- reports/agent/CONTEXT_TREE.md
- reports/agent/<completed_phase>_report.md

Build/perform:
- <specific items for the next phase>

Rules:
- <specific rules>
- <privacy rules>
- <validation rules>
- <deferred items>

After completion, write/update:
- reports/agent/<next_phase>_report.md
- reports/agent/PIPELINE_STATUS.md
- reports/agent/CONTEXT_TREE.md
- reports/agent/NEXT_PHASE_PROMPT.md
```

## Included

- <what the next phase includes>

## Not included

- <what the next phase does not include>

## Known caveats

- <uncertain or deferred items>

## Approval question

Do you want me to run this next-phase prompt as written? Reply Yes to proceed, or tell me what to change.
````

## Phase-specific prompt content

The exact prompt must be specific to the actual project state and previous phase outputs. Include:

- The completed phase and report path.
- The recommended next phase and why it is next.
- Current project name/root, profile, adapter/database, source schema, and target schemas when known.
- Models, files, reports, or workflow artifacts expected in the next phase.
- Layer paths and schemas for layer work.
- Privacy, unknown field, key performance indicator, mapping, schema isolation, validation, and commit boundaries relevant to the next phase.
- Deferred or blocked items that must not be silently implemented.

Do not use stale, generic, or domain-specific examples as the next-phase prompt unless they match the current project evidence.
