---
wo: WO-114
title: Lane Return-Packet Schema
status: Complete
phase: 36
phase_name: Lane-Readiness Automation
wo_class: harness
write_scope:
  - docs/planning/WO-114-lane-return-packet-schema.md
  - docs/planning/WO-SCHEMA.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/reference/lane-packet.schema.json
  - tests/test_lane_packet_schema.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-114: Lane Return-Packet Schema

## Status

`Complete`

## Phase

Phase 36: Lane-Readiness Automation

## Objective

Define the machine-readable return packet that lane-readiness automation will validate before accepting or deferring a parallel lane.

## Scope

### In Scope
- [x] Add `plugins/vibeos/reference/lane-packet.schema.json`
- [x] Document lane packet semantics in `docs/planning/WO-SCHEMA.md`
- [x] Add schema-focused tests for ACCEPT and DEFER packets plus known-bad packets

### Out of Scope
- Implementing `check-lane-readiness.sh`
- Running scratch worktrees or rebases
- Validating actual rebase diffs against `write_scope`

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 35 | Machine-readable WO contracts | Complete |

## Acceptance Criteria

- [x] AC-1: Schema requires `wo_number`, `lane_status`, `gate_results`, `defects`, and `evidence_bundle_path`
- [x] AC-2: ACCEPT fixture with passing gates and no defects validates
- [x] AC-3: DEFER fixture with failed gate and defect validates
- [x] AC-4: Invalid lane status, missing evidence path, and malformed gate results fail validation
- [x] AC-5: `WO-SCHEMA.md` documents lane packet semantics and its handoff to WO-115

## Test Strategy

- **Unit tests:** `python3 -m pytest tests/test_lane_packet_schema.py`
- **Schema parse:** `jq . plugins/vibeos/reference/lane-packet.schema.json`
- **Full suite:** `python3 -m pytest tests`
- **Gate proof:** `bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos`

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: WO-114 is a schema/doc/test slice. Runtime anti-spoofing and rebase behavior remain WO-115.
- Test status: Pending at implementation start.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The schema should support both ACCEPT and DEFER packets without requiring real worktree execution. Evidence path remains required for both outcomes.
- Test status: Pending at implementation start.

### Pre-Commit Audit
- Status: `complete`
- Findings: Lane packet work is limited to schema, docs, and schema-check fixtures. Runtime readiness behavior remains reserved for WO-115.
- Test status: Focused schema tests passed; full suite passed; `pre_commit` gate passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Gates pass
- [x] Documentation updated

### Proof Commands

```bash
jq . plugins/vibeos/reference/lane-packet.schema.json >/dev/null
python3 -m py_compile tests/test_lane_packet_schema.py

python3 -m pytest tests/test_lane_packet_schema.py
# 5 passed in 0.01s

python3 -m pytest tests
# 158 passed in 33.98s

bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . --framework-dir plugins/vibeos
# Total: 10 | Passed: 6 | Failed: 0 | Skipped: 4
# Result: PASS
```
