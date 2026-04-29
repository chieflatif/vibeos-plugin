---
name: vibeos-status
description: Tactical VibeOS session status for Codex. Use when the user asks what's the status, what's in flight, where are we in this session, or wants a near-term update on current work rather than a strategic project briefing.
---

# VibeOS Status

Use this skill for tactical, session-level status.

## Workflow

1. Read:
   - `.vibeos/session-state.json`
   - `.vibeos/build-log.md`
   - `.vibeos/checkpoints/*.json`
   - `.vibeos/autonomy/heartbeats/*.json`
   - `.vibeos/autonomy/run-lease.json`
   - `.vibeos/autonomy/last-lease.json`
   - `.vibeos/autonomy/lease-conflict.json`
   - `.vibeos/autonomy/loop-state.json`
   - `.vibeos/autonomy/loop-history.jsonl`
   - `.vibeos/autonomy/resume-plan.json`
   - `.vibeos/autonomy/runner-report.json`
   - `.vibeos/autonomy/runtime-adapter-plan.json`
   - `.vibeos/autonomy/runtime-adapter-history.jsonl`
   - `.vibeos/autonomy/failure-report.json`
   - `.vibeos/autonomy/recovery-plan.json`
   - `.vibeos/autonomy/recovery-resolution.json`
   - `.vibeos/autonomy/recovery-resolution-history.jsonl`
   - `.vibeos/autonomy/scheduler-guard-report.json`
   - `.vibeos/autonomy/scheduler-profile.json`
   - `.vibeos/autonomy/smoke-report.json`
   - `.vibeos/config.json`
   - `docs/planning/WO-INDEX.md`
   - active WO files when present
2. Summarize:
   - current focus
   - what was completed in this session
   - what is still in motion
   - blockers, failed checks, or pending decisions
   - whether the session is standard or autonomous override
   - whether long-run autonomy is active, fresh, stale, paused, blocked, or complete
   - whether an active run lease or recent lease conflict exists
   - latest heartbeat run id, iteration, timestamp, and next action when available
   - latest loop tick status when available
   - latest resume-plan action and whether the runner blocked, executed, or handed off commands
   - latest runtime adapter provider and whether it planned or launched a handoff
   - latest failure detector status and any repeated handoff, runner, runtime, lease, or provider/session findings
   - latest recovery planner status and whether scheduling must pause before another tick
   - latest recovery resolution status and unresolved action count when present
   - latest scheduler guard status and whether it blocks another tick
   - latest scheduler profile and smoke-test status when present
3. Keep the update tactical. If the user wants the big-picture program view, hand off to `vibeos-project-status`.

## Rules

- Plain English first.
- Tactical scope only.
- Treat partial states truthfully.
