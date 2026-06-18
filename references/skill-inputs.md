# Skill Inputs — Collect Before Any Work

Read [project.config.yml](../project.config.yml). If values are missing, **ask the user** before proceeding.

## Required inputs

| Input | Config key | project default |
|---|---|---|
| dbt project name | `project.name` | `my_dbt_project` |
| dbt project root | `project.root` | `my_dbt_project` |
| dbt profile name | `dbt_profile_name` prompt or `project.profile` | ask if missing or ambiguous |
| Adapter | `database.adapter` | `postgres` |
| Host | `database.host` | `warehouse_host` |
| Port | `database.port` | `5432` |
| Database | `database.dbname` | `analytics` |
| Profile target schema | `database.target_schema` | `raw` |
| Source/raw schema | `source_schema` prompt or `source.schema` | ask if missing |
| Source name | `source_name` prompt or `source.name` | ask if missing |
| Domain folder | `domain` prompt or `domain` config | ask if missing |
| Layer 1 schema suffix | user name → `+schema` | `staging` |
| Layer 2 schema suffix | user name → `+schema` | `intermediate` |
| Layer 3 schema suffix | user name → `+schema` | `marts` |
| Agents schema | `agents.schema` | `AGENTS` |
| **GitHub repo name** *(ask user)* | `github_repo_name` | — |
| GitHub owner *(from CLI)* | `gh api user` | logged-in `gh` account |
| Default branch | `git.branch` | `main` |
| Push to GitHub after commit | `push_to_github` | `true` on full pipeline |

## GitHub repo resolution

**Do not hardcode GitHub accounts.** See [github-repo-resolution.md](github-repo-resolution.md).

1. Run `gh api user --jq ".login"` → `{owner}`
2. Ask user: `github_repo_name` (e.g. `analytics`)
3. Remote = `https://github.com/{owner}/{github_repo_name}.git`

## Target environments

| Target | Use |
|---|---|
| `dev` | Local development *(default)* |
| `ci` | GitHub Actions validation |
| `prod` | Production warehouse — **ask before changes** |

## Credentials

- **Never** hardcode passwords in skills, prompts, or project files.
- Use `~/.dbt/profiles.yml` locally.
- Use GitHub Secrets in CI (`WAREHOUSE_CREDENTIALS` for Agents Schema).
- If multiple dbt profiles exist, ask for `dbt_profile_name` before running `dbt debug`, `dbt deps`, `dbt parse`, or `dbt build`.
- Ask for `source_schema` and `source_name` before running codegen. Do not guess the source schema from the dbt profile target schema.

## Optional overrides (user prompt wins)

```text
github_repo_name: analytics              # repo slug — ask if missing
dbt_profile_name: hospital_analytics     # profile key from ~/.dbt/profiles.yml
domain: hospital                         # domain folder and naming context
source_schema: hospital_raw              # warehouse schema to inspect with codegen
source_name: hospital                    # dbt source name to write in YAML
github_repo: other-owner/analytics       # optional full override only
push_to_github: true | false
layer_names: staging, intermediate, marts
commit: ask | auto_yes | skip_all
materialization_profile: prod | dev
workflow_phase: init | sources | staging | intermediate | marts | semantic_layer | project_evaluator | docs | ci | agents_schema
```

## dbt packages & skills stack

See [dbt-packages-and-skills.md](dbt-packages-and-skills.md) — agent installs and uses all six capabilities on full pipeline.
