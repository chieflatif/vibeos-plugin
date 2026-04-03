# WO-056: Session State & Gate Manifest Infrastructure

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Create the session state tracking system and declarative gate manifest that all subsequent Phase 11 WOs depend on. Session state enables context-aware hooks and gates (audit visibility, active WO tracking, mode selection). The gate manifest replaces implicit gate configuration with explicit, declarative JSON.

## Context

Joan evolved two infrastructure patterns that enable its advanced governance:
1. **Session state** (`.vibeos/session-state.json`) — tracks active WO, audit mode, session identity, autonomous mode state. Hooks and gates read this to make context-aware decisions.
2. **Quality gate manifest** (`.claude/quality-gate-manifest.json`) — declarative JSON specifying per-gate: script path, tier, blocking status, phase, environment variables, conditions. Replaces implicit knowledge about which gates run when.

Both are foundational — other WOs (same-tree auditing, audit visibility, scope guards) depend on session state existing.

## Joan Sources

- `/Users/latifhorst/Joan/.vibeos/session-state.json` (runtime schema)
- `/Users/latifhorst/Joan/.vibeos/scripts/activate-new-line-session.sh` (session activation)
- `/Users/latifhorst/Joan/.claude/quality-gate-manifest.json` (gate manifest)
- `/Users/latifhorst/Joan/.vibeos/config.json` (autonomy negotiation state)

## Scope

### In Scope

1. **Session state schema** — Define `.vibeos/session-state.json` schema:
   - `session_id` — unique session identifier
   - `started_at` — ISO timestamp
   - `active_wo` — current WO file path
   - `mode` — autonomous | supervised
   - `audit_visibility_mode` — same-tree | snapshot | committed-tree
   - `audit_dispatch_profile` — same-tree | worktree
   - `audit_snapshot_ref` — git ref for snapshot mode

2. **Session activation script** — `scripts/activate-session.sh`:
   - Creates or updates session-state.json
   - Sets session ID, timestamp, active WO, mode
   - Generalized from Joan's `activate-new-line-session.sh` (no NWO/kernel references)

3. **Quality gate manifest** — `quality-gate-manifest.json`:
   - One entry per gate script with: script, tier, blocking, phase, env, condition
   - All existing 42 gates documented
   - New gates from Phase 11 added as they're created

4. **Hook manifest** — `hook-manifest.json`:
   - Documents all hooks with: name, event_type, script, config, timeout
   - Descriptive (not executable — hooks.json/settings.json remain authoritative)

### Out of Scope

- Joan-specific fields (started_from_nwo, kernel references)
- Autonomy negotiation changes (existing system in WO-011 is sufficient)
- Gate runner modifications (reads manifest but doesn't change execution)

## Acceptance Criteria

1. `.vibeos/session-state.json` schema documented with all fields and valid values
2. `scripts/activate-session.sh` creates valid session state, is idempotent
3. `quality-gate-manifest.json` covers all existing gates with correct tier/phase/blocking assignments
4. `hook-manifest.json` documents all existing hooks
5. Both manifests validate with `jq . file.json > /dev/null`
6. Build skill calls `activate-session.sh` at WO entry
7. All scripts have `FRAMEWORK_VERSION="2.1.0"`

## Dependencies

- Phase 10 (WO-055) — project-level bootstrap structure must exist

## Files Created/Modified

### Created
- `plugins/vibeos/scripts/activate-session.sh`
- `plugins/vibeos/reference/session-state-schema.md`
- `plugins/vibeos/quality-gate-manifest.json`
- `plugins/vibeos/hook-manifest.json`

### Modified
- `plugins/vibeos/skills/build/SKILL.md` — call activate-session.sh at WO entry
