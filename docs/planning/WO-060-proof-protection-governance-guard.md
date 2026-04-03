# WO-060: Proof Protection & Governance Guard Hooks

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Add two enforcement hooks: proof protection (blocks implementation agents from weakening test assertions and evidence) and governance guard (blocks user prompts that attempt to skip gates, bypass checks, or ignore audits).

## Context

Joan identified two attack vectors on build integrity:
1. **Proof weakening** — Implementation agents sometimes "fix" failing tests by removing assertions, deleting test files, or weakening expectations. The proof protection hook blocks this at the tool level.
2. **Governance bypass** — Users (or agents echoing user intent) sometimes try to skip gates or bypass audits. The governance guard blocks prompts containing dangerous patterns like "skip gate", "ignore test", "bypass check".

## Joan Sources

- `/Users/latifhorst/Joan/.claude/hooks/new-line-proof-protection.sh`
- Joan's governance-guard patterns from settings.json

## Scope

### In Scope

1. **`hooks/proof-protection.sh`** — PreToolUse hook for Write/Edit:
   - Generalized from Joan's `new-line-proof-protection.sh`
   - Blocks removal of assertion statements (assert, expect, should, must, verify, raise)
   - Protects test files from implementation agents
   - Protects evidence bundles (`docs/evidence/`)
   - Agent-aware: allows tester and test-auditor agents; blocks backend/frontend/doc-writer
   - Reads `.vibeos/current-agent.txt` for agent identification
   - Logs blocked attempts to `.vibeos/build-log.md`
   - Session-state aware: only active when a WO session is running

2. **`hooks/governance-guard.sh`** — UserPromptSubmit hook:
   - Blocks dangerous user prompt patterns:
     - `skip.*gate`, `ignore.*test`, `disable.*hook`
     - `bypass.*check`, `skip.*audit`, `no.*evidence`
     - `force.*deploy`, `skip.*review`
   - Returns blocking message explaining why the action is denied
   - Configurable via `BLOCKED_PATTERNS` env var

3. **Hook registration** — Add both to hooks.json/settings.json

### Out of Scope

- NWO-specific proof files (replay scenarios, kernel fixtures)
- Joan-specific governance patterns (Microsoft boundary, canon authority)

## Acceptance Criteria

1. `proof-protection.sh` blocks assertion removal in test files
2. `proof-protection.sh` allows tester/test-auditor agents to modify tests
3. `proof-protection.sh` blocks evidence bundle deletion
4. `governance-guard.sh` blocks all listed dangerous patterns
5. `governance-guard.sh` allows legitimate prompts through
6. Both hooks pass `bash -n` syntax validation
7. Both hooks registered in hooks.json
8. All scripts have `FRAMEWORK_VERSION="2.1.0"`

## Dependencies

- WO-056 — session state (proof-protection reads session state and current-agent.txt)

## Files Created

- `plugins/vibeos/hooks/scripts/proof-protection.sh`
- `plugins/vibeos/hooks/scripts/governance-guard.sh`

## Files Modified

- `plugins/vibeos/hooks/hooks.json` — register both hooks
