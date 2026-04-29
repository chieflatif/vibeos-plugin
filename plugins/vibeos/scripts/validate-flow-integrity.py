#!/usr/bin/env python3
"""Validate VibOS Comp mission artifacts for user-flow integrity."""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## Mission Promise",
    "## Core Workflow",
    "## Acceptance Criteria",
]

FLOW_TERMS = ["user", "workflow", "auth", "backend", "data", "error", "evidence"]


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def core_workflow_steps(text: str) -> int:
    match = re.search(r"## Core Workflow(?P<body>.*?)(?:\n## |\Z)", text, re.S)
    if not match:
        return 0
    body = match.group("body")
    return len(re.findall(r"(?m)^\s*(?:\d+\.|-)\s+\S+", body))


def validate(project_dir: Path):
    findings = []
    mission_path = project_dir / "MISSION.md"
    mission = read(mission_path)
    if not mission:
        return [
            {
                "id": "FLOW-MISSION-MISSING",
                "severity": "critical",
                "file": "MISSION.md",
                "message": "MISSION.md is required to validate user-flow integrity.",
            }
        ]

    for section in REQUIRED_SECTIONS:
        if section not in mission:
            findings.append(
                {
                    "id": "FLOW-MISSION-SECTION",
                    "severity": "high",
                    "file": "MISSION.md",
                    "message": f"Missing required flow section: {section}",
                }
            )

    if core_workflow_steps(mission) < 2:
        findings.append(
            {
                "id": "FLOW-CORE-WORKFLOW",
                "severity": "high",
                "file": "MISSION.md",
                "message": "Core workflow must contain at least two concrete user-flow steps.",
            }
        )

    lower = mission.lower()
    missing_terms = [term for term in FLOW_TERMS if term not in lower]
    if missing_terms:
        findings.append(
            {
                "id": "FLOW-HANDOFF-CONTEXT",
                "severity": "medium",
                "file": "MISSION.md",
                "message": "Mission does not explicitly describe flow handoff context: " + ", ".join(missing_terms),
            }
        )

    scorecard = read(project_dir / "SCORECARD.md")
    if scorecard and "Flow Integrity" not in scorecard:
        findings.append(
            {
                "id": "FLOW-SCORECARD-MISSING",
                "severity": "medium",
                "file": "SCORECARD.md",
                "message": "SCORECARD.md should include a Flow Integrity dimension.",
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
    payload = {"status": status, "findings": findings}
    if args.json:
        print(json.dumps(payload, indent=2))
    elif findings:
        label = "FAIL" if blocking else "WARN"
        print(f"[validate-flow-integrity] {label}: user-flow integrity findings detected")
        for finding in findings:
            print(f"- {finding['id']} [{finding['severity']}]: {finding['file']} - {finding['message']}")
    else:
        print("[validate-flow-integrity] PASS: mission flow integrity looks explicit")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
