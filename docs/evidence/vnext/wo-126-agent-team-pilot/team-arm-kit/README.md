# WO-126 Team Arm — Terminal Run Kit

This kit lets you run the **agent-team arm** of the WO-126 pilot in your **interactive Terminal `claude` session** (the only surface where Claude Code agent teams work). It mirrors the subagent arm already executed in the desktop app, so the two arms compare like-for-like.

You do **not** have to run this to close WO-126 — the pilot already closed at `FALLBACK_TO_SUBAGENTS`. Run it only if you want the one dimension the subagent arm cannot measure (**stall detection**) and a real team-vs-subagent comparison.

---

## Step 0 — Preconditions (already done for you)

- `.vibeos/config.json` has `features.agent_team_governance: true` (local, gitignored — not a repo default). This makes the WO-117 team-governance hooks (`TaskCreated`/`TaskCompleted`/`TeammateIdle`) fire and append to `.vibeos/team-governance/events.jsonl`.
- The two lane packets are in `lane-packets/` (identical to the subagent arm).

## Step 1 — Launch a Terminal team session

```bash
cd "/Users/latifhorst/cursor projects/vibeos-plugin"
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude
```

> The export only affects this Terminal process. It does **not** reach the desktop app. Agent teams are **Terminal-TUI-only** in v2.1.177.

## Step 2 — Verify teams are actually live

Inside the session, do one of:
- Press **Ctrl+T** — if a shared task list panel appears, teams are active.
- Or ask: *"Spawn a 2-person agent team to confirm teams are enabled, then stand it down."* — if a named teammate appears, teams are active.
- **Shift+Down** cycles teammates (you'll see a teammate name or a "no teammates" message).

If teams do **not** activate (your launch banner showed "3 setup issues" — those are MCP-related, not teams, but verify anyway): stop here. The pilot stays at `FALLBACK_TO_SUBAGENTS`; record "teams did not activate" in `evidence-template/pilot-summary.json` and you're done.

## Step 3 — Drive the pilot

Paste the contents of [`WO-126-TEAM-PILOT-BRIEF.md`](WO-126-TEAM-PILOT-BRIEF.md) as your first message. It tells the lead Claude to:
- spawn **exactly 2** named teammates (`lane-a-auditgates`, `lane-b-hygiene`),
- hand each its lane packet from `lane-packets/`,
- require each to write its return packet and cite WO-126 + its lane WO,
- keep the lanes disjoint (no same-file contention).

## Step 4 — Capture evidence (fill the templates in `evidence-template/`)

| Capture | How |
|---|---|
| `team-governance-events.jsonl` | `cp .vibeos/team-governance/events.jsonl evidence-template/team-governance-events.jsonl` after the run |
| `task-list-start.json` / `task-list-end.json` | Snapshot the shared task list (Ctrl+T) at spawn and at close |
| `cost-report.json` | Run `/cost` after both lanes close; record total tokens/USD |
| `coordinator-labor.json` | Note wall-clock spawn→both-closed and count lead interventions (messages, nudges, stall recoveries) |
| `defect-ledger.json` | List any defects the teammates caught before merge |
| lane return packets | Teammates write `lane-a-wo127-return.json` / `lane-b-wo128-return.json` |
| `pilot-summary.json` | Record whether teams ran, per-criterion results, and the verdict |

## Step 5 — Score the comparison

Compare against the subagent baseline in the parent dir (`../comparison-model.json` defines the five criteria and the decision logic). The **stall-detection** criterion is the one only this arm can satisfy — confirm `TeammateIdle` or a missing-return was detected within **5 min p95 / 10 min max** in `events.jsonl`.

If all five criteria pass and cost is within 25% of the subagent baseline, WO-126 may be re-scored **`PARTIAL_UNLOCK_CANDIDATE`**. Teams remain non-default regardless.

## If a teammate stalls, loses context, or edits out of scope

Per the WO-125 manual fallback:
1. Preserve `.vibeos/team-governance/events.jsonl` (copy it into `evidence-template/`).
2. Snapshot the task list and any partial return packets.
3. Mark `pilot-summary.json` verdict `FALLBACK_TO_SUBAGENTS`.
4. Finish the lanes via normal subagent execution (already done in the desktop arm).
5. Record the fallback reason before any completion claim.

## Cleanup

When done: `"Clean up the team"` to the lead, then optionally unset the flag:
`jq 'del(.features.agent_team_governance)' .vibeos/config.json | sponge .vibeos/config.json` (or edit by hand). The flag is local/gitignored, so leaving it on has no repo effect.
