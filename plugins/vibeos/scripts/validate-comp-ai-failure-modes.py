#!/usr/bin/env python3
"""Validate VibOS Comp artifacts for common AI-generated MVP failure modes."""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_MISSION_SECTIONS = [
    "## Mission Promise",
    "## Users And Buyers",
    "## Core Workflow",
    "## Flow Integrity",
    "## Objective Fidelity",
    "## System Invariants",
    "## Dependency Intelligence",
    "## Delivery Infrastructure",
    "## Product Scope",
    "## Enterprise Foundation Baseline",
    "## Threat Model",
    "## Observability And Operations",
    "## Performance Budgets",
    "## Acceptance Criteria",
    "## Downstream Handoff",
]

FOUNDATION_TERMS = [
    "identity",
    "access",
    "security",
    "testing",
    "observability",
    "deployment",
    "evidence",
    "flow",
    "objective",
    "invariant",
    "dependency",
    "version",
    "lockfile",
    "compatibility",
    "verified",
    "pipeline",
    "rollback",
    "health",
]

RISK_PATTERNS = [
    ("fake-completion", re.compile(r"\b(fake|pretend|claimed without evidence|not actually wired)\b", re.I)),
    ("demo-only", re.compile(r"\b(demo only|mock only|fixture only|hardcoded for demo|simulation only)\b", re.I)),
    ("placeholder", re.compile(r"\{\{[^}]+\}\}|TODO|FIXME|NotImplementedError|implement later", re.I)),
    ("fallback-only", re.compile(r"\b(fallback only|devmode fallback|temporary fallback|happy path only)\b", re.I)),
]

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".cs",
    ".rb",
}

EXCLUDED_DIRS = {
    ".git",
    ".vibeos/cache",
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".next",
    ".venv",
    "__pycache__",
}

GENERATED_REVIEW_ARTIFACTS = {
    "docs/evidence/RED-TEAM-REPORT.md",
    "EVIDENCE-DOSSIER.md",
}


def is_excluded(path: Path, project_dir: Path) -> bool:
    rel = path.relative_to(project_dir)
    if str(rel) in GENERATED_REVIEW_ARTIFACTS:
        return True
    parts = set(rel.parts)
    if parts & EXCLUDED_DIRS:
        return True
    return any(str(rel).startswith(prefix + "/") for prefix in EXCLUDED_DIRS if "/" in prefix)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def mission_findings(project_dir: Path):
    findings = []
    mission = project_dir / "MISSION.md"
    if not mission.exists():
        return [
            {
                "id": "COMP-MISSION-MISSING",
                "severity": "high",
                "file": "MISSION.md",
                "message": "MISSION.md is required for VibOS Comp gauntlet validation.",
            }
        ]

    text = read_text(mission)
    for section in REQUIRED_MISSION_SECTIONS:
        if section not in text:
            findings.append(
                {
                    "id": "COMP-MISSION-SECTION",
                    "severity": "high",
                    "file": "MISSION.md",
                    "message": f"Missing required mission section: {section}",
                }
            )

    lower = text.lower()
    missing_terms = [term for term in FOUNDATION_TERMS if term not in lower]
    if missing_terms:
        findings.append(
            {
                "id": "COMP-FOUNDATION-TERMS",
                "severity": "high",
                "file": "MISSION.md",
                "message": "Enterprise foundation baseline is missing: " + ", ".join(missing_terms),
            }
        )

    return findings


def risk_pattern_findings(project_dir: Path):
    findings = []
    for path in project_dir.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        if is_excluded(path, project_dir):
            continue

        text = read_text(path)
        rel = str(path.relative_to(project_dir))
        for label, pattern in RISK_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "id": f"COMP-AI-{label.upper()}",
                        "severity": "high",
                        "file": rel,
                        "line": line,
                        "message": f"Potential AI failure mode marker detected: {label}",
                    }
                )
    return findings


def load_registry(project_dir: Path):
    registry = project_dir / ".vibeos/reference/comp/ai-failure-modes.json"
    if not registry.exists():
        return None
    try:
        return json.loads(read_text(registry))
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--threshold", default="design_partner_mvp")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    findings = mission_findings(project_dir) + risk_pattern_findings(project_dir)
    payload = {
        "status": "fail" if findings else "pass",
        "threshold": args.threshold,
        "registry_loaded": load_registry(project_dir) is not None,
        "findings": findings,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    elif findings:
        print("[validate-comp-ai-failure-modes] FAIL: Comp AI failure mode risks detected")
        for finding in findings:
            location = finding["file"]
            if "line" in finding:
                location += f":{finding['line']}"
            print(f"- {finding['id']} [{finding['severity']}]: {location} - {finding['message']}")
    else:
        print("[validate-comp-ai-failure-modes] PASS: Comp mission and AI failure markers look clean")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
