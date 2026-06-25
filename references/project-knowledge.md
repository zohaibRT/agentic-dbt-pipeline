# Project Knowledge

Use this at the start of every run, before discovery summaries, phase plans, model design, semantic metrics, evaluator decisions, documentation, and final delivery.

## Purpose

The data engineer may have dbt standards, domain definitions, modeling preferences, metric rules, privacy policy, naming conventions, or lessons from previous projects. The agent must treat that knowledge as project context, not as casual chat memory.

This file covers project-specific knowledge. Built-in reusable analytics engineering knowledge lives in [skill-knowledge.md](skill-knowledge.md), [data-engineering-best-practices.md](data-engineering-best-practices.md), and [principal-data-engineering-standards.md](principal-data-engineering-standards.md).

Use project knowledge to override or extend the skill's reusable defaults for the current domain, source system, team, warehouse, and presentation needs. Do not copy large external documentation into a project knowledge file.

## Where the user can share knowledge

Read these files when they exist:

| File | Purpose |
|---|---|
| `AGENT_KNOWLEDGE.md` | Workspace-level data engineer instructions for this dbt run |
| `docs/dbt_knowledge.md` | Longer dbt/domain knowledge, standards, and examples |
| `docs/business_rules.md` | Domain rules, mappings, metric definitions, and exclusions |
| `reports/agent/CONTEXT_TREE.md` | Prior decisions, accepted assumptions, reports, and open items |
| `.agents/project_knowledge.md` | Agent-specific reusable instructions for the project |

The user may also provide knowledge in the prompt under `project_rules:`. Prompt rules override files when there is a conflict.

## What to capture

When the user shares useful dbt knowledge in chat, ask whether to persist it if it should affect future runs. If the user agrees, write it to `AGENT_KNOWLEDGE.md` or the most relevant project knowledge file.

Useful knowledge includes:

- dbt naming conventions
- Layer responsibilities
- Preferred materializations
- Source table inclusion or exclusion rules
- Business grain definitions
- Mapping rules and code definitions
- Key performance indicator definitions
- Semantic layer preferences
- Data privacy and masking rules
- Presentation layer expectations
- Testing standards and accepted evaluator exceptions
- Deployment, commit, or review rules

Do not store secrets, passwords, tokens, private keys, or sensitive row-level data in project knowledge files.

## Required behavior

- Read [skill-knowledge.md](skill-knowledge.md) for the built-in knowledge layer, then read project knowledge for local overrides.
- Read project knowledge before making phase recommendations.
- Summarize which knowledge files were found and used in the phase plan.
- If a rule conflicts with discovered data, stop and ask before overriding it.
- Record applied, deferred, or conflicting knowledge in the phase report and `reports/agent/CONTEXT_TREE.md`.
- Do not use knowledge from sibling workspaces, previous runs, or nearby folders unless the user explicitly provides or approves it.

## Phase plan section

Add this section to each non-bootstrap phase plan when knowledge files or `project_rules` exist:

```markdown
### Project Knowledge Used
| Source | Rule / Knowledge | Applied How | Conflict? |
|---|---|---|---|
| <file or prompt> | <rule> | <implementation or plan impact> | <none / needs approval> |
```

If no project knowledge exists, write:

```markdown
### Project Knowledge Used
No project knowledge file or project_rules were provided for this phase.
```
