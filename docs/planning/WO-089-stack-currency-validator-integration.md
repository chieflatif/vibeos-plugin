# WO-089: Stack Currency Validator Integration

## Status

`Complete`

## Phase

Phase 18: Stack Dependency Currency Packs

## Objective

Integrate stack dependency currency packs into `validate-dependency-intelligence.py` so detected stacks produce blocking findings when dependency evidence omits required runtime, framework, SDK, auth, database, AI, or deployment context.

## Scope

### In Scope
- [x] Load `.vibeos/reference/comp/stack-dependency-currency.json` when present
- [x] Detect stack packs from manifests, known dependency names, and deployment files
- [x] Emit blocking stack evidence findings when required pack terms are missing
- [x] Include detected packs in JSON validator output
- [x] Add validator tests for missing and passing stack currency evidence

### Out of Scope
- Online package registry calls during validation
- Exhaustive dependency graph solving
- Automatic source verification without project-provided evidence

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-088 | Stack Dependency Currency Pack Reference | Complete |

## Findings

1. The validator needs to enforce pack evidence only when pack metadata is installed, preserving compatibility for older projects.
2. Stack detection should be deterministic and local: manifests, known dependency names, and deployment files.
3. JSON output should expose detected packs so agents can explain which stack-specific evidence is missing.

## Acceptance Criteria

- [x] AC-1: Validator detects TypeScript/Node and frontend packs from `package.json`
- [x] AC-2: Validator blocks when detected pack evidence is missing
- [x] AC-3: Validator passes when stack currency evidence is present
- [x] AC-4: Tests cover pack parsing, detection, and enforcement

## Evidence

- [x] `plugins/vibeos/scripts/validate-dependency-intelligence.py`
- [x] `tests/test_dependency_intelligence.py`
- [x] Full repository validation run
