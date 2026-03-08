# WO-051: Midstream Baseline Bootstrap

## Status

`Complete`

## Phase

Phase 8: Resilience & Transparency

## Objective

Close the gap between guided audit completion and first build on midstream projects: define how the initial baseline is created from findings-registry.json, wire up the migration script for upgrading projects, and define the explicit syntax for skipping Phase 0 remediation.

## Scope

### In Scope
- [x] Define initial baseline creation: after plan skill writes findings-registry.json, create `.vibeos/baselines/midstream-baseline.json` from it
- [x] Add baseline creation step to plan skill Step 1c (after findings-registry.json is written)
- [x] Explain baseline creation to user: "I've established a quality baseline from your audit — future builds will only flag new issues, not these existing ones"
- [x] Wire migrate-baseline.sh into build skill: if old count-based baseline detected, auto-migrate
- [x] Build skill Step 7: handle "no baseline exists" gracefully — explain to user, offer to create from current state
- [x] baseline-check.sh: add `create` subcommand to bootstrap baseline from findings-registry.json
- [x] Define Phase 0 skip syntax: `/vibeos:build --skip-phase0` or user confirmation at decision point
- [x] Phase 0 skip: log as explicit risk acceptance in `.vibeos/build-log.md` and ACCEPTED-RISKS.md
- [x] Phase 0 skip explanation: present consequences before allowing skip (per communication contract)

### Out of Scope
- Changing findings-registry.json schema (WO-042 owns this)
- Changing baseline-check.sh comparison logic (WO-043 owns this)
- Automated remediation

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 7 | All Phase 7 WOs | Complete |

## Impact Analysis

- **Files modified:** `skills/plan/SKILL.md` (add baseline creation after Step 1c), `skills/build/SKILL.md` (auto-migration, no-baseline handling, Phase 0 skip syntax), `convergence/baseline-check.sh` (add `create` subcommand)
- **Files created:** None
- **Systems affected:** Midstream onboarding flow, baseline system, Phase 0 enforcement

## Acceptance Criteria

- [x] AC-1: After guided audit completes, initial midstream baseline is created automatically
- [x] AC-2: User sees explanation of what baseline means and how it protects them
- [x] AC-3: Old count-based baselines auto-migrated to finding-level on first build
- [x] AC-4: Build skill handles "no baseline exists" with clear user message and recovery path
- [x] AC-5: baseline-check.sh supports `create` subcommand for bootstrap
- [x] AC-6: Phase 0 skip has explicit syntax (build skill argument or decision point)
- [x] AC-7: Phase 0 skip logs risk acceptance with justification
- [x] AC-8: Phase 0 skip shows consequences before allowing (communication contract compliant)
- [x] AC-9: Greenfield projects unaffected (no baseline needed until midstream audit runs)

## Test Strategy

- **Bootstrap:** Run midstream flow (discover → plan with audit → build), verify baseline created automatically
- **Migration:** Create a project with count-based baseline, run build, verify auto-migration to finding-level
- **No baseline:** Run build on midstream project without baseline, verify graceful handling
- **Phase 0 skip:** Attempt to skip Phase 0, verify consequences shown and decision logged

## Implementation Plan

### Step 1: Add `create` Subcommand to baseline-check.sh
```bash
baseline-check.sh create \
  --baseline-file ".vibeos/baselines/midstream-baseline.json" \
  --source-findings ".vibeos/findings-registry.json"
```
- Read findings-registry.json
- Generate baseline with all current findings as "tracked" (not new)
- Write to baseline file with version 2.0 schema
- Output: `{"result": "CREATED", "findings_baselined": N, "baseline_file": "path"}`

### Step 2: Add Baseline Creation to Plan Skill Step 1c
After Step 1c-4 (write findings-registry.json) and Step 1c-5 (write midstream-report.md):
- Step 1c-6: Create initial baseline
  ```bash
  mkdir -p .vibeos/baselines
  bash "${CLAUDE_PLUGIN_ROOT}/convergence/baseline-check.sh" create \
    --baseline-file ".vibeos/baselines/midstream-baseline.json" \
    --source-findings ".vibeos/findings-registry.json"
  ```
- Tell user: "I've established a quality baseline with [N] tracked findings. From now on, only new issues will be flagged — these existing ones are tracked and won't block your builds."

### Step 3: Add Auto-Migration to Build Skill Step 7
Before running baseline-check.sh in finding-level mode:
1. Check if baseline file exists
2. If exists: check version field
3. If version 1.0 (count-based): run migrate-baseline.sh automatically
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/convergence/migrate-baseline.sh" \
     --input ".vibeos/baselines/midstream-baseline.json" \
     --output ".vibeos/baselines/midstream-baseline.json"
   ```
4. Tell user: "I upgraded your quality baseline from the old format to the new finding-level format. This gives you more precise tracking of individual issues."

### Step 4: Handle No-Baseline Case in Build Skill Step 7
If no baseline file exists when finding-level check runs:
- Don't fail silently
- Tell user: "No quality baseline exists yet. This means all current issues will be flagged as new."
- Offer: "I can create a baseline from the current state — existing issues become tracked, only new ones block. Want me to do that?"
- If yes: run baseline-check.sh create, then proceed
- If no: proceed with all findings treated as new (stricter)

### Step 5: Define Phase 0 Skip Syntax
In build skill Step 1 (Phase 0 enforcement section):
- When Phase 0 has incomplete fix-now WOs, present consequence-aware decision:
  > "Phase 0 has [N] unresolved remediation items including [top finding summary].
  >
  > Your options:
  > 1. **Build Phase 0 first** — Fix the critical issues before feature work. This means your codebase starts clean. Recommended for security-sensitive projects.
  > 2. **Skip Phase 0 for now** — Start feature work immediately. The [N] issues remain unfixed and could compound as you add code. You can return to them later with `/vibeos:build` (Phase 0 WOs will still be there). This decision will be logged as a risk acceptance.
  >
  > I recommend option 1 because [specific reasoning based on finding severity]."
- If user chooses skip: log to build-log.md and append to ACCEPTED-RISKS.md with justification

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: End-to-end midstream flow validation
- Risk: Auto-migration could lose precision if count-based baseline had manual adjustments

## Evidence

- [x] Initial baseline created automatically after guided audit
- [x] User explanation of baseline concept
- [x] Auto-migration from count-based to finding-level works
- [x] No-baseline case handled gracefully with user choice
- [x] Phase 0 skip shows consequences and logs acceptance
