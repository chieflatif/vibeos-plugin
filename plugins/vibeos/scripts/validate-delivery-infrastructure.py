#!/usr/bin/env python3
"""Validate VibOS Comp delivery infrastructure artifacts."""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_MISSION_SECTIONS = [
    "## Mission Promise",
    "## Delivery Infrastructure",
    "## Observability And Operations",
    "## Acceptance Criteria",
]

MISSION_TERMS = [
    "ci",
    "pipeline",
    "deploy",
    "environment",
    "secret",
    "observability",
    "health",
    "smoke",
    "rollback",
    "runbook",
]

EVIDENCE_TERMS = [
    "ci",
    "pipeline",
    "deploy",
    "environment",
    "secret",
    "observability",
    "health",
    "smoke",
    "rollback",
    "runbook",
]

CI_FILES = [
    ".github/workflows",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
    "Jenkinsfile",
    ".circleci/config.yml",
]

DEPLOYMENT_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "vercel.json",
    "netlify.toml",
    "fly.toml",
    "render.yaml",
    "railway.json",
    "wrangler.toml",
    "Procfile",
    "serverless.yml",
    "serverless.yaml",
]


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def exists_any(project_dir: Path, rels):
    found = []
    for rel in rels:
        path = project_dir / rel
        if path.exists():
            found.append(rel)
    if any(project_dir.rglob("*.tf")):
        found.append("terraform")
    if any(project_dir.rglob("pulumi.*")):
        found.append("pulumi")
    if any(project_dir.rglob("kustomization.yaml")) or any(project_dir.rglob("Chart.yaml")):
        found.append("kubernetes")
    return found


def section_item_count(text: str, section: str) -> int:
    match = re.search(rf"{re.escape(section)}(?P<body>.*?)(?:\n## |\Z)", text, re.S)
    if not match:
        return 0
    body = match.group("body")
    return len(re.findall(r"(?m)^\s*(?:-|\d+\.|\|)\s*\S+", body))


def validate(project_dir: Path):
    findings = []
    mission = read(project_dir / "MISSION.md")
    if not mission:
        return [
            {
                "id": "DELIVERY-MISSION-MISSING",
                "severity": "critical",
                "file": "MISSION.md",
                "message": "MISSION.md is required to validate delivery infrastructure.",
            }
        ]

    for section in REQUIRED_MISSION_SECTIONS:
        if section not in mission:
            findings.append(
                {
                    "id": "DELIVERY-MISSION-SECTION",
                    "severity": "high",
                    "file": "MISSION.md",
                    "message": f"Missing required delivery section: {section}",
                }
            )

    if "## Delivery Infrastructure" in mission and section_item_count(mission, "## Delivery Infrastructure") < 4:
        findings.append(
            {
                "id": "DELIVERY-MISSION-ITEMS",
                "severity": "high",
                "file": "MISSION.md",
                "message": "Delivery Infrastructure must list at least four concrete controls.",
            }
        )

    lower = mission.lower()
    missing_terms = [term for term in MISSION_TERMS if term not in lower]
    if missing_terms:
        findings.append(
            {
                "id": "DELIVERY-CONTEXT-TERMS",
                "severity": "medium",
                "file": "MISSION.md",
                "message": "Mission does not explicitly describe delivery context: " + ", ".join(missing_terms),
            }
        )

    ci_files = exists_any(project_dir, CI_FILES)
    deployment_files = exists_any(project_dir, DEPLOYMENT_FILES)

    evidence_path = project_dir / "docs/evidence/DELIVERY-INFRASTRUCTURE.md"
    evidence = read(evidence_path)
    if not evidence:
        findings.append(
            {
                "id": "DELIVERY-EVIDENCE-MISSING",
                "severity": "high",
                "file": "docs/evidence/DELIVERY-INFRASTRUCTURE.md",
                "message": "Delivery infrastructure evidence is required for VibOS Comp completion.",
            }
        )
    else:
        evidence_lower = evidence.lower()
        missing_evidence_terms = [term for term in EVIDENCE_TERMS if term not in evidence_lower]
        if missing_evidence_terms:
            findings.append(
                {
                    "id": "DELIVERY-EVIDENCE-CONTEXT",
                    "severity": "high",
                    "file": "docs/evidence/DELIVERY-INFRASTRUCTURE.md",
                    "message": "Delivery evidence is missing context: " + ", ".join(missing_evidence_terms),
                }
            )

    if ci_files and evidence and "test" not in evidence.lower():
        findings.append(
            {
                "id": "DELIVERY-PIPELINE-GATES",
                "severity": "high",
                "file": "docs/evidence/DELIVERY-INFRASTRUCTURE.md",
                "message": "CI/CD files exist but delivery evidence does not mention tests or gates in the pipeline.",
            }
        )

    if deployment_files and evidence and "rollback" not in evidence.lower():
        findings.append(
            {
                "id": "DELIVERY-ROLLBACK-MISSING",
                "severity": "high",
                "file": "docs/evidence/DELIVERY-INFRASTRUCTURE.md",
                "message": "Deployment files exist but delivery evidence does not document rollback or recovery.",
            }
        )

    scorecard = read(project_dir / "SCORECARD.md")
    if scorecard and "Delivery Infrastructure" not in scorecard:
        findings.append(
            {
                "id": "DELIVERY-SCORECARD-MISSING",
                "severity": "medium",
                "file": "SCORECARD.md",
                "message": "SCORECARD.md should include a Delivery Infrastructure dimension.",
            }
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    findings = validate(project_dir)
    blocking = any(f["severity"] in {"critical", "high"} for f in findings)
    status = "fail" if blocking else "warn" if findings else "pass"
    payload = {
        "status": status,
        "findings": findings,
        "detected_ci_files": exists_any(project_dir, CI_FILES),
        "detected_deployment_files": exists_any(project_dir, DEPLOYMENT_FILES),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif findings:
        label = "FAIL" if blocking else "WARN"
        print(f"[validate-delivery-infrastructure] {label}: delivery infrastructure findings detected")
        for finding in findings:
            print(f"- {finding['id']} [{finding['severity']}]: {finding['file']} - {finding['message']}")
    else:
        print("[validate-delivery-infrastructure] PASS: delivery infrastructure looks explicit")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
