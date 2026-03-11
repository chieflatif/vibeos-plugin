---
name: vibeos-autonomous
description: Full autonomous-session override for VibeOS in Codex. Use when the user says go autonomous, stop checking in, run on your own, stay in autonomous mode, or wants VibeOS to keep building until a real blocker or decision appears.
---

# VibeOS Autonomous

Use this skill to turn on a temporary full-autonomous session override.

## Workflow

1. Read or create `.vibeos/config.json`.
2. Preserve the negotiated autonomy level and set:
   - `autonomy.session_override.mode = "autonomous"`
   - `autonomy.session_override.active = true`
3. Read or create `.vibeos/session-state.json` and mark the session active in autonomous mode.
4. Append a mode-change entry to `.vibeos/build-log.md`.
5. Explain what changes:
   - routine check-ins stop
   - gates and audit rules still apply
   - the system will still pause for blockers, risk decisions, or plan boundaries
6. Continue immediately with `vibeos-build`.

## Rules

- Keep the override truthful and explicit in state files.
- When autonomous mode ends, clear the override and record the session handoff.
