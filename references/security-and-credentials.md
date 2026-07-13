# Security & Credentials

## Never

- Hardcode passwords, tokens, or private keys in `SKILL.md`, SQL, YAML, or commits.
- Paste full `profiles.yml` contents with passwords into prompts or issue comments.
- Commit `.env`, `profiles.yml`, or credential files. Commit `.env.example` only when it contains no secrets.
- Print secrets in terminal output or chat summaries.
- Change production schemas, profiles, or credentials without user approval.

## Always

- Inspect `.gitignore` before the first commit.
- Use `.env` or `project.config.yml` for **non-secret** connection metadata only.
- Reference credentials via:
  - Local: `~/.dbt/profiles.yml`
  - CI: GitHub Actions secrets
  - Agents Schema: `WAREHOUSE_CREDENTIALS` secret (YAML in GitHub)
- Ask for the dbt profile key, such as `dbt_profile_name: hospital_analytics`, instead of asking for passwords.
- When listing available dbt profiles, show only profile name, adapter, and non-secret notes such as host kind, database, target, or schema. Never show passwords, `pass` values, tokens, private keys, full connection strings, or the full `profiles.yml`.
- When connecting outside dbt, treat dbt's `pass` field as the password source. Also accept `password` if present. See [profile-credential-keys.md](profile-credential-keys.md). Do not report “password missing” only because the key is named `pass`.
- If authentication says “no password supplied”, first check whether `pass` exists and remap it. Ask whether the user meant the dbt `pass` field only as a field-name clarification, never as a request to paste the secret.

## `.gitignore` minimum entries

```gitignore
.venv/
target/
logs/
dbt_packages/
.env
profiles.yml
```

When Agents Schema is enabled, the dbt manifest is the only allowed exception:

```gitignore
target/*
!target/manifest.json
```

Do not commit other files from `target/`.

## Production guardrails

Before any change when `target=prod` or production database:

1. **Ask the user** to confirm.
2. Run `dbt parse` and scoped `dbt build` - not full-project unless approved.
3. Never `dbt run-operation` against prod without explicit approval.

## GitHub Actions secrets

| Secret | Purpose |
|---|---|
| `WAREHOUSE_CREDENTIALS` | Agents Schema sync (warehouse YAML) |
| dbt profile vars | CI `dbt build` *(project-specific)* |

Store warehouse credentials as YAML in the secret - not in the repository.
