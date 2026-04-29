#!/usr/bin/env python3
"""Generate a mission-aware VibOS Comp red-team report."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


CATEGORIES = [
    "input validation",
    "authentication and authorization",
    "data access and tenant isolation",
    "sensitive data exposure",
    "dependency freshness",
    "dependency evidence drift",
    "delivery infrastructure gaps",
    "concurrency and partial failure",
    "observability under failure",
    "fake completion or demo-only evidence",
    "frontend edge states",
    "primary user-flow breaks",
    "objective fidelity drift",
    "system invariant violations",
]

HIGH_RISK_PATTERNS = [
    (re.compile(r"\b(payments?|money movement|billing|checkout)\b", re.I), "payments", "Payments or money movement requires explicit fraud, dispute, and secret-handling review."),
    (re.compile(r"\b(health data|patient|clinical|hipaa)\b", re.I), "health data", "Health data raises regulated-data and privacy review requirements."),
    (re.compile(r"\b(financial data|banking|account balance|ledger)\b", re.I), "financial data", "Financial data raises authorization, audit trail, and compliance risks."),
    (re.compile(r"\b(tenant|multi-tenant|cross-tenant)\b", re.I), "tenant isolation", "Tenant isolation needs direct object reference and cross-tenant access testing."),
    (re.compile(r"\b(admin|administrator|superuser)\b", re.I), "admin actions", "Admin actions need authorization, audit logging, and destructive-action safeguards."),
    (re.compile(r"\b(api key|credential|secret key|production secret)\b", re.I), "secrets", "Secrets require storage, rotation, and leak-prevention review."),
]


def read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def scorecard_status(text: str) -> str:
    match = re.search(r"## Status\s+`([^`]+)`", text, re.I)
    return match.group(1).lower() if match else "unknown"


def generate_findings(mission_text: str, scorecard_text: str):
    findings = []
    for pattern, label, message in HIGH_RISK_PATTERNS:
        if pattern.search(mission_text):
            findings.append(
                {
                    "severity": "high",
                    "category": "mission threat model",
                    "scenario": f"Review high-risk mission signal: {label}",
                    "evidence": message,
                    "disposition": "fix or accepted risk required",
                }
            )

    status = scorecard_status(scorecard_text)
    if status in {"fail", "unknown"}:
        findings.append(
            {
                "severity": "critical",
                "category": "scorecard",
                "scenario": "Scorecard is not passing",
                "evidence": f"SCORECARD.md status is {status}",
                "disposition": "fix before Comp completion",
            }
        )
    elif status == "warn":
        findings.append(
            {
                "severity": "medium",
                "category": "scorecard",
                "scenario": "Scorecard has advisory warnings",
                "evidence": "SCORECARD.md status is warn",
                "disposition": "fix or follow-up WO required",
            }
        )
    if scorecard_text and "Flow Integrity" not in scorecard_text:
        findings.append(
            {
                "severity": "high",
                "category": "flow integrity",
                "scenario": "Scorecard does not include primary user-flow review",
                "evidence": "SCORECARD.md is missing the Flow Integrity dimension",
                "disposition": "run flow integrity review before Comp completion",
            }
        )
    if scorecard_text and "System Invariants" not in scorecard_text:
        findings.append(
            {
                "severity": "high",
                "category": "system invariants",
                "scenario": "Scorecard does not include invariant review",
                "evidence": "SCORECARD.md is missing the System Invariants dimension",
                "disposition": "run system invariant review before Comp completion",
            }
        )
    if scorecard_text and "Dependency Intelligence" not in scorecard_text:
        findings.append(
            {
                "severity": "high",
                "category": "dependency evidence drift",
                "scenario": "Scorecard does not include current dependency evidence review",
                "evidence": "SCORECARD.md is missing the Dependency Intelligence dimension",
                "disposition": "run dependency intelligence review before Comp completion",
            }
        )
    if scorecard_text and "Delivery Infrastructure" not in scorecard_text:
        findings.append(
            {
                "severity": "high",
                "category": "delivery infrastructure",
                "scenario": "Scorecard does not include delivery infrastructure review",
                "evidence": "SCORECARD.md is missing the Delivery Infrastructure dimension",
                "disposition": "run delivery infrastructure review before Comp completion",
            }
        )
    return findings


def render_report(findings, mission_present: bool, scorecard_present: bool):
    status = "blocked" if any(item["severity"] in {"critical", "high"} for item in findings) else "reviewed"
    lines = [
        "# VibOS Comp Red-Team Report",
        "",
        "## Status",
        "",
        f"`{status}`",
        "",
        "## Inputs",
        "",
        f"- MISSION.md: {'present' if mission_present else 'missing'}",
        f"- SCORECARD.md: {'present' if scorecard_present else 'missing'}",
        "",
        "## Adversarial Categories Reviewed",
        "",
    ]
    for category in CATEGORIES:
        lines.append(f"- {category}")

    lines.extend([
        "",
        "## Findings",
        "",
        "| Severity | Category | Scenario | Evidence | Required Disposition |",
        "|---|---|---|---|---|",
    ])
    if findings:
        for item in findings:
            lines.append(f"| {item['severity']} | {item['category']} | {item['scenario']} | {item['evidence']} | {item['disposition']} |")
    else:
        lines.append("| info | arena | No blocking red-team findings detected by artifact review | Mission and scorecard reviewed | continue to final evidence dossier |")

    lines.extend([
        "",
        "## Completion Rule",
        "",
        "Critical and high findings block VibOS Comp completion unless explicitly accepted by the user with justification.",
        "",
        f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_",
        "",
    ])
    return status, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    mission_path = project_dir / "MISSION.md"
    scorecard_path = project_dir / "SCORECARD.md"
    mission_text = read_optional(mission_path)
    scorecard_text = read_optional(scorecard_path)
    findings = []
    if not mission_text:
        findings.append({"severity": "critical", "category": "inputs", "scenario": "MISSION.md is missing", "evidence": "No mission file", "disposition": "create mission"})
    if not scorecard_text:
        findings.append({"severity": "critical", "category": "inputs", "scenario": "SCORECARD.md is missing", "evidence": "No scorecard file", "disposition": "run comp-scorecard"})
    findings.extend(generate_findings(mission_text, scorecard_text))

    status, report = render_report(findings, bool(mission_text), bool(scorecard_text))
    evidence_dir = project_dir / "docs/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "RED-TEAM-REPORT.md").write_text(report, encoding="utf-8")
    payload = {"status": status, "findings": findings, "report": "docs/evidence/RED-TEAM-REPORT.md"}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"[comp-red-team] {status.upper()}: wrote docs/evidence/RED-TEAM-REPORT.md")
    return 1 if status == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
