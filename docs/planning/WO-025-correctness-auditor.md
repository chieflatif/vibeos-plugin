# WO-025: Correctness Auditor Agent

## Status

`Draft`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Create a correctness auditor agent that checks for logic errors, missing error paths, incomplete implementations, and hardcoded values using the "would a user notice?" trace methodology.

## Scope

### In Scope
- [ ] Create `agents/correctness-auditor.md` with strict isolation
- [ ] Agent config: isolation: worktree, disallowedTools: Write, Edit, Agent, model: opus
- [ ] Logic error detection: off-by-one, wrong operator, incorrect condition
- [ ] Missing error paths: unhandled exceptions, missing null checks, no fallback
- [ ] Incomplete implementations: partial features, missing branches, dead code
- [ ] Hardcoded values: magic numbers, hardcoded URLs, environment-specific values
- [ ] "Would a user notice?" trace: for each finding, describe the user-visible impact
- [ ] Structured findings with severity and user impact description

### Out of Scope
- Security analysis (WO-023)
- Architecture analysis (WO-024)
- Test quality analysis (WO-026)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-023 | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/correctness-auditor.md
- **Systems affected:** Audit pipeline, correctness enforcement

## Acceptance Criteria

- [ ] AC-1: Agent runs in isolated worktree
- [ ] AC-2: Agent cannot use Write, Edit, or Agent tools
- [ ] AC-3: Logic errors identified with explanation of the bug
- [ ] AC-4: Missing error paths identified with failure scenario description
- [ ] AC-5: Each finding includes "would a user notice?" impact statement
- [ ] AC-6: Hardcoded values flagged with recommendation (config, env var, etc.)
- [ ] AC-7: Uses opus model for deep reasoning about correctness
- [ ] AC-8: Structured output with severity and user impact

## Test Strategy

- **Integration:** Dispatch against code with planted bugs, verify detection
- **User impact:** Verify each finding includes clear user-impact statement
- **False positives:** Verify acceptable false positive rate

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (opus), isolation (worktree), disallowedTools (Write, Edit, Agent), maxTurns
- Instructions: deep code review protocol focused on correctness

### Step 2: Implement Correctness Protocol
- Phase 1: Read each function, trace logic for off-by-one, wrong operators, edge cases
- Phase 2: For each public function, check: what happens on null input? empty input? max input?
- Phase 3: Check for incomplete switch/match statements, missing else branches
- Phase 4: Scan for magic numbers and hardcoded values
- Phase 5: For each finding, trace to user-visible impact

### Step 3: Implement User Impact Trace
- For each finding: "If this bug triggers, the user would see: [description]"
- Severity based on user impact: critical (data loss/corruption), high (feature broken), medium (degraded experience), low (cosmetic)

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch against code with planted bugs
- Risk: Opus model cost justified by need for deep reasoning; correctness requires careful analysis

## Evidence

- [ ] Agent file created with correct isolation config
- [ ] Planted bugs detected
- [ ] User impact statements present for each finding
- [ ] Structured findings returned
- [ ] Tool restrictions enforced
