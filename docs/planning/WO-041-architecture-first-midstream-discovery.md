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
- [ ] Update `skills/discover/SKILL.md` with midstream discovery flow
- [ ] Update `skills/plan/SKILL.md` Step 1b to require architecture-first before audits

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

- **Files modified:** `skills/discover/SKILL.md` (add midstream discovery path), `skills/plan/SKILL.md` (Step 1b requires architecture-first)
- **Files created:** None at plugin level — artifacts are created in the target project
- **Systems affected:** Discovery skill, plan skill, architecture auditor (now has a document to audit against)

## Acceptance Criteria

- [ ] AC-1: Existing code detected and directory structure mapped
- [ ] AC-2: Import graph analyzed — modules, dependencies, layers identified
- [ ] AC-3: Framework and database patterns detected with confidence levels
- [ ] AC-4: Draft ARCHITECTURE-OUTLINE.md generated from code analysis
- [ ] AC-5: Draft TECHNICAL-SPEC.md generated with detected stack
- [ ] AC-6: Draft project-definition.json generated with inferred values
- [ ] AC-7: User presented with inferred architecture and asked to validate/correct
- [ ] AC-8: Validated architecture document becomes the anchor for all subsequent audits
- [ ] AC-9: Architecture auditor can now audit against a real document (not just flag "missing")
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
- `docs/product/PRD.md` — skeleton with inferred product scope from code structure
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
Update `skills/plan/SKILL.md` Step 1b:
- Before running any audits, check if architecture documents exist
- If not: tell user to run `/vibeos:discover` first (which now handles midstream)
- Architecture document is a prerequisite for meaningful audits

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
