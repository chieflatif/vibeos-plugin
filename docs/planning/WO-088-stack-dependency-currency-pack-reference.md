# WO-088: Stack Dependency Currency Pack Reference

## Status

`Complete`

## Phase

Phase 18: Stack Dependency Currency Packs

## Objective

Add machine-readable stack dependency currency packs so VibOS Comp can require concrete current-source evidence for the runtime, framework, SDK, auth, database, AI, and deployment surfaces that commonly break when AI agents rely on stale model memory.

## Scope

### In Scope
- [x] Add `stack-dependency-currency.json`
- [x] Cover TypeScript/Node, frontend apps, Python/FastAPI, AI SDKs, auth/security packages, database/ORM packages, and deployment runtimes
- [x] Link stack variants to their currency packs
- [x] Update dependency evidence template and Comp mission guidance to reference stack currency packs

### Out of Scope
- Hardcoding current package or runtime version numbers
- Replacing project-specific source verification
- Covering every language ecosystem in the first pack

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-086 | Dependency Intelligence Auditor and Gate | Complete |
| WO-087 | Dependency Scorecard and Evidence Integration | Complete |

## Findings

1. Generic dependency evidence is not enough when failures are stack-specific.
2. Hardcoded latest versions become stale, so the pack should define required evidence, source targets, and commands rather than version numbers.
3. AI SDK, auth, database, and deployment dependencies carry outsized risk and need first-class evidence prompts.

## Acceptance Criteria

- [x] AC-1: Currency pack JSON is valid and machine-readable
- [x] AC-2: Common stack and high-impact dependency surfaces are represented
- [x] AC-3: Stack variants reference currency pack identifiers
- [x] AC-4: Evidence template asks for stack currency pack proof

## Evidence

- [x] `plugins/vibeos/reference/comp/stack-dependency-currency.json`
- [x] `tests/test_comp_blueprint.py`
- [x] Full repository validation run
