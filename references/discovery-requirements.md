# Discovery & Requirements Checkpoint

Use this as the first phase for a new dbt project or full pipeline request.

## Goal

Analyze the available source schemas enough to orient the project and the data engineer before planning any build work.

This phase is read-only. Do not create dbt projects, install packages, run codegen, write model files, create warehouse schemas, or change profiles during discovery.

Do not start discovery until the active `domain`, `dbt_profile_name`, and `source_schema` are confirmed from the prompt or `.env`. If `.env` is missing, follow [env-configuration.md](env-configuration.md) and stop for user input first. Do not inspect the repository, terminal output, other workspaces, or prior workspaces to suggest or choose a source schema.

Discovery is project-oriented, not setup-oriented. The discovery input, report, and chat output should focus on the source data and the future analytics project, not on environment setup, bootstrap, package installation, git, continuous integration, or agent configuration.

Discovery is also phased. Initial discovery should be lightweight and should not fully design every bronze, silver, gold, semantic, evaluator, and documentation artifact. See [phased-discovery.md](phased-discovery.md). Deeper discovery happens immediately before each layer/phase.

Discovery must include Mermaid diagrams when the source data has enough evidence to support them. Create an entity relationship diagram during discovery when any credible table relationships exist. Create other necessary Mermaid diagrams when they make the project easier to review, such as source inventory, candidate business process flow, or high-level medallion direction. Do not draw relationships or flows that are only guesses; list uncertain items as notes outside the diagram.

## Allowed read-only actions

- Load `.env` and non-secret config values
- Confirm the selected dbt profile name and adapter
- Run `dbt debug` only when a dbt project/profile already exists and the command is needed to verify read-only access
- Inspect source schemas, tables, columns, and row counts
- Check candidate primary keys, foreign keys, date columns, measures, status/code columns, and empty tables
- Inspect existing project files if the project already exists

## Discovery summary

After discovery, explain in Markdown:

- Project/domain being analyzed
- Source schemas/tables found and row counts
- Important entities and likely relationships
- Entity relationship diagram in Mermaid `erDiagram` when credible relationships are found
- Other necessary Mermaid diagrams, such as source inventory, business process flow, or high-level medallion direction, when they help the data engineer review the source
- Candidate business processes, such as appointments, encounters, claims, orders, tickets, or events
- Candidate facts, dimensions, and metrics implied by the source
- Empty tables, suspicious columns, missing keys, date ranges, and data quality notes
- Privacy/sensitive-field observations
- High-level medallion direction, without finalizing every layer design
- Suggested business questions or analytics use cases the source appears able to support
- Agent recommendation with evidence
- What looks right for the next phase
- What is not ready yet
- What the agent is confident about
- What the agent is not confident about
- Required user decisions before modeling
- Next phase to discover/build first
- Mermaid visibility/parse verification for any diagram included

Put setup/config context at the end under a short `Inputs Used` section only:

- Domain
- dbt profile name, without credentials
- Source schema
- Source tables inspected

Do not lead the discovery report with profile details, `.env` handling, package setup, bootstrap status, git status, virtual environment setup, continuous integration, or Agents Schema. Those belong in setup/bootstrap reports.

## Discovery files are required

Discovery must be written to files, not only posted in chat.

Before sending the discovery summary in chat, create or update these files:

```text
reports/agent/discovery_report.md
reports/agent/PIPELINE_STATUS.md
reports/agent/CONTEXT_TREE.md
```

If the dbt project root does not exist yet, create `reports/agent/` in the current workspace/run root. Move or preserve these files in the dbt project root later only if the project root is created elsewhere and the user approves that layout.

The chat response should be a concise summary plus links/paths to these files. Do not use chat as the only discovery record.

## Required discovery diagrams

Add a `Diagrams` section to `reports/agent/discovery_report.md`.

Required:

- Mermaid entity relationship diagram using `erDiagram` when profiling, constraints, column naming, or user-approved rules reveal credible relationships.
- Mermaid source inventory or source relationship flow when the schema has multiple tables and the entity relationship diagram alone is not enough to explain the source shape.
- Mermaid high-level medallion direction diagram when the next recommended path would be clearer visually.

Optional:

- Candidate business process flow, such as appointment -> encounter -> claim, order -> shipment -> invoice, or ticket -> assignment -> resolution.
- Metric or semantic-layer concept diagram only when useful for the requirements conversation; do not finalize metric design during initial discovery.

For every discovery diagram:

- Use Mermaid only.
- Use full wording in titles and notes.
- Verify visibility or parse status with [mermaid-diagrams.md](mermaid-diagrams.md).
- Record the verification result in `reports/agent/discovery_report.md` and `reports/agent/CONTEXT_TREE.md`.
- Mark uncertain relationships as notes outside the diagram instead of drawing them as confirmed edges.

## Requirements checkpoint

Before creating the bootstrap/init plan, ask whether the user wants to add or change requirements.

Use this wording:

```text
Discovery is complete. I have not built or changed anything yet.

Here is what I concluded from the source data:
<short Markdown summary>

My recommendation:
<recommended next step and why>

What looks right:
<safe or well-supported choices>

What is not ready yet:
<risks, missing data, ambiguous fields, or weak assumptions>

Confidence:
- Confident about: <validated source/project facts>
- Less confident about: <business meaning, privacy choices, metric dates, ambiguous fields, rebuild/refactor decisions, or anything not proven yet>

Needs your approval:
<business-impacting choices before the next build phase>

Before I plan the dbt build, do you want to add any requirements?
Examples: field mappings, columns to exclude, metric definitions, privacy rules, naming rules, facts/dimensions to prioritize, or tables to ignore.

Reply with your changes/requirements, or reply "continue" if you approve the recommendation and want me to prepare the Bootstrap & Init plan for approval.
```

If the user replies `continue`, `no changes`, `go ahead`, or similar, proceed to [phase-plan-approval.md](phase-plan-approval.md) for Bootstrap & Init.

If the user provides requirements, add them to the plan as `project_rules` and use them in later phases.

## Do not

- Treat discovery as approval to build.
- Ask for commit approval during discovery because no files should change.
- Skip the requirements checkpoint on a new full pipeline.
- Hide inferred business logic. Explain what was inferred and what still needs confirmation.

After discovery is summarized, confirm that `reports/agent/discovery_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md` were created or updated. Do not defer discovery files to Bootstrap & Init.
