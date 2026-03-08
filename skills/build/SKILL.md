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

## First-Run Onboarding

Check if this is the user's first time using VibeOS on this project (second entry point — users may invoke `/vibeos:build` directly):

1. Read `.vibeos/config.json` — if it does not exist or `onboarding_complete` is `false`, this is the first run
2. If first run, present the onboarding message:

> **Welcome to VibeOS**
>
> VibeOS turns Claude into an autonomous development engine. Here's how it works:
>
> 1. **You describe what you want to build** — I'll ask questions to understand your vision
> 2. **I create a development plan** — broken into phases and work orders (detailed task specs)
> 3. **I build autonomously** — writing tests first, then code, with quality checks at every step
> 4. **I check in with you** — at natural pause points so you can review, redirect, or continue
>
> **Your role:** You make the decisions — what to build, what quality level to target, when to ship. I handle the implementation, testing, and quality enforcement.
>
> **What to expect:** You'll see progress updates as each piece is built. I'll explain what I'm doing in plain English. When I need your input, I'll present clear options with their implications.

3. Create `.vibeos/config.json` (or update it) with `"onboarding_complete": true`

## Prerequisites

Before starting, verify these exist:
- `docs/planning/DEVELOPMENT-PLAN.md`
- `docs/planning/WO-INDEX.md`
- `project-definition.json`
- **Git repository:** Run `git rev-parse --is-inside-work-tree`. If not a git repo, warn: "This directory is not a git repository. State tracking, baselines, and convergence features won't work correctly. Initialize git with `git init` before building." Build can proceed but with degraded convergence.

If planning files are missing, tell the user to run `/vibeos:plan` first.

## WO Checkpoint & Resume

The build loop saves progress after each agent completes. If interrupted (context window reset, user pause, crash), the build resumes from where it left off.

**Checkpoint file:** `.vibeos/checkpoints/WO-NNN.json`

**Schema:**
```json
{
  "wo": "WO-NNN",
  "started_at": "ISO-8601",
  "last_updated": "ISO-8601",
  "current_step": 5,
  "total_steps": 8,
  "completed_agents": [
    {"agent": "investigator", "step": 4, "result": "PROCEED", "completed_at": "ISO-8601"},
    {"agent": "tester", "step": 5, "result": "tests-written", "completed_at": "ISO-8601"}
  ],
  "gate_attempts": 0,
  "audit_iterations": 0,
  "state_hash": "sha256"
}
```

**On WO start (Step 1):** Check for existing checkpoint:
1. Look for `.vibeos/checkpoints/WO-NNN.json`
2. If found: read checkpoint and announce resume:
   > "Resuming WO-NNN from step [N]/8. Already completed: [agent list]. Picking up at: [next step name]."
3. Skip to the next incomplete step
4. If not found: start fresh, create checkpoint directory: `mkdir -p .vibeos/checkpoints`

**After each agent completes (Steps 4-9):** Write/update checkpoint file with the completed agent and step number.

**On WO completion (Step 10):** Delete checkpoint file. If `.vibeos/checkpoints/` is empty, remove directory.

## Build Flow

### Step 1: Identify Next WO

If `$ARGUMENTS` contains a WO number, use that. Otherwise:

1. Read `docs/planning/DEVELOPMENT-PLAN.md`
2. Read `docs/planning/WO-INDEX.md`
3. **Phase 0 enforcement (midstream projects):** If Phase 0 exists (remediation phase) and has incomplete fix-now WOs, those must be built first. Do not proceed to Phase 1 until all Phase 0 fix-now WOs are complete. Tell the user:
   > "Phase 0 (remediation) has [N] incomplete fix-now items. These critical issues must be resolved before starting feature work. Building WO-NNN ([title]) next.
   >
   > Your options:
   > 1. **Build Phase 0 first** (recommended) — Fix the [N] critical issues before feature work. Your codebase starts clean and these issues won't compound as you add code.
   > 2. **Skip Phase 0 for now** — Start feature work immediately. The [N] issues remain unfixed: [top 2-3 finding summaries]. This will be logged as a risk acceptance. You can return to Phase 0 later.
   >
   > I recommend option 1 because [specific reasoning based on finding severity — e.g., 'the security findings could expose user data if exploited']."

   If user chooses to skip: log risk acceptance in `.vibeos/build-log.md` with timestamp and justification. Append to `docs/planning/ACCEPTED-RISKS.md` if it exists.
4. Find the current phase (first phase with incomplete WOs)
5. Within that phase, find the first WO whose:
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

**Progress banner:**
> "Starting WO-NNN: [title]. [1-sentence description of what this builds]."
> "[Step 1/8] Investigator — Reviewing requirements and checking dependencies before we start building..."

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

**Progress banner:**
> "[Step 2/8] Tester — Writing tests from your requirements. These tests define what 'working' means before any code is written."

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

**Progress banner:**
> "[Step 3/8] [Backend/Frontend] — Writing the code to make all tests pass..."

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

**Progress banner:**
> "[Step 4/8] Quality Gates — Running [N] automated quality checks..."

**On result:** Report inline: "Quality checks: [passed]/[total] passed. [top issue if any]."
**On retry:** "[issue description]. Fixing and re-checking (attempt [N] of 3)..."

Run pre_commit gates:
```bash
bash scripts/gate-runner.sh pre_commit --project-dir "${CLAUDE_PROJECT_DIR:-.}"
```

**Baseline-aware gate evaluation:**

After running gates, check each failure against known baselines.

**Auto-migration:** If `.vibeos/baselines/midstream-baseline.json` exists with version 1.0 (old count-based format), auto-migrate to finding-level format:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/migrate-baseline.sh" \
  --input ".vibeos/baselines/midstream-baseline.json" \
  --output ".vibeos/baselines/midstream-baseline.json"
```
Tell user: "I upgraded your quality baseline to the new finding-level format. This gives more precise tracking of individual issues."

**No baseline exists:** If `.vibeos/baselines/midstream-baseline.json` does not exist and `.vibeos/findings-registry.json` exists, create the baseline:
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" create \
  --mode finding-level \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --current-findings-file ".vibeos/findings-registry.json"
```
Tell user: "No quality baseline existed yet. I've created one from your audit findings — [N] existing issues are now tracked. Only new issues will block builds."

If neither baseline nor findings-registry exists (greenfield project), skip baseline checks entirely.

The system supports two modes:

**Finding-level mode (preferred, if `.vibeos/findings-registry.json` exists):**
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" check \
  --mode finding-level \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --current-findings-file ".vibeos/findings-registry.json"
```

This compares individual findings by fingerprint (SHA-256 of category:file:pattern:severity). New findings not in the baseline are flagged individually by ID and file, enabling precise tracking.

**Count-based mode (fallback, for projects without findings registry):**
```bash
bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" check \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --category "[gate-name]" --current-count [failure-count]
```

**Results:**
- **PASS:** No failures — proceed
- **TRACKED:** Failures within baseline (pre-existing) — log as tracked, proceed
- **FAIL:** Failures exceed baseline (new issues) — trigger fix cycle

**Gate fix loop (max 3 cycles):**
1. Parse gate results for new failures (exceeding baseline)
2. If all pass or tracked: proceed to Step 8
3. If new failures: **notify user before acting:**
   > "[Specific issue, e.g. 'Type annotations missing on 3 functions in src/api.py']. Fixing automatically and re-running quality checks (attempt [N] of 3)..."
4. Re-dispatch implementation agent with specific failure details
5. Re-run gates
6. Repeat until pass or 3 cycles exhausted

After successful gate pass with fewer failures than baseline, ratchet:
```bash
# Finding-level ratchet (removes fixed findings from baseline)
bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" ratchet \
  --mode finding-level \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --current-findings-file ".vibeos/findings-registry.json"

# Count-based ratchet (fallback)
bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" ratchet \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --category "[gate-name]" --current-count [failure-count]
```

**On 3 failed cycles:** Escalate to user with consequences:
> "Quality checks are still failing after 3 attempts. Here's what's failing: [specific issues].
>
> Your options:
> 1. **Try a different approach** — I'll rethink how to implement this and try again. This may resolve the issue but will use more time.
> 2. **Skip these checks for now** — Your code will be committed without passing [gate-name]. This means [specific risk, e.g., "type annotations won't be verified, which could let type-related bugs through"]. You can re-run these checks later with `/vibeos:gate`.
> 3. **Fix it yourself** — I'll show you exactly what's failing and where, so you can fix it directly. I'll re-run the checks when you're ready.
>
> I recommend option 1 because [reason based on which gates are failing and their severity]."

Log each gate run: `[timestamp] gate-runner WO-NNN pre_commit [PASS|FAIL] [details]`

### Step 8: Run Audit Cycle (Layer 2)

**Progress banner:**
> "[Step 5/8] Audit — Running 5 independent quality reviewers. This is the longest step and may take a minute..."

**On result:** "Audit complete: [confirmed] confirmed findings, [warnings] warnings. [critical summary if any]."
**On convergence retry:** "Fix applied. Re-running auditors to verify (iteration [N] of 5)..."

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
2. **Notify user before acting:**
   > "Audit found [N] issues to fix: [top finding summary]. Fixing automatically (iteration [N] of 5)..."
3. Re-dispatch the appropriate implementation agent (`backend` or `frontend`) with:
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
> "After [N] fix attempts, these issues remain:
> [list of findings with severity, file, description]
>
> These were flagged by: [auditor names]
> Fix attempts: [what was tried]
>
> Your options:
> 1. **Try a different approach** — I'll use a different strategy to fix these. May resolve them but no guarantee, and will use more time.
> 2. **Accept these findings** — These issues will be documented as known and tracked. [If security]: This means [specific security risk] remains in your code until fixed later. [If architecture]: This means [specific maintenance risk]. They won't block future work but will appear in phase audits.
> 3. **Fix yourself** — I'll give you the exact file locations and details. You fix them, I'll re-run the audit to verify.
>
> I recommend [X] because [specific reasoning based on finding severity and project context]."

Log each audit run:
```
[timestamp] audit WO-NNN layer2-audit cycle-[N] [PASS|FINDINGS] critical:[N] high:[N] medium:[N] low:[N]
```

Save the audit report to `.vibeos/audit-reports/WO-NNN-[timestamp].md`.

### Step 9: Dispatch Doc Writer Agent

**Progress banner:**
> "[Step 6/8] Documentation — Updating project docs and work order tracking..."

Set agent identity: `echo "doc-writer" > .vibeos/current-agent.txt`

Dispatch `agents/doc-writer.md` with:
- **Input:** WO file path, implementation report, test report
- **Purpose:** Update documentation, WO file, and tracking docs

**On result:**
- Verify WO file was updated with implementation notes
- Verify WO-INDEX.md was updated

Log: `[timestamp] doc-writer WO-NNN document [COMPLETE]`

### Step 10: WO Completion

**Progress banner:**
> "[Step 7/8] Completing WO — Updating tracking documents..."

After all agents succeed:
1. Mark WO status as `Complete` in WO file (if doc-writer didn't already)
2. Update WO-INDEX.md: move WO to Complete, add completion date
3. Update DEVELOPMENT-PLAN.md: set WO status to Complete
4. Clean up `.vibeos/current-agent.txt`
5. Delete checkpoint file: remove `.vibeos/checkpoints/WO-NNN.json` (if `.vibeos/checkpoints/` is empty, remove directory)
6. **Remediation aging check** (if `.vibeos/findings-registry.json` exists):
   - Read fix-later items from findings-registry.json
   - For each, check the `baselined_at_wo` field (set by WO-043 when the finding was baselined)
   - Read aging threshold from `.vibeos/config.json` `remediation_aging_threshold` (default: 5 WOs)
   - Count WOs completed since the finding was baselined
   - If any fix-later item exceeds the threshold, remind the user:
     > "Reminder: [N] fix-later remediation items have been deferred for [M] work orders. Consider scheduling them soon:
     > - [finding title] (deferred since WO-NNN)
     > - [finding title] (deferred since WO-NNN)
     > Run `/vibeos:status` to see the full list."

Report to user:
> "WO-NNN ([title]) is complete.
> - [N] tests written and passing
> - [M] quality gates passed
> - [L] audit findings resolved
> - [K] files created/modified
> - TDD enforcement: [B] test file modification attempts blocked
> - Documentation updated
> - This work order dispatched [N] agents across [M] iterations ([X] gate retries, [Y] audit convergence cycles)
>
> Phase [P]: [completed]/[total] work orders complete.
> Next: WO-NNN+1 ([next title]) is ready."

**TDD metric source:** Count lines matching `test-file-protection | BLOCKED` in `.vibeos/build-log.md` since this WO started (compare timestamps against checkpoint `started_at`).

### Step 11: Multi-WO Orchestration & Autonomy Check

**Progress banner:**
> "[Step 8/8] Check-in — Here's what was built: [summary]"

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
2. **Notify user before retrying:**
   > "The [agent-name] agent didn't complete in time. Retrying with a simplified prompt to help it focus on the essentials..."
3. Retry once with a simplified prompt
4. If retry fails: escalate to user

### Garbage Output
If an agent returns output that doesn't match the expected structure:
1. Log the raw output
2. **Notify user before retrying:**
   > "The [agent-name] agent returned unexpected output. Retrying with explicit format requirements..."
3. Retry once with explicit output format reminder
4. If retry fails: escalate to user

### Escalation Format
When escalating to user, always explain:
- What step was being executed
- What went wrong (in plain English)
- What was tried to fix it
- What options the user has (with consequences per Communication Contract)

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
| Checkpoint | .vibeos/checkpoints/WO-NNN.json | Resume state (deleted after WO completes) |
| Agent marker | .vibeos/current-agent.txt | Current agent identity for hooks |
| Test files | {test_dir}/ | TDD tests written by tester agent |
| Source files | {source_dirs}/ | Implementation by backend/frontend agents |
| Updated WO | docs/planning/ | Implementation notes and evidence |
