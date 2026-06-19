# dbt Pipeline

`dbt Pipeline` is a Cursor Agent Skill for setting up and maintaining dbt projects with a structured, agent-assisted workflow.

It helps an agent initialize a dbt project, configure sources, build bronze/silver/gold medallion layers, add semantic layer assets, run quality checks, generate docs, create CI workflows, publish dbt metadata to Agents Schema, and commit each stage separately.

## Installation

Install the skill with:

```bash
npx skills add zohaibRT/agentic-dbt-pipeline
```

This is the only skill users need to install manually. During bootstrap, the skill can install the required dbt Labs agent skills and dbt packages when they are missing.

## Prerequisites

- Python 3.12 or later
- `dbt-core` and the required dbt adapter, such as `dbt-postgres`
- A valid local dbt profile in `~/.dbt/profiles.yml`
- Node.js for `npx skills`
- GitHub CLI authenticated with `gh auth login`, if GitHub push is enabled
- Warehouse access for `dbt debug` and `dbt build`
- Snowflake, Databricks, or BigQuery credentials for Agents Schema sync, if enabled

Do not commit real warehouse credentials, `.env`, or `profiles.yml`. Use `.env.example` as a safe template for non-secret project settings.

## Usage

In Cursor chat, use:

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Build the dbt project using the settings from `.env`.
Run the full pipeline from source discovery through final delivery.
```

For a full copy-paste prompt, see [prompt.md](prompt.md).

Keep repeatable non-secret settings in `.env` by copying `.env.example`. Most projects only need domain, dbt profile, source schema/name, and repo intent there. The skill infers layer names, schema prefix, commit mode, push behavior, materialization, and Agents Schema handling unless you override them.

## Configuration

After installation, edit:

```text
.agents/skills/agentic-dbt-pipeline/project.config.yml
```

Use this file for non-secret defaults and advanced overrides:

- dbt project name and root path
- dbt profile name
- adapter, host, port, database, and default schema
- source schema and source YAML path
- layer names and model paths, when your team does not use the default bronze/silver/gold flow
- materialization profile
- GitHub repo behavior
- Agents Schema settings

Keep passwords, tokens, and private keys in local profiles or GitHub Secrets.

## Workflow

| Phase | What the skill does |
|---|---|
| Bootstrap | Installs dbt Labs agent skills and dbt packages when needed |
| Validation | Runs `dbt debug`, `dbt deps`, `dbt parse`, and scoped `dbt build` commands |
| Environment config | Loads non-secret `.env` values before asking for missing inputs |
| Subagents | Optionally parallelizes read-only profiling, planning, docs, and review work |
| Sources | Generates source YAML and adds source descriptions |
| Source profiling | Reviews row counts, keys, relationships, dates, measures, and status/code fields before modeling |
| Data engineering guardrails | Checks grain, tests, incremental strategy, snapshots, exposures, privacy, and performance |
| Staging | Builds source-cleaning models with `source()` references |
| Intermediate | Builds reusable business logic models with `ref()` references and mapping seeds when needed |
| Marts | Builds final dimension, fact, and reporting models with business-friendly fields |
| Semantic layer | Adds MetricFlow / dbt semantic layer YAML for mart metrics |
| Quality | Runs `dbt_project_evaluator` and uses `audit_helper` where useful |
| Documentation | Runs `dbt docs generate` and verifies manifest/catalog output |
| Human review | Summarizes assumptions, data quality notes, mappings, metrics, and open decisions |
| Git | Commits initialization, sources, each model layer, docs, CI, and Agents Schema separately |
| Agents Schema | Publishes dbt metadata into `AGENTS.*` so agents can query project context from the warehouse |
| CI | Creates GitHub Actions workflows for dbt validation and Agents Schema sync |
| Final delivery | Produces handoff notes with run commands, build status, known limitations, and next decisions |

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
10. Add CI workflows
11. Add Agents Schema workflow

By default, the agent asks before each commit and push.

## Verification

After the first run, confirm the installed files exist:

```text
.agents/skills/agentic-dbt-pipeline/SKILL.md
.agents/skills/agentic-dbt-pipeline/project.config.yml
.agents/skills/using-dbt-for-analytics-engineering/
```

The repository also includes a local config validator:

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
| [prompt.md](prompt.md) | Copy-paste prompt for Cursor |
| [project.config.yml](project.config.yml) | Default non-secret configuration |
| [references/bootstrap.md](references/bootstrap.md) | Bootstrap workflow |
| [references/git-workflow.md](references/git-workflow.md) | Commit and push workflow |
| [references/agents-schema-setup.md](references/agents-schema-setup.md) | Agents Schema workflow setup |
| [references/dbt-packages-and-skills.md](references/dbt-packages-and-skills.md) | dbt packages and companion skills |
| [references/data-engineering-best-practices.md](references/data-engineering-best-practices.md) | Data-engineering guardrails |
