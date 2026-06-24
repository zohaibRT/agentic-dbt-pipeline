# Source Confirmation

Use this whenever the configured source is missing, empty, inaccessible, ambiguous, mismatched, or appears to point at the wrong data.

## Core rule

This skill is reusable across many domains, clients, databases, datasets, tenants, and environments.

Never silently substitute a different data source than the one provided by the user, `.env`, or configuration.

When the requested source is missing, empty, ambiguous, or mismatched, pause and ask before switching databases, datasets, catalogs, schemas, tables, domains, tenants, clients, environments, or business assumptions.

## Source confirmation rule

If the configured source is unavailable, empty, inaccessible, or does not contain the expected data:

1. Stop active discovery beyond the configured source.
2. Report exactly what was checked.
3. List candidate alternatives only if already visible from safe metadata.
4. Explain the best guess and why.
5. Ask the user to approve the next source before inspecting, profiling, reporting, or updating files.

Do not continue with an alternate database, dataset, catalog, schema, table, client, tenant, business domain, environment, or assumption without explicit user confirmation.

Examples requiring confirmation:

- The configured source schema is empty but another schema has tables.
- The requested schema is missing but another schema has similar names.
- The provided database appears wrong.
- Multiple candidate source tables exist.
- The data looks like a different domain than expected.
- A production-like database is discovered while working in a development context.
- A tenant, client, or account-specific dataset appears to be different from the requested one.

## Ask-before-switching contract

Use this wording:

```text
I could not find the expected data in `<provided_source>`.

I found these possible alternatives from metadata only:
- `<candidate_1>`: <evidence>
- `<candidate_2>`: <evidence>

My best guess is `<candidate>` because `<evidence>`.

Do you want me to use this source?
```

The agent must wait for approval before continuing.

## Approved source lock

Once the user approves a source, treat it as locked for the current run.

If later steps suggest another source may be better, pause again and ask before switching.

Record the approved source lock in `reports/agent/CONTEXT_TREE.md` after discovery files are allowed to be written.

## Safe metadata only

Allowed before approval:

- List database, dataset, catalog, schema, or table names visible through the selected profile and adapter.
- Count candidate tables by schema when this is lightweight.
- Report non-secret metadata that explains why a candidate may be relevant.

Not allowed before approval:

- Profile candidate table rows.
- Inspect candidate columns beyond names already returned by safe metadata listing.
- Infer relationships or business entities.
- Create Mermaid diagrams from candidate sources.
- Write discovery reports for candidate sources.
- Update `.env` or `profiles.yml`.
- Continue to Bootstrap, codegen, source YAML, or modeling.
