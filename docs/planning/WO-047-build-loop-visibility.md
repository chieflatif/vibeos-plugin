# WO-047: Build Loop Visibility & Progress Reporting

## Status

`Draft`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Add mandatory progress reporting to the build loop so the user always knows what's happening: which step is running, which agent is active, what the agent is doing, and what happens next. Non-escalation events (retries, convergence iterations, gate re-runs) are no longer silent — the user sees a brief update for every meaningful state change.

## Scope

### In Scope
- [ ] Mandatory step banner at each build step transition: `"[Step N/M] agent-name — what it's doing"`
- [ ] Agent identification in every progress update
- [ ] Gate results reported inline: `"Quality checks: 11/12 passed. 1 pre-existing issue tracked."`
- [ ] Audit dispatch reported: `"Running 5 quality auditors in parallel..."`
- [ ] Audit results summarized: `"Auditors found 2 issues. 1 confirmed (flagged by 2 auditors), 1 warning."`
- [ ] Convergence retries reported: `"Fixing 2 audit findings automatically (attempt 2 of 5)..."`
- [ ] Gate fix retries reported: `"Quality check failed. Fixing [issue] and re-running (attempt 2 of 3)..."`
- [ ] Iteration and dispatch counts reported at WO completion: `"This WO dispatched [N] agents across [M] iterations ([X] gate retries, [Y] audit convergence cycles)"` (token counts are best-effort — the Agent tool may not expose token usage to the caller; dispatch counts are always available from the orchestrator's own tracking)
- [ ] Phase progress indicator: `"Phase 2: 3 of 5 work orders complete"`
- [ ] Update `skills/build/SKILL.md` with mandatory progress reporting at every step
- [ ] Define progress templates in the Communication Contract

### Out of Scope
- Time/effort estimation (inherently unreliable with LLMs)
- Real-time streaming progress bars
- Communication contract creation (WO-045)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-045 | User communication contract | Draft |
| WO-044 | Remediation roadmap (soft) | Draft |

**Soft dependency note:** WO-044 modifies `skills/build/SKILL.md` for Phase 0 enforcement and aging reminders. WO-047 should be implemented after WO-044 to add progress banners around those additions. The templates defined here (Step 1) must conform to WO-045's template schemas.

## Impact Analysis

- **Files modified:** `skills/build/SKILL.md` (add progress reporting at every step), `docs/USER-COMMUNICATION-CONTRACT.md` (add progress template variants that conform to WO-045 schema)
- **Systems affected:** Build loop, gate execution, audit cycle, convergence control
- **Note:** Standalone `/vibeos:audit` progress is out of scope — this WO focuses on the build loop where silence is most problematic. Audit skill progress can be a backlog item post-Phase 7.

## Acceptance Criteria

- [ ] AC-1: Every build step transition has a progress banner with step number and agent name
- [ ] AC-2: Gate results reported inline with pass/fail counts and top issue
- [ ] AC-3: Audit agent dispatch and completion reported
- [ ] AC-4: Convergence retries are not silent — user sees brief update
- [ ] AC-5: Gate fix retries are not silent — user sees what failed and that a retry is happening
- [ ] AC-6: Dispatch and iteration counts reported at WO completion (token counts best-effort if Agent tool exposes them)
- [ ] AC-7: Phase progress shown (N of M WOs complete)
- [ ] AC-8: Every agent dispatch has a pre-dispatch banner and a post-completion summary (the subagent model does not support mid-dispatch keepalives, so step banners before and after each dispatch are the primary mitigation for long silent periods)
- [ ] AC-9: Progress updates follow Communication Contract templates (WO-045)

## Test Strategy

- **Review:** Trace through build skill step by step, verify every transition has a progress update
- **Silent periods:** Identify any paths where the system could run for >30 seconds without user output
- **Template compliance:** Verify progress updates match Communication Contract format

## Implementation Plan

### Step 1: Define Progress Templates
Add to the Communication Contract (from WO-045):

```
STEP_BANNER: "[Step {N}/{M}] {agent-name} — {description in plain English}"
GATE_RESULT: "Quality checks: {passed}/{total} passed.{if failures} {top_issue_plain_english}{/if}"
AUDIT_DISPATCH: "Running {N} quality auditors to review your code..."
AUDIT_RESULT: "Audit complete: {confirmed} confirmed findings, {warnings} warnings.{if critical} {critical_summary}{/if}"
RETRY: "{what_failed}. Fixing automatically (attempt {N} of {max})..."
WO_SUMMARY: "This work order dispatched {N} agents across {M} iterations ({gate_retries} gate retries, {audit_cycles} audit convergence cycles).{if token_data} Used approximately {tokens} tokens ({audit_pct}% on quality enforcement).{/if}"
PHASE_PROGRESS: "Phase {N}: {completed}/{total} work orders complete."
```

### Step 2: Update Build Skill Steps
For each of the 11 steps in `skills/build/SKILL.md`, add mandatory progress output:

**Step 1 (Identify WO):**
> "Starting WO-NNN: [title]. [1-sentence description of what this builds]."

**Step 4 (Investigator):**
> "[Step 1/8] Investigator — Reviewing requirements and checking dependencies before we start building..."

**Step 5 (Tester):**
> "[Step 2/8] Tester — Writing tests from your requirements. These tests define what 'working' means before any code is written."

**Step 6 (Implementation):**
> "[Step 3/8] Backend — Writing the code to make all tests pass..."

**Step 7 (Gates):**
> "[Step 4/8] Quality Gates — Running [N] automated quality checks..."
> Result: "Quality checks: 11/12 passed. 1 pre-existing issue tracked (lint warning in legacy code)."
> On retry: "1 new quality issue found: [description]. Fixing and re-checking (attempt 2 of 3)..."

**Step 8 (Audit):**
> "[Step 5/8] Audit — Running 5 independent quality reviewers..."
> Result: "Audit complete: 1 confirmed finding (architecture), 2 warnings. Fixing the confirmed finding..."
> On convergence retry: "Fix applied. Re-running auditors to verify (iteration 2 of 5)..."

**Step 9 (Doc Writer):**
> "[Step 6/8] Documentation — Updating project docs and work order tracking..."

**Step 10 (Completion):**
> "[Step 7/8] Completing WO — Updating tracking documents..."

**Step 11 (Check-in):**
> "[Step 8/8] Check-in — Here's what was built: [summary]"

### Step 3: Silent Period Mitigation
The subagent model does not support streaming partial output back to the main thread during dispatch. The primary mitigation is the pre-dispatch and post-completion banners from Step 2, which ensure the user always knows what's happening before and after each agent runs. For the longest-running dispatches (audit agents in parallel), the pre-dispatch banner should set expectations:
> "[Step 5/8] Audit — Running 5 independent quality reviewers. This is the longest step and may take a minute..."

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Trace through build skill, verify no silent paths
- Risk: Too many progress updates could be noisy; balance visibility with signal-to-noise ratio

## Evidence

- [ ] Every step transition has a progress banner
- [ ] Gate results reported inline
- [ ] Audit dispatch and results reported
- [ ] Retries not silent
- [ ] Dispatch and iteration counts reported
- [ ] Every dispatch has pre/post banners
