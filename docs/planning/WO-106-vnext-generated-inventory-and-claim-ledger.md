# WO-106: vNext Generated Inventory and Claim Ledger

## Status

`Implemented Locally`

## Phase

Phase 33: VibeOS vNext Public Proof Foundation

## Objective

Create a source-generated inventory and claim ledger so public VibeOS vNext claims are derived from this repository instead of copied from stale website or legacy VibeOS counts.

## Scope

### In Scope
- [x] Add a deterministic inventory generator for skills, agents, hooks, scripts, gates, decision files, reference files, tests, and work orders
- [x] Include a claim ledger that marks source-derived count claims as allowed with the generated artifact
- [x] Include public overclaim blockers for Codex hook parity, automatic write-time enforcement, and repo-link readiness
- [x] Write a generated artifact under `docs/evidence/vnext/`
- [x] Add focused unit coverage for the generator

### Out of Scope
- Implementing U1-U7 behavior changes
- Selecting or creating the public tag
- Running fresh temp-repo install proof
- Producing the real sample execution trace
- Producing public media or website copy

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-121 website readiness matrix | Read-only source input | Complete |
| WO-122 website reconciliation matrix | Read-only source input | Complete |
| Joan4U 2026-06-09 harness blueprint and addendum | Read-only source input | Complete |
| WO-072 Runtime Capability Matrix | Existing local mechanism | Complete |

## Findings

1. WO-121 and WO-122 block stronger public VibeOS claims until counts and proof are generated from source.
2. The current repo has real assets for skills, agents, scripts, gates, hooks, references, and runtime capability detection, but public count claims would still be manually copied without a generated inventory artifact.
3. Codex support must stay limitation-aware; public claims must not imply Claude hook parity or automatic write-time enforcement across runtimes.

## Acceptance Criteria

- [x] AC-1: `generate-inventory.py` produces a JSON artifact with source-derived inventory counts
- [x] AC-2: Generated artifact includes a claim ledger for public-safe count claims
- [x] AC-3: Generated artifact explicitly blocks known overclaims from WO-121/WO-122
- [x] AC-4: Focused tests cover count generation, claim-ledger posture, and file writing
- [ ] AC-5: Downstream public amplification consumes this artifact after tag, install, runtime, gate, secret-scan, sample-trace, limitation, and media proof are complete

## Test Strategy

- **Unit tests:** `python3 -m pytest tests/test_generate_inventory.py`
- **Integration tests:** Run the generator against this repository
- **Real-path verification:** Inspect `docs/evidence/vnext/generated-inventory.json`
- **Verification command:** `python3 plugins/vibeos/scripts/generate-inventory.py --project-dir .`

## Implementation Plan

### Step 1: Generator
- Add `plugins/vibeos/scripts/generate-inventory.py`
- Expected outcome: one JSON artifact contains inventory, manifest summary, runtime-capability pointer, claim ledger, and public limitations

### Step 2: Tests
- Add `tests/test_generate_inventory.py`
- Expected outcome: generator behavior is covered without relying on this repo's live counts

### Step 3: Planning Integration
- Update `WO-INDEX.md` and `DEVELOPMENT-PLAN.md`
- Expected outcome: vNext proof foundation is represented as governed work

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Source inputs establish a proof gap; WO is additive and proof-infrastructure scoped.
- Test status: Pending at planning time.

### Pre-Implementation Audit
- Status: `complete`
- Findings: No Claude/Cursor runtime behavior changes; first slice is source-derived evidence only.
- Test status: Pending at implementation start.

### Pre-Commit Audit
- Status: `partial`
- Findings: `gate-runner.sh pre_commit` dry-run works, but live execution stops before gates with `AttributeError: 'str' object has no attribute 'get'` because the runner expects tier objects while the current manifest stores tier labels as strings. Standalone secret scanning also fails on an existing AWS-looking fake key in the embedded test fixture. Both appear pre-existing and outside this WO's proof-inventory scope.
- Test status: `python3 -m pytest tests` passed; direct full `python3 -m pytest` still collects the embedded fixture and fails on `ModuleNotFoundError: No module named 'test_fixture'`.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [ ] Gates pass
- [x] Documentation updated
