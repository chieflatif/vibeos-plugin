---
wo: WO-116
title: PostToolUse + SubagentStop + SessionEnd/PreCompact Hooks
status: Complete
phase: 37
phase_name: Hook Lifecycle Modernization
wo_class: harness
write_scope:
  - docs/planning/WO-116-hook-lifecycle-modernization.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/hooks/hooks.json
  - plugins/vibeos/hook-manifest.json
  - plugins/vibeos/hooks/scripts/gate-result-capture.sh
  - plugins/vibeos/hooks/scripts/validate-agent-return.sh
  - plugins/vibeos/hooks/scripts/state-flush.sh
  - tests/test_hook_lifecycle.py
  - tests/test_status_reconciliation.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-116: PostToolUse + SubagentStop + SessionEnd/PreCompact Hooks

## Status

`Complete`

## Phase

Phase 37: Hook Lifecycle Modernization

## Objective

Add current Claude Code lifecycle hooks that capture gate outcomes after Bash runs, validate subagent return packets, and flush durable session state before session end or compaction.

## Scope

### In Scope
- [x] Add `PostToolUse` Bash hook `gate-result-capture.sh`
- [x] Add `SubagentStop` hook `validate-agent-return.sh`
- [x] Add `SessionEnd` and `PreCompact` hook `state-flush.sh`
- [x] Document the new hooks in `hook-manifest.json`
- [x] Add synthetic JSON-stdin fire tests for each hook

### Out of Scope
- Codex hook parity claims
- Prompt, HTTP, MCP, or experimental agent hook handlers
- Agent-team governance hooks (`TaskCreated`, `TaskCompleted`, `TeammateIdle`) reserved for WO-117
- ConfigChange model downgrade guard reserved for WO-119

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 34 | Gate floor | Complete |

## Acceptance Criteria

- [x] AC-1: `hooks.json` registers the four lifecycle hook events with command handlers
- [x] AC-2: `gate-result-capture.sh` records gate/test Bash outcomes without claiming to block completed tool effects
- [x] AC-3: `validate-agent-return.sh` allows PASS audit packets and blocks FAIL or critical/high audit packets
- [x] AC-4: `state-flush.sh` records durable flush evidence for `SessionEnd` and `PreCompact`
- [x] AC-5: `hook-manifest.json` documents every configured command hook and sync tests pass

## Test Strategy

- **Synthetic hook tests:** `python3 -m pytest tests/test_hook_lifecycle.py`
- **Manifest sync:** `python3 -m pytest tests/test_status_reconciliation.py`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Current Claude Code hook docs support the targeted lifecycle events. `PostToolUse` is capture-only here because completed tool effects cannot be prevented retroactively.
- Test status: Pending at implementation start.

### Pre-Implementation Audit
- Status: `complete`
- Findings: All new hooks are command handlers with synthetic stdin fixtures. This avoids prompt/http/mcp/agent handler expansion and keeps Codex parity out of scope.
- Test status: Pending at implementation start.

### Pre-Commit Audit
- Status: `complete`
- Findings: Hook lifecycle modernization is limited to Claude command hooks. `PostToolUse` is capture-only and does not claim to prevent completed tool effects. Manifest sync now validates event/script pairs, including duplicate script registration for different lifecycle events.
- Test status: Focused hook lifecycle tests passed; manifest sync tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
jq . plugins/vibeos/hooks/hooks.json >/dev/null
jq . plugins/vibeos/hook-manifest.json >/dev/null

python3 -m pytest tests/test_hook_lifecycle.py tests/test_status_reconciliation.py
# 10 passed in 0.39s

python3 -m pytest tests
# 168 passed in 34.74s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
