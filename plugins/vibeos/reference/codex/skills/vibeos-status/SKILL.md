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
   - `.vibeos/config.json`
   - `docs/planning/WO-INDEX.md`
   - active WO files when present
2. Summarize:
   - current focus
   - what was completed in this session
   - what is still in motion
   - blockers, failed checks, or pending decisions
   - whether the session is standard or autonomous override
3. Keep the update tactical. If the user wants the big-picture program view, hand off to `vibeos-project-status`.

## Rules

- Plain English first.
- Tactical scope only.
- Treat partial states truthfully.
