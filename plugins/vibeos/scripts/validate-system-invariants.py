#!/usr/bin/env python3
"""Validate VibOS Comp mission artifacts for explicit system invariants."""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## Mission Promise",
    "## Core Workflow",
    "## System Invariants",
    "## Acceptance Criteria",
]

INVARIANT_TERMS = ["invariant", "state", "auth", "data", "error", "recovery", "evidence"]


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def invariant_items(text: str) -> int:
    match = re.search(r"## System Invariants(?P<body>.*?)(?:\n## |\Z)", text, re.S)
    if not match:
        return 0
    body = match.group("body")
    return len(re.findall(r"(?m)^\s*(?:-|\d+\.)\s+\S+", body))


def validate(project_dir: Path):
    findings = []
    mission_path = project_dir / "MISSION.md"
    mission = read(mission_path)
    if not mission:
        return [
            {
                "id": "INV-MISSION-MISSING",
                "severity": "critical",
                "file": "MISSION.md",
                "message": "MISSION.md is required to validate system invariants.",
            }
        ]

    for section in REQUIRED_SECTIONS:
        if section not in mission:
            findings.append(
                {
                    "id": "INV-MISSION-SECTION",
                    "severity": "high",
                    "file": "MISSION.md",
                    "message": f"Missing required invariant section: {section}",
                }
            )

    if "## System Invariants" in mission and invariant_items(mission) < 3:
        findings.append(
            {
                "id": "INV-ITEM-COUNT",
                "severity": "high",
                "file": "MISSION.md",
                "message": "System Invariants must list at least three concrete invariants.",
            }
        )

    lower = mission.lower()
    missing_terms = [term for term in INVARIANT_TERMS if term not in lower]
    if missing_terms:
        findings.append(
            {
                "id": "INV-CONTEXT-TERMS",
                "severity": "medium",
                "file": "MISSION.md",
                "message": "Mission does not explicitly describe invariant context: " + ", ".join(missing_terms),
            }
        )

    scorecard = read(project_dir / "SCORECARD.md")
    if scorecard and "System Invariants" not in scorecard:
        findings.append(
            {
                "id": "INV-SCORECARD-MISSING",
                "severity": "medium",
                "file": "SCORECARD.md",
                "message": "SCORECARD.md should include a System Invariants dimension.",
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
        print(f"[validate-system-invariants] {label}: system invariant findings detected")
        for finding in findings:
            print(f"- {finding['id']} [{finding['severity']}]: {finding['file']} - {finding['message']}")
    else:
        print("[validate-system-invariants] PASS: mission system invariants look explicit")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
