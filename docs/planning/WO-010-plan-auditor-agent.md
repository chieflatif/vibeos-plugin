# WO-010: Plan Auditor Agent

## Status

`Draft`

## Phase

Phase 2: Product Discovery & Planning

## Objective

Create a plan auditor agent that runs the WO-AUDIT-FRAMEWORK.md 10-question checklist at the Planning checkpoint, returning structured findings with severity ratings.

## Scope

### In Scope
- [ ] Create `agents/plan-auditor.md` with isolation and tool restrictions
- [ ] Agent config: isolation: worktree, disallowedTools: Write, Edit, Agent, model: opus
- [ ] Implement all 10 questions from WO-AUDIT-FRAMEWORK.md Planning checkpoint
- [ ] Return structured findings: question, pass/fail, severity, evidence, recommendation
- [ ] Severity levels: critical, major, minor, info
- [ ] Agent cannot modify any files (read-only audit)

### Out of Scope
- Security auditor (WO-023)
- Architecture auditor (WO-024)
- Full audit cycle (WO-028)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-007 | Must complete first | Draft |
| WO-AUDIT-FRAMEWORK.md | Must exist | Created |

## Impact Analysis

- **Files created:** agents/plan-auditor.md
- **Systems affected:** Audit infrastructure, agent dispatch

## Acceptance Criteria

- [ ] AC-1: Agent runs in isolated worktree (cannot affect main working tree)
- [ ] AC-2: Agent cannot use Write, Edit, or Agent tools
- [ ] AC-3: All 10 Planning checkpoint questions evaluated
- [ ] AC-4: Each finding includes: question ID, pass/fail, severity, evidence quote, recommendation
- [ ] AC-5: Structured JSON-compatible output returned to caller
- [ ] AC-6: Agent uses opus model for deep reasoning
- [ ] AC-7: Agent completes within maxTurns limit

## Test Strategy

- **Integration:** Dispatch plan auditor against a sample WO, verify structured findings returned
- **Isolation:** Verify agent cannot write files (tool restriction enforced)
- **Coverage:** Verify all 10 questions are addressed in output

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (opus), isolation (worktree), disallowedTools (Write, Edit, Agent), maxTurns
- Instructions: read WO file, read DEVELOPMENT-PLAN.md, evaluate 10-question checklist
- Output format: structured findings array

### Step 2: Implement Checklist Evaluation
- Each of 10 questions maps to specific file reads and checks
- Evidence gathered from actual file contents, not assumptions
- Severity assigned based on impact (critical = blocks implementation, major = causes rework)

### Step 3: Test Dispatch and Verification
- Dispatch against a known-good WO — expect mostly passing
- Dispatch against a deliberately flawed WO — expect failures detected
- Verify output structure is parseable

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch and verify structured findings
- Risk: Opus model cost per audit run; must be justified by audit quality

## Evidence

- [ ] Agent file created with correct frontmatter
- [ ] Dispatch succeeds in isolated worktree
- [ ] All 10 questions evaluated
- [ ] Structured findings returned
- [ ] Tool restrictions enforced (no Write/Edit/Agent)
