#!/usr/bin/env python3
"""Check VibOS Comp integration readiness from COMP-PLAN and worktree scopes."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def evidence_exists(project_dir: Path, wo_id: str) -> bool:
    evidence_root = project_dir / "docs/evidence"
    candidates = [
        evidence_root / f"{wo_id}.md",
        evidence_root / wo_id,
        evidence_root / wo_id.lower(),
    ]
    return any(path.exists() for path in candidates)


def collect_packages(project_dir: Path):
    scopes_path = project_dir / ".vibeos/worktree-scopes.json"
    if not scopes_path.exists():
        raise FileNotFoundError(".vibeos/worktree-scopes.json is required")

    scopes = load_json(scopes_path)
    packages = []
    for branch, scope in sorted(scopes.get("branches", {}).items()):
        for wo_id in scope.get("wo_ids", []):
            packages.append(
                {
                    "wo_id": wo_id,
                    "branch": branch,
                    "description": scope.get("description", ""),
                    "exclusive_paths": scope.get("exclusive_paths", []),
                    "evidence": evidence_exists(project_dir, wo_id),
                }
            )
    return packages, scopes


def render_evidence(project_dir: Path, status: str, packages, missing, scopes):
    evidence_dir = project_dir / "docs/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Comp Integration Evidence",
        "",
        "## Status",
        "",
        f"`{status}`",
        "",
        "## Inputs",
        "",
        "- `MISSION.md`",
        "- `COMP-PLAN.md`",
        "- `.vibeos/worktree-scopes.json`",
        "- Flow integrity evidence",
        "- System invariant evidence",
        "- Dependency intelligence evidence",
        "- Delivery infrastructure evidence",
        "",
        "## Work Package Evidence",
        "",
        "| WO | Branch | Evidence Status | Notes |",
        "|---|---|---|---|",
    ]
    for package in packages:
        evidence_status = "present" if package["evidence"] else "missing"
        notes = package["description"] or "No description"
        lines.append(f"| {package['wo_id']} | `{package['branch']}` | {evidence_status} | {notes} |")

    lines.extend([
        "",
        "## Shared Path Risks",
        "",
    ])
    for path in scopes.get("shared_paths", []):
        lines.append(f"- `{path}`")

    lines.extend([
        "",
        "## Unresolved Risks",
        "",
    ])
    if missing:
        for wo_id in missing:
            lines.append(f"- `{wo_id}` is missing required integration evidence.")
    else:
        lines.append("- No missing work package evidence detected by this check.")

    lines.extend([
        "",
        "## Required Integrated Checks",
        "",
        "- Cross-boundary contracts",
        "- Flow integrity and objective fidelity",
        "- System invariants and state safety",
        "- Dependency intelligence current-source, compatibility, lockfile, audit, and upgrade-path evidence",
        "- Delivery infrastructure CI/CD, deployment, observability, smoke, rollback, and runbook evidence",
        "- Full relevant test suite",
        "- `comp_gauntlet`",
        "- Security and observability checks",
        "",
        "## Completion Claim",
        "",
        "Integration is not complete until the required integrated checks above have passing evidence.",
        "",
        f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_",
        "",
    ])
    (evidence_dir / "COMP-INTEGRATION-EVIDENCE.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    required = [project_dir / "MISSION.md", project_dir / "COMP-PLAN.md"]
    missing_inputs = [str(path.relative_to(project_dir)) for path in required if not path.exists()]
    if missing_inputs:
        payload = {"status": "fail", "missing_inputs": missing_inputs, "missing_evidence": []}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print("[comp-integration-check] FAIL: missing inputs: " + ", ".join(missing_inputs), file=sys.stderr)
        return 1

    try:
        packages, scopes = collect_packages(project_dir)
    except (FileNotFoundError, ValueError) as exc:
        payload = {"status": "fail", "error": str(exc), "missing_evidence": []}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"[comp-integration-check] FAIL: {exc}", file=sys.stderr)
        return 1

    missing = [package["wo_id"] for package in packages if not package["evidence"]]
    status = "blocked" if missing else "ready_for_integrated_checks"
    render_evidence(project_dir, status, packages, missing, scopes)

    payload = {
        "status": status,
        "packages": packages,
        "missing_evidence": missing,
        "evidence_file": "docs/evidence/COMP-INTEGRATION-EVIDENCE.md",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif missing:
        print("[comp-integration-check] FAIL: missing package evidence: " + ", ".join(missing))
    else:
        print("[comp-integration-check] PASS: package evidence is present; run integrated checks next")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
