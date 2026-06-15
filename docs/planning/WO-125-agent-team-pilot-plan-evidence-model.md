---
wo: WO-125
title: Agent-Team Pilot Plan + Evidence Model
status: Complete
phase: 41
phase_name: Agent-Team Pilot
wo_class: planning
write_scope:
  - docs/planning/WO-125-agent-team-pilot-plan-evidence-model.md
  - docs/planning/AGENT-TEAM-PILOT-DESIGN.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - docs/evidence/vnext/wo-125-agent-team-pilot/**
  - tests/test_agent_team_pilot_plan.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - plan-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: 1
  cost_ceiling_usd: 0
loop_goal: agent-team pilot gates are defined before WO-126 execution
loop_ceiling_turns: 1
loop_ceiling_cost_usd: 0
---

# WO-125: Agent-Team Pilot Plan + Evidence Model

## Status

`Complete`

## Phase

Phase 41: Agent-Team Pilot

## Objective

Define the WO-126 agent-team pilot, evidence bundle, manual fallback, version pin, and go/no-go thresholds before any live agent-team execution.

## Source Evidence

- The vNext master plan scopes WO-125 to a pilot design doc, version pin, manual fallback, and team-governance hook flag for pilot only.
- WO-117 installed dormant team-governance hooks and kept agent teams non-default.
- WO-124 showed that modern orchestration surfaces need canary proof and cost comparison before stronger adoption claims.
- Official Claude Code docs checked on 2026-06-15 state that agent teams are experimental, disabled by default, enabled with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, and require Claude Code `2.1.32+`.
- Local runtime pin records Claude Code `2.1.177` and `agent_teams_status_with_opt_in: experimental_available`.

## Scope

### In Scope

- [x] Add an agent-team pilot design doc
- [x] Record local Claude Code version and agent-team opt-in capability
- [x] Define manual fallback to sequential/subagent execution
- [x] Define the WO-126 evidence bundle
- [x] Define go/no-go criteria before execution: stall latency, pre-merge defects caught, coordinator labor, scope safety, and cost posture
- [x] Add deterministic tests for the plan/evidence model

### Out of Scope

- Running an agent team
- Enabling agent teams by default
- Running WO-126
- Claiming production readiness, Codex equivalence, or long-run autonomy
- Website changes

## Acceptance Criteria

- [x] AC-1: Pilot design doc exists
- [x] AC-2: Version pin records Claude Code version, opt-in env, and local agent-team capability with opt-in
- [x] AC-3: Manual fallback is explicit and keeps sequential/subagent execution as the recovery path
- [x] AC-4: Go/no-go criteria are defined before pilot execution
- [x] AC-5: Evidence model requires task-list state, hook logs, lane packets, cost, defect ledger, coordinator labor, and pilot summary
- [x] AC-6: Tests validate the plan and evidence model

## Remaining Limitations

- This WO is planning and evidence modeling only.
- It does not prove agent teams work in this repo.
- It does not approve default agent-team use.
- The WO-126 pilot must still run live and may close as `NO_GO`, `FALLBACK_TO_SUBAGENTS`, or `PARTIAL_UNLOCK_CANDIDATE`.

## Test Strategy

- **Focused tests:** `python3 -m pytest tests/test_agent_team_pilot_plan.py`
- **Index:** `python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit

- Status: `complete`
- Findings: Agent teams must stay experimental and pilot-only. WO-126 must not begin until the pilot can be scored against explicit thresholds.
- Test status: Focused tests selected.

### Closeout Audit

- Status: `complete`
- Findings: The plan defines pre-pilot go/no-go thresholds, preserves manual fallback, pins the local Claude version/capability, and keeps agent teams non-default.
- Test status: Focused tests, frontmatter lint, generated index validation, full suite, and `pre_commit` gate passed.

## Evidence

- [x] Planning artifact complete
- [x] Version pin captured
- [x] Evidence model captured
- [x] Tests added
- [x] Full suite passed
- [x] Gates passed

### Proof Commands

```bash
cat docs/evidence/vnext/wo-125-agent-team-pilot/claude-version.txt
# 2.1.177 (Claude Code)

jq . docs/evidence/vnext/wo-125-agent-team-pilot/runtime-pin.json >/dev/null
jq . docs/evidence/vnext/wo-125-agent-team-pilot/evidence-model.json >/dev/null

python3 -m pytest tests/test_agent_team_pilot_plan.py
# 5 passed in 0.01s

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py lint --project-dir .
# [wo-frontmatter] PASS: frontmatter contracts are valid

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py generate-index --project-dir . --out docs/planning/WO-INDEX.md
# wrote docs/planning/WO-INDEX.md

python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
# [wo-frontmatter] PASS: WO-INDEX.md generated block is current

python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .
# [generate-inventory] PASS: wrote docs/evidence/vnext/generated-inventory.json

python3 -m pytest tests
# 228 passed in 50.05s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
