# WO-041: Architecture-First Midstream Discovery

## Status

`Draft`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

When the plugin detects existing code, the first action is to infer the architecture from the codebase — directory structure, import graph, framework patterns, database connections, API surface — and produce draft product documents (architecture doc, technical spec, architecture outline) that the user validates before any audits or planning proceed.

## Scope

### In Scope
- [ ] Reverse-engineer architecture from existing code (imports, directories, framework patterns)
- [ ] Generate draft `docs/product/ARCHITECTURE-OUTLINE.md` from code analysis
- [ ] Generate draft `docs/product/TECHNICAL-SPEC.md` from detected stack
- [ ] Generate draft `docs/product/PRD.md` skeleton from code structure and README
- [ ] Generate `project-definition.json` with inferred values and confidence levels
- [ ] Present inferred architecture to user: "Here's what I see in your codebase. Is this right?"
- [ ] User validates, corrects, or extends the architecture document
- [ ] Identify architectural patterns: layered, modular, monolith, microservice, MVC, etc.
- [ ] Map module boundaries, public APIs, internal interfaces
- [ ] Detect database connections, ORMs, migration frameworks
- [ ] Detect auth patterns (middleware, decorators, session management)
- [ ] Detect test infrastructure (framework, directory, naming convention, coverage)
- [ ] Update `skills/discover/SKILL.md` with midstream discovery flow (major: adds complete alternate code path — the current skill is purely greenfield with no concept of existing code; this adds early detection branching and a full midstream Steps 2-5 equivalent)
- [ ] Update `skills/plan/SKILL.md` Step 1b: **replace** the existing 55-line midstream logic (run-gates-then-baseline) with architecture-first requirement — existing Step 1b is superseded by the WO-041/042/043/044 pipeline
- [ ] Handle PRD.md collision: if `docs/product/PRD.md` already exists (from prior `/vibeos:discover` run), merge inferred data rather than overwrite

### Out of Scope
- Running audits (WO-042)
- Baseline creation (WO-043)
- Remediation planning (WO-044)
- Code modification or fixes

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 6 complete | Must complete first | Complete |

## Impact Analysis

- **Files modified:** `skills/discover/SKILL.md` (major: adds complete midstream alternate path with early detection branch, code analysis steps, and user validation — the current skill is purely greenfield), `skills/plan/SKILL.md` (Step 1b: **replaces** existing midstream logic with architecture-first requirement)
- **Files created:** None at plugin level — artifacts are created in the target project (`docs/product/ARCHITECTURE-OUTLINE.md`, `docs/product/TECHNICAL-SPEC.md`, `docs/product/PRD.md`, `project-definition.json`)
- **Systems affected:** Discovery skill (structural change), plan skill (Step 1b replacement), architecture auditor (now has a document to audit against)
- **Note:** WO-046 also modifies `skills/discover/SKILL.md` to add onboarding. WO-041 should be implemented first; WO-046 wraps its onboarding check around WO-041's midstream branch.

## Acceptance Criteria

- [ ] AC-1: Existing code detected and directory structure mapped
- [ ] AC-2: Import graph analyzed — modules, dependencies, layers identified
- [ ] AC-3: Framework and database patterns detected with confidence levels
- [ ] AC-4: Draft ARCHITECTURE-OUTLINE.md generated from code analysis
- [ ] AC-5: Draft TECHNICAL-SPEC.md generated with detected stack
- [ ] AC-6: Draft project-definition.json generated with inferred values
- [ ] AC-7: User presented with inferred architecture and asked to validate/correct
- [ ] AC-8: Validated architecture document becomes the anchor for all subsequent audits
- [ ] AC-9: Generated ARCHITECTURE-OUTLINE.md is in the path the architecture auditor checks (`docs/product/ARCHITECTURE-OUTLINE.md`), enabling it to audit against a real document instead of flagging "missing"
- [ ] AC-10: Greenfield projects unaffected — existing discover flow unchanged

## Test Strategy

- **Integration:** Run midstream discovery on a project with known architecture, verify inferred architecture matches
- **Validation:** Verify user is asked to validate and can correct inferences
- **Greenfield:** Verify existing discover flow unchanged for empty projects

## Implementation Plan

### Step 1: Add Midstream Path to Discover Skill
Update `skills/discover/SKILL.md` to detect existing code at the start:
- If existing code found: switch to midstream discovery flow
- If empty project: continue with existing greenfield flow

### Step 2: Implement Code Analysis
The midstream discovery flow:
1. Map directory structure (source dirs, test dirs, config files, docs)
2. Detect language and framework from indicators (package.json, requirements.txt, go.mod, etc.)
3. Analyze import graph — build module dependency map
4. Detect patterns: layered architecture, MVC, service-repository, etc.
5. Identify database layer (ORM, raw SQL, migration framework)
6. Identify auth layer (middleware, decorators, session management)
7. Identify API surface (routes, endpoints, controllers)
8. Identify test infrastructure (framework, patterns, coverage)

### Step 3: Generate Draft Documents
From code analysis, generate:
- `docs/product/ARCHITECTURE-OUTLINE.md` — layers, modules, dependencies, boundaries
- `docs/product/TECHNICAL-SPEC.md` — detected stack, frameworks, database, auth
- `docs/product/PRD.md` — skeleton with inferred product scope from code structure. **Collision handling:** if PRD.md already exists (from prior `/vibeos:discover` run), merge inferred data into the existing document rather than overwriting
- `project-definition.json` — with `source: "inferred"` and confidence levels

### Step 4: User Validation
Present the inferred architecture to the user:
> "I've analyzed your codebase and here's what I found:
>
> **Architecture:** [pattern] with [N] modules across [M] layers
> **Stack:** [language] + [framework] + [database]
> **Module map:**
> - [module]: [purpose] ([N] files, depends on [deps])
> - ...
>
> **What I'm confident about:** [high-confidence inferences]
> **What I'm less sure about:** [low-confidence inferences, with questions]
>
> Is this accurate? What should I add or correct?"

After user validates, write the final architecture document.

### Step 5: Update Plan Skill
**Replace** the existing `skills/plan/SKILL.md` Step 1b midstream logic (lines 49-103, which currently runs gates, dispatches 5 audit agents, stores baselines, and creates remediation WOs) with architecture-first requirement:
- Before running any audits, check if architecture documents exist
- If not: tell user to run `/vibeos:discover` first (which now handles midstream)
- Architecture document is a prerequisite for meaningful audits
- The existing Step 1b gate/audit/baseline flow is superseded by the WO-042/043/044 pipeline
- **Interim limitation:** After WO-041 replaces Step 1b but before WO-044 is implemented, midstream projects will not have remediation WO creation. This is acceptable because the full pipeline (WO-041 → WO-042 → WO-043 → WO-044) must all be implemented before the midstream flow is functional end-to-end.

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — run on project with known architecture
- Risk: Inference quality depends on code conventions; unconventional codebases may need more user correction

## Evidence

- [ ] Code analysis produces accurate module map
- [ ] Architecture document matches actual code structure
- [ ] User validation loop works
- [ ] Architecture auditor has a document to audit against
- [ ] Greenfield flow unaffected
