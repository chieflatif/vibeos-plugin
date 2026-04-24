#!/usr/bin/env python3
"""VibeOS local evidence recall utility.

Indexes durable VibeOS evidence artifacts and returns bounded, source-cited
results. This is advisory recall, not runtime enforcement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

FRAMEWORK_VERSION = "2.2.0"
STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "the", "to", "with"}
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:/-]*", re.I)
HEADING_RE = re.compile(r"(?m)^(#{1,3})\s+(.+)$")
REF_RE = re.compile(r"(WO-\d{3}[a-z]?|F-\d{2,4}|ADR-\d+|\.vibeos/[A-Za-z0-9_./-]+|docs/[A-Za-z0-9_./-]+|[A-Za-z0-9_-]+\.(?:json|md))", re.I)

SOURCES = [
    ("docs/planning/WO-*.md", "work_order", "canonical", 0.95, "Work Order contract and evidence"),
    ("docs/planning/POST-PHASE-*.md", "audit_report", "canonical", 0.90, "Phase audit evidence"),
    ("docs/planning/PLANNING-AUDIT-*.md", "audit_report", "canonical", 0.90, "Planning audit evidence"),
    ("docs/planning/SPIKE-RESULTS.md", "research_report", "canonical", 0.90, "Prior spike evidence"),
    ("docs/planning/DEVELOPMENT-PLAN.md", "roadmap", "canonical", 0.95, "Roadmap and dependencies"),
    ("docs/planning/WO-INDEX.md", "work_order_index", "canonical", 0.95, "Work Order status index"),
    ("docs/FILE-INVENTORY.md", "artifact_inventory", "canonical", 0.95, "Artifact inventory"),
    ("docs/USER-COMMUNICATION-CONTRACT.md", "communication_contract", "canonical", 0.90, "User communication contract"),
    ("docs/research/RESEARCH-REGISTRY.md", "research_registry", "canonical", 0.95, "Freshness evidence registry"),
    ("docs/product/PRODUCT-ANCHOR.md", "product_anchor", "canonical", 0.95, "Product anchor"),
    ("docs/decisions/DEVIATIONS.md", "deviation_log", "canonical", 0.95, "Deviation log"),
    (".claude/skills/*/SKILL.md", "skill_contract", "canonical", 0.90, "Claude skill contract"),
    (".codex/skills/*/SKILL.md", "codex_skill_contract", "canonical", 0.86, "Codex skill contract"),
    ("plugins/vibeos/skills/*/SKILL.md", "skill_contract", "canonical", 0.86, "Framework skill contract"),
    (".claude/quality-gate-manifest.json", "gate_manifest", "canonical", 0.92, "Gate configuration"),
    ("plugins/vibeos/quality-gate-manifest.json", "gate_manifest", "canonical", 0.86, "Framework gate configuration"),
    (".claude/hook-manifest.json", "hook_manifest", "canonical", 0.90, "Hook configuration"),
    ("plugins/vibeos/hook-manifest.json", "hook_manifest", "canonical", 0.84, "Framework hook configuration"),
    (".vibeos/session-state.json", "runtime_state", "local", 0.95, "Session state"),
    (".vibeos/build-log.md", "runtime_log", "local", 0.90, "Build log"),
    (".vibeos/checkpoints/*.json", "checkpoint", "local", 0.95, "Resume checkpoint"),
    (".vibeos/baselines/*.json", "baseline", "local", 0.92, "Quality baseline"),
    (".vibeos/findings-registry.json", "findings_registry", "local", 0.95, "Finding registry"),
    (".vibeos/audit-reports/*", "audit_report", "local", 0.92, "Audit report"),
    (".vibeos/session-audits/*", "session_audit", "local", 0.92, "Session audit"),
    (".vibeos/reference/governance/*.ref", "governance_reference", "template", 0.78, "Governance template"),
    ("plugins/vibeos/reference/governance/*.ref", "governance_reference", "template", 0.74, "Framework governance template"),
]


def split_terms(text: str) -> list[str]:
    terms: list[str] = []
    for raw in TOKEN_RE.findall(text):
        lowered = raw.lower()
        for part in [lowered, *re.split(r"[._:/-]+", lowered)]:
            if len(part) > 1 and part not in STOPWORDS:
                terms.append(part)
    return terms


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(split_terms(text)) * 1.33))


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def bounded_excerpt(text: str, limit: int = 700) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def tags_for(path: str, text: str) -> list[str]:
    hay = f"{path}\n{text}".lower()
    mapping = {
        "audit": ("audit", "auditor", "consensus"),
        "baseline": ("baseline", "ratchet"),
        "build": ("build", "implementation"),
        "checkpoint": ("checkpoint", "resume"),
        "codex": ("codex", "agents.md"),
        "deviation": ("deviation", "accepted risk"),
        "evidence": ("evidence", "finding"),
        "gate": ("gate", "manifest"),
        "memory": ("memory", "recall", "context"),
        "midstream": ("midstream", "existing project"),
        "plan": ("plan", "planning"),
        "product-anchor": ("product anchor", "anti-goal"),
        "research": ("research", "freshness"),
        "session-state": ("session-state", "session state"),
        "status": ("status", "current state"),
        "token": ("token", "budget"),
        "work-order": ("work order", "wo-"),
    }
    tags = {tag for tag, needles in mapping.items() if any(n in hay for n in needles)}
    tags.update(wo.upper() for wo in re.findall(r"WO-\d{3}[a-z]?", text, re.I))
    return sorted(tags)


def references(text: str) -> list[str]:
    return sorted({m.group(1).rstrip(".,);]") for m in REF_RE.finditer(text)})


def chunks(path: Path, text: str) -> list[tuple[str, int, str]]:
    if path.suffix == ".json":
        try:
            text = json.dumps(json.loads(text), indent=2, sort_keys=True)
        except json.JSONDecodeError:
            pass
        return [("Document", 1, text)]
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [("Document", 1, text)] if split_terms(text) else []
    out = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if len(split_terms(body)) >= 8:
            out.append((match.group(2).strip(), line_for_offset(text, start), body))
    return out


def iter_sources(root: Path):
    seen: set[Path] = set()
    for pattern, kind, canonicality, confidence, reason in SOURCES:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or path in seen or ".git" in path.parts or "node_modules" in path.parts:
                continue
            seen.add(path)
            yield path, kind, canonicality, confidence, reason


def add_graph_scores(records: list[dict]) -> None:
    counts: dict[str, int] = {}
    for record in records:
        for ref in record["references"]:
            counts[ref.lower()] = counts.get(ref.lower(), 0) + 1
    raw = [len(r["references"]) + sum(counts.get(ref.lower(), 0) for ref in r["references"]) for r in records]
    max_raw = max(raw or [1])
    for record, score in zip(records, raw):
        record["graph_score"] = round(score / max_raw, 4)


def build_index(root: Path) -> dict:
    records = []
    inventory = []
    for path, kind, canonicality, confidence, reason in iter_sources(root):
        source_path = rel(path, root)
        text = path.read_text(encoding="utf-8", errors="ignore")
        inventory.append({"source_path": source_path, "record_type": kind, "canonicality": canonicality, "confidence": confidence})
        for title, line, body in chunks(path, text):
            excerpt = bounded_excerpt(body)
            record_id = hashlib.sha256(f"{source_path}:{line}:{title}".encode()).hexdigest()[:16]
            record_tags = tags_for(source_path, body)
            record_refs = references(body)
            records.append({
                "id": record_id,
                "source_path": source_path,
                "source_locator": f"{source_path}:{line}",
                "record_type": kind,
                "canonicality": canonicality,
                "title": title,
                "excerpt": excerpt,
                "confidence": confidence,
                "freshness": "template" if canonicality == "template" else "current",
                "tags": record_tags,
                "references": record_refs,
                "reason_for_inclusion": reason,
                "terms": sorted(set(split_terms(f"{source_path} {title} {' '.join(record_tags)} {body}"))),
                "excerpt_token_estimate": estimate_tokens(excerpt),
            })
    add_graph_scores(records)
    return {
        "schema_version": "evidence-recall-1.0",
        "framework_version": FRAMEWORK_VERSION,
        "record_count": len(records),
        "source_count": len(inventory),
        "records": records,
        "source_inventory": inventory,
    }


def default_cache(root: Path) -> Path:
    return root / ".vibeos" / "cache" / "evidence-recall-index.json"


def load_or_build(root: Path, fresh: bool) -> dict:
    cache = default_cache(root)
    if not fresh and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    index = build_index(root)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def query(index: dict, query_text: str, limit: int, diversify: bool) -> list[dict]:
    q_terms = set(split_terms(query_text))
    q_refs = {r.upper() for r in re.findall(r"WO-\d{3}[a-z]?", query_text, re.I)}
    ranked = []
    for record in index["records"]:
        terms = set(record.get("terms", []))
        tags = set(split_terms(" ".join(record["tags"])))
        refs = {r.upper() for r in record["references"]}
        overlap = len(q_terms & terms) / max(len(q_terms), 1)
        score = (
            overlap * 0.70
            + len(q_terms & tags) * 0.08
            + len(q_refs & refs) * 0.12
            + record["graph_score"] * 0.06
            + record["confidence"] * 0.06
        )
        if record["canonicality"] == "template":
            score -= 0.08
        if score <= 0:
            continue
        item = {k: record[k] for k in ("source_path", "source_locator", "record_type", "title", "excerpt", "confidence", "freshness", "tags", "references", "reason_for_inclusion")}
        item["score"] = round(score, 4)
        item["matched_terms"] = sorted(q_terms & terms)
        ranked.append(item)
    ranked.sort(key=lambda item: (-item["score"], item["source_locator"]))
    if not diversify:
        return ranked[:limit]
    selected = []
    seen_sources: set[str] = set()
    for item in ranked:
        if item["source_path"] in seen_sources:
            continue
        selected.append(item)
        seen_sources.add(item["source_path"])
        if len(selected) >= limit:
            break
    return selected


def print_results(results: list[dict]) -> None:
    for item in results:
        print(f"{item['score']:.4f} {item['source_locator']} :: {item['title']}")
        print(f"  tags: {', '.join(item['tags']) or '-'}")
        print(f"  excerpt: {item['excerpt']}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="VibeOS local evidence recall")
    sub = parser.add_subparsers(dest="command", required=True)
    index_parser = sub.add_parser("index", help="build evidence recall index")
    index_parser.add_argument("--repo", default=None)
    index_parser.add_argument("--out", default=None)
    query_parser = sub.add_parser("query", help="query evidence recall index")
    query_parser.add_argument("query")
    query_parser.add_argument("--repo", default=None)
    query_parser.add_argument("--limit", type=int, default=8)
    query_parser.add_argument("--fresh", action="store_true")
    query_parser.add_argument("--no-diversify", action="store_true")
    query_parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    script_root = Path(__file__).resolve().parents[2]
    root = Path(args.repo).resolve() if args.repo else script_root
    if args.command == "index":
        index = build_index(root)
        out = Path(args.out).resolve() if args.out else default_cache(root)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        print(f"index: {out}")
        print(f"records: {index['record_count']}")
        print(f"sources: {index['source_count']}")
        return 0
    index = load_or_build(root, args.fresh)
    results = query(index, args.query, args.limit, not args.no_diversify)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
