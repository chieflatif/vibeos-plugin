# WO-009: /vibeos:plan Skill

## Status

`Draft`

## Phase

Phase 2: Product Discovery & Planning

## Objective

Implement the `/vibeos:plan` skill that runs the PROJECT-INTAKE.md questionnaire, applies the decision engine, and generates a complete DEVELOPMENT-PLAN.md with phased work orders.

## Scope

### In Scope
- [ ] Create `skills/plan.md` implementing the full planning flow
- [ ] Run PROJECT-INTAKE.md 18-question questionnaire
- [ ] Pre-fill answers from project-definition.json when available
- [ ] Apply decision engine trees: gate-selection, phase-selection, hook-selection, architecture-rules, compliance-mapping
- [ ] Generate DEVELOPMENT-PLAN.md with phased, ordered work orders
- [ ] Run mechanical setup: create project directories, copy gate scripts, generate manifests
- [ ] Generate WO-INDEX.md tracking all work orders
- [ ] Enforce communication contract throughout

### Out of Scope
- Product discovery (WO-008)
- Autonomy negotiation (WO-011)
- Build orchestration (WO-019)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-008 | Must complete first | Draft |
| VibeOS-2 PROJECT-INTAKE.md | Source material | Exists |
| VibeOS-2 decision-engine/ | Source material | Exists |

## Impact Analysis

- **Files created:** skills/plan.md, generated DEVELOPMENT-PLAN.md, WO-INDEX.md, project structure
- **Systems affected:** Decision engine integration, project scaffolding

## Acceptance Criteria

- [ ] AC-1: All 18 intake questions asked (or pre-filled from project-definition.json)
- [ ] AC-2: Decision engine trees applied correctly based on intake answers
- [ ] AC-3: DEVELOPMENT-PLAN.md generated with correct phase ordering
- [ ] AC-4: Each WO in plan has: title, objective, dependencies, acceptance criteria
- [ ] AC-5: Gate scripts copied to target project
- [ ] AC-6: Manifests generated (gate-manifest.json, hook-manifest.json)
- [ ] AC-7: WO-INDEX.md created with all WOs listed
- [ ] AC-8: Pre-fill works — questions with known answers from discovery are not re-asked

## Test Strategy

- **Integration:** Run plan skill after discover, verify DEVELOPMENT-PLAN.md generated
- **Decision engine:** Verify correct gates/phases selected for different project types
- **Pre-fill:** Run with project-definition.json present, verify questions skipped

## Implementation Plan

### Step 1: Create Skill File
- Define skill metadata
- Map PROJECT-INTAKE.md flow into skill steps
- Integrate pre-fill logic from project-definition.json

### Step 2: Implement Decision Engine Integration
- Read decision tree files
- Apply gate-selection based on project type and compliance needs
- Apply phase-selection based on project complexity
- Apply hook-selection based on workflow requirements
- Apply architecture-rules based on tech stack
- Apply compliance-mapping based on regulatory needs

### Step 3: Implement Plan Generation
- Generate DEVELOPMENT-PLAN.md with phases and WOs
- Generate WO-INDEX.md
- Order WOs by dependencies

### Step 4: Implement Mechanical Setup
- Create project directory structure
- Copy gate scripts from bundled assets
- Generate manifests

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — full flow from intake to plan generation
- Risk: Decision engine complexity — tree logic must be thoroughly tested for each combination

## Evidence

- [ ] Skill file created
- [ ] DEVELOPMENT-PLAN.md generated from test run
- [ ] Decision engine correctly selects gates/phases for test cases
- [ ] Pre-fill from project-definition.json works
- [ ] Mechanical setup creates correct directory structure
