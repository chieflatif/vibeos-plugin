# WO-070: Evidence Recall Indexer and Query Command

## Status

`Complete`

## Phase

Phase 13: Evidence Memory Research

## Objective

Add a small VibeOS-native evidence recall utility that indexes existing governance artifacts and returns bounded, source-cited results without external dependencies or runtime enforcement claims.

## Scope

### In Scope
- [x] Add a local evidence index builder over canonical VibeOS planning, audit, skill, manifest, and runtime state artifacts
- [x] Store generated indexes under `.vibeos/cache/`
- [x] Add a query entry point that returns cited, bounded recall results
- [x] Prefer current project artifacts over lower-confidence templates
- [x] Add tests for citation, bounded excerpts, cache writing, and source diversification
- [x] Document the generated cache artifact

### Out of Scope
- Claude Code `MEMORY.md` synchronization
- Ruflo, AgentDB, Graphify, Obsidian, vector databases, daemons, or network services
- Automatic runtime enforcement in Codex
- Replacing Work Orders, findings, audits, gates, or session state
- Rewriting existing skills to depend on recall output

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-069 | Evidence-backed spike | Complete |
| WO-031 | Token budget tracking precedent | Complete |
| WO-056 | Session state and gate manifest infrastructure | Complete |
| WO-068 | Codex enforcement boundary baseline | Complete |

## Findings

1. WO-069 measured a 57%+ average recall payload reduction with zero critical evidence misses when recall used source diversification, bounded excerpts, and source citations.
2. The first WO-069 benchmark failed until noisy duplicate chunks from large files were suppressed, so source diversification and bounded excerpts are required correctness behavior.
3. Runtime memory must remain advisory. The query command can point agents at evidence, but it cannot become a substitute for reading source artifacts before high-risk edits.

## Anchor Alignment

This supports the product promise by helping VibeOS preserve project context without replaying excessive files. It aligns with the engineering principles by keeping recall deterministic, local, source-cited, and non-authoritative.

## Research & Freshness

- Current evidence required: no new external product behavior is introduced.
- Last verified on: 2026-04-24.
- Sources to verify: WO-069 benchmark report and local repository artifacts.
- Prompt engineering profile: N/A — deterministic local utility, not prompt behavior.

## Approved Deviations

None.

## Impact Analysis

- **Files created:** `plugins/vibeos/scripts/evidence-recall.py`, `tests/test_evidence_recall.py`
- **Files modified:** `docs/FILE-INVENTORY.md`, `docs/planning/DEVELOPMENT-PLAN.md`, `docs/planning/WO-INDEX.md`, this WO
- **Systems affected:** Adds an explicit evidence recall utility; no build, audit, gate, hook, or Codex enforcement behavior changes automatically

## Acceptance Criteria

- [x] AC-1: `evidence-recall.py index` builds a JSON index from canonical VibeOS evidence sources
- [x] AC-2: Default index output path is `.vibeos/cache/evidence-recall-index.json`
- [x] AC-3: `evidence-recall.py query` returns source-cited results with bounded excerpts
- [x] AC-4: Results diversify by source file by default to avoid noisy duplicate chunks
- [x] AC-5: Every record includes source path, source locator, type, confidence, freshness, tags, references, and reason for inclusion
- [x] AC-6: Tests cover indexing, query citation, excerpt bounding, cache writing, and source diversification
- [x] AC-7: The utility runs without network access and without third-party packages

## Test Strategy

- **Unit tests:** `python3 -m unittest tests.test_evidence_recall`
- **Syntax tests:** `python3 -m py_compile plugins/vibeos/scripts/evidence-recall.py tests/test_evidence_recall.py`
- **Real-path verification:** build an index from this repo and query for evidence memory terms
- **Verification command:** `python3 plugins/vibeos/scripts/evidence-recall.py query "evidence memory token" --repo . --fresh --limit 5`

## Implementation Plan

### Step 1: Add Indexer
- Add a Python script that scans canonical evidence sources
- Emit compact records with bounded excerpts and source locators
- Expected outcome: reproducible local index

### Step 2: Add Query Command
- Rank results by term overlap, tags, references, confidence, and graph score
- Diversify results by source file
- Expected outcome: concise cited recall payloads

### Step 3: Add Tests
- Use temporary fixture projects so tests do not depend on this repo's full contents
- Verify cache path, citations, excerpts, and diversification
- Expected outcome: deterministic test coverage for the utility's core behavior

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: WO-069 provides sufficient measured evidence for this implementation.
- Test status: Acceptance and verification commands defined before implementation.

### Pre-Implementation Audit
- Status: `complete`
- Findings: The implementation is scoped to a local utility and generated cache. No runtime enforcement or external memory dependency is introduced.
- Test status: Unit, syntax, and real-path checks selected.

### Pre-Commit Audit
- Status: `complete`
- Findings: The utility stays advisory, cited, bounded, and local. Source diversification is implemented because WO-069 showed it was required to avoid noisy recall.
- Test status: Unit tests, syntax checks, real-path query, and diff hygiene passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Real-path query verified
- [x] Documentation updated
- [x] No external runtime dependency introduced

Verification commands run:
- `python3 -m py_compile plugins/vibeos/scripts/evidence-recall.py tests/test_evidence_recall.py`
- `python3 -m unittest tests.test_evidence_recall`
- `python3 plugins/vibeos/scripts/evidence-recall.py index --repo . --out /tmp/vibeos-evidence-recall-index.json`
- `python3 plugins/vibeos/scripts/evidence-recall.py query "evidence memory token" --repo . --fresh --limit 5`
- `git diff --check`
