# Environment Configuration

Use `.env` for reusable, non-secret dbt project settings so the prompt can stay short and human-friendly.

## Precedence

Resolve inputs in this order:

1. User prompt values
2. `.env` values
3. `project.config.yml`
4. Ask the user

Do not let `.env` silently override a value the user provided in the prompt.

## Supported keys

| `.env` key | Prompt/config meaning |
|---|---|
| `DBT_DOMAIN` | `domain` |
| `DBT_PROFILE_NAME` | `dbt_profile_name` / `project.profile` |
| `DBT_SOURCE_SCHEMA` | `source_schema` / `source.schema` |
| `DBT_SOURCE_NAME` | `source_name` / `source.name` |
| `DBT_LAYER_SCHEMA_PREFIX` | `layer_schema_prefix` |
| `DBT_GITHUB_REPO_NAME` | `github_repo_name` |
| `DBT_LAYER_1` | first medallion layer |
| `DBT_LAYER_2` | second medallion layer |
| `DBT_LAYER_3` | third medallion layer |
| `DBT_COMMIT` | `commit` |
| `DBT_PUSH_TO_GITHUB` | `push_to_github` |
| `DBT_MATERIALIZATION_PROFILE` | `materialization_profile` |
| `DBT_AUTO_AGENTS_SCHEMA` | `auto_agents_schema` |
| `DBT_USE_SUBAGENTS` | `use_subagents` |

## What belongs in `.env`

Good:

- Domain name
- dbt profile key
- Source schema
- dbt source name
- Layer schema prefix
- Layer names
- Local-only or GitHub repo name
- Commit/push preferences
- Materialization profile
- Subagent preference for faster read-only analysis
- Agents Schema preference for supported destinations

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
