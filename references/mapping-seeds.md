# Mapping Seeds and Coverage

Use this when `project_rules` include manual mappings, code translations, department/group mappings, category mappings, or user-provided business labels.

Read [privacy-and-unknown-fields.md](privacy-and-unknown-fields.md) before creating mappings for unclear coded fields.

Read [schema-isolation.md](schema-isolation.md). Seeds must not build into the source schema.

## When to create seeds

Create dbt seeds when mappings are stable business reference data, for example:

- Source status code -> business status
- Department code -> department group
- Provider specialty -> service line
- Product category -> reporting category
- Location code -> region

Do not create seeds for mappings that already exist as reliable warehouse reference tables. Use those source tables instead.

Do not create mapping seeds for ambiguous, placeholder, abbreviated, generic, or poorly named fields from guessed meanings. If definitions are missing, recommend passing them through bronze/staging as raw unmapped fields, deferring mappings, and excluding them from gold/marts by default.

## Seed location and naming

- Folder: `seeds/{domain}/`
- File: `{source_name}__<mapping_name>.csv`
- Include one row per source value
- Include an explicit fallback or unmapped handling rule when the user approves it

Example columns:

```csv
source_value,target_value,description,is_active
```

## dbt project config

If seeds are added, configure them in `dbt_project.yml`:

```yaml
seeds:
  {project.name}:
    {domain}:
      +schema: {layer_schema_prefix}_seeds
```

Ask before changing physical schema naming.

Default seed schema: `{layer_schema_prefix}_seeds`.

## Usage by layer

- Staging: keep raw codes and lightly cleaned values. Do not apply heavy mappings unless it is simple standardization.
- Intermediate: join mapping seeds and create business-friendly fields.
- Marts: expose mapped business fields; hide or de-emphasize raw codes unless useful for audit.

## Coverage tests

When a mapping seed is used, add tests or validation queries for:

- Mapping seed key is unique and not null
- Every mapped source value is covered, or unmapped values are intentionally handled
- No inactive mapping is used in final marts unless explicitly allowed

If unmapped values exist, summarize them and ask whether to add mappings, keep an "Unknown" bucket, or exclude them.

If a field has no confirmed business definition, do not treat its observed values as "unmapped values" for a seed yet. First ask the user to approve the safe default or provide definitions.

## Commit

Commit mapping seeds separately when they are a meaningful business artifact:

```text
Add mapping seeds for <domain>
```
