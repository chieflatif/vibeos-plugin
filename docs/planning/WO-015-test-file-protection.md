# WO-015: Test File Protection Hook

## Status

`Complete`

## Phase

Phase 3: Autonomous Build Loop

## Objective

Create a PreToolUse hook that prevents implementation agents from modifying test files, enforcing the TDD boundary where only the tester agent writes tests.

## Scope

### In Scope
- [x] Create PreToolUse hook matching Write|Edit tool calls
- [x] Check if target file path is in a test directory (tests/, test/, __tests__/, spec/)
- [x] Determine current agent identity (implementation vs. tester)
- [x] If implementation agent targets a test file: exit 2 (block the tool call)
- [x] If tester agent targets a test file: allow
- [x] Primary mechanism: hook input (tool call metadata)
- [x] Fallback mechanism: `.vibeos/current-agent.txt` marker file
- [x] Log all blocked attempts for audit trail

### Out of Scope
- Test quality enforcement (WO-037)
- Test diff auditing (WO-038)
- Full audit of test modifications (WO-026)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-014 | Must complete first | Draft |
| WO-006 | Hook infrastructure | Draft |

## Impact Analysis

- **Files created:** hooks/test-file-protection hook file
- **Systems affected:** PreToolUse hook chain, Write/Edit tool calls

## Acceptance Criteria

- [x] AC-1: Hook fires on every Write and Edit tool call
- [x] AC-2: Test directories correctly identified across languages (tests/, test/, __tests__/, spec/)
- [x] AC-3: Implementation agent blocked from writing to test files (exit 2)
- [x] AC-4: Tester agent allowed to write to test files
- [x] AC-5: Non-test files are never blocked by this hook
- [x] AC-6: Blocked attempts logged with agent identity and target file
- [x] AC-7: Fallback to .vibeos/current-agent.txt when hook input lacks agent identity

## Test Strategy

- **Unit:** Test path matching logic for test directories across languages
- **Integration:** Simulate Write call to test file from implementation agent, verify block
- **Integration:** Simulate Write call to test file from tester agent, verify allow
- **Fallback:** Test .vibeos/current-agent.txt marker file mechanism

## Implementation Plan

### Step 1: Create Hook File
- Hook type: PreToolUse
- Tool match: Write|Edit
- Extract target file path from tool call input

### Step 2: Implement Path Detection
- Regex/glob patterns for test directories: tests/, test/, __tests__/, spec/
- Also match files like *_test.go, *_test.py, *.test.js, *.spec.ts
- Language-agnostic pattern set

### Step 3: Implement Agent Identity Check
- Primary: read agent identity from hook input/context
- Fallback: read .vibeos/current-agent.txt
- If identity unknown: allow (fail open with warning logged)

### Step 4: Implement Block Logic
- If implementation agent + test file: exit 2 (block)
- Log: "[TEST-PROTECTION] BLOCKED: {agent} attempted to modify {file}"
- If tester agent + test file: exit 0 (allow)
- If any agent + non-test file: exit 0 (allow)

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration tests for block/allow scenarios
- Risk: If neither hook input nor marker file reliably identifies the agent, enforcement degrades to prompt-only. This is a known architectural risk.

## Evidence

- [x] Hook file created
- [x] Implementation agent blocked from test files
- [x] Tester agent allowed to write test files
- [x] Non-test files never blocked
- [x] Block attempts logged
- [x] Fallback mechanism tested
