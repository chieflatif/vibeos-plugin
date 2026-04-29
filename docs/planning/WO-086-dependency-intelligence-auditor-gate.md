# WO-086: Dependency Intelligence Auditor and Gate

## Status

`Complete`

## Phase

Phase 17: Dependency Intelligence & Current Evidence

## Objective

Add a first-class Dependency Intelligence Auditor and deterministic dependency intelligence gate so VibOS Comp validates dependency choices against current evidence, compatibility, lockfile discipline, transitive risk, security audit output, and upgrade paths before stale model memory can ship.

## Scope

### In Scope
- [x] Add isolated and same-tree Dependency Intelligence Auditor role contracts
- [x] Add dependency intelligence reference template and checklist
- [x] Add deterministic `validate-dependency-intelligence.py` gate
- [x] Wire dependency intelligence validation into `comp_gauntlet`
- [x] Include dependency intelligence review in high-tier audit dispatch manifests
- [x] Install Dependency Intelligence Auditor through Claude/Cursor and Codex bootstrap surfaces

### Out of Scope
- Replacing ecosystem-native audit tools
- Automatically proving every transitive dependency is risk-free
- Claiming current dependency evidence without dated source, compatibility, lockfile, audit, or upgrade-path proof

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-084 | System Invariant Auditor and Gate | Complete |
| WO-085 | Invariant Scorecard and Evidence Integration | Complete |

## Findings

1. AI agents often default to dependencies, APIs, and framework versions that match stale model memory rather than the current ecosystem.
2. Downstream vulnerability and version checks are necessary but not enough; dependency choices need upstream evidence before implementation begins.
3. Enterprise MVPs need package-manager, lockfile, compatibility, security audit, and upgrade-path proof because dependency churn can break deployment, security, and future iteration.

## Research & Freshness

- Verified on: 2026-04-29.
- Local sources: dependency version gates, Comp gauntlet, enterprise MVP foundation blueprint, audit dispatch, Codex and Claude bootstrap surfaces.
- External sources: none required for harness wiring; target projects must provide current-source dependency evidence when choosing packages.

## Impact Analysis

- **Files created:** `plugins/vibeos/agents/dependency-intelligence-auditor.md`, `plugins/vibeos/agents/dependency-intelligence-auditor-same-tree.md`, `plugins/vibeos/reference/comp/DEPENDENCY-INTELLIGENCE.md.ref`, `plugins/vibeos/reference/comp/dependency-intelligence-checklist.json`, `plugins/vibeos/scripts/validate-dependency-intelligence.py`, `tests/test_dependency_intelligence.py`
- **Files modified:** Comp gate manifests, bootstrap scripts, build/audit/plan/checkpoint/session-audit skills, Codex support, audit dispatcher
- **Systems affected:** mission intake, planning, Work Order execution, audit dispatch, Comp gauntlet, Codex/Claude install surfaces

## Acceptance Criteria

- [x] AC-1: Dependency Intelligence Auditor role contract exists for isolated and same-tree review
- [x] AC-2: Dependency intelligence gate fails when `MISSION.md` is missing or lacks dependency intelligence context
- [x] AC-3: Dependency intelligence gate fails when dependency manifests exist without expected lockfile or evidence
- [x] AC-4: `comp_gauntlet` includes the dependency intelligence gate
- [x] AC-5: High-tier audit dispatch includes dependency intelligence review
- [x] AC-6: Codex bootstrap installs Dependency Intelligence Auditor TOML and contract artifacts

## Test Strategy

- **Unit tests:** validate checklist schema and validator pass/fail/warn behavior
- **Bootstrap tests:** verify Codex agent TOML and contract generation includes Dependency Intelligence Auditor
- **Manifest tests:** verify `comp_gauntlet` dry-run includes dependency intelligence gate

## Evidence

- [x] `tests/test_dependency_intelligence.py`
- [x] `tests/test_codex_bootstrap.py`
- [x] `tests/test_gate_runner.py`
- [x] Full repository validation run
