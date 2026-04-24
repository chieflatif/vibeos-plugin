# WO-069: Structured Evidence Memory Spike

## Status

`Complete`

## Phase

Phase 13: Evidence Memory Research

## Objective

Determine whether a small, provenance-preserving memory index over existing VibeOS evidence artifacts can materially reduce context/token usage without weakening the Work Order, finding, audit, or gate discipline.

## Scope

### In Scope
- [x] Inventory VibeOS evidence artifacts that are candidates for structured recall
- [x] Define a minimal evidence-memory record schema with source provenance, confidence, freshness, category, and references
- [x] Prototype a local index over existing artifacts using JSON or SQLite only
- [x] Prototype simple graph ranking over artifact references, Work Order links, finding identifiers, and recurring entities
- [x] Benchmark recall against representative `status`, `discover`, `plan`, `build`, and audit workflows
- [x] Produce an adopt/skip recommendation with measured context/token impact and failure modes

### Out of Scope
- Adding Ruflo, AgentDB, Obsidian, Graphify, daemon processes, or external orchestration as runtime dependencies
- Replacing Work Orders, findings, audits, gates, or session-state files
- Claiming automatic enforcement in Codex beyond AGENTS, skills, explicit gates, and Git hooks
- Writing to Claude Code `MEMORY.md` or topic files during this spike
- Persisting personal chat transcripts or broad conversational memory

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-031 | Token budget tracking precedent | Complete |
| WO-049 | Resume and recovery state precedent | Complete |
| WO-056 | Session state and gate manifest infrastructure | Complete |
| WO-068 | Codex enforcement boundary baseline | Complete |
| Claude Code memory docs | External product model evidence | Verified |
| Lucas memory setup review | External approach evidence | Investigated |
| Ruflo review | External approach evidence | Investigated |

## Findings

1. VibeOS already has durable project state through Work Orders, session state, checkpoints, audits, gate outputs, baselines, Product Anchor, Research Registry, and Deviation Log. The opportunity is not generic memory; it is ranked recall of existing evidence with source links.
2. Claude Code's native memory model uses `MEMORY.md` and topic files, with startup loading and on-demand imports. Any future Claude-facing memory should respect that model rather than creating a competing vault.
3. The Lucas memory setup repo is mostly process guidance around Obsidian, chat import, and Graphify. The only potentially significant idea for VibeOS is code/evidence graphing, and local Graphify testing on this repo showed limited value because VibeOS is Markdown/Bash-heavy rather than AST-heavy application code.
4. Ruflo's useful ideas are narrower than its framework surface: native-memory bridging, graph ranking over stored insights, and a clear ledger-vs-executor boundary. Its swarms, daemons, provider routing, and broad token-saving claims are not appropriate for VibeOS without independent evidence.
5. Codex support must remain truthful: memory may suggest relevant evidence, but Codex has no Claude-style runtime hooks or isolated subagent enforcement.

## Impact Analysis

- **Files created:** `spikes/wo-069/evidence_memory.py`, `docs/planning/WO-069-structured-evidence-memory-spike-report.md`
- **Files modified:** `docs/planning/WO-069-structured-evidence-memory-spike.md`, `docs/planning/WO-INDEX.md`, `docs/planning/DEVELOPMENT-PLAN.md`
- **Systems affected:** no runtime behavior changed; planning now has evidence to justify a follow-up implementation WO

## Acceptance Criteria

- [x] AC-1: Evidence artifact inventory identifies canonical sources, non-canonical sources, ownership, freshness rules, and exclusion rules
- [x] AC-2: Proposed memory schema includes `source_path`, source locator, record type, confidence, freshness/expiry, tags, references, and reason-for-inclusion
- [x] AC-3: Prototype indexes at least Work Orders, session-state schema/state, audit reports, gate manifests/results, Research Registry, Product Anchor, Deviation Log, and checkpoints where present
- [x] AC-4: Prototype recall returns only source-cited records and never emits unsupported synthesized facts
- [x] AC-5: Benchmark compares baseline manual/context loading against indexed recall on at least five representative workflows
- [x] AC-6: Adopt recommendation requires at least 2x reduction in relevant context/read tokens or at least 40% workflow token reduction with zero missed critical evidence in the benchmark set
- [x] AC-7: Skip recommendation is accepted if thresholds are not met, maintenance cost is high, or recall quality risks stale or uncited claims
- [x] AC-8: Final report explicitly states whether to proceed, defer, or abandon the memory index and lists the smallest next implementation WO if proceeding

## Test Strategy

- **Unit tests:** `python3 -m py_compile spikes/wo-069/evidence_memory.py`
- **Integration tests:** `python3 spikes/wo-069/evidence_memory.py build --repo . --out /tmp/wo-069-evidence-index.json`
- **Real-path verification:** benchmarked six representative VibeOS workflow queries against expected critical evidence
- **Verification command:** `python3 spikes/wo-069/evidence_memory.py benchmark --repo . --top 16 --out /tmp/wo-069-benchmark-final.json`

## Implementation Plan

### Step 1: Inventory Existing Evidence
- Map every durable VibeOS artifact that can support recall
- Classify each artifact as canonical, derived, transient, or excluded
- Expected outcome: source map and freshness policy

### Step 2: Design Minimal Record Schema
- Define evidence-memory records with provenance, confidence, freshness, and references
- Define exclusion rules for low-value, stale, private, generated, or uncited records
- Expected outcome: schema proposal and validation rules

### Step 3: Build Disposable Prototype
- Create a local JSON or SQLite indexer in a spike-only path
- Ingest existing repo artifacts without mutating source documents
- Expected outcome: reproducible index build and query command

### Step 4: Add Simple Graph Ranking
- Link records through WO IDs, finding IDs, file paths, audit names, decision names, and explicit references
- Rank by direct match, freshness, confidence, graph centrality, and workflow relevance
- Expected outcome: ranked recall with citations and explainable scoring

### Step 5: Benchmark Against Real Workflows
- Measure baseline context/read volume for representative workflows
- Compare indexed recall against baseline for relevance, completeness, and token/read reduction
- Expected outcome: quantified adopt/skip recommendation

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: The spike is justified because existing durable evidence is scattered across WOs, skills, audit reports, manifests, and runtime state; the opportunity is recall, not generic chat memory.
- Test status: Benchmark cases and adoption threshold defined before implementation.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Prototype is isolated under `spikes/wo-069/`, uses only local file reads and JSON output, and does not modify VibeOS runtime behavior.
- Test status: Syntax, index build, and benchmark commands selected.

### Pre-Commit Audit
- Status: `complete`
- Findings: The first benchmark failed; source diversification, normalized matching, concise recall payloads, and large-chunk penalties were required before the spike cleared the threshold. Those constraints are now documented as required design.
- Test status: Final benchmark passed with 57.0% average recall payload reduction, 2.82x average ratio, and zero critical evidence misses.

## Evidence

- [x] Research inventory complete
- [x] Prototype complete or explicitly rejected with evidence
- [x] Benchmarks complete
- [x] Recommendation documented
- [x] No external runtime dependency introduced
- [x] Documentation updated if proceeding to implementation

Spike output:
- Prototype: `spikes/wo-069/evidence_memory.py`
- Report: `docs/planning/WO-069-structured-evidence-memory-spike-report.md`
- Index build result: 1,537 records from 137 sources
- Final benchmark: 57.0% average recall payload reduction, 2.82x average baseline-to-recall ratio, 0 critical misses

Reference material reviewed before creating this WO:
- Claude Code memory documentation: `https://code.claude.com/docs/en/memory`
- Lucas memory setup repo: `https://github.com/lucasrosati/claude-code-memory-setup`
- Ruflo repo: `https://github.com/ruvnet/ruflo`
