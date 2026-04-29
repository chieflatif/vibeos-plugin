# WO-093: Long-Run Autonomy Control Plane

## Status

`Complete`

## Phase

Phase 21: Long-Run Autonomy

## Objective

Define 24-48 hour autonomy as a resumable operating protocol with heartbeat evidence, checkpoints, audit cadence, explicit stop conditions, and truthful handoff state.

## Scope

### In Scope
- [x] Add long-run autonomy reference protocol
- [x] Add machine-readable long-run autonomy policy
- [x] Update autonomous/build/status/checkpoint/session-audit skills to use heartbeat and cadence controls
- [x] Update session-state schema for long-run fields
- [x] Update Codex surface instructions so long-run claims remain truthful

### Out of Scope
- Claiming one model context can remain alive indefinitely
- Running production deployments without explicit user approval
- Adding external scheduler infrastructure

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-056 | Session State & Gate Manifest Infrastructure | Complete |
| WO-077 | Swarm Worktree Planner | Complete |
| WO-091 | Delivery Scorecard and Evidence Integration | Complete |

## Findings

1. Existing autonomous mode suppressed routine check-ins, but it did not define 24-48 hour run mechanics.
2. Existing checkpoints covered mid-WO resume, but not heartbeat freshness, audit cadence, or long-run closeout.
3. A credible long-run harness needs durable state that survives context resets, runtime interruptions, and handoff between Codex and Claude/Cursor.

## Acceptance Criteria

- [x] AC-1: Long-run autonomy protocol exists as a reference file
- [x] AC-2: Policy defines duration, heartbeat, checkpoint, audit, and stop-condition rules
- [x] AC-3: Skills describe heartbeat and checkpoint cadence for 24-48 hour runs
- [x] AC-4: Session-state schema includes long-run fields
- [x] AC-5: Codex instructions avoid claiming uninterrupted runtime without durable resume state

## Evidence

- [x] `plugins/vibeos/reference/autonomy/LONG-RUN-AUTONOMY.md.ref`
- [x] `plugins/vibeos/reference/autonomy/long-run-autonomy-policy.json`
- [x] `plugins/vibeos/skills/autonomous/SKILL.md`
- [x] `plugins/vibeos/skills/build/SKILL.md`
- [x] `plugins/vibeos/reference/session-state-schema.md`
