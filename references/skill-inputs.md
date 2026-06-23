# Skill Inputs - Resolve Before Any Work

Read [project.config.yml](../project.config.yml), [project-naming.md](project-naming.md), [schema-isolation.md](schema-isolation.md), and [env-configuration.md](env-configuration.md). Ask the user only for values the agent cannot infer safely.

## Normal user inputs

Most runs need only these non-secret values:

| Input | Config key | When to ask |
|---|---|---|
| Domain | `domain` prompt or `DBT_DOMAIN` | Ask if missing; used for modeling context and folders |
| dbt profile name | `dbt_profile_name` prompt or `DBT_PROFILE_NAME` | Ask if missing or multiple profiles exist |
| Source/raw schema | `source_schema` prompt or `DBT_SOURCE_SCHEMA` | Ask if missing; codegen must inspect a real warehouse schema |

Do not ask a new user for project name, dbt source name, layer schema prefix, layer names, materialization, commit mode, or GitHub repo unless they explicitly want to override the defaults.

## Agent-resolved settings

| Input | Config key | project default |
|---|---|---|
| dbt project name | `dbt_project_name`, `DBT_PROJECT_NAME`, or derived by [project-naming.md](project-naming.md) | derive from source/domain |
| dbt project root | `dbt_project_root`, `DBT_PROJECT_ROOT`, or derived project name | same as project name |
| dbt profile name | `dbt_profile_name` prompt, `DBT_PROFILE_NAME`, or `project.profile` | ask if missing or ambiguous |
| Adapter | `database.adapter` | `postgres` |
| Host | `database.host` | `warehouse_host` |
| Port | `database.port` | `5432` |
| Database | `database.dbname` | `analytics` |
| Profile target schema | `database.target_schema` | `dbt_work`; must not equal `source_schema` |
| Source/raw schema | `source_schema` prompt, `DBT_SOURCE_SCHEMA`, or `source.schema` | required human input when missing |
| Source name | `source_name`, `DBT_SOURCE_NAME`, or derived from `source_schema` / `domain` | derive; ask only for existing-project collisions |
| Layer schema prefix | `layer_schema_prefix`, `DBT_LAYER_SCHEMA_PREFIX`, or derived by [schema-isolation.md](schema-isolation.md) | derive; ask only when existing schemas conflict |
| Domain folder | `domain` prompt, `DBT_DOMAIN`, or `domain` config | required human input when missing |
| Project rules | `project_rules` prompt | optional; ask if unclear |
| Layer 1 schema suffix | prompt, advanced `.env`, or config -> `+schema` | `bronze` |
| Layer 2 schema suffix | prompt, advanced `.env`, or config -> `+schema` | `silver` |
| Layer 3 schema suffix | prompt, advanced `.env`, or config -> `+schema` | `gold` |
| Agents schema | `agents.schema` | `AGENTS` |
| GitHub repo name | `github_repo_name`, `DBT_GITHUB_REPO_NAME`, or existing remote | local-only unless push is requested |
| GitHub owner *(from CLI)* | `gh api user` | only needed when pushing |
| Default branch | `git.branch` | `main` |
| Push to GitHub after commit | `push_to_github` | `false` unless explicitly requested or approved |

## GitHub repo resolution

**Do not hardcode GitHub accounts.** See [github-repo-resolution.md](github-repo-resolution.md).

Default to local commits only. Do not ask for a GitHub repo during ordinary local builds.

Only resolve GitHub when the user asks to push, provides `github_repo_name` / `DBT_GITHUB_REPO_NAME`, or the project already has a non-local `origin` remote.

1. Run `gh api user --jq ".login"` -> `{owner}` only when a push or new remote is needed
2. Ask user for `github_repo_name` only when push is requested and no repo can be inferred
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
- Ask for `source_schema` before running codegen or writing layer config. Derive `source_name` from `source_schema` or `domain` unless the user explicitly overrides it. Derive `layer_schema_prefix` with [schema-isolation.md](schema-isolation.md); do not default physical schemas to short source names such as `dh`. Do not guess the source schema from the dbt profile target schema.
- If `project_rules` include mappings, joins, metrics, exclusions, privacy rules, naming rules, or special instructions, apply them exactly and ask before interpreting ambiguous rules.

## Optional overrides (user prompt wins)

```text
dbt_project_name: hospital_analytics     # optional; otherwise derived from source/domain
dbt_project_root: hospital_analytics     # optional; defaults to dbt_project_name
dbt_profile_name: hospital_analytics     # profile key from ~/.dbt/profiles.yml
domain: hospital                         # domain folder and naming context
source_schema: hospital_raw              # warehouse schema to inspect with codegen
source_name: hospital                    # optional; otherwise derived from source_schema/domain
layer_schema_prefix: hospital            # optional; otherwise derived from existing schemas/domain/source schema/descriptive source name
project_rules:                           # optional business/modeling rules
  field_mappings: []
  joins: []
  metrics: []
  exclusions: []
  privacy: []
  naming: []
  special_instructions: []
github_repo: other-owner/analytics       # optional full override only
github_repo_name: analytics              # optional repo slug; use only when pushing
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
```

Advanced `.env` overrides:

```text
DBT_PROJECT_NAME=<dbt_project_name>
DBT_PROJECT_ROOT=<dbt_project_root>
DBT_SOURCE_NAME=<dbt_source_name>
DBT_GITHUB_REPO_NAME=<repo_name_if_push_is_required>
```

Prompt values override `.env`. Do not commit `.env`; commit only `.env.example`.

On a fresh clone, if `.env` is missing, follow [env-configuration.md](env-configuration.md): create a safe local `.env` from `.env.example`, stop, and ask the user to fill `DBT_DOMAIN`, `DBT_PROFILE_NAME`, and `DBT_SOURCE_SCHEMA` before running dbt commands.

Do not satisfy missing required inputs from sibling projects or previous runs. Sibling projects may be shown as hints, but the user must confirm the active domain, profile, and source schema before discovery or dbt commands. Do not say the `.env` was created from a "sibling project pattern"; say it was created from `.env.example`.

## dbt packages & skills stack

See [dbt-packages-and-skills.md](dbt-packages-and-skills.md) - agent installs and uses all six capabilities on full pipeline.
