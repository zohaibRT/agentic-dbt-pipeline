# dbt Pipeline

`dbt Pipeline` is a Cursor Agent Skill for setting up and maintaining dbt projects with a structured, agent-assisted workflow.

It helps an agent initialize a dbt project, configure sources, build staging/intermediate/mart layers, add semantic layer assets, run quality checks, generate docs, create CI workflows, publish dbt metadata to Agents Schema, and commit each stage separately.

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

Do not commit real warehouse credentials, `.env`, or `profiles.yml`.

## Usage

In Cursor chat, use:

```text
Use the dbt Pipeline skill (`agentic-dbt-pipeline`).

Goal: Build a <domain> dbt project using medallion layers from the available source schemas.

Required inputs:
- domain: <hospital | it_company | finance | retail | etc.>
- dbt_profile_name: <profile key from ~/.dbt/profiles.yml>
- source_schema: <raw/source schema to inspect>
- source_name: <friendly dbt source name>
- layer_schema_prefix: <usually same as source_name>
- github_repo_name: <repo slug only>

layer_names:
  layer_1: bronze
  layer_2: silver
  layer_3: gold

project_rules:
  field_mappings:
    - <source_table.source_column> -> <target_column>: <meaning/rule>
  joins:
    - <left_table.column> -> <right_table.column>: <relationship>
  metrics:
    - <metric_name>: <definition, grain, filters>
  privacy:
    - <PII/PHI handling, masking, or exclusion rules>
```

For a full copy-paste prompt, see [prompt.md](prompt.md).

## Configuration

After installation, edit:

```text
.agents/skills/agentic-dbt-pipeline/project.config.yml
```

Use this file for non-secret project settings:

- dbt project name and root path
- dbt profile name
- adapter, host, port, database, and default schema
- source schema and source YAML path
- layer names and model paths
- materialization profile
- GitHub repo behavior
- Agents Schema settings

Keep passwords, tokens, and private keys in local profiles or GitHub Secrets.

## Workflow

| Phase | What the skill does |
|---|---|
| Bootstrap | Installs dbt Labs agent skills and dbt packages when needed |
| Validation | Runs `dbt debug`, `dbt deps`, `dbt parse`, and scoped `dbt build` commands |
| Sources | Generates source YAML and adds source descriptions |
| Staging | Builds source-cleaning models with `source()` references |
| Intermediate | Builds reusable business logic models with `ref()` references |
| Marts | Builds final dimension, fact, and reporting models |
| Semantic layer | Adds MetricFlow / dbt semantic layer YAML for mart metrics |
| Quality | Runs `dbt_project_evaluator` and uses `audit_helper` where useful |
| Documentation | Runs `dbt docs generate` and verifies manifest/catalog output |
| Git | Commits initialization, sources, each model layer, docs, CI, and Agents Schema separately |
| Agents Schema | Publishes dbt metadata into `AGENTS.*` so agents can query project context from the warehouse |
| CI | Creates GitHub Actions workflows for dbt validation and Agents Schema sync |

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
