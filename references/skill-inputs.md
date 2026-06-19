# Skill Inputs - Collect Before Any Work

Read [project.config.yml](../project.config.yml), [project-naming.md](project-naming.md), [schema-isolation.md](schema-isolation.md), and [env-configuration.md](env-configuration.md). If values are missing after prompt, `.env`, config, and project-name derivation, **ask the user** before proceeding.

## Required inputs

| Input | Config key | project default |
|---|---|---|
| dbt project name | `dbt_project_name`, `DBT_PROJECT_NAME`, or derived by [project-naming.md](project-naming.md) | derive from repo/source/domain |
| dbt project root | `dbt_project_root`, `DBT_PROJECT_ROOT`, or derived project name | same as project name |
| dbt profile name | `dbt_profile_name` prompt, `DBT_PROFILE_NAME`, or `project.profile` | ask if missing or ambiguous |
| Adapter | `database.adapter` | `postgres` |
| Host | `database.host` | `warehouse_host` |
| Port | `database.port` | `5432` |
| Database | `database.dbname` | `analytics` |
| Profile target schema | `database.target_schema` | `dbt_work`; must not equal `source_schema` |
| Source/raw schema | `source_schema` prompt, `DBT_SOURCE_SCHEMA`, or `source.schema` | ask if missing |
| Source name | `source_name` prompt, `DBT_SOURCE_NAME`, or `source.name` | ask if missing |
| Layer schema prefix | `layer_schema_prefix` prompt, `DBT_LAYER_SCHEMA_PREFIX`, or `source_name` | default to `source_name` |
| Domain folder | `domain` prompt, `DBT_DOMAIN`, or `domain` config | ask if missing |
| Project rules | `project_rules` prompt | optional; ask if unclear |
| Layer 1 schema suffix | prompt, advanced `.env`, or config -> `+schema` | `bronze` |
| Layer 2 schema suffix | prompt, advanced `.env`, or config -> `+schema` | `silver` |
| Layer 3 schema suffix | prompt, advanced `.env`, or config -> `+schema` | `gold` |
| Agents schema | `agents.schema` | `AGENTS` |
| **GitHub repo name** *(ask user)* | `github_repo_name` | - |
| GitHub owner *(from CLI)* | `gh api user` | logged-in `gh` account |
| Default branch | `git.branch` | `main` |
| Push to GitHub after commit | `push_to_github` | `false` for `local-only`; otherwise ask |

## GitHub repo resolution

**Do not hardcode GitHub accounts.** See [github-repo-resolution.md](github-repo-resolution.md).

1. Run `gh api user --jq ".login"` -> `{owner}`
2. Ask user: `github_repo_name` (e.g. `analytics`)
3. Remote = `https://github.com/{owner}/{github_repo_name}.git`

## Target environments

| Target | Use |
|---|---|
| `dev` | Local development *(default)* |
| `ci` | GitHub Actions validation |
| `prod` | Production warehouse - **ask before changes** |

## Credentials

- **Never** hardcode passwords in skills, prompts, or project files.
- Use `.env` only for non-secret reusable project settings.
- Use `~/.dbt/profiles.yml` locally.
- Use GitHub Secrets in CI (`WAREHOUSE_CREDENTIALS` for Agents Schema).
- Treat config values like `auto`, `my_dbt_project`, `default`, `example`, or `<...>` as placeholders, not real project/profile inputs.
- If multiple dbt profiles exist, ask for `dbt_profile_name` before running `dbt debug`, `dbt deps`, `dbt parse`, or `dbt build`.
- Do not use `dbt_profile_name` as the project folder. The profile is only the connection key. Derive project name/root from [project-naming.md](project-naming.md).
- Keep `source_schema` read-only. If the dbt profile target schema equals `source_schema`, stop and follow [schema-isolation.md](schema-isolation.md) before any build.
- Ask for `source_schema` and `source_name` before running codegen or writing layer config. Default `layer_schema_prefix` to `source_name` unless the user overrides it. Do not guess the source schema from the dbt profile target schema.
- If `project_rules` include mappings, joins, metrics, exclusions, privacy rules, naming rules, or special instructions, apply them exactly and ask before interpreting ambiguous rules.

## Optional overrides (user prompt wins)

```text
github_repo_name: analytics              # repo slug - ask if missing
dbt_project_name: hospital_analytics     # optional; otherwise derived from repo/source/domain
dbt_project_root: hospital_analytics     # optional; defaults to dbt_project_name
dbt_profile_name: hospital_analytics     # profile key from ~/.dbt/profiles.yml
domain: hospital                         # domain folder and naming context
source_schema: hospital_raw              # warehouse schema to inspect with codegen
source_name: hospital                    # dbt source name to write in YAML
layer_schema_prefix: hospital            # optional; defaults to source_name
project_rules:                           # optional business/modeling rules
  field_mappings: []
  joins: []
  metrics: []
  exclusions: []
  privacy: []
  naming: []
  special_instructions: []
github_repo: other-owner/analytics       # optional full override only
push_to_github: <true|false>             # optional; omit for approval-based default
layer_names: bronze, silver, gold        # optional; defaults shown
commit: ask | auto_yes | skip_all
materialization_profile: prod | dev
workflow_phase: init | sources | staging | intermediate | marts | semantic_layer | project_evaluator | docs | ci | agents_schema
```

## Optional `.env`

For repeat projects, allow the user to keep required fields in `.env`:

```text
DBT_DOMAIN=<domain_name>
DBT_PROFILE_NAME=<dbt_profile_name>
DBT_SOURCE_SCHEMA=<raw_source_schema>
DBT_SOURCE_NAME=<dbt_source_name>
DBT_GITHUB_REPO_NAME=<repo_name_or_local_only>
```

Advanced `.env` overrides:

```text
DBT_PROJECT_NAME=<dbt_project_name>
DBT_PROJECT_ROOT=<dbt_project_root>
```

Prompt values override `.env`. Do not commit `.env`; commit only `.env.example`.

## dbt packages & skills stack

See [dbt-packages-and-skills.md](dbt-packages-and-skills.md) - agent installs and uses all six capabilities on full pipeline.
