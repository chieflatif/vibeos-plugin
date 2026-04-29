#!/usr/bin/env python3
"""Generate a VibOS Comp SCORECARD.md from mission, plan, and evidence artifacts."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DIMENSIONS = [
    {"id": "functionality", "label": "Functionality", "required_evidence": ["MISSION.md", "COMP-PLAN.md"], "required_terms": [], "blocking_at": ["design_partner_mvp", "production_ready"]},
    {"id": "flow_integrity", "label": "Flow Integrity", "required_evidence": ["MISSION.md", "docs/evidence/FLOW-INTEGRITY.md"], "required_terms": ["workflow", "auth", "backend", "error"], "blocking_at": ["local_proof", "design_partner_mvp", "production_ready"]},
    {"id": "objective_fidelity", "label": "Objective Fidelity", "required_evidence": ["MISSION.md"], "required_terms": ["mission", "promise", "objective"], "blocking_at": ["local_proof", "design_partner_mvp", "production_ready"]},
    {"id": "system_invariants", "label": "System Invariants", "required_evidence": ["MISSION.md", "docs/evidence/SYSTEM-INVARIANTS.md"], "required_terms": ["invariant", "state"], "blocking_at": ["local_proof", "design_partner_mvp", "production_ready"]},
    {"id": "security", "label": "Security", "required_evidence": [], "required_terms": ["security", "identity", "access"], "blocking_at": ["local_proof", "design_partner_mvp", "production_ready"]},
    {"id": "observability", "label": "Observability", "required_evidence": [], "required_terms": ["observability", "health", "logs"], "blocking_at": ["design_partner_mvp", "production_ready"]},
    {"id": "performance", "label": "Performance", "required_evidence": [], "required_terms": ["performance", "latency"], "blocking_at": ["design_partner_mvp", "production_ready"]},
    {"id": "architecture", "label": "Architecture", "required_evidence": [".vibeos/worktree-scopes.json"], "required_terms": [], "blocking_at": ["design_partner_mvp", "production_ready"]},
    {"id": "dependencies", "label": "Dependencies", "required_evidence": [], "required_terms": ["dependency", "freshness"], "blocking_at": ["design_partner_mvp", "production_ready"]},
    {"id": "dependency_intelligence", "label": "Dependency Intelligence", "required_evidence": ["MISSION.md", "docs/evidence/DEPENDENCY-INTELLIGENCE.md"], "required_terms": ["dependency", "version", "compatibility", "security"], "blocking_at": ["local_proof", "design_partner_mvp", "production_ready"]},
    {"id": "delivery_infrastructure", "label": "Delivery Infrastructure", "required_evidence": ["MISSION.md", "docs/evidence/DELIVERY-INFRASTRUCTURE.md"], "required_terms": ["ci", "deploy", "observability", "rollback"], "blocking_at": ["local_proof", "design_partner_mvp", "production_ready"]},
    {"id": "operability", "label": "Operability", "required_evidence": [], "required_terms": ["deployment", "runbook"], "blocking_at": ["design_partner_mvp", "production_ready"]},
    {"id": "evidence", "label": "Evidence", "required_evidence": ["docs/evidence/COMP-INTEGRATION-EVIDENCE.md"], "required_terms": ["evidence"], "blocking_at": ["local_proof", "design_partner_mvp", "production_ready"]},
]


def load_dimensions(project_dir: Path):
    path = project_dir / ".vibeos/reference/comp/scorecard-dimensions.json"
    if not path.exists():
        return DEFAULT_DIMENSIONS
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("dimensions", DEFAULT_DIMENSIONS)
    except json.JSONDecodeError:
        return DEFAULT_DIMENSIONS


def corpus(project_dir: Path) -> str:
    texts = []
    for rel in ["MISSION.md", "COMP-PLAN.md", "docs/evidence/FLOW-INTEGRITY.md", "docs/evidence/SYSTEM-INVARIANTS.md", "docs/evidence/DEPENDENCY-INTELLIGENCE.md", "docs/evidence/DELIVERY-INFRASTRUCTURE.md", "docs/evidence/COMP-INTEGRATION-EVIDENCE.md"]:
        path = project_dir / rel
        if path.exists():
            texts.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(texts).lower()


def score_dimension(project_dir: Path, dimension, threshold: str, text: str):
    missing = []
    for rel in dimension.get("required_evidence", []):
        if not (project_dir / rel).exists():
            missing.append(rel)
    for term in dimension.get("required_terms", []):
        if term.lower() not in text:
            missing.append(f"term:{term}")

    if not missing:
        return {"status": "pass", "evidence": "required evidence present", "risks": ""}
    if threshold in dimension.get("blocking_at", []):
        return {"status": "fail", "evidence": "missing " + ", ".join(missing), "risks": "blocking at threshold"}
    return {"status": "warn", "evidence": "missing " + ", ".join(missing), "risks": "advisory at threshold"}


def render(threshold: str, results):
    status = "fail" if any(item["status"] == "fail" for item in results.values()) else "warn" if any(item["status"] == "warn" for item in results.values()) else "pass"
    lines = [
        "# VibOS Comp Scorecard",
        "",
        "## Status",
        "",
        f"`{status}`",
        "",
        "## Threshold",
        "",
        f"`{threshold}`",
        "",
        "## Dimension Results",
        "",
        "| Dimension | Status | Evidence | Risks |",
        "|---|---|---|---|",
    ]
    for key, result in results.items():
        lines.append(f"| {result['label']} | {result['status']} | {result['evidence']} | {result['risks']} |")

    failures = [result for result in results.values() if result["status"] == "fail"]
    warnings = [result for result in results.values() if result["status"] == "warn"]
    lines.extend(["", "## Blocking Failures", ""])
    if failures:
        for result in failures:
            lines.append(f"- {result['label']}: {result['evidence']}")
    else:
        lines.append("- None detected by scorecard artifact checks.")

    lines.extend(["", "## Advisory Findings", ""])
    if warnings:
        for result in warnings:
            lines.append(f"- {result['label']}: {result['evidence']}")
    else:
        lines.append("- None detected by scorecard artifact checks.")

    lines.extend([
        "",
        "## Completion Claim",
        "",
        "Comp completion requires this scorecard plus passing command output for the relevant gates and tests.",
        "",
        f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_",
        "",
    ])
    return status, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--threshold", default="design_partner_mvp", choices=["local_proof", "design_partner_mvp", "production_ready"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    text = corpus(project_dir)
    dimensions = load_dimensions(project_dir)
    results = {}
    for dimension in dimensions:
        result = score_dimension(project_dir, dimension, args.threshold, text)
        result["label"] = dimension.get("label", dimension["id"])
        results[dimension["id"]] = result

    status, markdown = render(args.threshold, results)
    (project_dir / "SCORECARD.md").write_text(markdown, encoding="utf-8")
    payload = {"status": status, "threshold": args.threshold, "results": results, "scorecard": "SCORECARD.md"}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"[comp-scorecard] {status.upper()}: wrote SCORECARD.md")
    return 1 if status == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
