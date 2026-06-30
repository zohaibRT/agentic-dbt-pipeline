# dbt Analytics Engineer

`dbt Analytics Engineer` is a generic, domain-neutral agent skill for setting up and maintaining dbt analytics-engineering projects with a structured, agent-assisted workflow. It is not ecommerce-only; ecommerce, hospital, finance, customer relationship management, operations, and other examples are examples only.

It helps an agent start with read-only source discovery, initialize a dbt project, configure sources, build bronze/silver/gold medallion layers, add semantic layer assets, run quality checks, generate documentation, recommend a presentation layer, optionally create a Power BI handoff after approval, create continuous integration workflows, publish dbt metadata to Agents Schema, write per-phase status reports, commit each stage separately, and finish with a clear user-facing run summary. It also requires explicit data-engineering decisions before each build phase, so the agent does not silently guess grain, joins, metrics, privacy, or materialization.

## Installation

Install the skill with:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

This is the only skill users need to install manually. During project setup and configuration, the skill can install the required dbt Labs agent skills and dbt packages when they are missing.

## Prerequisites

- Python 3.12 or later
- `dbt-core` and the required dbt adapter, such as `dbt-postgres`
- A valid local dbt profile in `~/.dbt/profiles.yml`
- Node.js for `npx skills`
- GitHub command line interface authenticated with `gh auth login`, if GitHub push is enabled
- Warehouse access for `dbt debug` and `dbt build`
- Snowflake, Databricks, or BigQuery credentials for Agents Schema sync, if enabled

Do not commit real warehouse credentials, `.env`, or `profiles.yml`. Use `.env.example` as a safe template for non-secret project settings.

## Usage

In your agent chat, use:

```text
Use the dbt Analytics Engineer skill (`agentic-dbt-pipeline`).

Build the dbt project using the settings from `.env`.
Run the full pipeline from source discovery through final delivery.

First, perform read-only discovery only: inspect source schemas/tables, create necessary Mermaid discovery diagrams including an entity relationship diagram when credible relationships exist, summarize what you conclude from the data, include a recommended medallion direction for sources, bronze/staging, silver/intermediate, and gold/marts, recommend the best next path with evidence, and ask whether I want to add or change requirements.

After I answer, run project setup and configuration automatically, then before each build phase, write/update `AGENT_PLAN.md`, explain what will be built, what looks right, what is not ready yet, confidence about proven vs uncertain items, and what needs my approval, then wait for approval. After each completed phase, write/update `reports/agent/<phase>_report.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`.
```

For a full copy-paste prompt, see [prompt.md](prompt.md).

All diagrams created by the skill use Mermaid. Entity relationships use Mermaid `erDiagram`, and added or changed diagrams must be verified as visible/parseable before the related phase is marked complete.

Keep repeatable non-secret settings in `.env` by copying `.env.example`. If `.env` is missing on a fresh clone, the skill creates a safe local `.env` template, lists available dbt profiles with adapter and non-secret notes, and asks you to fill the required values before running dbt. Most projects only need domain, dbt profile, and source schema there. The skill infers project name/root, dbt source name, layer names, schema prefix, commit mode, push behavior, materialization, and Agents Schema handling unless you override them. Add GitHub repository details only when you want the agent to push.

Discovery uses the adapter from the selected dbt profile. If `.env` points to a PostgreSQL profile, the skill uses PostgreSQL discovery only; it does not probe AWS, Redshift, or other warehouses unless you explicitly change profiles.

## Configuration

After installation, edit:

```text
.agents/skills/agentic-dbt-pipeline/project.config.yml
```

Use this file for non-secret defaults and advanced overrides:

- dbt project name and root path, when you do not want the skill to derive them from source/domain
- dbt profile name
- adapter, host, port, database, and default schema
- source schema and source YAML path
- layer names and model paths, when your team does not use the default bronze/silver/gold flow
- materialization profile
- GitHub repository behavior, only when pushing to a remote
- Agents Schema settings

Keep passwords, tokens, and private keys in local profiles or GitHub Secrets.

## Workflow

| Phase | What the skill does |
|---|---|
| Discovery | First phase, read-only only. Inspects schemas, tables, columns, row counts, candidate keys, date fields, status fields, amount fields, relationships, grain evidence, possible facts, dimensions, marts, and metrics. Writes `reports/agent/discovery_report.md`, `reports/agent/requirements.md`, `reports/agent/PIPELINE_STATUS.md`, and `reports/agent/CONTEXT_TREE.md`, then asks whether requirements should be added, removed, or changed before setup/build |
| Project setup and configuration | Runs automatically after discovery requirements are accepted; setup-only scaffold, dependency install, connection validation, parse validation, and setup reports |
| Validation | Runs `dbt debug`, `dbt deps`, `dbt parse`, and scoped `dbt build` commands |
| Environment configuration | Loads non-secret `.env` values before asking for missing inputs |
| Warehouse adapter routing | Uses only the adapter from the selected dbt profile for discovery |
| Subagents | Optionally parallelizes read-only profiling, planning, documentation, and review work |
| Phase planning | Writes a Markdown plan before each non-setup phase and waits for approval before building |
| Agent recommendations | Recommends the best path with evidence, confidence, and risks, then asks the data engineer to approve or change business-impacting choices |
| Data engineer decision gate | Documents grain, keys, joins, mappings, metrics, privacy, tests, materialization, and validation evidence before build |
| Phase reports | Writes `reports/agent/<phase>_report.md`, `PIPELINE_STATUS.md`, and `CONTEXT_TREE.md` after each phase |
| Sources | Generates source YAML and adds source descriptions |
| Schema isolation | Keeps source, medallion, evaluator, seeds, snapshots, and agent metadata in separate schemas |
| Source profiling | Reviews row counts, keys, relationships, dates, measures, and status/code fields before modeling |
| Mermaid diagrams | Uses Mermaid for all diagrams, including entity relationship diagrams, and records visibility/parse verification |
| Data engineering guardrails | Checks grain, tests, incremental strategy, snapshots, exposures, privacy, and performance |
| Staging | Builds source-cleaning models with `source()` references |
| Intermediate | Builds reusable business logic models with `ref()` references and mapping seeds when needed |
| Marts | Builds as many credible dimensions, facts, bridge tables, and reporting marts as the source data and approved requirements support. It does not force a fixed model count |
| Semantic layer | Adds MetricFlow / dbt semantic layer YAML for approved and reconciled mart metrics |
| Quality | Runs `dbt_project_evaluator` and uses `audit_helper` where useful |
| Documentation | Runs `dbt docs generate`, verifies manifest/catalog output, and can serve documentation locally for viewing |
| Presentation layer | After documentation, recommends business-facing presentation options with possible key performance indicators, semantic metrics, dashboard/report pages, source models, caveats, and privacy notes. If approved and no other technology is specified, defaults to a Power BI PBIP/TMDL handoff |
| Power BI handoff | Optional after approval. Produces a Power BI-ready star schema plan, semantic model plan, DAX measure specifications, dashboard page plan, static validation results, Model Context Protocol validation when available, and Desktop open validation when available |
| Human review | Summarizes assumptions, data quality notes, mappings, metrics, and open decisions |
| Git | Commits initialization, sources, each model layer, documentation, continuous integration, and Agents Schema separately |
| Agents Schema | Publishes dbt metadata into `AGENTS.*` so agents can query project context from the warehouse |
| Continuous integration | Creates GitHub Actions workflows for dbt validation and Agents Schema synchronization |
| Final delivery | Produces a short summary plus handoff notes with run commands, build status, known limitations, and next decisions |

## Commit Strategy

The skill is designed to keep project history readable. It commits each stage separately:

1. Initialize dbt project
2. Add dbt packages
3. Configure safe project/profile examples
4. Define dbt sources
5. Add staging models
6. Add intermediate models
7. Add mart models
8. Add semantic layer metrics
9. Add tests and documentation
10. Add continuous integration workflows
11. Add Agents Schema workflow

By default, the agent asks before each commit. It asks about push only when a GitHub remote is configured or requested.
It asks for approval before each non-setup build phase after showing the Markdown plan. Project setup and configuration is automatic setup-only unless a safety gate is triggered.
After each completed phase, it writes a phase report showing what passed, warned, failed, was skipped, and still needs review, then updates the context tree for future phases.

## Generated Reports

The skill keeps a reviewable audit trail in `reports/agent/`:

- `discovery_report.md` and `requirements.md` for source-derived requirements and evidence
- `<phase>_report.md` for each completed or blocked phase
- `PIPELINE_STATUS.md` for current phase status
- `CONTEXT_TREE.md` for reusable project memory
- `presentation_report.md` or `presentation_layer_report.md` when the presentation layer is recommended or created
- `powerbi_model_plan.md`, `dashboard_pages.md`, and `dax_measures.md` when Power BI is approved
- `final_delivery.md` for the final handoff

Every build phase plan must explain what will be built, why it is recommended, evidence, proven items, uncertain items, blocked or deferred scope, and what needs approval.

## Safety Rules

The skill must not commit `.env`, `profiles.yml`, `target/`, `logs/`, `dbt_packages/`, `.venv/`, secrets, tokens, or private keys. It must not run destructive SQL or modify source data without explicit approval, and source schemas remain read-only. It must not create fake key performance indicators from unclear columns, expose sensitive/private fields in marts without approval, or overwrite user work without showing a plan first.

## Verification

After the first run, confirm the installed files exist:

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md
.agents/skills/agentic-dbt-pipeline/project.config.yml
.agents/skills/using-dbt-for-analytics-engineering/
```

The repository also includes a local configuration validator:

```bash
python scripts/validate_config.py --root .
```

When Agents Schema is enabled, verify that the GitHub workflow creates an `AGENTS` schema and queryable metadata tables such as `AGENTS.DBT_MODEL`.

## Included dbt Packages

The skill can add and install these dbt packages:

- `dbt-labs/codegen`
- `dbt-labs/dbt_utils`
- `dbt-labs/dbt_project_evaluator`
- `dbt-labs/audit_helper`

## References

| File | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Main skill orchestration instructions |
| [prompt.md](prompt.md) | Copy-paste prompt for an agent session |
| [project.config.yml](project.config.yml) | Default non-secret configuration |
| [references/bootstrap.md](references/bootstrap.md) | Automatic project setup and configuration workflow |
| [references/discovery-requirements.md](references/discovery-requirements.md) | Read-only discovery and requirements checkpoint before build planning |
| [references/profile-listing.md](references/profile-listing.md) | Safe available-profile table when `DBT_PROFILE_NAME` is missing or ambiguous |
| [references/phase-plan-approval.md](references/phase-plan-approval.md) | Markdown plan and approval gate before every phase |
| [references/recommendation-and-review.md](references/recommendation-and-review.md) | Agent recommendations, what looks right, risks, and approval boundaries |
| [references/writing-style.md](references/writing-style.md) | Full wording for user-facing output |
| [references/warehouse-adapter-routing.md](references/warehouse-adapter-routing.md) | Use the selected dbt profile adapter for discovery |
| [references/mermaid-diagrams.md](references/mermaid-diagrams.md) | Mermaid-only diagrams and visibility verification |
| [references/phase-completion-report.md](references/phase-completion-report.md) | Per-phase reports and pipeline status file |
| [references/context-tree.md](references/context-tree.md) | Curated project memory for inputs, decisions, outputs, and report links |
| [references/data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) | Required senior data-engineering decision checks before build |
| [references/privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md) | Safe defaults for sensitive fields and unclear coded fields |
| [references/git-workflow.md](references/git-workflow.md) | Commit and push workflow |
| [references/schema-isolation.md](references/schema-isolation.md) | Source, layer, evaluator, seeds, snapshots, and metadata schema separation |
| [references/agents-schema-setup.md](references/agents-schema-setup.md) | Agents Schema workflow setup |
| [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | dbt packages and companion skills |
| [references/project-evaluator.md](references/project-evaluator.md) | Project evaluator setup for bronze/silver/gold |
| [references/data-engineering-best-practices.md](references/data-engineering-best-practices.md) | Data-engineering guardrails |
