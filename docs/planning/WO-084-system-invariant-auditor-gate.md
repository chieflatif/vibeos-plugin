# WO-084: System Invariant Auditor and Gate

## Status

`Complete`

## Phase

Phase 16: System Invariants & State Safety

## Objective

Add a first-class System Invariant Auditor and deterministic invariant gate so VibOS Comp validates the rules that must always remain true across state transitions, ownership, authorization, retries, duplicate side effects, partial failure, recovery, and future change.

## Scope

### In Scope
- [x] Add isolated and same-tree System Invariant Auditor role contracts
- [x] Add system invariant reference template and checklist
- [x] Add deterministic `validate-system-invariants.py` gate
- [x] Wire invariant validation into `comp_gauntlet`
- [x] Include invariant review in high-tier audit dispatch manifests
- [x] Install System Invariant Auditor through Claude/Cursor and Codex bootstrap surfaces

### Out of Scope
- Replacing security, data integrity, contract, correctness, or flow auditors
- Proving every possible invariant automatically
- Claiming invariant safety without negative, retry, recovery, or durable-boundary evidence

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-082 | Flow Auditor and Flow Integrity Gate | Complete |
| WO-083 | Objective Fidelity Scorecard Integration | Complete |

## Findings

1. Happy-path AI builds can look complete while still allowing impossible states, ownership breaks, duplicate side effects, or unrecoverable failures.
2. Flow integrity proves the user journey, but it does not fully prove durable state safety.
3. System invariants need explicit mission, planning, testing, audit, and scorecard pressure so future AI changes do not silently break core rules.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: Flow Auditor, Comp gauntlet, enterprise MVP foundation blueprint, audit dispatch, scorecard generator.
- External sources: none required.

## Impact Analysis

- **Files created:** `plugins/vibeos/agents/system-invariant-auditor.md`, `plugins/vibeos/agents/system-invariant-auditor-same-tree.md`, `plugins/vibeos/reference/comp/SYSTEM-INVARIANTS.md.ref`, `plugins/vibeos/reference/comp/system-invariant-checklist.json`, `plugins/vibeos/scripts/validate-system-invariants.py`, `tests/test_system_invariants.py`
- **Files modified:** mission template, Comp mission skills, planner, integration captain, gate manifests, audit dispatcher, build/audit skills, bootstrap tests
- **Systems affected:** mission intake, planning, Work Order execution, audit dispatch, Comp gauntlet, Codex/Claude install surfaces

## Acceptance Criteria

- [x] AC-1: System Invariant Auditor role contract exists for isolated and same-tree review
- [x] AC-2: Invariant gate fails when `MISSION.md` is missing or lacks required invariant sections
- [x] AC-3: Invariant gate warns without blocking for advisory invariant context gaps
- [x] AC-4: `comp_gauntlet` includes the invariant gate
- [x] AC-5: High-tier audit dispatch includes invariant review
- [x] AC-6: Codex bootstrap installs System Invariant Auditor TOML and contract artifacts

## Test Strategy

- **Unit tests:** validate checklist schema and validator pass/fail/warn behavior
- **Bootstrap tests:** verify Codex agent TOML and contract generation includes System Invariant Auditor
- **Manifest tests:** verify `comp_gauntlet` dry-run includes invariant gate

## Evidence

- [x] `tests/test_system_invariants.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] `tests/test_gate_runner.py`
- [x] Full repository validation run
