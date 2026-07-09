/*
Proof name: <business friendly proof name>
Phase: discovery

STATUS VOCABULARY
- PASS: evidence supports the claim
- WARN: usable with a documented limitation
- FAIL: claim is wrong or unsafe
- BLOCKED: waiting on user input or approval
- SKIPPED: intentionally not run

Purpose: <what this proves and why it matters>
Why this proof exists: <why a human or verifier should trust the discovery claim>
Source objects: <schema.table or metadata source>
Expected result: <expected row count, zero duplicates, allowed statuses, non-negative amount, etc.>
Captured result at run time:
<small aggregate result table copied from command output>
Status: PASS | WARN | FAIL | BLOCKED | SKIPPED
Why this status: <one sentence explaining PASS/WARN/FAIL/BLOCKED/SKIPPED>
Re-run notes: <profile/target/schema assumptions and any safe filters>
Sensitive data handling: Aggregate results only; no row-level direct identifiers stored.
Linked JSON artifact: discovery_raw.json tables[] / queries_executed[]
*/

<runnable SQL query>;
