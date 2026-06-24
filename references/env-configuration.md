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

## Skill-managed defaults

Do not require these in the prompt or `.env`:

| Decision | Default behavior |
|---|---|
| Project name/root | Derive from source schema or domain; never from dbt profile |
| dbt source name | Derive from source schema or domain |
| Schema isolation | Keep source schema read-only; route evaluator/seeds/snapshots to separate schemas |
| Layer schema prefix | Derive from explicit override, existing medallion schemas, domain, source schema, or descriptive source name |
| Layer names | Use `bronze`, `silver`, `gold` |
| Commit behavior | Ask before each phase commit |
| GitHub behavior | Commit locally by default; ask for repo details only when the user requests a push |
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
| `DBT_GITHUB_REPO_NAME` | `github_repo_name` |
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

Use advanced override keys only when the project should intentionally differ from the skill defaults.
Add a GitHub repo name only when the user wants the agent to push to a remote. For local-only work, omit it.

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

After resolving `DBT_PROFILE_NAME`, follow [warehouse-adapter-routing.md](warehouse-adapter-routing.md) before discovery. Read the selected profile key from `~/.dbt/profiles.yml`, resolve its adapter `type`, and use only that adapter's discovery path. Do not probe AWS, Redshift, Snowflake, BigQuery, Databricks, or any unrelated connector just because credentials, tools, or other profiles exist.

## First run when `.env` is missing

When the user runs the default prompt in a freshly cloned skill or dbt project and `.env` is missing:

1. Check whether `.env.example` exists.
2. If `.env.example` exists, create a local `.env` from it only when `.env` is gitignored or clearly excluded from commits.
3. If `.env.example` is missing, create `.env.example` with the minimal placeholder keys, then create local `.env` from it.
4. Do not fill fake real values. Leave placeholders for values the user must provide.
5. Stop before dbt discovery, `dbt debug`, `dbt deps`, codegen, or build commands.
6. Tell the user exactly which required values are missing and ask them to update `.env` or provide the values in chat.

When `.env` is missing, do not search the repo for alternate config files, inspect terminal history/output, inspect other workspaces, inspect old dbt projects, query warehouse schemas, or look at previous runs to decide what to do. The data engineer controls the active project inputs.

Do not infer required first-run values from other workspaces, old dbt projects, old `.env` files, existing medallion schemas, warehouse object names, terminal output, or previous runs. Do not scan or summarize other workspaces to suggest values. Ask the user directly.

Never combine missing-`.env` setup with discovery in the same response. Missing `.env` is a hard stop until the user confirms the required values.

Required first-run values:

```text
DBT_DOMAIN=<domain_name>
DBT_PROFILE_NAME=<dbt_profile_name>
DBT_SOURCE_SCHEMA=<raw_source_schema>
```

Optional project rules can be provided in chat after discovery:

```text
Project rules:
- Field mappings:
- Joins:
- Metrics:
- Exclusions:
- Privacy:
- Naming:
- Special instructions:
```

Use this user-facing message shape:

```text
I did not find `.env` in this workspace, so I created a local `.env` from `.env.example`.
Please send these required non-secret values and I will update `.env` for this run:

- DBT_DOMAIN: <business domain, for example hospital or retail>
- DBT_PROFILE_NAME: <dbt profile key from ~/.dbt/profiles.yml>
- DBT_SOURCE_SCHEMA: <raw/source schema to inspect>

Keep passwords in ~/.dbt/profiles.yml, not in `.env`.
After I update `.env`, I will summarize the values and wait for your approval before read-only discovery.

Optional: add project rules in chat if you have mappings, metrics, privacy rules, exclusions, or special instructions.
```

If the user provides the three values in chat, update the local `.env`, summarize only those user-provided values, and ask for approval before discovery. Do not add extra inferred values.

Never commit `.env`. Commit `.env.example` only if it contains placeholders and comments, not real project credentials or private connection details.
