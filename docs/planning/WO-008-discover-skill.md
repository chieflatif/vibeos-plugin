# WO-008: /vibeos:discover Skill

## Status

`Complete`

## Phase

Phase 2: Product Discovery & Planning

## Objective

Implement the `/vibeos:discover` skill that runs the PRODUCT-DISCOVERY.md flow to capture user intent and generate all foundational product documents.

## Scope

### In Scope
- [x] Create `skills/discover/SKILL.md` implementing the full product discovery flow
- [x] Capture intent: what the user wants to build, in their own words
- [x] Determine product shape (web app, API, CLI, mobile, etc.)
- [x] Run targeted follow-up questions based on product shape
- [x] Generate PROJECT-IDEA.md from captured intent
- [x] Generate project-definition.json (structured, machine-readable)
- [x] Generate PRODUCT-BRIEF.md (plain-English summary)
- [x] Generate PRD.md (product requirements document)
- [x] Generate TECHNICAL-SPEC.md (technical specification)
- [x] Generate ARCHITECTURE-OUTLINE.md (high-level architecture)
- [x] Generate ASSUMPTIONS-AND-RISKS.md
- [x] Enforce communication contract throughout all interactions

### Out of Scope
- Project intake questionnaire (WO-009)
- Decision engine application (WO-009)
- DEVELOPMENT-PLAN.md generation (WO-009)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 1 complete | Must complete first | Draft |
| VibeOS-2 PRODUCT-DISCOVERY.md | Source material | Exists |
| Communication contract (WO-006) | Must be enforced | Draft |

## Impact Analysis

- **Files created:** skills/discover/SKILL.md, templates for generated artifacts
- **Systems affected:** Skill dispatch, document generation pipeline

## Acceptance Criteria

- [x] AC-1: Skill captures user intent through conversational flow
- [x] AC-2: Product shape correctly identified from user description
- [x] AC-3: Follow-up questions are targeted to product shape (not generic)
- [x] AC-4: All 7 artifacts generated with correct structure
- [x] AC-5: project-definition.json is valid JSON with all required fields
- [x] AC-6: Communication contract enforced — plain English, no jargon, outcome language
- [x] AC-7: Artifacts stored in target project's docs/ directory

## Test Strategy

- **Integration:** Run discover skill with sample project idea, verify all 7 artifacts generated
- **Validation:** Each artifact follows its expected structure
- **Contract:** Verify all user-facing output uses communication contract language

## Implementation Plan

### Step 1: Create Skill File
- Define skill metadata and entry instructions
- Map the PRODUCT-DISCOVERY.md flow into skill steps
- Embed communication contract requirements

### Step 2: Implement Conversational Flow
- Intent capture phase: open-ended question, active listening
- Product shape determination: classify from user description
- Follow-up questions: branching by product shape

### Step 3: Implement Artifact Generation
- Template each artifact with required sections
- Generate from captured data, not from assumptions
- Validate project-definition.json schema

### Step 4: Integration Test
- Run end-to-end with sample input
- Verify all artifacts present and well-formed

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — run full flow, verify 7 artifacts
- Risk: Conversational flow quality depends on prompt engineering; may need iteration

## Evidence

- [x] Skill file created
- [x] All 7 artifacts generated from test run
- [x] project-definition.json validates against schema
- [x] Communication contract language verified in all outputs
