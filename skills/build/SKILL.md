---
name: build
description: Autonomous build orchestrator that executes work orders end-to-end. Dispatches investigator, tester, implementation, and documentation agents in sequence with quality gate enforcement and error recovery.
argument-hint: "[optional: WO number to build, e.g. 'WO-001']"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:build — Autonomous Build Orchestrator

Execute work orders autonomously with TDD, layered agents, quality gates, and error recovery.

## Communication Contract

Throughout this entire flow:
- Report progress at each major step (agent dispatch, test results, gate results)
- Explain what happened and what's next after each agent completes
- On errors: explain what went wrong in plain English, what was tried, and what needs user input
- Never ask "what do you want to build?" — read the plan and execute

## Prerequisites

Before starting, verify these exist:
- `docs/planning/DEVELOPMENT-PLAN.md`
- `docs/planning/WO-INDEX.md`
- `project-definition.json`

If any are missing, tell the user to run `/vibeos:plan` first.

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

**Gate fix loop (max 3 cycles):**
1. Parse gate results for failures
2. If all pass: proceed to Step 8
3. If failures: re-dispatch implementation agent with specific failure details
4. Re-run gates
5. Repeat until pass or 3 cycles exhausted

**On 3 failed cycles:** Escalate to user:
> "Quality gates are still failing after 3 fix attempts. Here's what's failing: [details]. Would you like me to: (a) try again with a different approach, (b) skip these gates for now, or (c) let you fix it manually?"

Log each gate run: `[timestamp] gate-runner WO-NNN pre_commit [PASS|FAIL] [details]`

### Step 8: Dispatch Doc Writer Agent

Set agent identity: `echo "doc-writer" > .vibeos/current-agent.txt`

Dispatch `agents/doc-writer.md` with:
- **Input:** WO file path, implementation report, test report
- **Purpose:** Update documentation, WO file, and tracking docs

**On result:**
- Verify WO file was updated with implementation notes
- Verify WO-INDEX.md was updated

Log: `[timestamp] doc-writer WO-NNN document [COMPLETE]`

### Step 9: WO Completion

After all agents succeed:
1. Mark WO status as `Complete` in WO file (if doc-writer didn't already)
2. Verify WO-INDEX.md shows Complete
3. Verify DEVELOPMENT-PLAN.md shows Complete
4. Clean up `.vibeos/current-agent.txt`

Report to user:
> "WO-NNN ([title]) is complete.
> - [N] tests written and passing
> - [M] quality gates passed
> - [K] files created/modified
> - Documentation updated
>
> Next: WO-NNN+1 ([next title]) is ready."

### Step 10: Autonomy Check

Based on `.vibeos/config.json`:

**If level = "wo":** Stop. Report completion and wait for user to say "continue" or "proceed".

**If level = "phase":** Check if the current phase has more WOs:
- If yes: loop back to Step 1 for the next WO
- If no: report phase completion and stop

**If level = "major":** Continue to next WO unless a major decision is needed (architecture change, scope change, user input required).

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
