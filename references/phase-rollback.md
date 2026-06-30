# Phase Rollback And Redo

Use this when a phase completed but the data engineer wants to undo it, redo it differently, or roll back because a grain, privacy, mapping, metric, naming, or source decision changed.

Rollback is a controlled workflow. Do not quietly delete files, drop warehouse objects, rewrite reports, or change pipeline memory without an approved rollback plan.

## Core rule

Before rollback, write or update `AGENT_PLAN.md` and ask for approval unless the user explicitly requested a narrow file-only revert and no warehouse objects or reports are affected.

The source schema remains read-only. Never roll back by updating, deleting, truncating, repairing, or backfilling source tables.

## Rollback plan

The plan must include:

- Phase or artifact being rolled back
- Reason for rollback
- Files to remove, regenerate, or keep
- Warehouse objects that may need to be dropped, rebuilt, or left as stale
- Reports/status files to update
- Git state: whether to create a new corrective commit, revert a prior commit, or leave changes uncommitted
- Validation commands after rollback
- Whether downstream phases must be marked stale or blocked

Use this template:

```markdown
# Rollback Plan

## Rollback Scope
- Phase: <sources / staging / intermediate / marts / semantic_layer / evaluator / docs / analytics_insight_reporting / presentation_layer>
- Reason: <why rollback is needed>

## Files
| Action | Path | Reason |
|---|---|---|
| keep/remove/regenerate | <path> | <reason> |

## Warehouse Objects
| Action | Object | Approval Required? | Reason |
|---|---|---|---|
| leave/drop/rebuild | <schema.object> | <yes/no> | <reason> |

## Status And Memory Updates
- `reports/agent/PIPELINE_STATUS.md`: <planned status change>
- `reports/agent/CONTEXT_TREE.md`: <decision/status update>
- Phase report: <append rollback note or replace after rebuild>

## Validation After Rollback
```powershell
<commands>
```

## Approval Needed
Reply `approve rollback` to continue, or tell me what to change.
```

## File rollback

Prefer additive correction commits over destructive history rewrites.

When the user wants to redo a phase:

1. Identify files created by that phase from the phase report, context tree, and git diff/log.
2. Keep user-authored files unless the user explicitly says to remove them.
3. Remove or regenerate only files inside the approved phase scope.
4. Update `AGENT_PLAN.md` with the rollback result.
5. Update `reports/agent/PIPELINE_STATUS.md` so the rolled-back phase is not shown as complete.
6. Update `reports/agent/CONTEXT_TREE.md` so stale decisions, models, metrics, or presentation scope are marked rolled back, stale, or superseded.

Do not use destructive git commands such as `git reset --hard` or `git checkout --` unless the user explicitly asks for that exact operation and the scope is safe.

## Warehouse rollback

Dropping or replacing warehouse objects requires explicit approval.

Safe defaults:

- If a phase will be immediately rebuilt, prefer `dbt build --full-refresh` for approved incremental models when appropriate.
- If stale schemas or tables exist from a previous failed naming/prefix choice, list them and ask before dropping.
- If source schema contains dbt-created artifacts, do not drop them automatically. Report them and ask for cleanup approval.

Before dropping any non-source object, show:

```sql
-- candidate cleanup objects
select table_schema, table_name
from information_schema.tables
where table_schema in ('<layer_schema_prefix>_bronze', '<layer_schema_prefix>_silver', '<layer_schema_prefix>_gold')
order by table_schema, table_name;
```

Adapter-specific cleanup SQL must be reviewed before execution.

## Downstream invalidation

If an upstream phase is rolled back, downstream phases that depend on it are no longer trusted.

Mark downstream items as stale or blocked in `PIPELINE_STATUS.md` and `CONTEXT_TREE.md`:

| Rolled-back phase | Mark stale or blocked |
|---|---|
| Sources | Staging, intermediate, marts, semantic layer, evaluator, docs, analytics insight reporting, presentation layer |
| Staging | Intermediate, marts, semantic layer, evaluator, docs, analytics insight reporting, presentation layer |
| Intermediate | Marts, semantic layer, evaluator, docs, analytics insight reporting, presentation layer |
| Marts | Semantic layer, evaluator, docs, analytics insight reporting, presentation layer |
| Semantic layer | Docs, analytics insight reporting, presentation layer when metrics were used |
| Docs | Analytics insight reporting and presentation layer when they rely on docs artifacts |
| Analytics insight reporting | Presentation layer |
| Presentation layer | Final delivery presentation status |

Do not keep final delivery marked complete after a rollback invalidates required outputs.

## Redo after rollback

After rollback, return to the normal phase workflow:

1. Run focused phase discovery.
2. Write/update `AGENT_PLAN.md`.
3. Ask for phase approval.
4. Implement only the approved phase.
5. Run dbt validation and layer data validation where applicable.
6. Update phase report, `PIPELINE_STATUS.md`, and `CONTEXT_TREE.md`.
7. Ask for commit approval.

## Completion report

Append a rollback section to the affected phase report:

```markdown
## Rollback / Redo

| Item | Result |
|---|---|
| Rollback approved by | <user / prompt / ticket> |
| Files changed | <paths> |
| Warehouse objects changed | <objects or none> |
| Downstream phases marked stale | <phases> |
| Validation after rollback | <PASS/WARN/FAIL/BLOCKED> |
| Next phase checkpoint | <phase needing approval> |
```
