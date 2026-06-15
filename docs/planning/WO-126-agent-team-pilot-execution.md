---
wo: WO-126
title: "Pilot execution: parallel WO lanes as team"
status: In Progress
phase: 41
phase_name: Agent-Team Pilot
wo_class: planning
write_scope:
  - docs/planning/WO-126-agent-team-pilot-execution.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-126-agent-team-pilot/**
  - tests/test_agent_team_pilot_execution.py
  - .vibeos/config.json
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - plan-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
  notes: "Bounded canary. Exactly 2 lane subagents; read-only planning slices; no framework code changed."
loop_goal: "WO-126 closes with one of NO_GO / FALLBACK_TO_SUBAGENTS / PARTIAL_UNLOCK_CANDIDATE, with a two-arm evidence bundle."
loop_ceiling_turns: 1
loop_ceiling_cost_usd: 0
---

# WO-126: Pilot Execution — Parallel WO Lanes as Team

## Status

`In Progress` — subagent arm complete and verdict recorded (`FALLBACK_TO_SUBAGENTS`); the optional Terminal team arm is pending the operator to complete the two-arm comparison and potentially re-score.

## Phase

Phase 41: Agent-Team Pilot

## Objective

Run the WO-125-designed agent-team canary on two disjoint Phase 42 lanes (Lane A = WO-127, Lane B = WO-128), produce the required evidence bundle, and close with one of the three allowed verdicts. Per operator request, run it as an explicit **two-arm comparison**: a subagent baseline and a real agent-team challenger.

## Key Finding — Agent Teams Did Not Run in the Executing Surface

The session that received this WO is the **Claude Desktop app** (`CLAUDE_CODE_ENTRYPOINT=claude-desktop`), not the operator's Terminal `claude`. Two independent, decisive blockers:

1. **Env not inherited.** The operator exported `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in a Terminal process and launched `claude` there. An environment variable only affects the process that inherited it; the desktop app is a separate process tree and read the variable as `UNSET`.
2. **Surface constraint.** Per official Claude Code docs (`code.claude.com/docs/en/agent-teams`), agent teams are **interactive-Terminal-TUI-only** in v2.1.177 — not exposed in the desktop app, web, or SDK/headless surfaces.

This is the exact condition the WO-125 design anticipated: when agent teams are unavailable in the executing session, the sanctioned outcome is the manual fallback verdict `FALLBACK_TO_SUBAGENTS`. Evidence: [runtime-pin.json](../evidence/vnext/wo-126-agent-team-pilot/runtime-pin.json).

## Two-Arm Design

Both arms run the **same two disjoint lanes** with the **same lane packets** and the **same return-packet shape**, so the five go/no-go criteria compare like-for-like.

| Arm | Surface | Mechanism | Role | Status |
|---|---|---|---|---|
| Subagents | claude-desktop | Agent tool, 2 parallel scoped subagents | Baseline | Complete |
| Teams | terminal-tui | Claude Code agent teams (2 named teammates, WO-117 hooks) | Challenger | Pending operator run via [team-arm-kit](../evidence/vnext/wo-126-agent-team-pilot/team-arm-kit/README.md) |

## Lane Scope Reduction (and why)

Full WO-127 (three new gate behaviors + per-gate fixtures + manifest registration) and full WO-128 (lint + two policies + prune script + doc-budget + orphan detection + fixtures) are **too broad for a bounded, cost-controlled agent-team canary**. Implementing executable gate/lint/prune logic during the pilot would mix substantive Phase 42 delivery with pilot-mechanism evaluation and contaminate the cost/labor comparison.

Each lane was therefore reduced to a **self-contained, read-only planning/evidence slice**: an implementation-ready spec + fixture plan that a follow-up WO can execute deterministically. This keeps cost low, risk near-zero (no framework code touched), and the comparison clean. The slices are genuinely useful — they de-risk Phase 42 and already surfaced real defects.

## Subagent Arm Results (baseline)

- **Teammates spawned:** exactly 2 — `lane-a-auditgates` (WO-127), `lane-b-hygiene` (WO-128).
- **Both lanes:** `COMPLETE`, in scope, returned full packets citing WO-126 + their lane WO.
- **Lane A return:** [lane-a-wo127-return.json](../evidence/vnext/wo-126-agent-team-pilot/lane-packets/lane-a-wo127-return.json) — three gate specs (validate-auditor-artifacts, validate-waiver-expiry, executed-vs-declared assertion), fixture plan, manifest registration plan. **3 defects** (1 major).
- **Lane B return:** [lane-b-wo128-return.json](../evidence/vnext/wo-126-agent-team-pilot/lane-packets/lane-b-wo128-return.json) — config schema, three script specs, doc-budget + orphan-doc design, fixtures. **2 defects**.

### Go/No-Go scoring — subagent arm

| Criterion | Target | Subagent-arm result |
|---|---|---|
| Stall detection latency | within 5 min p95 / 10 min max | **N/A** — structurally unmeasurable in the subagent arm; the Agent tool returns synchronously with no `TeammateIdle` hook. Requires the Terminal team arm. |
| Pre-merge defects caught | ≥1 material issue before merge, or clean evidence per lane | **PASS** — 5 defects caught pre-merge, incl. **D-A1 (major)**: gate-runner silently SKIPs missing-script gates — the live Joan NF-1 hole WO-127 targets. |
| Coordinator labor vs sequential | ≤80% of sequential baseline | **PASS** — ~60% of sequential (1 dispatch, 0 mid-flight interventions, 40.6% parallel wall-clock saving). |
| Scope safety | zero unauthorized writes, zero missing-WO closures | **PASS** — git-verified zero out-of-scope writes; both tasks cited WO references at create and close. |
| Cost posture | captured + reviewed; no default adoption if >25% over baseline | **BASELINE SET** — 157,456 lane subagent tokens recorded as the comparison baseline. |

Result: **4 of 4 measurable criteria pass.** Stall detection is the one dimension only the team arm can measure.

## Verdict

**`FALLBACK_TO_SUBAGENTS`** (this session).

**Rationale.** Real Claude Code agent teams could not run in the executing desktop surface (env not inherited + TUI-only feature). Per the WO-125 manual-fallback design, the sanctioned outcome is `FALLBACK_TO_SUBAGENTS`. The fallback executed cleanly: two parallel scoped subagents completed both disjoint lanes, in scope, catching five pre-merge defects at a coordination cost ~60% of sequential. For a desktop-first operator, the subagent/workflow path is the production path; agent teams are a terminal-only experiment that remains non-default. The two-arm harness is in place so the operator can run the Terminal team arm to obtain the missing stall-detection dimension and, if it scores well across all five criteria within 25% of the cost baseline, re-score WO-126 as `PARTIAL_UNLOCK_CANDIDATE`.

## Manual Fallback Record (per WO-125)

1. `.vibeos/team-governance/events.jsonl` — not present in the desktop arm (no team runtime fired those events); the desktop-arm lifecycle is recorded as derived records in [team-governance-events.jsonl](../evidence/vnext/wo-126-agent-team-pilot/team-governance-events.jsonl). The Terminal arm will produce the real file.
2. Task-list state captured: [task-list-start.json](../evidence/vnext/wo-126-agent-team-pilot/task-list-start.json), [task-list-end.json](../evidence/vnext/wo-126-agent-team-pilot/task-list-end.json).
3. Pilot state marked `FALLBACK_TO_SUBAGENTS` in [pilot-summary.json](../evidence/vnext/wo-126-agent-team-pilot/pilot-summary.json).
4. Bounded slice finished via normal subagent execution (both lanes complete).
5. Fallback reason recorded before this completion claim (this section + pilot-summary).

## Scope

### In Scope
- [x] Two-arm pilot harness (subagent baseline + portable Terminal team kit)
- [x] Exactly 2 disjoint lane subagents with narrow lane packets
- [x] Full evidence bundle for the subagent arm
- [x] Lane scope reduction to planning/evidence slices, with recorded reason
- [x] Deterministic test over the evidence bundle
- [x] Verdict in the three-level language

### Out of Scope
- Implementing WO-127 / WO-128 framework code (only specced)
- Enabling agent teams by default
- Any Phase 43 upgrade-path work
- Website changes; production-readiness / parity / 24-48h autonomy claims

## Acceptance Criteria
- [x] AC-1: Two-arm pilot executed/prepared; subagent arm complete
- [x] AC-2: Exactly 2 teammates, disjoint scope, no same-file contention
- [x] AC-3: Evidence bundle present (runtime-pin, task-list start/end, team-governance events, lane packets, cost, defect ledger, coordinator labor, pilot summary, comparison model)
- [x] AC-4: Zero unauthorized path writes (git-verified); every task cites its WO
- [x] AC-5: Verdict is one of NO_GO / FALLBACK_TO_SUBAGENTS / PARTIAL_UNLOCK_CANDIDATE
- [x] AC-6: Deterministic test validates the bundle structure and verdict enum
- [ ] AC-7 (optional): Terminal team arm run to complete the comparison and the stall-detection criterion

## Test Strategy
- **Focused:** `python3 -m pytest tests/test_agent_team_pilot_execution.py`
- **Index:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Evidence
- [x] Two-arm evidence bundle under `docs/evidence/vnext/wo-126-agent-team-pilot/`
- [x] Subagent-arm scope safety git-verified
- [x] Deterministic test added
- [x] Fallback reason recorded before completion claim

### Proof Commands
```bash
jq . docs/evidence/vnext/wo-126-agent-team-pilot/pilot-summary.json >/dev/null
jq -r .verdict docs/evidence/vnext/wo-126-agent-team-pilot/pilot-summary.json
# FALLBACK_TO_SUBAGENTS

python3 -m pytest tests/test_agent_team_pilot_execution.py
python3 plugins/vibeos/scripts/wo-frontmatter-lint.py lint --project-dir .
python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .
python3 -m pytest tests
bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
```

## Remaining Limitations
- Agent teams were not exercised live; stall-detection latency is unproven until the Terminal team arm runs.
- The lane outputs are planning slices, not implemented Phase 42 gates/scripts.
- Cost is in reported output tokens, not USD (no USD figure exposed in this session).
- This WO does not approve default agent-team use, claim Claude/Codex parity, claim production readiness, or claim 24-48h autonomy.
