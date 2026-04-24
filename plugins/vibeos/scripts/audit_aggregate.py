#!/usr/bin/env python3
"""VibeOS audit aggregator.

Reads per-auditor findings files under a dispatch directory, validates
completeness, computes severity totals, applies basic blocking logic,
and writes summary.json plus findings.md.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FRAMEWORK_VERSION = "2.2.0"
SECTION_RE = re.compile(r"^##\s+(Critical|Major|Minor|Informational)\b", re.IGNORECASE)
FINDING_RE = re.compile(r"^###\s+F-\d+")
PHASE_LEVEL_TRIGGERS = ("phase-exit", "live-fire", "security-change", "canon-revision")


def run(audit_dir: Path) -> int:
    summary_path = audit_dir / "summary.json"
    findings_path = audit_dir / "findings.md"
    dispatch_path = audit_dir / "dispatch-manifest.json"

    with dispatch_path.open(encoding="utf-8") as handle:
        dispatch = json.load(handle)

    required = set(dispatch.get("required_auditors", []))
    companion_required = dispatch.get("companion_required", "none")

    present_files = {
        path.stem.replace("-findings", ""): path for path in audit_dir.glob("*-findings.md")
    }
    present_auditors = set(present_files.keys()) - {"companion"}
    missing_required = sorted(required - present_auditors)
    companion_present = "companion" in present_files

    if missing_required:
        print("ERROR: required findings files missing:", file=sys.stderr)
        for auditor in missing_required:
            print(f"  - {auditor}-findings.md", file=sys.stderr)
        return 1

    if companion_required == "mandatory" and not companion_present:
        print("ERROR: companion-findings.md missing", file=sys.stderr)
        return 1

    structural_failures: list[str] = []
    required_sections = ("critical", "major", "minor", "informational")
    for path in present_files.values():
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            structural_failures.append(f"{path.name}: empty file")
            continue
        lines_lower = {line.strip().lower() for line in text.splitlines()}
        missing_sections = [section for section in required_sections if f"## {section}" not in lines_lower]
        if missing_sections:
            structural_failures.append(f"{path.name}: missing sections {missing_sections}")

    if structural_failures:
        print("ERROR: findings files fail structural validation:", file=sys.stderr)
        for failure in structural_failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    sev_counts: dict[str, dict[str, int]] = {}
    total = {"critical": 0, "major": 0, "minor": 0, "informational": 0}
    composite_lines: list[str] = []

    for auditor_name in sorted(present_files):
        findings_file = present_files[auditor_name]
        text = findings_file.read_text(encoding="utf-8")
        counts = {"critical": 0, "major": 0, "minor": 0, "informational": 0}
        section: str | None = None
        for line in text.splitlines():
            stripped = line.strip()
            section_match = SECTION_RE.match(stripped)
            if section_match:
                section = section_match.group(1).lower()
                continue
            if section and FINDING_RE.match(stripped):
                counts[section] += 1
        sev_counts[auditor_name] = counts
        for severity, count in counts.items():
            total[severity] += count
        composite_lines.append(f"## {auditor_name} — {counts}")
        composite_lines.append("")
        composite_lines.append(text)
        composite_lines.append("")

    trigger = dispatch.get("trigger", "")
    tier_val = str(dispatch.get("tier", ""))
    blocking_critical = total["critical"] > 0
    blocking_major = total["major"] > 0 and (
        trigger in PHASE_LEVEL_TRIGGERS or (trigger == "wo-exit" and tier_val in ("3", "4"))
    )
    blocking = blocking_critical or blocking_major

    summary = {
        "dispatch_id": audit_dir.name,
        "trigger": dispatch.get("trigger"),
        "tier": dispatch.get("tier"),
        "phase": dispatch.get("phase"),
        "auditors": sev_counts,
        "totals": total,
        "blocking": blocking,
        "notes": {
            "blocking_reason": (
                "critical finding present"
                if blocking_critical
                else "major finding at blocking tier/phase"
                if blocking_major
                else "none"
            ),
            "required_auditors_present": True,
            "companion_present": companion_present,
        },
    }

    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    findings_path.write_text("\n".join(composite_lines) + "\n", encoding="utf-8")
    print(f"summary: {summary_path}")
    print(f"findings: {findings_path}")
    print(f"totals: {total}")
    print(f"blocking: {blocking}")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: audit_aggregate.py <audit_dir>", file=sys.stderr)
        return 2
    audit_dir = Path(sys.argv[1])
    if not audit_dir.is_dir():
        print(f"error: audit dir not found: {audit_dir}", file=sys.stderr)
        return 1
    return run(audit_dir)


if __name__ == "__main__":
    raise SystemExit(main())
