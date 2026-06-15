# Agent-Team Pilot Design

## Purpose

Define the WO-126 pilot before any agent-team execution starts. This is a canary for Claude Code agent teams, not a default orchestration path for VibeOS.

## Source Inputs

- WO-117 installed dormant team-governance hooks for `TaskCreated`, `TaskCompleted`, `TeammateIdle`, and `WorktreeCreate`.
- WO-124 proved dynamic workflow canaries can be useful but full fan-out remains too expensive for default adoption.
- Official Claude Code docs checked on 2026-06-15: agent teams are experimental, disabled by default, require Claude Code `2.1.32+`, use `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, and carry known limits around session resumption, task coordination, and shutdown behavior.
- Local runtime pin: `docs/evidence/vnext/wo-125-agent-team-pilot/runtime-pin.json` records Claude Code `2.1.177` and `agent_teams_status_with_opt_in: experimental_available`.

## Pilot Shape

WO-126 may run only two or three disjoint-scope WOs as named teammates. The pilot must use separate ownership lanes with no same-file edit contention:

| Lane | Shape | Evidence |
|---|---|---|
| Lane A | docs/evidence or planning-only task | task record, hook log, lane packet |
| Lane B | deterministic script/test task | task record, focused tests, lane packet |
| Lane C | optional small fixture/test task | task record, gate output, lane packet |

The lead may assign work only after a shared task list exists and every task cites the governing WO. Team tasks must remain reportable through WO-117 hook logs.

## Required Feature Flags

Agent teams remain off by default. The pilot may enable them only for the WO-126 session/worktree:

```json
{
  "features": {
    "agent_team_governance": true
  }
}
```

Claude Code agent teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` for the pilot shell. The flag is not a repository default.

## Manual Fallback

If any teammate stalls, loses context, edits out of scope, or fails to return a lane packet, the lead must stop agent-team execution and fall back to the existing sequential/subagent path:

1. Preserve `.vibeos/team-governance/events.jsonl`.
2. Capture current task-list state and any partial lane packet.
3. Mark the pilot state `FALLBACK_TO_SUBAGENTS`.
4. Finish the active WO through the normal VibeOS build/audit path.
5. Record the fallback reason before any completion claim.

## Go/No-Go Criteria

These thresholds are fixed before WO-126 starts:

| Criterion | Partial unlock target | No-go condition | Evidence artifact |
|---|---|---|---|
| Stall detection latency | `TeammateIdle` or missing-return detection recorded within 5 minutes p95 and 10 minutes max | Any unrecorded stall, or max latency over 10 minutes | `events.jsonl`, task-list snapshots, pilot summary |
| Pre-merge defects caught | At least one material issue caught before merge/closeout, or all scoped lanes explicitly record clean evidence with no post-closeout regression | Defect found only after closeout, or no evidence that checks ran before merge | lane packets, audit/gate output, defect ledger |
| Coordinator labor | Lead coordination time no more than 80% of a sequential baseline for same lane count | Coordination time equals/exceeds sequential baseline, or is not measured | time ledger, baseline estimate, pilot summary |
| Scope safety | Zero unauthorized path writes and zero missing WO references in task hooks | Any governance veto, out-of-scope edit, or missing-WO task closure | team-governance hook logs, git diff, lane packets |
| Cost posture | Pilot cost captured and reviewed; no default adoption if cost exceeds sequential/subagent baseline by more than 25% | Cost missing, unreconciled, or materially higher without a justified quality win | Claude output JSON, cost summary |

## Required Evidence Bundle

WO-126 must create `docs/evidence/vnext/wo-126-agent-team-pilot/` with:

- `runtime-pin.json`
- `task-list-start.json`
- `task-list-end.json`
- `team-governance-events.jsonl`
- `lane-packets/*.json`
- `cost-report.json`
- `defect-ledger.json`
- `coordinator-labor.json`
- `pilot-summary.json`

## Allowed Verdicts

WO-126 must close with one of:

- `NO_GO`
- `FALLBACK_TO_SUBAGENTS`
- `PARTIAL_UNLOCK_CANDIDATE`

It must not claim production readiness, default adoption, Claude/Codex parity, or 24-48 hour autonomy.
