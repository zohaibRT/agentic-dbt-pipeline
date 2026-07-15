# Agent Recommendation And Data Engineer Review

Use this in every discovery summary, phase plan, phase report, and final handoff.

## Core rule

The agent investigates and recommends. The data engineer approves, changes, or adds requirements. The agent then builds only the approved scope.

Approvals are narrow by default and controlled by the active workflow checkpoint. A discovery checkpoint response approves only source confirmation and automatic project setup and configuration. A phase checkpoint response approves only that phase. Do not convert one approval into permission to create all layers or close final delivery.

Do not push every modeling decision back to the user. Do the professional analysis first, state the recommended path with evidence, and ask only for decisions that affect business meaning, privacy, correctness, cost, or downstream usability.

## Required sections

Include these sections in discovery summaries and phase plans:

```markdown
### Agent Recommendation
- Recommended path: <what the agent recommends doing next>
- Why: <evidence from source data, dbt project, or validation>

### What Looks Right
- <safe or well-supported choice>

### What Is Not Ready Yet
- <risk, missing data, ambiguous field, unverified join, or weak assumption>

### Confidence
- Confident about: <facts supported by discovery, profiling, tests, or dbt validation>
- Less confident about: <business meaning, privacy choices, ambiguous fields, metric dates, rebuild/refactor choices, or anything not proven yet>

### Needs Data Engineer Approval
- <business-impacting choice that must be approved before build>

### Not Deciding Alone
- <privacy, metric, mapping, grain, schema, cost, or production behavior the agent will not choose silently>
```

If a section has no items, write `None found for this phase` instead of omitting it.

## Recommendation rules

- Recommend a default next action whenever the evidence supports one.
- Explain why the recommendation is safe enough to build, or why it should wait.
- State confidence separately from the recommendation. Confidence should distinguish proven technical facts from business assumptions.
- Separate technical confidence from business approval. A query can validate a join, but the business owner still owns metric meaning.
- Ask for approval only on the current phase, not the whole pipeline.
- Stop after each phase report unless the next phase was explicitly approved by name.
- Mark low-risk technical defaults as agent-owned, such as derived project name, source name, layer folder names, test selection, and package routing.
- Mark high-impact choices as user-approved before build, such as fact grain, final metrics, PII/PHI exposure, mappings, table exclusions, schema behavior changes, full refresh, and accepted evaluator warnings.

## Mandatory: recommend before asking

Every OPEN human decision on `HUMAN_ATTENTION_BOARD.md`, every OPEN KPI gap on `KPI_GAP_REGISTER.md`, and every checkpoint chat summary must include a concrete agent recommendation.

Bad (ask-only):

```text
What should Active mean?
Pick status vs not_deleted.
```

Good (recommend, then ask to accept or override):

```text
Agent recommendation: define Active Subscription Count as
`status = 'Active' AND deleted = false`.
Why: status already separates portfolio states; not_deleted alone would count 826 vs 271 Active rows and inflate the KPI.
Please reply: Accept recommendation / Override with your rule.
```

Required fields for every OPEN decision:

| Field | Requirement |
|---|---|
| Agent recommendation | One concrete rule, mapping, filter, default, or next build path |
| Why recommended | Evidence from proofs, counts, uniqueness, privacy, or reconciliation |
| Alternatives considered | At least one rejected option and why it is weaker |
| Ask from human | Accept recommendation, override with exact rule, or defer with reason |

Never leave Recommendation as empty, `TBD`, `needs discussion`, or `pick one` without choosing a preferred answer first.

Also read [kpi-gap-and-stakeholder-warnings.md](kpi-gap-and-stakeholder-warnings.md) for the required chat **Agent recommends** section.

## Examples

Good recommendation:

```markdown
### Agent Recommendation
- Recommended path: Build bronze for all confirmed source tables and exclude unclear placeholder columns from silver/gold until their meaning is provided.
- Why: Source profiling found stable primary keys and populated source tables, but some ambiguous or poorly named fields have no clear business definition.

### What Looks Right
- Appointments can be the first fact area because row counts, date fields, status values, and patient/provider keys are present.
- Providers and patients are strong dimension candidates because their keys are non-null and referenced by appointments.

### What Is Not Ready Yet
- Claims metrics should wait if claims are empty or billing definitions are missing.
- Placeholder fields should not be promoted into gold without a definition.

### Confidence
- Confident about: table inventory, source grains, tested key integrity, appointment/provider/patient relationships, and the first-pass star-schema shape.
- Less confident about: business meaning of ambiguous source fields, whether direct identifiers should appear in gold, which date drives each metric, and whether to rebuild from scratch or align with existing warehouse models.

### Needs Data Engineer Approval
- Whether patient names or insurance fields may appear in gold models.
- Whether appointment status `Completed` is the only attended appointment definition.

### Not Deciding Alone
- PHI/PII exposure in marts.
- Final revenue metric definitions.
```

Bad behavior:

- Asking the user to design all facts and dimensions without a recommendation.
- Listing blockers without recommending the safest unblock path.
- Writing Attention Board Recommendation as `pick one`, `TBD`, or only a question.
- Building gold metrics from ambiguous fields without approval.
- Treating source discovery as approval to build.
- Hiding business assumptions only in SQL.
