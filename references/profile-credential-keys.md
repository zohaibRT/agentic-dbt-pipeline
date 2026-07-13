# Profile Credential Keys

Use this when connecting to a warehouse from a dbt profile for discovery, `dbt debug`, or any read-only Python/SQL bridge.

Also read [security-and-credentials.md](security-and-credentials.md) and [warehouse-adapter-routing.md](warehouse-adapter-routing.md).

## Core rule

dbt warehouse profiles commonly store the password under **`pass`**, not `password`.

Before saying “credential missing” or “no password supplied”, check both keys on the selected profile target:

| Key | Meaning |
|---|---|
| `pass` | Standard dbt Postgres/Redshift/Snowflake-style password field |
| `password` | Alternate field some tools/connectors use |

Resolution order for a direct connector (for example psycopg):

1. If `pass` is present and non-empty → use it as the connector password parameter
2. Else if `password` is present and non-empty → use it
3. Else if either key is an `env_var(...)` / Jinja reference → resolve that environment variable securely
4. Else treat the credential as missing

Never print, log, commit, or paste the value of `pass` or `password`.

## Preferred discovery path

Prefer the dbt connection itself when possible:

```text
dbt debug
dbt show --inline "select 1"
```

When a direct Python/SQL client is required, map profile fields like this for PostgreSQL:

```text
host     <- host
port     <- port
dbname   <- dbname / database
user     <- user
password <- pass  (fallback: password)
```

Do **not** require a profile key literally named `password` when `pass` already exists.

## Before declaring a credential blocker

Run this non-secret check:

```powershell
python <skill>/scripts/check_profile_credential_keys.py --profile <DBT_PROFILE_NAME>
```

Interpret:

| Result | Meaning | Next step |
|---|---|---|
| `PASS` / credential key found | Profile has `pass` and/or `password` (or env-var ref) | Map `pass` → connector password and retry |
| `FAIL` / no credential key | Neither key exists on the target | Ask user to add `pass` in `~/.dbt/profiles.yml` or choose another profile |
| Key exists but auth still fails | Wrong value, env var unset, or server rejection | Report auth failure; do not claim “password key missing” |

## What to ask the user

If the checker finds no credential key:

```text
I checked ~/.dbt/profiles.yml for profile <name>.
I did not find a `pass` or `password` key on the selected target.

dbt usually stores the warehouse password under `pass`.
Please add or fix that key locally in ~/.dbt/profiles.yml, or tell me a different profile to use.
Do not paste the password in chat.
```

If the checker finds `pass` but a connector still says “no password supplied”:

```text
The selected profile already has dbt's `pass` field.
My connector was looking only for `password`. I will remap `pass` to the connector password parameter and retry.
I will not print or store the secret.
```

Do **not** ask “is pass the password?” in a way that invites the user to paste the secret. Explain the field-name mapping and retry.

## Never

- Ask the user to paste the password into chat
- Print `pass` / `password` values
- Treat absence of the literal key `password` as proof that credentials are missing when `pass` exists
- Write credentials into reports, `.env`, SQL proofs, or commits
