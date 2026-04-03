# WO-064: Build/Audit Skill Enhancements

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Integrate all Phase 11 infrastructure into the build and audit skills: audit visibility mode selection, same-tree agent dispatch, audit report registration, Codex complementary audit triggers, partial WO states, and enhanced prereq check with rich session context.

## Context

This is the integration WO — all the pieces built in WO-056 through WO-063 need to be wired into the build orchestrator and audit skill to actually function. Joan's build and audit skills evolved significantly beyond the VibeOS baseline to incorporate:
1. Audit visibility mode selection before agent dispatch
2. Same-tree vs worktree agent dispatch based on visibility mode
3. Audit report registration after audit completion
4. Independent audit validation before WO closure
5. Partial WO states (6 truthful states beyond Complete/Incomplete)
6. Enhanced prereq check with recovery hints and lifecycle detection

## Joan Sources

- `/Users/latifhorst/Joan/.claude/skills/build/SKILL.md` (795 lines)
- `/Users/latifhorst/Joan/.claude/skills/audit/SKILL.md` (229 lines)
- `/Users/latifhorst/Joan/.claude/hooks/prereq-check.sh`

## Scope

### In Scope

1. **Build skill enhancements** (`skills/build/SKILL.md`):
   - Call `activate-session.sh` at WO entry
   - Call `select-audit-visibility-mode.sh` before audit dispatch
   - Dispatch same-tree agents when `audit_dispatch_profile: same-tree`
   - Dispatch worktree agents when `audit_dispatch_profile: worktree`
   - Call `register-audit-report.sh` after audit completion
   - Call `validate-independent-audit.sh` before WO closure
   - Support 6 partial WO states:
     - `Implemented Locally` — code exists but real path not proven
     - `Awaiting Gate Cleanup` — behavior exists but gates fail
     - `Awaiting Real-Path Verification` — tests pass but entrypoint not exercised
     - `Dev-Mode Complete` — works in dev path, not production-like
     - `Awaiting Checkpoint` — WO done but checkpoint closure pending
     - `Awaiting Evidence` — behavior done but artifacts incomplete

2. **Audit skill enhancements** (`skills/audit/SKILL.md`):
   - Call `select-audit-visibility-mode.sh` before dispatch
   - Dispatch same-tree agents when appropriate
   - Include visibility metadata in output headers
   - Register audit reports after completion
   - Expanded auditor list (add contract-validator + plan-auditor)

3. **Enhanced prereq check** (`hooks/prereq-check.sh`):
   - Rich session context on startup
   - Recovery hint: "Resume {WO} at step {current}/{total}"
   - Lifecycle detection: virgin, discovered, planned, building, checkpoint, complete
   - Anchor checks: PRODUCT-ANCHOR.md, ENGINEERING-PRINCIPLES.md, RESEARCH-REGISTRY.md
   - Plan/index mismatch reporting

4. **Agent identity tracking** — Build skill writes `.vibeos/current-agent.txt` when dispatching agents:
   - Contains agent name (e.g., "backend", "tester", "security-auditor")
   - Cleared after agent returns
   - Used by proof-protection hook (WO-060) to allow/deny test modifications

### Out of Scope

- Joan-specific auditor preferences (evidence-auditor-joan, plan-auditor-joan)
- NWO session tracking (generalized to standard WO sessions)
- Joan canon index authority (uses standard DEVELOPMENT-PLAN.md)

## Acceptance Criteria

1. Build skill calls session activation, visibility selection, report registration, and audit validation
2. Build skill correctly dispatches same-tree vs worktree agents
3. Build skill supports all 6 partial WO states
4. Audit skill selects visibility mode and dispatches appropriate agent variants
5. Audit skill includes visibility metadata in output
6. Prereq check provides recovery hints and lifecycle detection
7. Build skill writes/clears `.vibeos/current-agent.txt` during agent dispatch
8. All scripts pass `bash -n` syntax validation
9. All scripts have `FRAMEWORK_VERSION="2.1.0"`

## Dependencies

- WO-057 — same-tree agents
- WO-058 — audit visibility and registration
- WO-062 — Codex audit integration

## Files Modified

- `plugins/vibeos/skills/build/SKILL.md`
- `plugins/vibeos/skills/audit/SKILL.md`
- `plugins/vibeos/hooks/scripts/prereq-check.sh`

## Files Created

None — all modifications to existing files.
