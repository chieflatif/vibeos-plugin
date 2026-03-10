---
name: autonomous
description: Force VibeOS back into full autonomous session mode. Use when the user says "go autonomous", "stop checking in", "run on your own", "stay in autonomous mode", or wants VibeOS to keep building until it hits a real blocker, finishes the plan, or needs an explicit risk decision.
argument-hint: "[optional: brief goal or scope reminder]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:autonomous — Full Autonomous Session Override

Turn on a temporary full-autonomous session override, record the session state, and continue building without routine check-ins.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Explain clearly that autonomous mode still obeys the Product Anchor, Engineering Principles, gates, and audit rules
- Do not stop for routine progress check-ins while the autonomous session override is active
- If the system pauses, explain that it is because a real blocker, explicit risk decision, or plan boundary required intervention

## Prerequisites

Before enabling autonomous mode, verify these exist:
- `project-definition.json`
- `docs/planning/DEVELOPMENT-PLAN.md`
- `docs/planning/WO-INDEX.md`

If planning files are missing, explain that VibeOS needs discovery and planning before it can run autonomously.

## Autonomous Flow

### Step 1: Read and Update Project Config

1. Read `.vibeos/config.json` if it exists.
2. Preserve the negotiated autonomy level if one already exists.
3. Update `.vibeos/config.json` so it includes:

```json
{
  "autonomy": {
    "level": "wo|phase|major",
    "negotiated_at": "ISO-8601 timestamp",
    "session_override": {
      "mode": "autonomous",
      "active": true,
      "set_at": "ISO-8601 timestamp",
      "set_by": "/vibeos:autonomous"
    }
  }
}
```

If the file does not exist, create `.vibeos/` and write a valid config file that includes the override.

### Step 2: Create or Refresh Session State

Create or update `.vibeos/session-state.json`.

Use this shape:

```json
{
  "session_id": "ISO timestamp or CLAUDE_SESSION_ID",
  "mode": "autonomous",
  "active": true,
  "started_at": "ISO-8601 timestamp",
  "last_updated": "ISO-8601 timestamp",
  "started_from_wo": "WO-NNN or unknown",
  "completed_wos": [],
  "phase_checkpoints": [],
  "last_audit_report": null,
  "last_audited_at": null
}
```

If a session file already exists:
- keep any existing `completed_wos` and `phase_checkpoints`
- set `active` back to `true`
- update `mode` to `autonomous`
- clear any stale `ended_at` or `paused_at` fields

### Step 3: Log the Mode Change

Ensure `.vibeos/build-log.md` exists, then append a log entry like:

```text
[timestamp] autonomy session autonomous [enabled] full autonomous session override requested
```

### Step 4: Explain What Happens Next

Tell the user, in plain English:
- VibeOS will keep building without routine check-ins
- quality gates, audit agents, anchor checks, and prompt-engineering rules still apply
- VibeOS will still pause for blockers, explicit risk decisions, or if the plan is complete

If `$ARGUMENTS` includes a scope reminder, include that reminder in the confirmation.

### Step 5: Continue Building Immediately

After updating config and session state:
1. Read `skills/build/SKILL.md`
2. Continue directly into the build flow
3. Treat the autonomous session override as active for the rest of the build session

While the override is active:
- do not stop for routine WO or phase check-ins
- at phase boundaries, run the checkpoint flow automatically before continuing
- only pause when a real blocker, escalation, explicit risk decision, or plan-completion condition requires it

### Step 6: Clearing the Override

When the user later says "stop autonomous mode", "change autonomy", or the autonomous session finishes:
- set `.vibeos/config.json` `autonomy.session_override.active` to `false`
- update `.vibeos/session-state.json` with `active: false` and an `ended_at` timestamp

## Output Summary

| Artifact | Path | Purpose |
|---|---|---|
| Config | `.vibeos/config.json` | Preserves negotiated autonomy and temporary autonomous-session override |
| Session state | `.vibeos/session-state.json` | Tracks the current or most recent autonomous session |
| Build log | `.vibeos/build-log.md` | Records when autonomous mode was enabled |
