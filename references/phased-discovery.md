# Phased Discovery

Use phased discovery so the agent supports the data engineer one layer at a time instead of designing the entire project upfront.

## Core rule

Do not try to fully design bronze, silver, gold, semantic metrics, evaluator exceptions, and CI during the first discovery.

Use:

```text
Project discovery -> sources discovery -> bronze discovery -> silver discovery -> gold discovery -> semantic/evaluator/docs discovery
```

Each phase should discover only what is needed to make the next plan accurate, recommend the best next action with evidence, then ask for approval before implementation.

## Phase discovery scope

| Phase | Discovery focus | What not to do yet |
|---|---|---|
| Project discovery | Source inventory, table counts, obvious entities, high-level risks, user requirements | Do not design every model in detail |
| Sources | Real schemas/tables/columns for source YAML, source names, excluded tables | Do not write staging transformations yet |
| Bronze / staging | Per-table grain, columns, casts, renames, source tests, sensitive columns to pass/drop | Do not design joins or marts |
| Silver / intermediate | Relationships, join cardinality, mapping needs, reusable business logic, grain preservation | Do not finalize BI facts/dims/metrics |
| Gold / marts | Facts, dimensions, reporting marts, metric grains, privacy exposure, materialization | Do not create semantic metrics before marts are approved |
| Semantic layer | Metric definitions on approved gold models, dimensions/entities, time spine | Do not invent metrics not supported by gold |
| Evaluator/docs | Quality warnings, accepted exceptions, docs coverage, exposures | Do not hide unresolved model issues |

## Required behavior

Before every build phase:

1. Run only the read-only checks needed for that phase.
2. State the agent recommendation, what looks right, what is not ready yet, and what needs data engineer approval.
3. Update `AGENT_PLAN.md` with the phase-specific discovery findings and recommendation.
4. Add or update the related phase report under `reports/agent/`.
5. Update `reports/agent/CONTEXT_TREE.md`.
6. Ask the data engineer to approve the phase plan.

## User control

The data engineer owns business meaning. The agent may recommend, but must ask before:

- Choosing a fact grain that affects metrics
- Joining tables when cardinality can multiply rows
- Excluding source tables or important columns
- Dropping, masking, or exposing PII/PHI
- Creating mapping seeds from ambiguous code values
- Defining final metrics
- Accepting evaluator warnings as intentional

## Chat summary

At each phase, keep the chat summary short:

```text
I completed <phase> discovery and wrote:
- reports/agent/<phase>_discovery.md or <phase>_report.md
- reports/agent/CONTEXT_TREE.md

Here are the 3-5 key findings:
- ...

My recommendation:
- ...

What needs your approval:
- ...

Approval needed before build:
Reply "approve <phase>" to continue, or tell me what to change.
```

Do not flood chat with full discovery details when the file exists.
