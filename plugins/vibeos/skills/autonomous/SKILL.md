---
name: autonomous
description: Force VibeOS back into full autonomous session mode. Use when the user says "go autonomous", "stop checking in", "run on your own", "stay in autonomous mode", or wants VibeOS to keep building until it hits a real blocker, finishes the plan, or needs an explicit risk decision.
argument-hint: "[optional: brief goal or scope reminder]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion
---

# /vibeos:autonomous — Full Autonomous Session Override

Turn on a temporary full-autonomous session override, record the session state, and continue building without routine check-ins. For 24-48 hour runs, use the long-run autonomy control plane: heartbeat files, checkpoints, audit cadence, failure detection, recovery planning, recovery resolution, and resumable handoff state.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

**Skill-specific addenda:**
- Explain clearly that autonomous mode still obeys the Product Anchor, Engineering Principles, gates, and audit rules
- Do not stop for routine progress check-ins while the autonomous session override is active
- If the system pauses, explain that it is because a real blocker, explicit risk decision, or plan boundary required intervention
- Treat long-run autonomy as resumable execution, not a promise that one model context stays alive forever

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
    },
    "long_run": {
      "active": true,
      "target_hours": 24,
      "max_hours": 48,
      "heartbeat_interval_minutes": 30,
      "checkpoint_interval_minutes": 60,
      "audit_interval_minutes": 180,
      "evidence_dir": ".vibeos/autonomy",
      "stop_conditions": [
        "security_or_secret_risk",
        "destructive_or_irreversible_action",
        "unclear_product_decision",
        "repeated_gate_failure",
        "provider_or_session_limit",
        "repeated_no_progress_loop",
        "plan_complete"
      ]
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
  "last_audited_at": null,
  "long_run": {
    "run_id": "longrun-session-id",
    "active": true,
    "target_hours": 24,
    "max_hours": 48,
    "heartbeat_interval_minutes": 30,
    "checkpoint_interval_minutes": 60,
    "audit_interval_minutes": 180,
    "loop_iteration": 0,
    "last_heartbeat_at": "ISO-8601 timestamp",
    "last_checkpoint_at": null,
    "last_audit_at": null
  }
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

### Step 4: Record the First Long-Run Heartbeat

If `.vibeos/scripts/autonomy-heartbeat.py` exists, record the first heartbeat before continuing:

```bash
python3 ".vibeos/scripts/autonomy-heartbeat.py" \
  --status running \
  --iteration 0 \
  --summary "autonomous long-run session enabled" \
  --next-action "continue build loop"
```

This creates `.vibeos/autonomy/heartbeats/*.json`, updates `.vibeos/session-state.json`, and gives future sessions a durable resume point.

Then write the first supervisor plan:

```bash
python3 ".vibeos/scripts/autonomy-supervisor.py" --project-dir "."
python3 ".vibeos/scripts/autonomy-runner.py" --project-dir "." --json
```

This creates `.vibeos/autonomy/resume-plan.json`, which records whether the next loop should continue building, record a heartbeat, run a checkpoint, run an audit, or stop.
The runner writes `.vibeos/autonomy/runner-report.json`, blocks untrusted shell commands, and marks Codex/Claude continuation steps as handoff-required model work.
External schedulers or runtime adapters can call `python3 ".vibeos/scripts/autonomy-loop.py" --project-dir "." --json` to run one deterministic supervisor-plus-runner tick and write `.vibeos/autonomy/loop-state.json`.
When the loop reports `handoff_required`, `python3 ".vibeos/scripts/autonomy-runtime-adapter.py" --project-dir "." --json` writes the Codex/Claude handoff plan without launching it. Use `--execute` only when the surrounding automation is intentionally allowed to start a new runtime process.
If loop ticks, runtime handoffs, runner blocks, lease conflicts, or provider/session limit signals repeat, run `python3 ".vibeos/scripts/autonomy-failure-detector.py" --project-dir "." --json` and then `python3 ".vibeos/scripts/autonomy-recovery-planner.py" --project-dir "." --json`. Use `python3 ".vibeos/scripts/autonomy-recovery-resolution.py" --project-dir "." --action-id "<ACTION_ID>" --summary "<what changed>" --evidence "<path-or-note>" --json` to record evidence for resolved recovery actions. `python3 ".vibeos/scripts/autonomy-scheduler-guard.py" --project-dir "." --json` must pass before scheduling another tick.
Before installing a scheduler profile, generate it with `python3 ".vibeos/scripts/autonomy-scheduler-profile.py" --project-dir "." --json` and run `python3 ".vibeos/scripts/autonomy-smoke.py" --runtime-provider codex --json` against a disposable target or reviewed project path.

### Step 5: Explain What Happens Next

Tell the user, in plain English:
- VibeOS will keep building without routine check-ins
- for 24-48 hour runs, VibeOS will write heartbeat, checkpoint, and audit evidence so the run can resume safely if the runtime is interrupted
- quality gates, audit agents, anchor checks, and prompt-engineering rules still apply
- VibeOS will still pause for blockers, explicit risk decisions, or if the plan is complete

If `$ARGUMENTS` includes a scope reminder, include that reminder in the confirmation.

### Step 6: Continue Building Immediately

After updating config and session state:
1. Read `skills/build/SKILL.md`
2. Continue directly into the build flow
3. Treat the autonomous session override as active for the rest of the build session

While the override is active:
- do not stop for routine WO or phase check-ins
- use `autonomy-loop.py` for scheduler-safe loop ticks when a non-model process is driving the session
- respect `.vibeos/autonomy/run-lease.json`; if a lease conflict appears, treat another autonomy driver as active
- use `autonomy-runtime-adapter.py` for dry-run-first Codex/Claude runtime handoff planning
- use `autonomy-failure-detector.py` for repeated handoff loops, runner blocks, runtime failures, lease conflicts, and provider/session limits
- use `autonomy-recovery-planner.py` for plan-only recovery actions after failure detection
- use `autonomy-recovery-resolution.py` to record summary and evidence for resolved recovery actions
- use `autonomy-scheduler-guard.py` to block scheduler-driven ticks while recovery actions lack matching resolution evidence
- use `autonomy-scheduler-profile.py` only to generate reviewed profile files; it does not install cron, launchd, or CI jobs
- use `autonomy-smoke.py` before trusting a scheduler profile
- record a long-run heartbeat at least every 30 minutes, after every WO boundary, and after every checkpoint/audit boundary
- classify each supervisor resume plan with `autonomy-runner.py`; use `--execute` only for allowlisted local VibeOS scripts
- save checkpoints at least every 60 minutes or after each agent/work-package boundary
- run a checkpoint or session audit at least every 180 minutes or phase boundary
- at phase boundaries, run the checkpoint flow automatically before continuing
- only pause when a real blocker, escalation, explicit risk decision, or plan-completion condition requires it

### Step 7: Clearing the Override

When the user later says "stop autonomous mode", "change autonomy", or the autonomous session finishes:
- set `.vibeos/config.json` `autonomy.session_override.active` to `false`
- update `.vibeos/session-state.json` with `active: false` and an `ended_at` timestamp
- record a terminal heartbeat:
  ```bash
  python3 ".vibeos/scripts/autonomy-heartbeat.py" --status complete --summary "autonomous session complete" --next-action "run session audit"
  ```
- run long-run closeout validation:
  ```bash
  python3 ".vibeos/scripts/validate-long-run-autonomy.py" --project-dir "." --require-closed
  ```

## Output Summary

| Artifact | Path | Purpose |
|---|---|---|
| Config | `.vibeos/config.json` | Preserves negotiated autonomy and temporary autonomous-session override |
| Session state | `.vibeos/session-state.json` | Tracks the current or most recent autonomous session |
| Build log | `.vibeos/build-log.md` | Records when autonomous mode was enabled |
| Heartbeats | `.vibeos/autonomy/heartbeats/*.json` | Durable evidence and resume points for 24-48 hour autonomous runs |
| Run lease | `.vibeos/autonomy/run-lease.json` | Active driver lease preventing concurrent loop/runtime mutation |
| Lease evidence | `.vibeos/autonomy/last-lease.json` | Last acquired and released lease evidence |
| Lease conflict | `.vibeos/autonomy/lease-conflict.json` | Latest blocked concurrent driver attempt |
| Loop state | `.vibeos/autonomy/loop-state.json` | Latest scheduler-safe supervisor-plus-runner tick state |
| Loop history | `.vibeos/autonomy/loop-history.jsonl` | Append-only loop tick history for stuck-loop detection |
| Runner report | `.vibeos/autonomy/runner-report.json` | Records safe resume-plan classification, execution, blocked commands, and model handoffs |
| Runtime adapter plan | `.vibeos/autonomy/runtime-adapter-plan.json` | Planned or executed Codex/Claude handoff command |
| Runtime adapter history | `.vibeos/autonomy/runtime-adapter-history.jsonl` | Append-only runtime handoff history for repeated failure detection |
| Failure report | `.vibeos/autonomy/failure-report.json` | Repeated loop, blocked runner, runtime, lease, and provider/session failure report |
| Recovery plan | `.vibeos/autonomy/recovery-plan.json` | Plan-only recovery actions for detected autonomy failure classes |
| Recovery resolution | `.vibeos/autonomy/recovery-resolution.json` | Evidence-backed resolution state for recovery-plan actions |
| Recovery resolution history | `.vibeos/autonomy/recovery-resolution-history.jsonl` | Append-only recovery resolution history |
| Scheduler guard report | `.vibeos/autonomy/scheduler-guard-report.json` | Pre-tick guard result for unresolved recovery actions |
| Scheduler profile | `.vibeos/autonomy/scheduler-profile.json` | Generated scheduler profile manifest |
| Smoke report | `.vibeos/autonomy/smoke-report.json` | Disposable autonomy smoke-test result |
