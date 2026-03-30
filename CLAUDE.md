---
description: "Scientific Method workflow. Always active."
---

# Workflow: The Scientific Method

CRITICAL: "VERIFY MY DATA" means running tests, checking outputs, and gathering empirical evidence. Assumptions without empirical validation violate scientific methodology.

ASK as in: ASK the Data, ASK the TEST RESULTS, ASK the USER, ASK the Web Research tool, etc.

## Mandatory Workflow

ANY and ALL work MUST follow ONLY this WORKFLOW or a serious breach of PROTOCOL will have occurred.

### 1. GATHER DATA

Gather data SCIENTIFICALLY from PRIMARY SOURCES:
- The `docs/` folder in the project root if there is one
- The codebase itself
- The USER (who can also act as a go-between for web research)

### 2. PLAN

Write an `ACTION_PLAN.md` in the ROOT folder and present it to the USER for APPROVAL.
TAKE NO FURTHER ACTION WITHOUT USER APPROVAL.

Plan approval is only valid if the user responds with exactly: **"I approve your plan, proceed."**

ACTION_PLAN.md template requirements:
- Add **Branch:** [branch-name] field after Date
- Add **Related Work:** [previous work summaries] if applicable

### 3. EXECUTE

Execute the approved ACTION_PLAN.md in STAGES:
- Update each TASK's status upon completion
- Add a detailed WORK SUMMARY for each STAGE upon STAGE completion
- For any code changes, RUN all relevant tests and INCLUDE test results as MANDATORY VERIFICATION
- Continue until every TASK and STAGE is marked COMPLETE

### 4. VERIFY

Verify each STAGE's WORK SUMMARY and add WRITTEN PROOF to the ACTION_PLAN.md:
- Use REAL ANNOTATIONS to show LINE BY LINE that every TASK and STAGE is INDISPUTABLY COMPLETE
- WRITTEN PROOF MUST INCLUDE: test execution output, and performance measurements where applicable
- Append insights, learnings, surprises, solutions, or other KNOWLEDGE TRANSFER for future developers

Verification checklist:
- Technical validation (tests, functionality)
- Documentation of results
- Self-verification against protocol

#### Code Comment Cleanup (part of Verification)

After verification, go through the code and clean up comments:
- Avoid over-commenting. Prefer better function names, variable names, or docstrings over comments.
- Self-descriptive code is preferable, but don't avoid comments when they genuinely clarify intent.
- Refactor agent-added comments into more descriptive, readable code where possible.
- Follow Python PEP comment guidelines.
- Comments that contradict the code are worse than no comments. Always keep comments up-to-date when code changes.

### 5. APPROVE

PRESENT work to the USER for APPROVAL. **STOP. DO NOT PROCEED** until explicit USER approval is received.

Work approval is only valid if the user responds with exactly: **"I approve your work, proceed."**

### 6. ARCHIVE

Upon receiving explicit USER APPROVAL, and ONLY then:
1. Rename `ACTION_PLAN.md` as `[DATE][TASK]WORK_SUMMARY.md`
2. Move to `DEV_LOGS/` folder
3. Confirm LOG matches completed ACTION_PLAN.md
4. DELETE the original `ACTION_PLAN.md` file
5. Propose a commit message based on best practices (see `commit-message` skill)

CRITICAL: Never move ACTION_PLAN.md to DEV_LOGS without explicit USER approval.
CRITICAL: Always delete original ACTION_PLAN.md after successful archiving.

## WORK_SUMMARY Documentation Requirements

- Add **Branch:** field in header section
- Add **Branch Duration:** (start date - "in progress") for active branches
- Add **Related Work:** cross-references to other work on same branch

<protocol-summary>
## Protocol Summary

1. **GATHER DATA** — Read primary sources (docs/, codebase, user). Never assume.
2. **PLAN** — Write ACTION_PLAN.md, present to user. STOP until user responds: "I approve your plan, proceed."
3. **EXECUTE** — Work in stages. Update task status. Run tests for every code change. Include test results.
4. **VERIFY** — Add written proof (test output, annotations) to ACTION_PLAN.md. Clean up code comments.
5. **APPROVE** — Present to user. STOP until user responds: "I approve your work, proceed."
6. **ARCHIVE** — Rename to [DATE][TASK]WORK_SUMMARY.md, move to DEV_LOGS/, delete original ACTION_PLAN.md.

**CRITICAL constraints:**
- NEVER proceed past PLAN or APPROVE without explicit user approval using the exact phrases above
- NEVER move ACTION_PLAN.md to DEV_LOGS/ without explicit user approval
- ALWAYS delete original ACTION_PLAN.md after successful archiving
- "VERIFY MY DATA" means running tests and gathering empirical evidence — assumptions without validation violate protocol
</protocol-summary>
