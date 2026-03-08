# WO-010: Plan Auditor Agent

## Status

`Complete`

## Phase

Phase 2: Product Discovery & Planning

## Objective

Create a plan auditor agent that runs the WO-AUDIT-FRAMEWORK.md 10-question checklist at the Planning checkpoint, returning structured findings with severity ratings.

## Scope

### In Scope
- [x] Create `agents/plan-auditor.md` with isolation and tool restrictions
- [x] Agent config: isolation: worktree, disallowedTools: Write, Edit, Agent, model: opus
- [x] Implement all 10 questions from WO-AUDIT-FRAMEWORK.md Planning checkpoint
- [x] Return structured findings: question, pass/fail, severity, evidence, recommendation
- [x] Severity levels: critical, major, minor, info
- [x] Agent cannot modify any files (read-only audit)

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

- [x] AC-1: Agent runs in isolated worktree (cannot affect main working tree)
- [x] AC-2: Agent cannot use Write, Edit, or Agent tools
- [x] AC-3: All 10 Planning checkpoint questions evaluated
- [x] AC-4: Each finding includes: question ID, pass/fail, severity, evidence quote, recommendation
- [x] AC-5: Structured JSON-compatible output returned to caller
- [x] AC-6: Agent uses opus model for deep reasoning
- [x] AC-7: Agent completes within maxTurns limit

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

- [x] Agent file created with correct frontmatter
- [x] Dispatch succeeds in isolated worktree
- [x] All 10 questions evaluated
- [x] Structured findings returned
- [x] Tool restrictions enforced (no Write/Edit/Agent)
