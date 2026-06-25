# Subagent Workflow

Use subagents only when they can reduce time without creating conflicting edits or unsafe warehouse actions.

## Good subagent tasks

Subagents are useful for read-only or draft work:

- Source profiling by table group
- Source YAML review
- Proposed staging model plan
- Proposed intermediate join and grain review
- Proposed mart/fact/dimension design
- Mapping coverage review
- Test and documentation review
- Project evaluator warning summary
- Final handoff review

## Tasks the main agent must keep

The main agent remains responsible for:

- Reading the skill instructions and deciding the workflow
- Running `dbt debug`, `dbt deps`, `dbt parse`, `dbt build`, and `dbt docs generate`
- Editing shared files unless the user explicitly asks for subagent edits
- Resolving conflicts between subagent recommendations
- Asking the user for missing inputs or approvals
- Committing and pushing
- Final answer and project status

## Parallel pattern

After inputs and source access are resolved, split safe work:

1. Main agent runs read-only discovery and gathers requirements.
2. Main agent runs project setup and configuration, dependency install, and source generation when needed.
3. Main agent gives each subagent a narrow task with read-only instructions.
4. Subagents return concise findings using the handoff format below.
5. Main agent merges findings into a single implementation plan.
6. Main agent edits files, runs dbt validation, commits, and summarizes.

## Handoff format

Ask each subagent to return:

```text
Scope:
Files or tables reviewed:
Findings:
Recommended models/tests/docs:
Risks or open questions:
SQL snippets, if useful:
```

## Guardrails

- Do not send secrets, full `profiles.yml`, passwords, tokens, or private keys to subagents.
- Do not let multiple agents edit the same files at the same time.
- Do not let subagents run destructive SQL, production commands, commits, or pushes.
- Prefer subagents for analysis; keep implementation serialized through the main agent.
- If subagent findings disagree, the main agent summarizes the disagreement and chooses the safer path or asks the user.

## Suggested subagent split

For a full project:

- Subagent A: source profiling and raw table grains
- Subagent B: staging tests and naming review
- Subagent C: intermediate joins, mappings, and grain risks
- Subagent D: marts, metrics, semantic layer, and docs review

Use fewer subagents for small projects. Do not add subagents if setup overhead would take longer than doing the work directly.
