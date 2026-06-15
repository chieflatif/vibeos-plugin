# WO-126 Team-Arm Pilot Brief (paste this as your first message in the Terminal team session)

You are the **lead** of a bounded VibeOS agent-team pilot (WO-126), running in an interactive Claude Code Terminal session with agent teams enabled. Stay tightly scoped and cost-controlled.

## Hard boundaries (non-negotiable)
- Do NOT touch `/Users/latifhorst/latifhorstweb/**` or `/Users/latifhorst/Joan4U/**`.
- Spawn **exactly 2** teammates. Do not spawn a third unless you first document a blocking reason.
- This is experimental and non-default regardless of outcome. Do not claim production readiness, Claude/Codex parity, default team adoption, or 24-48h autonomy.
- Do not expose secrets. Do not run broad open-ended repo audits.

## What to do
1. Confirm the working dir is `/Users/latifhorst/cursor projects/vibeos-plugin` and that `.vibeos/config.json` has `features.agent_team_governance: true`.
2. Spawn 2 named teammates with disjoint scope:
   - **`lane-a-auditgates`** — give it the lane packet `docs/evidence/vnext/wo-126-agent-team-pilot/team-arm-kit/lane-packets/lane-a-wo127.json` (WO-127 gate planning slice).
   - **`lane-b-hygiene`** — give it the lane packet `docs/evidence/vnext/wo-126-agent-team-pilot/team-arm-kit/lane-packets/lane-b-wo128.json` (WO-128 hygiene planning slice).
3. Each teammate task MUST cite **WO-126** plus its lane WO (**WO-127** or **WO-128**) in the subject or description — the `TaskCreated` governance hook will veto a task with no WO reference.
4. Each teammate does **read-only** investigation and writes **only** its single allowed return packet:
   - lane A → `docs/evidence/vnext/wo-126-agent-team-pilot/team-arm-kit/evidence-template/lane-a-wo127-return.json`
   - lane B → `docs/evidence/vnext/wo-126-agent-team-pilot/team-arm-kit/evidence-template/lane-b-wo128-return.json`
   (Use the `evidence_to_return` keys listed in each lane packet. Do NOT modify any file under `plugins/`, `tests/`, `.vibeos/`, `docs/planning/`, the generated inventory, or the other lane's files.)
5. Keep the lanes disjoint — no same-file contention.

## Evidence to capture (this is the whole point of the team arm)
- After both lanes close, copy `.vibeos/team-governance/events.jsonl` into `evidence-template/team-governance-events.jsonl`.
- Confirm in that log that any `TeammateIdle` / missing-return was detected within **5 minutes (p95) / 10 minutes (max)** — this stall-detection figure is the one dimension the desktop subagent arm could not measure.
- Run `/cost` and record totals into `evidence-template/cost-report.json`.
- Record wall-clock (spawn → both closed) and your intervention count into `evidence-template/coordinator-labor.json`.
- Fill `evidence-template/pilot-summary.json`: whether teams ran, per-criterion results, and the verdict (`NO_GO`, `FALLBACK_TO_SUBAGENTS`, or `PARTIAL_UNLOCK_CANDIDATE`).

## If anything stalls or goes out of scope
Stop the team, preserve `.vibeos/team-governance/events.jsonl`, snapshot partial packets, mark the verdict `FALLBACK_TO_SUBAGENTS`, and record the reason. The desktop subagent arm already completed both lanes, so no work is lost.

## Comparison
Score against the subagent baseline at `docs/evidence/vnext/wo-126-agent-team-pilot/` (see `comparison-model.json`). Report the five criteria: stall-detection latency, pre-merge defects caught, coordinator labor vs sequential, scope safety, cost posture.
