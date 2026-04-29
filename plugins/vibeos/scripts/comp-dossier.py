#!/usr/bin/env python3
"""Generate a concise VibOS Comp evidence dossier."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ARTIFACTS = [
    ("MISSION.md", "Mission and foundation baseline"),
    ("COMP-PLAN.md", "Work package and worktree plan"),
    ("SCORECARD.md", "Dimension scorecard"),
    ("docs/evidence/FLOW-INTEGRITY.md", "Primary user-flow and objective fidelity evidence"),
    ("docs/evidence/SYSTEM-INVARIANTS.md", "System invariant and state safety evidence"),
    ("docs/evidence/DEPENDENCY-INTELLIGENCE.md", "Dependency current-source, compatibility, lockfile, audit, and upgrade evidence"),
    ("docs/evidence/DELIVERY-INFRASTRUCTURE.md", "CI/CD, deployment, observability, smoke, rollback, and runbook evidence"),
    ("docs/evidence/COMP-INTEGRATION-EVIDENCE.md", "Integration evidence"),
    ("docs/evidence/RED-TEAM-REPORT.md", "Adversarial review"),
]


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def status_from_markdown(text: str) -> str:
    match = re.search(r"## Status\s+`([^`]+)`", text, re.I)
    return match.group(1).lower() if match else "unknown"


def artifact_rows(project_dir: Path):
    rows = []
    for rel, purpose in ARTIFACTS:
        path = project_dir / rel
        text = read(path)
        status = status_from_markdown(text) if text else "missing"
        if status == "unknown" and text:
            status = "present"
        rows.append((rel, purpose, status))
    return rows


def claim_states(rows):
    states = []
    for rel, purpose, status in rows:
        if status in {"pass", "reviewed", "ready_for_integrated_checks", "present"}:
            state = "proven"
        elif status in {"warn", "blocked", "fail", "missing"}:
            state = "partial"
        else:
            state = "partial"
        states.append((purpose, state, rel))
    return states


def speed_metrics(project_dir: Path) -> str:
    build_log = project_dir / ".vibeos/build-log.md"
    if not build_log.exists():
        return "- Speed metrics not captured in `.vibeos/build-log.md`."
    text = read(build_log)
    wo_count = len(re.findall(r"\bWO-[0-9]+", text))
    return f"- Build log present. Work order references captured: {wo_count}."


def residual_risks(project_dir: Path) -> list:
    risks = []
    for rel in ["SCORECARD.md", "docs/evidence/RED-TEAM-REPORT.md", "docs/evidence/COMP-INTEGRATION-EVIDENCE.md"]:
        text = read(project_dir / rel)
        for line in text.splitlines():
            lower = line.lower()
            if any(term in lower for term in ["risk", "blocked", "fail", "missing", "accepted"]):
                risks.append(f"`{rel}`: {line.strip()}")
    return risks[:20]


def render(project_dir: Path):
    rows = artifact_rows(project_dir)
    states = claim_states(rows)
    missing_required = [rel for rel, _, status in rows if status == "missing" and rel in {"MISSION.md", "SCORECARD.md"}]
    scorecard_status = next((status for rel, _, status in rows if rel == "SCORECARD.md"), "missing")
    red_team_status = next((status for rel, _, status in rows if rel == "docs/evidence/RED-TEAM-REPORT.md"), "missing")
    overall = "proven" if scorecard_status == "pass" and red_team_status == "reviewed" and not missing_required else "partial"

    lines = [
        "# VibOS Comp Evidence Dossier",
        "",
        "## Executive Summary",
        "",
        f"Overall completion state: `{overall}`. This dossier summarizes the artifacts and evidence available for review.",
        "",
        "## Claim States",
        "",
        "| Claim | State | Evidence |",
        "|---|---|---|",
    ]
    for claim, state, rel in states:
        lines.append(f"| {claim} | {state} | `{rel}` |")

    lines.extend(["", "## Artifact Index", "", "| Artifact | Purpose | Status |", "|---|---|---|"])
    for rel, purpose, status in rows:
        lines.append(f"| `{rel}` | {purpose} | {status} |")

    lines.extend(["", "## Speed And Rework Metrics", "", speed_metrics(project_dir), "", "## Residual Risks", ""])
    risks = residual_risks(project_dir)
    if risks:
        lines.extend(f"- {risk}" for risk in risks)
    else:
        lines.append("- No residual risks detected in scorecard, integration evidence, or red-team report text.")

    lines.extend([
        "",
        "## Completion Boundary",
        "",
        "This dossier is a review index. It does not replace raw test output, audit artifacts, screenshots, logs, or deployment evidence.",
        "",
        f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_",
        "",
    ])
    return overall, "\n".join(lines), missing_required


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    overall, dossier, missing_required = render(project_dir)
    out = project_dir / "EVIDENCE-DOSSIER.md"
    out.write_text(dossier, encoding="utf-8")
    payload = {"status": overall, "dossier": "EVIDENCE-DOSSIER.md", "missing_required": missing_required}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"[comp-dossier] {overall.upper()}: wrote EVIDENCE-DOSSIER.md")
    return 1 if missing_required else 0


if __name__ == "__main__":
    sys.exit(main())
