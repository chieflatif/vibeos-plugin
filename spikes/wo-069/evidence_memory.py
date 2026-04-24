#!/usr/bin/env python3
"""WO-069 disposable structured evidence-memory prototype.

Builds a local, source-cited index over VibeOS evidence artifacts and runs a
small benchmark against representative workflows. This is research code, not
runtime VibeOS behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "into", "is", "it", "of", "on", "or", "the", "to", "with",
}

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:/-]*", re.I)
REF_RE = re.compile(
    r"(WO-\d{3}[a-z]?|F-\d{2,4}|ADR-\d+|\.vibeos/[A-Za-z0-9_./-]+|"
    r"docs/[A-Za-z0-9_./-]+|plugins/[A-Za-z0-9_./-]+|"
    r"[A-Za-z0-9_-]+\.json|[A-Za-z0-9_-]+\.md)",
    re.I,
)


@dataclass(frozen=True)
class SourceSpec:
    pattern: str
    record_type: str
    canonicality: str
    confidence: float
    reason: str


SOURCES = [
    SourceSpec("docs/planning/WO-*.md", "work_order", "canonical", 0.95, "Work Order contract and evidence"),
    SourceSpec("docs/planning/POST-PHASE-*.md", "audit_report", "canonical", 0.90, "Phase audit evidence"),
    SourceSpec("docs/planning/PLANNING-AUDIT-*.md", "audit_report", "canonical", 0.90, "Planning audit evidence"),
    SourceSpec("docs/planning/SPIKE-RESULTS.md", "research_report", "canonical", 0.90, "Prior technical spike evidence"),
    SourceSpec("docs/planning/DEVELOPMENT-PLAN.md", "roadmap", "canonical", 0.95, "Roadmap and dependency evidence"),
    SourceSpec("docs/planning/WO-INDEX.md", "work_order_index", "canonical", 0.95, "Work Order status index"),
    SourceSpec("docs/FILE-INVENTORY.md", "artifact_inventory", "canonical", 0.95, "VibeOS artifact inventory"),
    SourceSpec("docs/USER-COMMUNICATION-CONTRACT.md", "communication_contract", "canonical", 0.90, "User-facing language contract"),
    SourceSpec("plugins/vibeos/skills/*/SKILL.md", "skill_contract", "canonical", 0.90, "Executable skill instructions"),
    SourceSpec("plugins/vibeos/reference/session-state-schema.md", "schema", "canonical", 0.95, "Session-state schema"),
    SourceSpec("plugins/vibeos/reference/governance/*.ref", "governance_reference", "template", 0.82, "Install-time governance template"),
    SourceSpec("plugins/vibeos/reference/product/*.ref", "product_reference", "template", 0.80, "Install-time product template"),
    SourceSpec("plugins/vibeos/reference/codex/AGENTS.md.ref", "codex_reference", "template", 0.90, "Codex enforcement contract"),
    SourceSpec("plugins/vibeos/reference/codex/skills/*/SKILL.md", "codex_skill_reference", "template", 0.84, "Codex skill template"),
    SourceSpec("plugins/vibeos/quality-gate-manifest.json", "gate_manifest", "canonical", 0.92, "Gate configuration"),
    SourceSpec("plugins/vibeos/hook-manifest.json", "hook_manifest", "canonical", 0.90, "Hook configuration"),
    SourceSpec(".vibeos/config.json", "runtime_state", "local", 0.75, "Local VibeOS config"),
    SourceSpec(".vibeos/session-state.json", "runtime_state", "local", 0.95, "Current or latest session state"),
    SourceSpec(".vibeos/build-log.md", "runtime_log", "local", 0.90, "Build history"),
    SourceSpec(".vibeos/checkpoints/*.json", "checkpoint", "local", 0.95, "Resume checkpoint"),
    SourceSpec(".vibeos/baselines/*.json", "baseline", "local", 0.92, "Quality baseline"),
    SourceSpec(".vibeos/findings-registry.json", "findings_registry", "local", 0.95, "Finding-level baseline registry"),
    SourceSpec(".vibeos/audit-reports/*", "audit_report", "local", 0.92, "Audit report"),
    SourceSpec(".vibeos/session-audits/*", "session_audit", "local", 0.92, "Session audit report"),
]


BENCHMARKS = [
    {
        "name": "status_session_recovery",
        "query": "status current session state checkpoint build log gate manifest",
        "baseline_paths": [
            "docs/FILE-INVENTORY.md",
            "plugins/vibeos/skills/status/SKILL.md",
            "plugins/vibeos/skills/session-audit/SKILL.md",
            "plugins/vibeos/reference/session-state-schema.md",
            "docs/planning/WO-056-session-state-gate-manifest.md",
        ],
        "critical_paths": [
            "plugins/vibeos/skills/status/SKILL.md",
            "plugins/vibeos/reference/session-state-schema.md",
        ],
    },
    {
        "name": "build_resume_checkpoint",
        "query": "build resume active work order checkpoint recovery session state",
        "baseline_paths": [
            "plugins/vibeos/skills/build/SKILL.md",
            "plugins/vibeos/skills/checkpoint/SKILL.md",
            "docs/planning/WO-049-mid-wo-resume-and-error-recovery.md",
            "plugins/vibeos/reference/session-state-schema.md",
        ],
        "critical_paths": [
            "plugins/vibeos/skills/build/SKILL.md",
            "docs/planning/WO-049-mid-wo-resume-and-error-recovery.md",
            "plugins/vibeos/reference/session-state-schema.md",
        ],
    },
    {
        "name": "audit_findings_consensus",
        "query": "audit findings consensus same tree audit registration report finding registry",
        "baseline_paths": [
            "plugins/vibeos/skills/audit/SKILL.md",
            "docs/planning/WO-028-audit-skill.md",
            "docs/planning/WO-058-audit-visibility-registration.md",
            "plugins/vibeos/reference/governance/WO-AUDIT-FRAMEWORK.md.ref",
        ],
        "critical_paths": [
            "plugins/vibeos/skills/audit/SKILL.md",
            "docs/planning/WO-028-audit-skill.md",
            "docs/planning/WO-058-audit-visibility-registration.md",
        ],
    },
    {
        "name": "midstream_baseline_remediation",
        "query": "midstream finding level baseline remediation roadmap accepted risk plan",
        "baseline_paths": [
            "plugins/vibeos/skills/plan/SKILL.md",
            "docs/planning/WO-041-architecture-first-midstream-discovery.md",
            "docs/planning/WO-043-finding-level-baseline.md",
            "docs/planning/WO-044-remediation-roadmap.md",
        ],
        "critical_paths": [
            "plugins/vibeos/skills/plan/SKILL.md",
            "docs/planning/WO-043-finding-level-baseline.md",
            "docs/planning/WO-044-remediation-roadmap.md",
        ],
    },
    {
        "name": "codex_enforcement_boundary",
        "query": "codex enforcement boundary git hooks runtime hooks agents structured memory",
        "baseline_paths": [
            "docs/planning/WO-068-codex-cross-surface-hardening.md",
            "docs/planning/WO-069-structured-evidence-memory-spike.md",
            "plugins/vibeos/reference/codex/AGENTS.md.ref",
            "plugins/vibeos/reference/codex/skills/vibeos-build/SKILL.md",
        ],
        "critical_paths": [
            "docs/planning/WO-068-codex-cross-surface-hardening.md",
            "docs/planning/WO-069-structured-evidence-memory-spike.md",
            "plugins/vibeos/reference/codex/AGENTS.md.ref",
        ],
    },
    {
        "name": "token_memory_research",
        "query": "token budget tracking context token reduction benchmark memory evidence",
        "baseline_paths": [
            "docs/planning/WO-031-token-budget.md",
            "docs/planning/WO-069-structured-evidence-memory-spike.md",
            "docs/planning/PLANNING-AUDIT-001.md",
            "plugins/vibeos/reference/prompt-engineering-bible/bible/01-core/memory-engineering.md",
        ],
        "critical_paths": [
            "docs/planning/WO-031-token-budget.md",
            "docs/planning/WO-069-structured-evidence-memory-spike.md",
        ],
    },
]


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def tokens(text: str) -> list[str]:
    found: list[str] = []
    for raw in TOKEN_RE.findall(text):
        lowered = raw.lower()
        pieces = [lowered]
        pieces.extend(re.split(r"[._:/-]+", lowered))
        for piece in pieces:
            if len(piece) > 1 and piece not in STOPWORDS:
                found.append(piece)
    return found


def token_estimate(text: str) -> int:
    return max(1, math.ceil(len(tokens(text)) * 1.33))


def recall_payload_tokens(record: dict, excerpt_cap: int = 180) -> int:
    citation_bits = " ".join([
        record["source_locator"],
        record["title"],
        " ".join(record["matched_terms"]),
        " ".join(record["tags"]),
    ])
    return token_estimate(citation_bits) + min(record["token_estimate"], excerpt_cap)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def extract_refs(text: str) -> list[str]:
    refs = {m.group(1).rstrip(".,);]") for m in REF_RE.finditer(text)}
    return sorted(refs)


def tags_for(path: str, text: str) -> list[str]:
    hay = f"{path}\n{text}".lower()
    tags = set()
    tag_terms = {
        "audit": ["audit", "auditor", "consensus"],
        "baseline": ["baseline", "ratchet"],
        "build": ["build", "implementation"],
        "checkpoint": ["checkpoint", "resume"],
        "codex": ["codex", "agents.md"],
        "deviation": ["deviation", "accepted risk"],
        "evidence": ["evidence", "finding"],
        "gate": ["gate", "manifest"],
        "memory": ["memory", "recall", "context"],
        "midstream": ["midstream", "existing project"],
        "plan": ["plan", "planning"],
        "product-anchor": ["product anchor", "anti-goal"],
        "research": ["research", "freshness"],
        "session-state": ["session-state", "session state"],
        "status": ["status", "current state"],
        "token": ["token", "budget"],
        "work-order": ["work order", "wo-"],
    }
    for tag, needles in tag_terms.items():
        if any(n in hay for n in needles):
            tags.add(tag)
    for wo in re.findall(r"WO-\d{3}[a-z]?", text, re.I):
        tags.add(wo.upper())
    return sorted(tags)


def markdown_chunks(text: str) -> Iterable[tuple[str, int, str]]:
    matches = list(re.finditer(r"(?m)^(#{1,3})\s+(.+)$", text))
    if not matches:
        yield "Document", 1, text
        return
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = match.group(2).strip()
        chunk = text[start:end].strip()
        if len(tokens(chunk)) >= 12:
            yield title, line_for_offset(text, start), chunk


def json_summary(text: str) -> str:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    return json.dumps(parsed, indent=2, sort_keys=True)


def iter_sources(root: Path) -> Iterable[tuple[Path, SourceSpec]]:
    seen: set[Path] = set()
    for spec in SOURCES:
        for path in sorted(root.glob(spec.pattern)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            yield path, spec


def build_index(root: Path) -> dict:
    records = []
    source_inventory = []
    for path, spec in iter_sources(root):
        source_path = rel(path, root)
        text = json_summary(read_text(path)) if path.suffix == ".json" else read_text(path)
        chunks = [("Document", 1, text)] if path.suffix == ".json" else list(markdown_chunks(text))
        source_inventory.append({
            "source_path": source_path,
            "record_type": spec.record_type,
            "canonicality": spec.canonicality,
            "confidence": spec.confidence,
            "freshness_rule": "local-current" if spec.canonicality == "local" else spec.canonicality,
            "exclusion_rule": "exclude if generated, stale, private, or not source-cited",
            "token_estimate": token_estimate(text),
        })
        for title, line, chunk in chunks:
            record_id = hashlib.sha256(f"{source_path}:{line}:{title}".encode()).hexdigest()[:16]
            records.append({
                "id": record_id,
                "source_path": source_path,
                "source_locator": f"{source_path}:{line}",
                "record_type": spec.record_type,
                "canonicality": spec.canonicality,
                "title": title,
                "content": chunk,
                "confidence": spec.confidence,
                "freshness": "template" if spec.canonicality == "template" else "current",
                "tags": tags_for(source_path, chunk),
                "references": extract_refs(chunk),
                "reason_for_inclusion": spec.reason,
                "token_estimate": token_estimate(chunk),
            })
    add_graph_scores(records)
    return {
        "schema_version": "wo-069-spike-0.1",
        "record_schema": {
            "required": [
                "id", "source_path", "source_locator", "record_type", "confidence",
                "freshness", "tags", "references", "reason_for_inclusion",
            ],
            "citation_required": True,
            "mutation_policy": "read-only source ingestion; no source artifact writes",
        },
        "source_inventory": source_inventory,
        "records": records,
    }


def add_graph_scores(records: list[dict]) -> None:
    ref_counts: dict[str, int] = {}
    for record in records:
        for ref in record["references"]:
            ref_counts[ref.lower()] = ref_counts.get(ref.lower(), 0) + 1
    raw_scores = []
    for record in records:
        refs = record["references"]
        score = len(refs) + sum(ref_counts.get(ref.lower(), 0) for ref in refs)
        raw_scores.append(score)
    max_score = max(raw_scores or [1])
    for record, raw in zip(records, raw_scores):
        record["graph_score"] = round(raw / max_score, 4)


def query_index(index: dict, query: str, limit: int) -> list[dict]:
    q_tokens = set(tokens(query))
    q_refs = {r.upper() for r in re.findall(r"WO-\d{3}[a-z]?", query, re.I)}
    candidates = []
    for record in index["records"]:
        text = " ".join([
            record["source_path"], record["title"], " ".join(record["tags"]), record["content"]
        ]).lower()
        r_tokens = set(tokens(text))
        overlap = len(q_tokens & r_tokens) / max(len(q_tokens), 1)
        tag_hits = len(q_tokens & set(tokens(" ".join(record["tags"])))) * 0.08
        ref_hits = len(q_refs & {r.upper() for r in record["references"]}) * 0.15
        path_bonus = len(q_tokens & set(tokens(record["source_path"]))) * 0.04
        type_bonus = len(q_tokens & set(tokens(record["record_type"]))) * 0.05
        size_penalty = min(record["token_estimate"] / 3500, 0.18)
        score = (
            overlap * 0.68
            + tag_hits
            + ref_hits
            + path_bonus
            + type_bonus
            + record["graph_score"] * 0.07
            + record["confidence"] * 0.07
            - size_penalty
        )
        if score > 0:
            item = dict(record)
            item["score"] = round(score, 4)
            item["matched_terms"] = sorted(q_tokens & r_tokens)
            candidates.append(item)

    ranked = sorted(candidates, key=lambda r: (-r["score"], r["token_estimate"], r["source_locator"]))
    selected = []
    seen_sources: set[str] = set()
    for item in ranked:
        if item["source_path"] in seen_sources:
            continue
        selected.append(item)
        seen_sources.add(item["source_path"])
        if len(selected) >= limit:
            return selected
    return selected


def benchmark(index: dict, root: Path, top: int) -> dict:
    cases = []
    for case in BENCHMARKS:
        results = query_index(index, case["query"], top)
        retrieved_paths = {r["source_path"] for r in results}
        baseline_tokens = sum(
            token_estimate(read_text(root / p)) for p in case["baseline_paths"] if (root / p).exists()
        )
        recall_tokens = sum(recall_payload_tokens(r) for r in results)
        missing = sorted(set(case["critical_paths"]) - retrieved_paths)
        reduction = 1 - (recall_tokens / baseline_tokens) if baseline_tokens else 0
        ratio = baseline_tokens / recall_tokens if recall_tokens else 0
        cases.append({
            "name": case["name"],
            "query": case["query"],
            "baseline_tokens": baseline_tokens,
            "recall_tokens": recall_tokens,
            "reduction": round(reduction, 4),
            "ratio": round(ratio, 2),
            "critical_missing": missing,
            "top_sources": sorted(retrieved_paths)[:12],
            "top_results": [
                {
                    "source_locator": r["source_locator"],
                    "title": r["title"],
                    "score": r["score"],
                    "payload_token_estimate": recall_payload_tokens(r),
                }
                for r in results[:6]
            ],
        })
    avg_reduction = sum(c["reduction"] for c in cases) / max(len(cases), 1)
    avg_ratio = sum(c["ratio"] for c in cases) / max(len(cases), 1)
    critical_misses = sum(len(c["critical_missing"]) for c in cases)
    return {
        "top_n": top,
        "cases": cases,
        "summary": {
            "case_count": len(cases),
            "avg_reduction": round(avg_reduction, 4),
            "avg_ratio": round(avg_ratio, 2),
            "critical_misses": critical_misses,
            "passes_threshold": avg_ratio >= 2.0 and avg_reduction >= 0.40 and critical_misses == 0,
        },
    }


def print_benchmark(result: dict) -> None:
    print("| Case | Baseline Tokens | Recall Payload Tokens | Reduction | Ratio | Critical Misses |")
    print("|---|---:|---:|---:|---:|---|")
    for case in result["cases"]:
        misses = ", ".join(case["critical_missing"]) if case["critical_missing"] else "none"
        print(
            f"| {case['name']} | {case['baseline_tokens']} | {case['recall_tokens']} | "
            f"{case['reduction']:.1%} | {case['ratio']}x | {misses} |"
        )
    summary = result["summary"]
    print()
    print(
        f"Summary: avg reduction {summary['avg_reduction']:.1%}, "
        f"avg ratio {summary['avg_ratio']}x, critical misses {summary['critical_misses']}, "
        f"passes threshold {summary['passes_threshold']}"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="WO-069 structured evidence-memory prototype")
    parser.add_argument("command", choices=["build", "query", "benchmark"])
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--out", help="Write index or benchmark JSON")
    parser.add_argument("--query", help="Query string for query command")
    parser.add_argument("--top", type=int, default=12, help="Result limit")
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    index = build_index(root)

    if args.command == "build":
        if args.out:
            Path(args.out).write_text(json.dumps(index, indent=2), encoding="utf-8")
        else:
            print(json.dumps({
                "records": len(index["records"]),
                "sources": len(index["source_inventory"]),
                "schema_version": index["schema_version"],
            }, indent=2))
        return 0

    if args.command == "query":
        if not args.query:
            parser.error("--query is required for query")
        results = query_index(index, args.query, args.top)
        for result in results:
            print(f"{result['score']:.4f} {result['source_locator']} :: {result['title']}")
        return 0

    result = benchmark(index, root, args.top)
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print_benchmark(result)
    return 0 if result["summary"]["passes_threshold"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
