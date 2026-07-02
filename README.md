# dbt Analytics Engineer

`dbt Analytics Engineer` is a generic, domain-neutral agent skill for setting up and maintaining dbt analytics-engineering projects with a structured, agent-assisted workflow. It is not ecommerce-only; ecommerce, hospital, finance, customer relationship management, operations, and other examples are examples only.

It helps an agent start with read-only source discovery, initialize a dbt project, configure sources, build bronze/silver/gold medallion layers, add semantic layer assets, run quality checks, generate documentation, design analytics insight reporting outputs, recommend a presentation layer, optionally create a Power BI handoff after approval, create continuous integration workflows, publish dbt metadata to Agents Schema, write per-phase status reports, commit each stage separately, and finish with a clear user-facing run summary. It also requires explicit data-engineering decisions before each build phase, so the agent does not silently guess grain, joins, metrics, privacy, or materialization.

## Installation

Install the skill with:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

This is the only skill users need to install manually. During project setup and configuration, the skill can install the required dbt Labs agent skills and dbt packages when they are missing.

Some versions of `npx skills add` install only the entry `SKILL.md` file into agent folders. On first use, this skill checks for its local resources and hydrates missing `references/`, `scripts/`, `agents/`, `project.config.yml`, `prompt.md`, and `.env.example` from this repository into the installed skill folder before continuing.

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

After I answer, run project setup and configuration automatically, then before each build phase, write/update `AGENT_PLAN.md`, explain what will be built, what looks right, what is not ready yet, confidence about proven vs uncertain items, and what needs my approval, then wait for approval. After each completed phase, write/update `reports/agent/<phase>_report.md`, `reports/agent/PIPELINE_STATUS.md`, `reports/agent/CONTEXT_TREE.md`, and `reports/agent/NEXT_PHASE_PROMPT.md`. Show me the exact next-phase prompt and ask whether to run it as written with a clickable/native question when the agent platform supports it.
```

For a full copy-paste prompt, see [prompt.md](prompt.md).

All diagrams created by the skill use Mermaid. Entity relationships use Mermaid `erDiagram`, and added or changed diagrams must be verified as visible/parseable before the related phase is marked complete.

## Configuration

Skill install and project configuration are different locations.

| Location | What it is | Created when |
|---|---|---|
| `.agents/skills/agentic-dbt-pipeline/` | Installed skill files (`SKILL.md`, `references/`, `scripts/`, `project.config.yml`, `prompt.md`, `.env.example`) | `npx skills add` (plus hydration on first agent run if needed) |
| `.env` in your workspace or dbt project root | Your active project settings for this run | **First agent run**, not during skill install |
| `~/.dbt/profiles.yml` | Warehouse credentials | You maintain this separately |

### What install does not create

`npx skills add` does **not** create `.env` in your workspace. That is intentional:

- `.env` is local, gitignored, and project-specific
- The skill creates it on the **first prompt** when it is missing
- Until then, you will only see `.env.example` inside the installed skill folder after hydration

### First-time setup flow

1. Install the skill:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

2. Open your dbt project workspace in the agent (or create/open the folder where the dbt project should live).

3. Run the prompt from [prompt.md](prompt.md). You do **not** need to create `.env` manually first.

4. On first run, if `.env` is missing in the workspace, the agent will:
   - use `.env.example` from the workspace if present, otherwise from `.agents/skills/agentic-dbt-pipeline/.env.example`
   - create a local `.env` in the workspace root with placeholder values
   - list available dbt profiles from `~/.dbt/profiles.yml`
   - stop and ask you for `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA`

5. Update `.env` in the workspace root with your real values, then approve the agent to continue.

6. Optional advanced overrides: edit `.agents/skills/agentic-dbt-pipeline/project.config.yml` only when you need non-default skill behavior. Most users should use workspace `.env` instead.

Keep repeatable non-secret settings in workspace `.env`. Most projects only need domain, dbt profile, and source schema there; optionally add `DBT_BUSINESS_DESCRIPTION` to explain the client, business process, reporting goals, and decision context. The skill infers project name/root, project slug for layer folders, dbt source name, layer names, schema prefix, commit mode, push behavior, materialization, and Agents Schema handling unless you override them. Add GitHub repository details only when you want the agent to push.

Discovery uses the adapter from the selected dbt profile. If `.env` points to a PostgreSQL profile, the skill uses PostgreSQL discovery only; it does not probe AWS, Redshift, or other warehouses unless you explicitly change profiles.

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
| Next-phase prompt | After each completed phase, writes `reports/agent/NEXT_PHASE_PROMPT.md`, shows the exact prompt for the recommended next phase, asks a clickable/native approval question when supported, and accepts natural approval such as Yes, Proceed, Continue, Looks good, or Go ahead for that displayed prompt only |
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
| Analytics insight reporting | After documentation, discovers and documents trusted business outputs, a domain-neutral key performance indicator discovery matrix, source-to-final key performance indicator reconciliation, key performance indicator catalog, dashboard spec, readiness scorecard, and deferred insights before presentation work |
| Presentation layer | After analytics insight reporting, recommends business-facing presentation options using the reporting design files as scope. If approved and no other technology is specified, defaults to Matplotlib report figures with SQL-backed validation |
| Matplotlib report figures | Optional after approval. Produces reproducible Python figure generation, full measure/key performance indicator coverage from analytics insight catalogs, PNG/PDF outputs, SQL verification, prerequisites install when needed, and report spec under `reports/agent/10_presentation/matplotlib/` |
| Power BI handoff | Optional after explicit Power BI approval. Produces a Power BI-ready star schema plan, semantic model plan, DAX measure specifications, dashboard page plan, static validation results, Microsoft Power BI Modeling Model Context Protocol validation when available, and Desktop open validation when available |
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
10. Add analytics insight reporting design
11. Add continuous integration workflows
12. Add Agents Schema workflow

By default, the agent asks before each commit. It asks about push only when a GitHub remote is configured or requested.
It asks for approval before each non-setup build phase after showing the Markdown plan. Project setup and configuration is automatic setup-only unless a safety gate is triggered.
After each completed phase, it writes a phase report showing what passed, warned, failed, was skipped, and still needs review, then updates the context tree and prepares `reports/agent/NEXT_PHASE_PROMPT.md` for the recommended next phase. The agent must also summarize in chat what was completed, what is recommended next, what the next phase will and will not include, and paste the exact next-phase prompt before asking approval. It should ask approval with a clickable/native question when supported so the user can choose `Yes, run this prompt` instead of typing. Text approvals like `Yes`, `Proceed`, `Approved`, `Continue`, `Run this prompt`, `Looks good`, or `Go ahead` still work for that displayed prompt only. Silence is never approval, and changed scope requires a revised prompt before work continues.

When the next-phase prompt is approved, the agent should not run that file alone. It first reloads the phase context bundle: `SKILL.md`, `prompt.md`, phase references, `AGENT_PLAN.md`, `PIPELINE_STATUS.md`, `CONTEXT_TREE.md`, `requirements.md` when present, the latest phase report, `NEXT_PHASE_PROMPT.md`, and project knowledge files when present.

## Generated Reports

The skill keeps a reviewable audit trail in `reports/agent/`:

- `discovery_report.md` and `requirements.md` for source-derived requirements and evidence
- `<phase>_report.md` for each completed or blocked phase
- `PIPELINE_STATUS.md` for current phase status
- `CONTEXT_TREE.md` for reusable project memory
- `NEXT_PHASE_PROMPT.md` for the exact prompt proposed for the recommended next phase
- `analytics_insight_report.md`, `kpi_discovery_matrix.md`, `kpi_reconciliation_report.md`, `kpi_lineage_proofs.md`, `kpi_variance_report.md`, `reporting_catalog.md`, `kpi_catalog.md`, `dashboard_spec.md`, `insight_backlog.md`, and `reporting_readiness_scorecard.md` after analytics insight reporting
- `cardinality_report.md`, `relationship_profile.md`, `join_safety_report.md`, and `grain_validation_report.md` when relationships, joins, final models, or Power BI relationships are in scope
- `presentation_report.md` or `presentation_layer_report.md` when the presentation layer is recommended or created
- `matplotlib/README.md`, `matplotlib/requirements-matplotlib.txt`, `matplotlib/report_spec.md`, `matplotlib/kpi_figure_coverage.md`, `matplotlib/generate_report.py`, `matplotlib/figures/`, and `matplotlib/sql_verification/` when Matplotlib is approved
- `powerbi_model_plan.md`, `dashboard_pages.md`, and `dax_measures.md` when Power BI is approved
- `final_delivery.md` for the final handoff

## Power BI Validation

When a Power BI PBIP/TMDL artifact is approved, the skill prefers the official Microsoft Power BI Modeling Model Context Protocol server for semantic model validation:

```bash
npx @microsoft/powerbi-modeling-mcp@latest --start
```

Repository: [microsoft/powerbi-modeling-mcp](https://github.com/microsoft/powerbi-modeling-mcp)

The agent must still run static PBIP/TMDL validation and Power BI Desktop open validation when available. If the Model Context Protocol server is unavailable, the presentation report must say why instead of claiming model-load validation passed.

For PBIP/PBIR/TMDL structure, the skill points agents to the official Microsoft Power BI Desktop project documentation at [Power BI Desktop developer mode documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/), plus semantic model and report folder references under `references/powerbi-official-docs.md`.

The skill includes a neutral PBIP starter template at `assets/powerbi/pbip_template/`. When Power BI is approved, the agent should instantiate it with `scripts/generate_powerbi_pbip.py` and then add the project-specific gold tables, relationships, measures, pages, visuals, and validation evidence. Existing local PBIP files can be used only as optional structural references after the agent shows the exact path and gets user approval.

The Power BI validator blocks known Desktop open failures before handoff, including bare Power Query M steps such as `AddedKey = Table.AddColumn(...)` at TMDL root and linguistic metadata content-type mismatches such as JSON `{ "Version": "1.0.0" }` inside XML-typed metadata.

Every build phase plan must explain what will be built, why it is recommended, evidence, proven items, uncertain items, blocked or deferred scope, and what needs approval.

## Safety Rules

The skill must not commit `.env`, `profiles.yml`, `target/`, `logs/`, `dbt_packages/`, `.venv/`, secrets, tokens, or private keys. It must not run destructive SQL or modify source data without explicit approval, and source schemas remain read-only. It must not create fake key performance indicators from unclear columns, expose sensitive/private fields in marts without approval, or overwrite user work without showing a plan first.

## Verification

After the first run, confirm the installed files exist:

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md
.agents/skills/agentic-dbt-pipeline/project.config.yml
.agents/skills/agentic-dbt-pipeline/references/
.agents/skills/agentic-dbt-pipeline/scripts/
.agents/skills/agentic-dbt-pipeline/agents/
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
| [references/next-phase-prompt.md](references/next-phase-prompt.md) | Required next-phase prompt and interactive approval gate after each phase |
| [references/context-tree.md](references/context-tree.md) | Curated project memory for inputs, decisions, outputs, and report links |
| [references/data-engineer-decision-gate.md](references/data-engineer-decision-gate.md) | Required senior data-engineering decision checks before build |
| [references/privacy-and-unknown-fields.md](references/privacy-and-unknown-fields.md) | Safe defaults for sensitive fields and unclear coded fields |
| [references/git-workflow.md](references/git-workflow.md) | Commit and push workflow |
| [references/schema-isolation.md](references/schema-isolation.md) | Source, layer, evaluator, seeds, snapshots, and metadata schema separation |
| [references/agents-schema-setup.md](references/agents-schema-setup.md) | Agents Schema workflow setup |
| [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | dbt packages and companion skills |
| [references/project-evaluator.md](references/project-evaluator.md) | Project evaluator setup for bronze/silver/gold |
| [references/data-engineering-best-practices.md](references/data-engineering-best-practices.md) | Data-engineering guardrails |
| [references/analytics-insight-reporting.md](references/analytics-insight-reporting.md) | Business reporting design before presentation layer |
| [references/matplotlib-presentation-layer.md](references/matplotlib-presentation-layer.md) | Default Matplotlib static report figures workflow |
