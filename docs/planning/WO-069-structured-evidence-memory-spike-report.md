# WO-069 Structured Evidence Memory Spike Report

## Recommendation

Proceed with a narrow VibeOS-native evidence recall implementation. Do not adopt Ruflo, AgentDB, Obsidian, Graphify, daemons, swarms, or broad chat-memory import.

The spike cleared the significance threshold when measured as a source-cited recall preflight: six representative workflows averaged a 57.0% recall payload reduction, a 2.82x baseline-to-recall ratio, and zero critical evidence misses.

This does not prove that every future task will use 57% fewer tokens. It proves that a small, local index can usually identify the right VibeOS evidence sources with much less context than rereading the baseline file set.

## What Was Built

Prototype:

- `spikes/wo-069/evidence_memory.py`

The prototype:

- scans canonical VibeOS evidence artifacts
- emits source-cited records with provenance, confidence, freshness, tags, references, and inclusion rationale
- computes a simple graph score from Work Order IDs, file references, finding IDs, and artifact references
- runs deterministic query ranking with source diversification
- benchmarks recall payloads against representative workflow baselines

No runtime hooks, external services, package dependencies, or `.vibeos` source mutations were introduced.

## Evidence Inventory

### Canonical Sources

These are appropriate for production recall:

| Source | Use |
|---|---|
| `docs/planning/WO-*.md` | Work Order contracts, findings, acceptance criteria, implementation evidence |
| `docs/planning/WO-INDEX.md` | Work Order status and dependencies |
| `docs/planning/DEVELOPMENT-PLAN.md` | Phase roadmap and dependency model |
| `docs/planning/POST-PHASE-*.md` | Phase-level audit evidence |
| `docs/planning/PLANNING-AUDIT-*.md` | Planning audit findings and dispositions |
| `docs/planning/SPIKE-RESULTS.md` | Prior architecture validation evidence |
| `docs/FILE-INVENTORY.md` | Generated artifact map |
| `docs/USER-COMMUNICATION-CONTRACT.md` | User-facing explanation contract |
| `plugins/vibeos/skills/*/SKILL.md` | Workflow behavior contracts |
| `plugins/vibeos/reference/session-state-schema.md` | Session-state schema |
| `plugins/vibeos/quality-gate-manifest.json` | Gate inventory and configuration |
| `plugins/vibeos/hook-manifest.json` | Hook inventory and configuration |

### Local Runtime Sources

These should be indexed when present in target projects:

| Source | Use |
|---|---|
| `.vibeos/session-state.json` | Current or latest session state |
| `.vibeos/build-log.md` | Build history |
| `.vibeos/checkpoints/*.json` | Mid-WO resume state |
| `.vibeos/baselines/*.json` | Quality baselines |
| `.vibeos/findings-registry.json` | Finding-level dispositions and baseline links |
| `.vibeos/audit-reports/*` | Audit report evidence |
| `.vibeos/session-audits/*` | Session closeout evidence |

### Template Sources

These are useful with lower confidence because they describe install-time templates rather than current project facts:

| Source | Use |
|---|---|
| `plugins/vibeos/reference/governance/*.ref` | Governance templates |
| `plugins/vibeos/reference/product/*.ref` | Product artifact templates |
| `plugins/vibeos/reference/codex/**` | Codex-facing install templates |

### Exclusions

Production recall should exclude private chat transcripts, broad conversational memory, unverified external summaries, generated dependency/vendor directories, `.git`, `node_modules`, raw temporary logs, and any record without a source path and locator.

## Record Schema

Minimum production record:

```json
{
  "id": "stable hash",
  "source_path": "docs/planning/WO-069-structured-evidence-memory-spike.md",
  "source_locator": "docs/planning/WO-069-structured-evidence-memory-spike.md:58",
  "record_type": "work_order",
  "canonicality": "canonical",
  "title": "Acceptance Criteria",
  "content_excerpt": "bounded excerpt",
  "confidence": 0.95,
  "freshness": "current",
  "tags": ["memory", "token", "work-order"],
  "references": ["WO-031", "WO-056"],
  "reason_for_inclusion": "Work Order contract and evidence"
}
```

Hard rules:

- Every recall item must cite `source_locator`.
- Template records must rank below current project records when both match.
- Stale or generated records must be excluded or marked lower-confidence.
- Recall output should be bounded excerpts plus citations, not full-file replay.

## Benchmark

Command:

```bash
python3 spikes/wo-069/evidence_memory.py benchmark --repo . --top 16 --out /tmp/wo-069-benchmark-final.json
```

Results:

| Case | Baseline Tokens | Recall Payload Tokens | Reduction | Ratio | Critical Misses |
|---|---:|---:|---:|---:|---|
| status_session_recovery | 6069 | 3752 | 38.2% | 1.62x | 0 |
| build_resume_checkpoint | 17403 | 3534 | 79.7% | 4.92x | 0 |
| audit_findings_consensus | 6102 | 3226 | 47.1% | 1.89x | 0 |
| midstream_baseline_remediation | 15381 | 3410 | 77.8% | 4.51x | 0 |
| codex_enforcement_boundary | 6200 | 3253 | 47.5% | 1.91x | 0 |
| token_memory_research | 5993 | 2910 | 51.4% | 2.06x | 0 |

Summary:

- Average reduction: 57.0%
- Average baseline-to-recall ratio: 2.82x
- Critical misses: 0
- Threshold: passed

## Interpretation

The strongest cases are build resume and midstream baseline/remediation because those workflows otherwise require reading large skill and WO files. The weaker cases are status and Codex boundary checks because the relevant source set is already small.

The first unrefined benchmark failed: it returned duplicate chunks from large files, missed critical sources, and produced only a 1.31x average ratio. The passing result required source diversification, normalized path/tag matching, bounded excerpts, and a lower score for overly large chunks. Those constraints should be considered required design, not optional polish.

## Risks

- Ranking can still surface noisy but related evidence, especially broad help/build chunks.
- Template references can look authoritative unless they are clearly lower-confidence than current project artifacts.
- A recall preflight can point to the right source but still require full source reading before high-risk edits.
- Benchmark cases are representative, not exhaustive.
- Token savings disappear if recall output expands into full-file summaries.

## Next Work Order

Create a focused implementation WO only if this spike is accepted:

**WO-070: Evidence Recall Indexer and Query Command**

Minimum scope:

- Add a local, no-network index builder over canonical VibeOS evidence sources
- Store generated index under `.vibeos/cache/` or another clearly derived cache path
- Add an explicit evidence query entry point for `status`, `build`, `audit`, and `plan` preflight use
- Keep every result source-cited
- Keep recall output bounded
- Add tests for source inventory, schema validation, source diversification, stale/template ranking, and critical-evidence recall

Do not add Claude `MEMORY.md` sync, Ruflo/AgentDB, Graphify, Obsidian, or background daemons in WO-070.
