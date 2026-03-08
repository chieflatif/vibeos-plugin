---
name: build
description: Autonomous build orchestrator that executes work orders end-to-end. Dispatches investigator, tester, implementation, and documentation agents in sequence with two-layer quality enforcement (Layer 1 gates + Layer 2 audit agents) and error recovery.
argument-hint: "[optional: WO number to build, e.g. 'WO-001']"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:build — Autonomous Build Orchestrator

Execute work orders autonomously with TDD, layered agents, quality gates, and error recovery.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`${CLAUDE_PLUGIN_ROOT}/docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Never ask "what do you want to build?" — read the plan and execute

## Prerequisites

Before starting, verify these exist:
- `docs/planning/DEVELOPMENT-PLAN.md`
- `docs/planning/WO-INDEX.md`
- `project-definition.json`

If any are missing, tell the user to run `/vibeos:plan` first.

## Token Tracking

After every agent dispatch, record token usage:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/token-tracker.sh" record \
  --agent "[agent-name]" --wo "WO-NNN" \
  --input-tokens [N] --output-tokens [N]
```

After each WO completes, check audit overhead:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/token-tracker.sh" overhead
```

If audit overhead exceeds 30%, log a warning in the build log and report to the user.

## Build Flow

### Step 1: Identify Next WO

If `$ARGUMENTS` contains a WO number, use that. Otherwise:

1. Read `docs/planning/DEVELOPMENT-PLAN.md`
2. Read `docs/planning/WO-INDEX.md`
3. Find the current phase (first phase with incomplete WOs)
4. Within that phase, find the first WO whose:
   - Dependencies are all Complete
   - Status is Draft or Implementation Ready

If no WO is available, report that all WOs in the current phase are complete and suggest running `/vibeos:status`.

### Step 2: Read Autonomy Config

Read `.vibeos/config.json` if it exists:
- `autonomy.level = "wo"` — pause after this WO completes
- `autonomy.level = "phase"` — continue until phase completes
- `autonomy.level = "major"` — continue until a major decision is needed

Default to "wo" if config doesn't exist.

### Step 3: Set Agent Identity

Write the current agent name to `.vibeos/current-agent.txt` before each agent dispatch. This enables the test file protection hook to identify which agent is running.

```
echo "investigator" > .vibeos/current-agent.txt
```

Update this file before each agent dispatch.

### Step 4: Dispatch Investigator Agent

Dispatch `agents/investigator.md` with:
- **Input:** WO file path, development plan path
- **Purpose:** Revalidate assumptions, check dependencies, analyze codebase, flag risks

**On result:**
- If recommendation is BLOCK (critical issues): pause, report to user, ask how to proceed
- If recommendation is PROCEED WITH CAUTION: log risks, continue
- If recommendation is PROCEED: continue

Log the dispatch to `.vibeos/build-log.md`:
```
[timestamp] investigator WO-NNN investigate [PROCEED|CAUTION|BLOCK]
```

### Step 5: Dispatch Tester Agent (TDD)

Set agent identity: `echo "tester" > .vibeos/current-agent.txt`

Dispatch `agents/tester.md` with:
- **Input:** WO file path, project language/framework info
- **Purpose:** Write tests from spec BEFORE implementation exists

**On result:**
- Verify test files were created
- Verify tests fail (correct TDD behavior — no implementation yet)
- If tests somehow pass: investigate (might indicate the feature already exists)

Log: `[timestamp] tester WO-NNN write-tests [count] tests written, all failing`

### Step 6: Dispatch Implementation Agent

Determine which agent to use:
- Read WO scope to determine if it's backend, frontend, or both
- If backend: dispatch `agents/backend.md`
- If frontend: dispatch `agents/frontend.md`
- If both: dispatch backend first, then frontend

Set agent identity before each: `echo "backend" > .vibeos/current-agent.txt`

Dispatch with:
- **Input:** WO file path, test file paths, investigation report
- **Purpose:** Implement code to make tests pass

**On result:**
- Check test results — all tests should pass
- Check self-check results — no stubs, no secrets, types present
- If tests still failing: retry once with specific failure details
- If retry fails: escalate to user

Log: `[timestamp] backend WO-NNN implement [PASS|FAIL] [test count] tests`

### Step 7: Run Quality Gates

Run pre_commit gates:
```bash
bash scripts/gate-runner.sh pre_commit --project-dir "${CLAUDE_PROJECT_DIR:-.}"
```

**Baseline-aware gate evaluation:**

After running gates, check each failure against known baselines:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" check \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --category "[gate-name]" --current-count [failure-count]
```

- **PASS:** No failures — proceed
- **TRACKED:** Failures within baseline (pre-existing) — log as tracked, proceed
- **FAIL:** Failures exceed baseline (new issues) — trigger fix cycle

**Gate fix loop (max 3 cycles):**
1. Parse gate results for new failures (exceeding baseline)
2. If all pass or tracked: proceed to Step 8
3. If new failures: re-dispatch implementation agent with specific failure details
4. Re-run gates
5. Repeat until pass or 3 cycles exhausted

After successful gate pass with fewer failures than baseline, ratchet:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" ratchet \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --category "[gate-name]" --current-count [failure-count]
```

**On 3 failed cycles:** Escalate to user:
> "Quality gates are still failing after 3 fix attempts. Here's what's failing: [details]. Would you like me to: (a) try again with a different approach, (b) skip these gates for now, or (c) let you fix it manually?"

Log each gate run: `[timestamp] gate-runner WO-NNN pre_commit [PASS|FAIL] [details]`

### Step 8: Run Audit Cycle (Layer 2)

After gates pass, run the full audit cycle for deeper quality enforcement.

Dispatch the audit skill logic (do NOT invoke `/vibeos:audit` as a skill — instead, dispatch the audit agents directly following the same pattern as `skills/audit/SKILL.md`):

1. Dispatch all 5 audit agents in parallel where possible:
   - `agents/security-auditor.md`
   - `agents/architecture-auditor.md`
   - `agents/correctness-auditor.md`
   - `agents/test-auditor.md`
   - `agents/evidence-auditor.md`

2. Collect findings and apply consensus logic (see `skills/audit/SKILL.md` Step 4)

3. Filter by severity:
   - **Critical or High findings:** trigger audit-fix cycle
   - **Medium or Low findings:** log as warnings in build log, do not block

**Audit-fix cycle with convergence control:**

Before starting the fix cycle, capture the initial state hash:
```bash
PREV_HASH=$(bash "${CLAUDE_PLUGIN_ROOT}/convergence/state-hash.sh" --project-dir "${CLAUDE_PROJECT_DIR:-.}")
```

For each fix cycle iteration:
1. Extract critical/high findings with file paths and recommendations
2. Re-dispatch the appropriate implementation agent (`backend` or `frontend`) with:
   - The specific findings to fix
   - The file paths and line numbers
   - The recommended fixes from the auditors
3. Capture new state hash after fixes:
   ```bash
   CURR_HASH=$(bash "${CLAUDE_PLUGIN_ROOT}/convergence/state-hash.sh" --project-dir "${CLAUDE_PROJECT_DIR:-.}")
   ```
4. Run convergence check:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/convergence/convergence-check.sh" \
     --current-hash "$CURR_HASH" --previous-hash "$PREV_HASH" \
     --iteration $N --max-iterations 5 \
     --critical-count $CRITICAL --high-count $HIGH \
     --previous-critical $PREV_CRITICAL --previous-high $PREV_HIGH \
     --tests-pass "$TESTS_PASS"
   ```
5. Act on convergence decision:
   - **CONVERGED:** proceed to Step 9
   - **CONTINUE:** re-run audit agents, loop back to step 1
   - **STUCK or MAX_ITER:** escalate to user
6. Update `PREV_HASH=$CURR_HASH` and store previous finding counts

**Escalation format (STUCK or MAX_ITER):**
> "Audit findings remain after [N] fix attempts ([reason from convergence check]).
> Unresolved findings:
> [list of findings with severity, file, description]
>
> These were flagged by: [auditor names]
> Fix attempts: [what was tried]
>
> Would you like to: (a) try a different approach, (b) accept the remaining findings, or (c) fix manually?"

Log each audit run:
```
[timestamp] audit WO-NNN layer2-audit cycle-[N] [PASS|FINDINGS] critical:[N] high:[N] medium:[N] low:[N]
```

Save the audit report to `.vibeos/audit-reports/WO-NNN-[timestamp].md`.

### Step 9: Dispatch Doc Writer Agent

Set agent identity: `echo "doc-writer" > .vibeos/current-agent.txt`

Dispatch `agents/doc-writer.md` with:
- **Input:** WO file path, implementation report, test report
- **Purpose:** Update documentation, WO file, and tracking docs

**On result:**
- Verify WO file was updated with implementation notes
- Verify WO-INDEX.md was updated

Log: `[timestamp] doc-writer WO-NNN document [COMPLETE]`

### Step 10: WO Completion

After all agents succeed:
1. Mark WO status as `Complete` in WO file (if doc-writer didn't already)
2. Update WO-INDEX.md: move WO to Complete, add completion date
3. Update DEVELOPMENT-PLAN.md: set WO status to Complete
4. Clean up `.vibeos/current-agent.txt`
5. Check token overhead:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/convergence/token-tracker.sh" overhead
   ```

Report to user:
> "WO-NNN ([title]) is complete.
> - [N] tests written and passing
> - [M] quality gates passed
> - [L] audit findings resolved
> - [K] files created/modified
> - Documentation updated
>
> Next: WO-NNN+1 ([next title]) is ready."

### Step 11: Multi-WO Orchestration & Autonomy Check

After WO completion, determine whether to continue with the next WO.

**11a. Read autonomy config** from `.vibeos/config.json` (default: "wo").

**11b. Detect phase boundary:**
- Read the current WO's phase from DEVELOPMENT-PLAN.md
- Identify the next eligible WO (Step 1 logic)
- If the next WO is in a different phase: this is a phase boundary

**11c. Apply autonomy rules:**

**If level = "wo":** Stop. Report completion and wait for user to say "continue" or "proceed".

**If level = "phase":**
- If phase boundary reached: stop and report phase completion
- If more WOs in current phase: loop back to Step 1 for the next WO
- At phase boundary, report:
  > "Phase [N] ([name]) is complete.
  > - [X] WOs completed in this phase
  > - [Y] total tests passing
  > - [Z] audit findings resolved
  >
  > Next phase: Phase [N+1] ([name]) with [W] WOs."

**If level = "major":** Continue to next WO unless:
- Phase boundary reached (pause for phase transition report)
- A WO has BLOCK recommendation from investigator
- An escalation was triggered during the WO
- Architecture change is needed (flagged by architecture auditor)

**11d. Dependency check for next WO:**
Before looping back to Step 1:
1. Read DEVELOPMENT-PLAN.md for the next WO's dependencies
2. Verify all dependencies have status "Complete"
3. If dependencies unmet: skip to the next eligible WO in the same phase
4. If no eligible WOs remain in the phase: report phase complete, stop
5. If skipping: log which WO was skipped and why

**11e. Human check-in report:**

When pausing (any autonomy level), generate a check-in report:

> **Build Progress Check-in**
>
> **Completed this session:**
> - WO-NNN: [title] — [1-line summary of what was built]
> - [additional WOs if autonomy=phase or major]
>
> **Quality summary:**
> - Tests: [N] passing, [M] failing
> - Gates: [N]/[M] passing
> - Audit: [N] findings resolved, [M] warnings remaining
> - Token usage: [N] total ([X]% audit overhead)
>
> **Next up:** WO-NNN ([title])
> [1-sentence description of what this WO will build]
>
> **Your options:**
> 1. **Continue** — proceed with the next WO
> 2. **Adjust plan** — modify WO scope, reorder priorities, or add new WOs
> 3. **Change autonomy** — switch between wo/phase/major levels
> 4. **Redirect** — work on something different (creates new WO)
> 5. **Stop** — save progress and end the build session

**On user response:**
- **Continue:** loop back to Step 1 with next eligible WO
- **Adjust plan:** ask user for changes, update DEVELOPMENT-PLAN.md and WO-INDEX.md, then loop back to Step 1
- **Change autonomy:** present the 3 levels, save selection to `.vibeos/config.json`, then loop back to Step 1
- **Redirect:** create a new WO using the WO template from `reference/governance/WO-TEMPLATE.md.ref`, add to plan, then build it
- **Stop:** log session end to build-log.md, report final progress summary, exit

Log the check-in: `[timestamp] check-in WO-NNN [user-choice]`

**11f. Loop or stop:**
- If continuing: loop back to Step 1 with the next eligible WO
- If stopping: report final progress summary and save build state

## Error Recovery

### Agent Timeout
If an agent doesn't complete within its maxTurns:
1. Log the timeout
2. Retry once with a simplified prompt
3. If retry fails: escalate to user

### Garbage Output
If an agent returns output that doesn't match the expected structure:
1. Log the raw output
2. Retry once with explicit output format reminder
3. If retry fails: escalate to user

### Escalation Format
When escalating to user, always explain:
- What step was being executed
- What went wrong (in plain English)
- What was tried to fix it
- What options the user has

## Build Log

All events are appended to `.vibeos/build-log.md`. Format:

```
# Build Log

## WO-NNN: [title]

| Timestamp | Agent | Action | Result |
|---|---|---|---|
| [ISO-8601] | [agent] | [action] | [result summary] |
```

The build log is append-only — never overwrite previous entries.

## Output Summary

| Artifact | Path | Purpose |
|---|---|---|
| Build log | .vibeos/build-log.md | Append-only execution history |
| Agent marker | .vibeos/current-agent.txt | Current agent identity for hooks |
| Test files | {test_dir}/ | TDD tests written by tester agent |
| Source files | {source_dirs}/ | Implementation by backend/frontend agents |
| Updated WO | docs/planning/ | Implementation notes and evidence |
