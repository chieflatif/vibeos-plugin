---
name: session-audit
description: Audit the current or most recent VibeOS build session end-to-end. Use when the user says "audit this session", "review what happened in this session", "session audit", or wants a closeout review of the work completed during an autonomous run.
argument-hint: "[optional: current|last|session id]"
allowed-tools: Read, Write, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:session-audit — Session Closeout Review

Audit everything completed in the current or most recent VibeOS session, then produce a session-level report.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Explain the session summary in plain English before diving into audit details
- Distinguish between "what happened in the session" and "what still needs follow-up"
- If findings require a choice, present options with pros, cons, and a recommendation

## Prerequisites

Before starting, verify these exist:
- `.vibeos/build-log.md`
- `docs/planning/DEVELOPMENT-PLAN.md`
- `docs/planning/WO-INDEX.md`

If the build log is missing, report that no VibeOS session history is available yet.

## Session Scope Resolution

### Step 1: Determine Which Session To Audit

1. Read `.vibeos/session-state.json` if it exists.
2. If `$ARGUMENTS` specifies `current`, `last`, or a specific `session_id`, use that when possible.
3. If `.vibeos/session-state.json` exists, use it as the primary session record.
4. If no session file exists, infer the most recent session from `.vibeos/build-log.md` by finding the most recent contiguous block of WO activity and state that inference explicitly.

### Step 2: Gather Session Evidence

Read:
- `.vibeos/build-log.md`
- `.vibeos/session-state.json` if present
- `docs/planning/WO-INDEX.md`
- each WO file listed in the session's `completed_wos`, or the inferred WOs from the build log
- `.vibeos/audit-reports/` entries that match the session WOs, if present
- anchor documents when they exist:
  - `docs/product/PRODUCT-ANCHOR.md`
  - `docs/ENGINEERING-PRINCIPLES.md`
  - `docs/research/RESEARCH-REGISTRY.md`
  - `docs/decisions/DEVIATIONS.md`

Capture:
- session start and end times
- autonomy mode
- WOs completed during the session
- active or unresolved blockers
- touched files or affected areas, when available

### Step 3: Run Session-End Verification

1. Run pre-commit quality checks on the current project state:
   ```bash
   bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure --project-dir "${CLAUDE_PROJECT_DIR:-.}"
   ```
2. If the project has a `session_end` phase configured, run it too:
   ```bash
   bash ".vibeos/scripts/gate-runner.sh" session_end --continue-on-failure --project-dir "${CLAUDE_PROJECT_DIR:-.}"
   ```
3. Dispatch the 6 audit agents (security, architecture, correctness, test, evidence, product-drift).

Pass each auditor:
- the project-definition path
- the session WO list
- the session-state path if present
- the build-log path

Ask auditors to focus on session-created regressions, missed evidence, drift, and unresolved risk that came out of the session.

### Step 4: Produce the Session Audit Report

Format the output like this:

```markdown
## Session Audit

**Session:** [session id or inferred session]
**Mode:** [autonomous|standard]
**Started:** [timestamp]
**Ended / Current:** [timestamp]

### Session Summary

- **Work orders completed:** [list]
- **Phase movement:** [phase summary]
- **Top outcomes:** [plain English summary]

### Verification Summary

- **Pre-commit gates:** [pass/fail summary]
- **Session-end gates:** [pass/fail/skipped summary]
- **Audit result:** [pass/conditional pass/fail]

### Findings

| Severity | Count | What it means |
|---|---|---|
| Critical | [N] | [plain English explanation] |
| High | [N] | [plain English explanation] |
| Medium | [N] | [plain English explanation] |
| Low | [N] | [plain English explanation] |

### Drift and Standards

- **Product anchor alignment:** [aligned/partial/drift]
- **Engineering principles alignment:** [aligned/partial/drift]
- **Freshness gaps:** [none or summary]
- **Open deviations:** [none or summary]

### Recommendation

[1-3 sentence recommendation on whether to continue, fix follow-ups first, or run a checkpoint]
```

### Step 4b: Automated Retrospective

After compiling the session audit, generate a pattern analysis:

1. **Read the findings registry** (`.vibeos/findings-registry.json`) if it exists
2. **Identify recurring patterns:**
   - If >3 findings in one agent run were later marked `false_positive` with tag `stale_worktree` — recommend enabling worktree freshness guard
   - If >2 findings tagged `contract_drift` — recommend promoting contract validation gate to blocking
   - If >5 findings tagged `silent_pass` — recommend running detect-testing-antipatterns.py at pre_commit phase
   - If any gate has been "within baseline" for >2 phases — flag for resolution or removal
3. **Generate recommendations** for framework configuration changes
4. **Store retrospective** at `.vibeos/retrospectives/phase-{N}-retro.md`

Create `.vibeos/retrospectives/` if it does not exist.

The retrospective is informational — it recommends changes but does not make them. The human decides whether to apply recommendations.

### Step 5: Save the Report

Save the report to:

```text
.vibeos/session-audits/session-[session-id-or-date].md
```

Create `.vibeos/session-audits/` if needed.

If `.vibeos/session-state.json` exists, update:
- `last_audited_at`
- `last_audit_report`

## Error Handling

- If no session markers exist, infer the most recent session from the build log and say so clearly
- If session-specific WO evidence is incomplete, continue the audit and mark those gaps explicitly
- Never invent completed work that is not backed by build-log or WO evidence
