# Environment Configuration

Use `.env` for reusable, non-secret dbt project settings so the prompt can stay short and human-friendly.

## Precedence

Resolve inputs in this order:

1. User prompt values
2. `.env` values
3. `project.config.yml`
4. Ask the user

Do not let `.env` silently override a value the user provided in the prompt.

## Minimal `.env` keys

Keep the normal `.env` small. These are the only fields most users should fill:

| `.env` key | Meaning |
|---|---|
| `DBT_DOMAIN` | `domain` |
| `DBT_PROFILE_NAME` | `dbt_profile_name` / `project.profile` |
| `DBT_SOURCE_SCHEMA` | `source_schema` / `source.schema` |
| `DBT_GITHUB_REPO_NAME` | `github_repo_name` |

For local-only runs, accepted values include `local-only`, `local`, `none`, `no`, `false`, `na`, and `n/a`.

## Skill-managed defaults

Do not require these in the prompt or `.env`:

| Decision | Default behavior |
|---|---|
| Project name/root | Derive from repo, source schema, source name, or domain; never from dbt profile |
| dbt source name | Derive from source schema or domain |
| Schema isolation | Keep source schema read-only; route evaluator/seeds/snapshots to separate schemas |
| Layer schema prefix | Derive from explicit override, existing medallion schemas, domain, source schema, or descriptive source name |
| Layer names | Use `bronze`, `silver`, `gold` |
| Commit behavior | Ask before each phase commit |
| Push behavior | Do not push for `local-only`; otherwise ask before pushing |
| Materialization | Use production-friendly defaults from `project.config.yml` |
| Agents Schema | Prepare only when requested and supported by the warehouse adapter |

## Advanced override keys

These keys are supported for teams that need a non-default workflow, but keep them out of `.env.example`:

| `.env` key | Prompt/config meaning |
|---|---|
| `DBT_PROJECT_NAME` | `dbt_project_name` |
| `DBT_PROJECT_ROOT` | `dbt_project_root` |
| `DBT_SOURCE_NAME` | `source_name` |
| `DBT_LAYER_SCHEMA_PREFIX` | `layer_schema_prefix` |
| `DBT_LAYER_1` | first medallion layer |
| `DBT_LAYER_2` | second medallion layer |
| `DBT_LAYER_3` | third medallion layer |
| `DBT_COMMIT` | `commit` |
| `DBT_PUSH_TO_GITHUB` | `push_to_github` |
| `DBT_MATERIALIZATION_PROFILE` | `materialization_profile` |
| `DBT_AUTO_AGENTS_SCHEMA` | `auto_agents_schema` |

## What belongs in `.env`

Good:

- Domain name
- dbt profile key
- Source schema
- Local-only or GitHub repo name

Use advanced override keys only when the project should intentionally differ from the skill defaults.

In `.env.example`, keep the core project fields as placeholders, not real profile or schema values.

Avoid:

- Warehouse passwords
- Personal access tokens
- Private keys
- Full `profiles.yml`
- Production credentials

Use `~/.dbt/profiles.yml` for local dbt credentials and GitHub Secrets for CI or Agents Schema credentials.

## How the agent should load it

If `.env` exists at the workspace root or dbt project root, read it before asking for missing project inputs.

Treat blank values as missing.

Summarize which non-secret values were loaded, but never print anything that looks like a password, token, or key.

If both `.env` and the prompt specify the same field with different values, use the prompt value and mention the difference in the phase summary.
