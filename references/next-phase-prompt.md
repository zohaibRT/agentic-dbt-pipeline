# Next Phase Prompt

Use this after every completed or blocked checkpoint when another phase is recommended.

The goal is to keep the data engineer in control without forcing exact magic phrases such as `approve sources`, `approve bronze`, `approve silver`, or `approve gold`.

## Core rule

After every completed phase, prepare the exact next-phase execution prompt, save it to `reports/agent/NEXT_PHASE_PROMPT.md`, print a visible Markdown control-panel summary in chat, paste the exact prompt in chat, and ask a simple approval question. When the agent runtime supports native questions, buttons, choice prompts, or approval widgets, use that interactive UI so the data engineer can click approval instead of copying, pasting, or typing a magic phrase.

The interactive question is **not** a replacement for the chat summary. Do not show only a native question card, approval widget, file diff, or hidden `NEXT_PHASE_PROMPT.md` reference. The user must see a normal chat message immediately above the question that explains what completed, what passed or failed, what the next phase will do, what it will not do, and how to approve.

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

## Approved next-phase context bundle

When the user approves the displayed next-phase prompt, do not execute `reports/agent/NEXT_PHASE_PROMPT.md` in isolation. First reload the phase context bundle so the original project rules, project memory, and prior validation are still active.

Required context bundle before running the approved next phase:

1. `SKILL.md`
2. `prompt.md`
3. Phase-specific references required by `SKILL.md`
4. `AGENT_PLAN.md`
5. `reports/agent/PIPELINE_STATUS.md`
6. `reports/agent/CONTEXT_TREE.md`
7. `reports/agent/00_discovery/requirements.md` when it exists, falling back to legacy `reports/agent/requirements.md` only when the canonical file is absent
8. The latest relevant phase report, such as `reports/agent/<completed_phase>_report.md`
9. `reports/agent/NEXT_PHASE_PROMPT.md`
10. Project knowledge files when present: `AGENT_KNOWLEDGE.md`, `docs/dbt_knowledge.md`, `docs/business_rules.md`, `.agents/project_knowledge.md`

`NEXT_PHASE_PROMPT.md` answers what exact checkpoint to run next. The context bundle answers how to behave safely, what already happened, what must not be forgotten, which approvals are scoped, and which validation/reporting rules still apply.

If any required context file is missing, continue only when the missing file is not applicable yet, and document the missing/not-applicable item in the phase plan or report. Do not use missing context as permission to ignore source safety, schema isolation, privacy, validation, commit, presentation, or approval rules.

## Interactive approval question

Prefer a platform-native interactive question when available. In Codex, use `request_user_input` or the current native question/approval UI when that tool is available in the active mode. In other agent runtimes, use the equivalent choice, button, or approval widget.

Recommended question:

```text
Do you want me to run this next-phase prompt as written?
```

Recommended options:

- Yes, run this prompt (Recommended) - approves only the displayed prompt for the active checkpoint.
- Tell me what to change - pauses so the user can provide changes; revise `AGENT_PLAN.md` and `reports/agent/NEXT_PHASE_PROMPT.md`, then ask again.
- Not now - pauses without running the next phase.

If the runtime only supports two options, use:

- Yes, run this prompt (Recommended)
- Tell me what to change

Do not set an automatic approval timeout. If the runtime requires a fallback or default result, default to not approved.

If native interactive questions are unavailable, use the text fallback:

```text
Do you want me to run this next-phase prompt as written? Reply Yes to proceed, or tell me what to change.
```

## Safety rules

- Do not proceed without explicit user approval.
- Do not treat silence as approval.
- Do not auto-run the next phase immediately after completing a phase.
- Do not hide the next-phase prompt.
- Do not tell the user only that the prompt is in `NEXT_PHASE_PROMPT.md`.
- Do not show only an interactive question without a visible Markdown completion summary directly before it.
- Do not ask the user to reply `Yes` when a native interactive question is available.
- Do not ask only for `approve <phase>` without showing the exact prompt.
- Do not make the user copy/paste the generated next-phase prompt back into chat when an interactive approval question is available.
- Do not execute `NEXT_PHASE_PROMPT.md` without reloading the approved next-phase context bundle.
- Always show what will be run before asking approval.
- Always save the prompt under `reports/agent/NEXT_PHASE_PROMPT.md`.

## Required chat output after each phase

After every completed phase, the chat summary must include:

1. Current checkpoint and status.
2. Short phase completion summary: what was done, built, and validated.
3. Validation results: pass, warn, fail, skipped, and any important evidence.
4. Next recommended phase and why it is next.
5. What the next phase will build or change.
6. Files/reports that will be created in the next phase.
7. What is included.
8. What is not included.
9. Known caveats or deferred items.
10. Exact next-phase execution prompt pasted in chat, not only linked by path.
11. Interactive approval question when available; text fallback when not available.

Use this visible chat shape immediately before any interactive approval question:

````markdown
## Phase Complete: <completed phase friendly name>

Status: <PASS / WARN / FAIL / BLOCKED>

What was completed:
- <short result>
- <short result>

Validation:
- <command or proof summary>: <PASS / WARN / FAIL / BLOCKED>

Reports written:
- `reports/agent/<phase>/<phase>_report.md`
- `reports/agent/PIPELINE_STATUS.md`
- `reports/agent/CONTEXT_TREE.md`

What needs review:
- <warning, open decision, blocker, or "None">

## Next Recommended Phase: <next phase friendly name>

Goal:
- <plain-language goal>

Includes:
- <included scope>

Does not include:
- <explicit excluded scope>

How to approve:
Use the clickable question below and choose **Yes, run this prompt**, or choose **Tell me what to change**.

Next-phase prompt file: `reports/agent/NEXT_PHASE_PROMPT.md`

The next phase prompt I will run if approved:
```text
<paste exact NEXT_PHASE_PROMPT.md content or the exact runnable prompt section>
```
````

If the phase status is `FAIL` or `BLOCKED`, do not ask for approval to continue as written. Show the same summary, explain the blocker, and ask what to fix or provide.

Use this text fallback when interactive questions are unavailable:

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

Use a native interactive question when available:

- Question: Do you want me to run this next-phase prompt as written?
- Recommended option: Yes, run this prompt
- Other options: Tell me what to change; Not now

Text fallback: Do you want me to run this next-phase prompt as written? Reply Yes to proceed, or tell me what to change.
````

## Phase-specific prompt content

The exact prompt must be specific to the actual project state and previous phase outputs. Include:

- The completed phase and report path.
- The context bundle files that must be reloaded before execution.
- The recommended next phase and why it is next.
- Current project name/root, profile, adapter/database, source schema, and target schemas when known.
- Models, files, reports, or workflow artifacts expected in the next phase.
- Layer paths and schemas for layer work.
- Privacy, unknown field, key performance indicator, mapping, schema isolation, validation, and commit boundaries relevant to the next phase.
- Deferred or blocked items that must not be silently implemented.

Do not use stale, generic, or domain-specific examples as the next-phase prompt unless they match the current project evidence.
