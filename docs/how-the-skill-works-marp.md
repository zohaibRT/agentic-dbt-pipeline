---
marp: true
theme: default
paginate: true
title: Evidence-Driven dbt Agent Process
description: Presentation deck explaining the agentic dbt pipeline process, trust model, and future improvements
style: |
  section {
    font-family: "Segoe UI", Arial, sans-serif;
    color: #172033;
    background: #f7f9fc;
  }
  h1 {
    color: #0f3d5e;
    font-size: 42px;
  }
  h2 {
    color: #0f3d5e;
    font-size: 32px;
  }
  strong {
    color: #0f766e;
  }
  table {
    font-size: 22px;
  }
  li {
    margin: 0.25em 0;
  }
  code {
    color: #0f3d5e;
  }
---

# Evidence-Driven dbt Agent Process

How the dbt pipeline skill works, why it is more trustworthy than a normal prompt, and what can still improve.

---

## Presentation Goal

This is not a claim that the skill is perfect.

The goal is to explain:

- what process we designed
- how the agent stays controlled
- how generated dbt work is verified
- what is templated versus agent-decided
- what still needs improvement

---

## The Problem We Wanted To Avoid

A normal agent flow can look like this:

```text
User prompt
-> agent builds models
-> dbt build passes
-> dashboard is created
-> everyone assumes the numbers are correct
```

That is risky.

`dbt build` proves the project runs. It does **not** prove the business logic is correct.

---

## The Process We Built

We changed the workflow to:

```text
Discovery
-> requirements
-> phased dbt build
-> layer verification
-> KPI and metric contracts
-> reconciliation
-> acceptance gate
-> independent verification
-> human sign-off
```

The agent can build only what it can prove.

---

## Main Principle

**No model, metric, key performance indicator, measure, dashboard value, or phase is complete without evidence.**

Evidence means:

- business definition
- source mapping
- dbt model or report location
- SQL proof file
- expected result
- captured result
- status: `PASS`, `WARN`, `FAIL`, or `BLOCKED`

---

## Three Types Of Correctness

| Correctness Type | What It Proves | Example |
|---|---|---|
| Technical correctness | The code runs | `dbt parse`, `dbt build`, tests |
| Data correctness | The data behaves correctly | row counts, grain, joins, duplicates |
| Business correctness | The number means the right thing | KPI definition, filters, date basis |

All three are needed.

---

## How The Agent Starts

The agent does not start by building models.

It first checks:

- selected dbt profile
- source schema
- source tables
- row counts
- keys and relationships
- date fields
- status fields
- amount or quantity fields
- sensitive or unclear fields

Then it writes discovery evidence.

---

## Discovery Is Controlled

If `.env` is missing, the agent should not guess.

It should ask for:

- business domain
- dbt profile name
- source schema

If the configured source is missing, empty, or looks wrong, the agent must stop and ask before switching databases, schemas, tables, clients, tenants, or domains.

---

## What Is Templated?

The process is template-driven.

The skill defines required structures for:

- discovery report
- requirements file
- approval checklist
- phase reports
- SQL proof files
- layer verification ledger
- KPI definition contracts
- metric verification matrix
- final delivery summary

This keeps different agents from inventing completely different formats.

---

## What Is Agent-Decided?

The agent still adapts to the source data.

It decides recommendations such as:

- likely facts and dimensions
- bronze, silver, and gold model shape
- candidate metrics
- useful report pages
- safe dimensions for filters
- deferred or blocked items

But those decisions must be backed by source evidence and approval gates.

---

## Template Versus Data Reality

| Area | Controlled By Template | Varies By Source Data |
|---|---|---|
| Discovery report | Required sections | tables, columns, relationships |
| Requirements | Required format | business rules and open questions |
| SQL proofs | Required header and status | actual queries and results |
| KPI contracts | Required fields | formula, filters, date basis |
| Dashboard plan | Required evidence | page names and visuals |

The template controls the structure. The source controls the content.

---

## Phased Build Flow

The project is built in checkpoints:

1. Discovery
2. Project setup
3. Sources
4. Bronze or staging
5. Silver or intermediate
6. Gold or marts
7. Semantic layer
8. Documentation
9. Analytics insight reporting
10. Optional presentation layer
11. Final verification

Each phase writes a report before moving forward.

---

## Why Phases Matter

Phases keep the data engineer in control.

Before each non-setup build phase:

- the agent writes a plan
- explains what will be built
- lists what will not be included
- shows evidence and risks
- waits for approval

Approval is checkpoint-specific, not unlimited permission.

---

## Layer Verification

After each layer, the agent must verify:

- row counts
- expected empty versus unexpected empty models
- grain and duplicate keys
- relationship integrity
- row loss or row multiplication
- status distributions
- date coverage
- measure sanity
- privacy exposure

Results go into the layer report and `LAYER_VERIFICATION_LEDGER.md`.

---

## KPI And Metric Verification

Every important metric or KPI needs a contract.

The contract records:

- business meaning
- formula
- grain
- date basis
- included rows
- excluded rows
- source tables or models
- SQL proof file
- expected result
- actual result
- difference or tolerance

Without this, the KPI is not trusted.

---

## Reconciliation Example

For a revenue KPI, the agent should prove:

```text
source revenue
= silver revenue components
= gold fact revenue
= semantic metric
= presentation value
```

If the values differ, the agent must identify the first failing layer.

The answer should not be "dbt build passed."

---

## Acceptance Gate

Before final delivery, the process runs scripts such as:

```bash
python scripts/run_acceptance_gate.py --root .
python scripts/check_requirement_traceability.py --root .
python scripts/check_layer_proof_coverage.py --root .
python scripts/verify_metric_reconciliation.py --root .
```

These scripts check whether the required evidence exists.

---

## Independent Verification

The builder agent is not the final judge.

A fresh verifier agent should read only:

- repository files
- dbt artifacts
- phase reports
- SQL proof files
- acceptance gate output

It should not rely on the builder chat.

This creates separation between builder and reviewer.

---

## Why This Is More Trustworthy

The process is more trustworthy because:

- decisions are written to files
- source assumptions are visible
- requirements are traceable
- models have proof records
- KPIs have contracts
- metrics are reconciled
- acceptance gates can fail the delivery
- humans still approve business meaning

It is evidence-driven, not chat-driven.

---

## What The Human Still Owns

The agent can recommend, but the data engineer owns:

- correct source selection
- business meaning
- privacy decisions
- ambiguous field mappings
- KPI approval
- accepted warnings
- final sign-off

This process supports the data engineer. It does not replace them.

---

## Presentation Layer Approach

After analytics insight reporting, the agent asks whether to build a presentation layer.

Default recommendation:

- rich Matplotlib browser report
- SQL-backed values
- tabs by business purpose
- KPI cards, trends, exception panels, detail sections

Power BI is supported as a controlled handoff, especially when a human-created PBIP template is safer.

---

## Why Power BI Needs Extra Care

Power BI files can fail because of:

- Desktop version mismatch
- TMDL or PBIP structure issues
- connection or credential handling
- relationship ambiguity
- generated DAX mismatch

So the safer workflow is:

1. human creates or confirms the connected template
2. agent injects approved measures only
3. agent validates the model and reports evidence

---

## What We Improved Recently

Recent improvements added:

- evidence-driven build process
- KPI definition contracts
- metric verification matrix
- requirement traceability checks
- layer proof coverage checks
- independent verifier agent
- acceptance gate workflow
- richer Matplotlib report standards
- stricter Power BI handoff rules

---

## Current Limitations

This process is strong, but not magic.

Known limitations:

- business definitions still need human approval
- source data can be incomplete or misleading
- SQL proofs need adapter-aware execution
- golden test data is not yet fully automated
- Power BI validation depends on local Desktop and tooling availability
- different agents may still phrase reports differently, even with templates

---

---

## How To Know You Are On Track

Read `docs/how-to-verify-generated-project.md`.

You are going in the right direction when:

- `PIPELINE_STATUS.md` has no unresolved `FAIL` or `BLOCKED`
- each built layer has `sql_proofs/` with captured results
- approved assumptions are locked in as dbt tests
- KPI variance report is clean or explained
- acceptance gate and verifier return `PASS` or documented `WARN`

---

## Structural vs Assumption Tests

| Type | Examples | Catches |
|---|---|---|
| Structural | `unique`, `not_null`, `relationships` | schema issues |
| Assumption | grain after join, date order, status implies field | business beliefs that break later |

Process:

```text
State assumption -> prove in sql_proofs -> lock in dbt test
```

Templates: `templates/dbt/tests/`

---

## Further Improvements

Useful next improvements:

- add sample projects for multiple domains
- add golden test datasets for common KPI patterns
- add stronger dbt unit test generation
- add adapter-specific proof query templates
- add a visual report template gallery
- add automated screenshot validation for Matplotlib reports
- add more Power BI Desktop version test cases
- add CI examples per warehouse adapter

---

## Key Message For The Audience

This is not just an agent that writes dbt code.

It is a controlled process where:

- discovery happens before build
- build happens in approved phases
- every important number needs proof
- final delivery can fail
- human approval still matters

That is why the process is practical for real analytics engineering work.

---

## Closing Statement

**The goal is not to prove the skill is perfect.**

The goal is to make agent-generated dbt work:

- repeatable
- reviewable
- evidence-backed
- safer for business reporting
- easier for a data engineer to trust or challenge

That is the process we built.
