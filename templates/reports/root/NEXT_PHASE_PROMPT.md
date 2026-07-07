# Next Phase Prompt

## Template Use

Use this file as the fixed structure for `reports/agent/NEXT_PHASE_PROMPT.md`.
After discovery, this should describe only the next approved checkpoint candidate, usually automatic project setup and configuration.

## Prompt

```text
Use the dbt Analytics Engineer skill (`agentic-dbt-pipeline`) and run only the next checkpoint shown below.

Current checkpoint:
<current checkpoint>

Approved context:
- Source schema: <source schema>
- dbt profile: <profile name>
- Adapter: <adapter>
- Discovery requirements: reports/agent/00_discovery/requirements.md
- Pipeline status: reports/agent/PIPELINE_STATUS.md
- Context tree: reports/agent/CONTEXT_TREE.md

Next checkpoint:
<next checkpoint>

Goal:
<one sentence goal>

Includes:
- <included scope>

Does not include:
- <excluded scope>

Validation required:
- <validation command or proof>

Stop conditions:
- <when to stop and ask>
```

## Approval Question

Use a normal chat summary before asking for approval. Use a clickable approval question only when the summary is visibly present directly above it. Otherwise use the text fallback.
